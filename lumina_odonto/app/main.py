"""Lumina Odonto: API baseada nas colunas reais de sql/schema.sql."""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import os
import jwt
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from app.opencl_search import OpenCLSearch, OpenCLUnavailable, sequential_search, normalize
from app.config import settings

DATABASE_URL = settings.database_url
JWT_SECRET = settings.jwt_secret
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
hasher = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
app = FastAPI(title='Lumina Odonto - API REST', version='2.0.0')
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in os.getenv('CORS_ORIGINS','http://localhost:3000').split(',') if x.strip()], allow_methods=['GET','POST','PATCH','DELETE'], allow_headers=['Authorization','Content-Type'])

@app.exception_handler(RequestValidationError)
async def private_validation_error(request: Request, exc: RequestValidationError):
    # Never return input, context, custom messages or arbitrary field names.
    known = {'body', 'query', 'path', 'header', 'patient_id', 'dentist_id',
             'description', 'notes', 'procedure_performed', 'appointment_id',
             'version', 'q', 'engine_name', 'offset', 'limit', 'email', 'password',
             'new_password', 'scheduled_at', 'duration_minutes', 'status',
             'full_name', 'cpf', 'birth_date', 'medical_record_number', 'action'}
    return JSONResponse(status_code=422, content={'detail': [
        {'loc': [part if isinstance(part, str) and part in known else 'field'
                 for part in error['loc']], 'msg': 'Campo ausente ou inválido',
         'type': 'validation_error'} for error in exc.errors()]})

class Login(BaseModel):
    email: str
    password: str
class Unlock(BaseModel):
    password: str
class PatientIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    cpf: str = Field(pattern=r'^\d{11}$')
    medical_record_number: str = Field(min_length=1, max_length=30)
    birth_date: str
class AppointmentIn(BaseModel):
    patient_id: int
    dentist_id: int
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, gt=0)
    notes: str | None = None
class EvolutionIn(BaseModel):
    patient_id: int
    description: str = Field(min_length=1)
    appointment_id: int | None = None
    procedure_performed: str | None = None
    notes: str | None = None
class EvolutionPatch(BaseModel):
    version: int = Field(ge=1, strict=True)
    description: str | None = None
    procedure_performed: str | None = None
    notes: str | None = None
class FinalizeIn(BaseModel):
    version: int = Field(ge=1, strict=True)
class AdminAccess(BaseModel):
    patient_id: int
    dentist_id: int
    action: str
class PasswordReset(BaseModel):
    new_password: str = Field(min_length=12)

def db_dep():
    with SessionLocal() as db:
        yield db

def one(db, query, **kwargs):
    return db.execute(text(query), kwargs).mappings().first()

def allrows(db, query, **kwargs):
    return [dict(r) for r in db.execute(text(query), kwargs).mappings().all()]

def require(condition, status=403, message='Acesso negado'):
    if not condition:
        raise HTTPException(status, message)

def token(user, kind, minutes):
    require(bool(JWT_SECRET) and len(JWT_SECRET) >= 32, 503, 'JWT_SECRET não configurado')
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': str(user['id']), 'clinic_id': user['clinic_id'], 'type': kind,
                       'session_version': user['session_version'], 'clinical_version': user['clinical_version'],
                       'iat': now, 'exp': now + timedelta(minutes=minutes)}, JWT_SECRET, algorithm='HS256')

def identity(kind):
    def dependency(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(db_dep)):
        require(creds is not None, 401, 'Token necessário')
        require(bool(JWT_SECRET) and len(JWT_SECRET) >= 32, 503, 'JWT_SECRET não configurado')
        try:
            payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=['HS256'])
            require(payload.get('type') == kind, 401, 'Tipo de token incorreto')
            user = one(db, 'SELECT * FROM users WHERE id=:id', id=int(payload['sub']))
        except (jwt.PyJWTError, KeyError, ValueError):
            raise HTTPException(401, 'Token inválido ou expirado')
        require(user and user['is_active'] and user['clinic_id'] == payload.get('clinic_id')
                and user['session_version'] == payload.get('session_version'), 401, 'Sessão inválida')
        if kind == 'clinical':
            require(user['role'] == 'DENTIST' and user['clinical_version'] == payload.get('clinical_version'),
                    401, 'Liberação clínica inválida')
        clinic = one(db, 'SELECT is_active FROM clinics WHERE id=:id', id=user['clinic_id'])
        require(clinic and clinic['is_active'], 403, 'Clínica inativa')
        return dict(user)
    return dependency

access_user = identity('access')
clinical_user = identity('clinical')

def dentist_for(db, user):
    d = one(db, 'SELECT id FROM dentists WHERE user_id=:uid', uid=user['id'])
    require(d is not None, 403, 'Perfil profissional inexistente')
    return d['id']

def patient_for(db, clinic_id, patient_id, active=True):
    p = one(db, 'SELECT * FROM patients WHERE id=:id AND clinic_id=:clinic' + (' AND is_active' if active else ''),
            id=patient_id, clinic=clinic_id)
    require(p is not None, 404, 'Paciente não encontrado')
    return p

def dentist_in_clinic(db, clinic_id, dentist_id, active=True):
    d = one(db, '''SELECT d.id FROM dentists d JOIN users u ON u.id=d.user_id
        WHERE d.id=:id AND u.clinic_id=:clinic AND u.role='DENTIST' ''' + (' AND u.is_active' if active else ''),
        id=dentist_id, clinic=clinic_id)
    require(d is not None, 422, 'Dentista incompatível com a clínica')

def link_for(db, clinic_id, patient_id, dentist_id, lock=False):
    query = '''SELECT * FROM clinical_access_links WHERE clinic_id=:clinic
               AND patient_id=:patient AND dentist_id=:dentist'''
    if lock:
        query += ' FOR UPDATE'
    return one(db, query, clinic=clinic_id, patient=patient_id, dentist=dentist_id)

def allowed(db, user, patient_id, lock=False):
    # Check the current state, not the identity snapshot from token decoding.
    dentist = dentist_for(db, user)
    link = link_for(db, user['clinic_id'], patient_id, dentist, lock)
    require(link and link['status'] == 'ACTIVE', 403, 'Acesso clínico não autorizado')
    current = one(db, 'SELECT * FROM users WHERE id=:id', id=user['id'])
    require(current and current['is_active'] and current['role'] == 'DENTIST'
            and current['clinic_id'] == user['clinic_id']
            and current['session_version'] == user['session_version']
            and current['clinical_version'] == user['clinical_version'], 401, 'Sessão inválida')
    clinic = one(db, 'SELECT is_active FROM clinics WHERE id=:id', id=user['clinic_id'])
    require(clinic and clinic['is_active'], 403, 'Clínica inativa')
    patient_for(db, user['clinic_id'], patient_id)
    require(dentist_for(db, user) == dentist, 403, 'Perfil profissional alterado')
    return dentist

def record_for(db, patient_id):
    record = one(db, 'SELECT id FROM medical_records WHERE patient_id=:patient', patient=patient_id)
    require(record is not None, 404, 'Prontuário não encontrado')
    return record['id']

def audit(db, user_id, action, resource, details=''):
    db.execute(text('INSERT INTO audit_logs (user_id,action,resource,details) VALUES (:uid,:action,:resource,:details)'),
               {'uid': user_id, 'action': action, 'resource': resource, 'details': details})

def change_link(db, actor, patient_id, dentist_id, source, action=None, appointment=None):
    clinic = actor['clinic_id']
    revoking = source == "ADMIN" and action == "REVOKED"
    patient_for(db, clinic, patient_id, active=not revoking)
    dentist_in_clinic(db, clinic, dentist_id, active=not revoking)
    # Lock de paciente serializa criação e alteração do vínculo para o mesmo paciente.
    db.execute(text('SELECT id FROM patients WHERE id=:id FOR UPDATE'), {'id': patient_id})
    patient_for(db, clinic, patient_id, active=not revoking)
    link = link_for(db, clinic, patient_id, dentist_id, lock=True)
    if source == 'APPOINTMENT':
        require(appointment is not None, 422, 'Consulta necessária')
        if link and link['status'] == 'ACTIVE':
            return link['id'], False
        action = 'GRANTED' if not link else 'REACTIVATED'
    else:
        require(action in ('GRANTED', 'REVOKED', 'REACTIVATED'), 422, 'Ação inválida')
        if action == 'REVOKED':
            require(link is not None and link['status'] == 'ACTIVE', 409, 'Vínculo não está ativo')
        elif action == 'GRANTED':
            require(link is None, 409, 'Vínculo já existe')
        else:
            require(link is not None and link['status'] == 'REVOKED', 409, 'Vínculo não está revogado')
    status = 'REVOKED' if action == 'REVOKED' else 'ACTIVE'
    if link:
        version = link['version'] + 1
        db.execute(text('UPDATE clinical_access_links SET status=:status,version=:version WHERE id=:id'),
                   {'status': status, 'version': version, 'id': link['id']})
        link_id = link['id']
    else:
        version = 1
        link_id = one(db, '''INSERT INTO clinical_access_links (clinic_id,patient_id,dentist_id,status,version)
            VALUES (:clinic,:patient,:dentist,:status,1) RETURNING id''',
            clinic=clinic, patient=patient_id, dentist=dentist_id, status=status)['id']
    db.execute(text('''INSERT INTO clinical_access_events
        (link_id,action,actor_user_id,appointment_id,source,appointment_scheduled_at,link_version)
        VALUES (:link,:action,:actor,:appointment,:source,:scheduled,:version)'''),
        {'link': link_id, 'action': action, 'actor': actor['id'],
         'appointment': appointment['id'] if appointment else None,
         'source': source, 'scheduled': appointment['scheduled_at'] if appointment else None,
         'version': version})
    audit(db, actor['id'], 'ACCESS_'+action, 'clinical_access_link', str(link_id))
    return link_id, True

@app.get('/health')
def health():
    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))
    return {'status': 'ok', 'database': 'connected'}

@app.post('/api/v1/auth/login')
def login(body: Login, db: Session = Depends(db_dep)):
    user = one(db, 'SELECT * FROM users WHERE email=:email AND is_active', email=body.email)
    require(user and hasher.verify(body.password, user['password_hash']), 401, 'Credenciais inválidas')
    clinic = one(db, 'SELECT is_active FROM clinics WHERE id=:id', id=user['clinic_id'])
    require(clinic and clinic['is_active'], 403, 'Clínica inativa')
    return {'access_token': token(user, 'access', 30), 'token_type': 'bearer'}

@app.post('/api/v1/auth/clinical-unlock')
def unlock(body: Unlock, user=Depends(access_user), db: Session = Depends(db_dep)):
    require(user['role'] == 'DENTIST', 403, 'Apenas dentistas')
    dentist_for(db, user)
    require(user['clinical_password_hash'] and hasher.verify(body.password, user['clinical_password_hash']),
            401, 'Senha clínica inválida')
    return {'clinical_token': token(user, 'clinical', 15), 'token_type': 'bearer'}

@app.post('/api/v1/patients', status_code=201)
def create_patient(body: PatientIn, user=Depends(access_user), db: Session = Depends(db_dep)):
    require(user['role'] in ('ADMINISTRATOR', 'RECEPTIONIST'))
    try:
        with db.begin_nested():
            p = one(db, '''INSERT INTO patients (clinic_id,full_name,cpf,medical_record_number,birth_date)
                VALUES (:clinic,:name,:cpf,:number,:birth) RETURNING id''', clinic=user['clinic_id'],
                name=body.full_name.strip(), cpf=body.cpf, number=body.medical_record_number,
                birth=body.birth_date)
            rec = one(db, 'INSERT INTO medical_records (patient_id) VALUES (:id) RETURNING id', id=p['id'])
            audit(db, user['id'], 'PATIENT_CREATED', 'patient', str(p['id']))
        db.commit()
        return {'patient_id': p['id'], 'medical_record_id': rec['id']}
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Paciente ou número de prontuário duplicado')

@app.post('/api/v1/appointments', status_code=201)
def appointment(body: AppointmentIn, user=Depends(access_user), db: Session = Depends(db_dep)):
    require(user['role'] in ('ADMINISTRATOR', 'RECEPTIONIST'))
    require(body.scheduled_at.utcoffset() is not None, 422, 'Data deve conter fuso horário')
    try:
        with db.begin_nested():
            patient_for(db, user['clinic_id'], body.patient_id)
            dentist_in_clinic(db, user['clinic_id'], body.dentist_id)
            appt = one(db, '''INSERT INTO appointments
                (clinic_id,patient_id,dentist_id,scheduled_at,duration_minutes,notes)
                VALUES (:clinic,:patient,:dentist,:scheduled,:duration,:notes)
                RETURNING id,scheduled_at''', clinic=user['clinic_id'], patient=body.patient_id,
                dentist=body.dentist_id, scheduled=body.scheduled_at, duration=body.duration_minutes, notes=body.notes)
            link_id, changed = change_link(db, user, body.patient_id, body.dentist_id, 'APPOINTMENT', appointment=appt)
            audit(db, user['id'], 'APPOINTMENT_CREATED', 'appointment', str(appt['id']))
        db.commit()
        return {'appointment_id': appt['id'], 'access_link_id': link_id, 'access_changed': changed}
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Conflito de horário ou integridade do agendamento')

@app.post('/api/v1/admin/access')
def admin_access(body: AdminAccess, user=Depends(access_user), db: Session = Depends(db_dep)):
    require(user['role'] == 'ADMINISTRATOR')
    with db.begin_nested():
        link_id, _ = change_link(db, user, body.patient_id, body.dentist_id, 'ADMIN', action=body.action)
    db.commit()
    return {'link_id': link_id, 'action': body.action}

@app.get('/api/v1/patients/{patient_id}/record')
def record(patient_id: int, user=Depends(clinical_user), db: Session = Depends(db_dep)):
    allowed(db, user, patient_id)
    return {'id': record_for(db, patient_id), 'patient_id': patient_id}

@app.get('/api/v1/patients/{patient_id}/evolutions')
def evolutions(patient_id: int, user=Depends(clinical_user), db: Session = Depends(db_dep)):
    dentist = allowed(db, user, patient_id)
    return allrows(db, '''SELECT e.* FROM clinical_evolutions e JOIN medical_records r ON r.id=e.medical_record_id
        WHERE r.patient_id=:patient AND (e.status='FINALIZED' OR (e.status='DRAFT' AND e.dentist_id=:dentist))
        ORDER BY e.recorded_at DESC''', patient=patient_id, dentist=dentist)

@app.post('/api/v1/evolutions', status_code=201)
def create_evolution(body: EvolutionIn, user=Depends(clinical_user), db: Session = Depends(db_dep)):
    try:
        with db.begin_nested():
            dentist = allowed(db, user, body.patient_id, lock=True)
            if body.appointment_id is not None:
                a = one(db, '''SELECT id FROM appointments WHERE id=:id AND clinic_id=:clinic
                    AND patient_id=:patient AND dentist_id=:dentist''', id=body.appointment_id,
                    clinic=user['clinic_id'], patient=body.patient_id, dentist=dentist)
                require(a is not None, 422, 'Consulta incompatível')
            require(body.description.strip(), 422, 'Descrição vazia')
            e = one(db, '''INSERT INTO clinical_evolutions
                (medical_record_id,dentist_id,appointment_id,description,procedure_performed,notes)
                VALUES (:record,:dentist,:appointment,:description,:procedure,:notes) RETURNING *''',
                record=record_for(db, body.patient_id), dentist=dentist, appointment=body.appointment_id,
                description=body.description, procedure=body.procedure_performed, notes=body.notes)
            audit(db, user['id'], 'EVOLUTION_CREATED', 'clinical_evolution', str(e['id']))
        db.commit()
        return dict(e)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Consulta já possui evolução ou há conflito de integridade')

def edit_context(db, user, evolution_id):
    row = one(db, '''SELECT e.*,r.patient_id FROM clinical_evolutions e
        JOIN medical_records r ON r.id=e.medical_record_id WHERE e.id=:id''', id=evolution_id)
    require(row is not None, 404, 'Evolução não encontrada')
    dentist = allowed(db, user, row['patient_id'], lock=True)
    e = one(db, 'SELECT * FROM clinical_evolutions WHERE id=:id FOR UPDATE', id=evolution_id)
    # Revalidação após adquirir locks.
    allowed(db, user, row['patient_id'])
    require(e['dentist_id'] == dentist and e['status'] == 'DRAFT', 403, 'Rascunho não editável')
    return e

@app.patch('/api/v1/evolutions/{evolution_id}')
def edit_evolution(evolution_id: int, body: EvolutionPatch, user=Depends(clinical_user), db: Session = Depends(db_dep)):
    with db.begin_nested():
        e = edit_context(db, user, evolution_id)
        require(e['version'] == body.version, 409, 'Versão desatualizada')
        changes = body.model_dump(exclude_unset=True, exclude={'version'})
        if 'description' in changes:
            require(changes['description'] is not None and changes['description'].strip(), 422, 'Descrição vazia')
        fields = {k: v for k, v in changes.items() if k in ('description','procedure_performed','notes')}
        require(fields, 422, 'Nenhum campo para atualizar')
        assigns = ', '.join(f'{k}=:{k}' for k in fields)
        updated = one(db, f'UPDATE clinical_evolutions SET {assigns},version=version+1 WHERE id=:id RETURNING *',
                      id=evolution_id, **fields)
        audit(db, user['id'], 'EVOLUTION_EDITED', 'clinical_evolution', str(evolution_id))
    db.commit()
    return dict(updated)

@app.post('/api/v1/evolutions/{evolution_id}/finalize')
def finalize(evolution_id: int, body: FinalizeIn, user=Depends(clinical_user), db: Session = Depends(db_dep)):
    with db.begin_nested():
        e = edit_context(db, user, evolution_id)
        require(e['version'] == body.version, 409, 'Versão desatualizada')
        updated = one(db, '''UPDATE clinical_evolutions SET status='FINALIZED',finalized_at=now(),
            version=version+1 WHERE id=:id RETURNING *''', id=evolution_id)
        audit(db, user['id'], 'EVOLUTION_FINALIZED', 'clinical_evolution', str(evolution_id))
    db.commit()
    return dict(updated)

@lru_cache(maxsize=1)
def opencl_engine():
    return OpenCLSearch()

@app.get('/api/v1/clinical/search')
def search(q: str, patient_id: int = Query(gt=0), engine_name: str = 'auto',
           offset: int = Query(0, ge=0), user=Depends(clinical_user), db: Session = Depends(db_dep)):
    require(0 < len(q.strip()) <= 128 and bool(normalize(q).strip()), 422, 'Termo inválido')
    require(engine_name in ('auto','cpu','opencl'), 422, 'Motor inválido')
    # Wait for any existing revocation BEFORE fetching clinical content.
    dentist = allowed(db, user, patient_id, lock=True)
    rows = allrows(db, """SELECT e.id,e.description,e.status,e.dentist_id,r.patient_id
        FROM clinical_evolutions e JOIN medical_records r ON r.id=e.medical_record_id
        WHERE r.patient_id=:patient
          AND (e.status='FINALIZED' OR (e.status='DRAFT' AND e.dentist_id=:dentist))
        ORDER BY e.id LIMIT 1001 OFFSET :offset""", patient=patient_id, dentist=dentist, offset=offset)
    more = len(rows) > 1000
    rows = rows[:1000]
    # Release locks during computation so a revocation can complete.
    db.rollback()
    texts = [r['description'] for r in rows]
    require(sum(len(normalize(t).encode('utf-8')) for t in texts) <= settings.opencl_max_text_bytes,
            413, 'Lote excede orçamento de bytes')
    used = 'cpu'
    if engine_name != 'cpu':
        try:
            indexes = opencl_engine().search(texts, q)
            used = 'opencl'
        except (OpenCLUnavailable, ValueError, RuntimeError):
            if engine_name == 'opencl':
                raise HTTPException(503, 'OpenCL indisponível')
            indexes = sequential_search(texts, q)
    else:
        indexes = sequential_search(texts, q)
    # Fresh transaction, recheck authorization after the kernel and lock until
    # response serialization. A revocation committed during compute wins.
    require(allowed(db, user, patient_id, lock=True) == dentist)
    return {'engine': used, 'total': len(indexes), 'results': [rows[i] for i in indexes],
            'candidate_limit': 1000, 'offset': offset, 'next_offset': offset + 1000 if more else None}

@app.post('/api/v1/admin/users/{user_id}/reset-login-password')
def reset_login(user_id: int, body: PasswordReset, user=Depends(access_user), db: Session = Depends(db_dep)):
    require(user['role'] == 'ADMINISTRATOR')
    target = one(db, 'SELECT * FROM users WHERE id=:id AND clinic_id=:clinic FOR UPDATE', id=user_id, clinic=user['clinic_id'])
    require(target is not None, 404, 'Usuário não encontrado')
    require(not (target['clinical_password_hash'] and hasher.verify(body.new_password, target['clinical_password_hash'])),
            422, 'Senhas devem ser diferentes')
    db.execute(text('UPDATE users SET password_hash=:hash,session_version=session_version+1 WHERE id=:id'),
               {'hash': hasher.hash(body.new_password), 'id': user_id})
    audit(db, user['id'], 'LOGIN_PASSWORD_RESET', 'user', str(user_id))
    db.commit()
    return {'ok': True}

@app.post('/api/v1/auth/reset-clinical-password')
def reset_clinical(body: PasswordReset, user=Depends(access_user), db: Session = Depends(db_dep)):
    require(user['role'] == 'DENTIST')
    dentist_for(db, user)
    require(not hasher.verify(body.new_password, user['password_hash']), 422, 'Senhas devem ser diferentes')
    db.execute(text('UPDATE users SET clinical_password_hash=:hash,clinical_version=clinical_version+1 WHERE id=:id'),
               {'hash': hasher.hash(body.new_password), 'id': user['id']})
    audit(db, user['id'], 'CLINICAL_PASSWORD_RESET', 'user', str(user['id']))
    db.commit()
    return {'ok': True}

# Registro dos módulos REST adicionais (importação tardia evita ciclo de imports).
from app.crud import install as install_crud
install_crud(app)

# As rotas clínicas precisam constar da captura de rotas estáticas do logger.
from app.clinical_patients import install as install_clinical_patients
install_clinical_patients(app)

# A política é instalada após registrar as rotas e antes de receber requisições.
from app.logging_policy import install_logging_policy
install_logging_policy(app)
