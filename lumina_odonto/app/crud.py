"""Endpoints administrativos e operacionais; registros clínicos são preservados."""
from datetime import date, datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix='/api/v1', tags=['Gestão e CRUD'])

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class ClinicPatch(Strict):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    address: str | None = None
    email: str | None = Field(default=None, max_length=255)

class UserCreate(Strict):
    full_name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=255)
    cpf: str = Field(pattern=r'^\d{11}$')
    phone: str | None = Field(default=None, max_length=20)
    role: Literal['ADMINISTRATOR','RECEPTIONIST','DENTIST']
    password: str = Field(min_length=12)
    clinical_password: str | None = Field(default=None, min_length=12)

class UserPatch(Strict):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, min_length=3, max_length=255)

class DentistCreate(Strict):
    user_id: int = Field(gt=0)
    cro_number: str = Field(min_length=1, max_length=30)
    cro_state: str = Field(pattern=r'^[A-Z]{2}$')
    specialty: str | None = Field(default=None, max_length=100)

class DentistPatch(Strict):
    specialty: str | None = Field(default=None, max_length=100)
    cro_number: str | None = Field(default=None, min_length=1, max_length=30)
    cro_state: str | None = Field(default=None, pattern=r'^[A-Z]{2}$')

class PatientPatch(Strict):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = None
    birth_date: date | None = None

class AppointmentPatch(Strict):
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    notes: str | None = None
    status: Literal['SCHEDULED','CONFIRMED','COMPLETED','CANCELED','NO_SHOW'] | None = None

class RecordPatch(Strict):
    general_notes: str | None = None

class Page(Strict):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


def appointment_dto(row):
    # scheduled_period is an internal PostgreSQL range, not a public field.
    return {k: v for k, v in row.items() if k != 'scheduled_period'}


def install(app):
    from app import main as m
    def require_role(user, *roles):
        m.require(user['role'] in roles, 403, 'Perfil sem permissão')

    def write(db, sql, params, user, action, resource, identifier=None):
        try:
            row = m.one(db, sql, **params)
            if row is None:
                raise HTTPException(404, 'Registro não encontrado')
            m.audit(db, user['id'], action, resource, str(identifier if identifier is not None else row['id']))
            result = appointment_dto(row) if resource == "appointment" else dict(row)
            if resource == "user":
                result = {k: v for k, v in result.items() if k not in ("password_hash", "clinical_password_hash", "session_version", "clinical_version")}
            db.commit()
            return result
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Conflito de integridade ou duplicidade')

    def patch(db, table, identifier, body, where, user, action, resource, fixed=None):
        fields = body.model_dump(exclude_unset=True)
        m.require(bool(fields), 422, 'Nenhum campo informado')
        if 'scheduled_at' in fields and fields['scheduled_at'] is not None:
            m.require(fields['scheduled_at'].utcoffset() is not None, 422, 'Informe fuso horário')
        fields.update(fixed or {})
        fields['id'] = identifier
        fields['clinic'] = user['clinic_id']
        assignments = ', '.join(f'{k}=:{k}' for k in fields if k not in ('id','clinic'))
        return write(db, f'UPDATE {table} SET {assignments} WHERE id=:id AND {where} RETURNING *',
                     fields, user, action, resource, identifier)

    @router.get('/auth/me', tags=['Autenticação'])
    def me(user=Depends(m.access_user)):
        return {k: user[k] for k in ('id','clinic_id','full_name','email','role','is_active')}

    @router.get('/clinics/me', tags=['Clínicas'])
    def clinic_me(user=Depends(m.access_user), db=Depends(m.db_dep)):
        return dict(m.one(db, 'SELECT * FROM clinics WHERE id=:id', id=user['clinic_id']))

    @router.patch('/clinics/me', tags=['Clínicas'])
    def clinic_update(body: ClinicPatch, user=Depends(m.access_user), db=Depends(m.db_dep)):
        require_role(user, 'ADMINISTRATOR')
        return patch(db, 'clinics', user['clinic_id'], body, 'id=:clinic', user, 'CLINIC_UPDATED', 'clinic')

    @router.get('/users', tags=['Usuários'])
    def users(limit: int = Query(50,ge=1,le=100), offset: int = Query(0,ge=0), user=Depends(m.access_user), db=Depends(m.db_dep)):
        require_role(user, 'ADMINISTRATOR')
        return m.allrows(db, '''SELECT id,clinic_id,full_name,email,cpf,phone,role,is_active,created_at,updated_at
            FROM users WHERE clinic_id=:clinic ORDER BY id LIMIT :limit OFFSET :offset''',
            clinic=user['clinic_id'],limit=limit,offset=offset)

    @router.get('/users/{user_id}', tags=['Usuários'])
    def user_get(user_id: int, user=Depends(m.access_user), db=Depends(m.db_dep)):
        require_role(user, 'ADMINISTRATOR')
        row=m.one(db, '''SELECT id,clinic_id,full_name,email,cpf,phone,role,is_active,created_at,updated_at
            FROM users WHERE id=:id AND clinic_id=:clinic''',id=user_id,clinic=user['clinic_id'])
        m.require(row is not None,404,'Usuário não encontrado')
        return dict(row)

    @router.post('/users',status_code=201,tags=['Usuários'])
    def user_create(body: UserCreate,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user, 'ADMINISTRATOR')
        m.require(body.role=='DENTIST' or body.clinical_password is None,422,'Senha clínica exclusiva de dentista')
        if body.clinical_password:
            m.require(body.password != body.clinical_password,422,'Senhas devem ser diferentes')
        return write(db,'''INSERT INTO users (clinic_id,full_name,email,cpf,phone,role,password_hash,clinical_password_hash)
            VALUES (:clinic,:name,:email,:cpf,:phone,:role,:hash,:clinical) RETURNING
            id,clinic_id,full_name,email,cpf,phone,role,is_active,created_at''',
            {'clinic':user['clinic_id'],'name':body.full_name,'email':body.email,'cpf':body.cpf,
             'phone':body.phone,'role':body.role,'hash':m.hasher.hash(body.password),
             'clinical':m.hasher.hash(body.clinical_password) if body.clinical_password else None},
            user,'USER_CREATED','user')

    @router.patch('/users/{user_id}', tags=['Usuários'])
    def user_update(user_id:int,body:UserPatch,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user, 'ADMINISTRATOR')
        return patch(db,'users',user_id,body,'clinic_id=:clinic',user,'USER_UPDATED','user')

    @router.delete('/users/{user_id}',tags=['Usuários'])
    def user_deactivate(user_id:int,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user, 'ADMINISTRATOR')
        m.require(user_id!=user['id'],409,'Não é possível desativar a própria conta')
        return write(db,'''UPDATE users SET is_active=false,session_version=session_version+1,
            clinical_version=clinical_version+1 WHERE id=:id AND clinic_id=:clinic AND is_active
            RETURNING id,is_active''',{'id':user_id,'clinic':user['clinic_id']},user,'USER_DEACTIVATED','user',user_id)

    @router.get('/dentists',tags=['Dentistas'])
    def dentists(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),user=Depends(m.access_user),db=Depends(m.db_dep)):
        return m.allrows(db,'''SELECT d.*,u.full_name,u.is_active FROM dentists d JOIN users u ON u.id=d.user_id
            WHERE u.clinic_id=:clinic ORDER BY d.id LIMIT :limit OFFSET :offset''',clinic=user['clinic_id'],limit=limit,offset=offset)

    @router.get('/dentists/{dentist_id}',tags=['Dentistas'])
    def dentist_get(dentist_id:int,user=Depends(m.access_user),db=Depends(m.db_dep)):
        row=m.one(db,'''SELECT d.*,u.full_name,u.is_active FROM dentists d JOIN users u ON u.id=d.user_id
            WHERE d.id=:id AND u.clinic_id=:clinic''',id=dentist_id,clinic=user['clinic_id'])
        m.require(row is not None,404,'Dentista não encontrado')
        return dict(row)

    @router.post('/dentists',status_code=201,tags=['Dentistas'])
    def dentist_create(body:DentistCreate,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR')
        candidate=m.one(db,'''SELECT id FROM users WHERE id=:id AND clinic_id=:clinic AND role='DENTIST' AND is_active''',
                        id=body.user_id,clinic=user['clinic_id'])
        m.require(candidate is not None,422,'Usuário dentista inválido')
        return write(db,'''INSERT INTO dentists (user_id,cro_number,cro_state,specialty)
            VALUES (:uid,:cro,:state,:specialty) RETURNING *''',
            {'uid':body.user_id,'cro':body.cro_number,'state':body.cro_state,'specialty':body.specialty},
            user,'DENTIST_CREATED','dentist')

    @router.patch('/dentists/{dentist_id}',tags=['Dentistas'])
    def dentist_update(dentist_id:int,body:DentistPatch,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR')
        return patch(db,'dentists',dentist_id,body,
            'user_id IN (SELECT id FROM users WHERE clinic_id=:clinic)',user,'DENTIST_UPDATED','dentist')

    @router.get('/patients',tags=['Pacientes'])
    def patients(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),
                 user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR','RECEPTIONIST')
        return m.allrows(db,'''SELECT p.*,r.id AS medical_record_id FROM patients p
            LEFT JOIN medical_records r ON r.patient_id=p.id WHERE p.clinic_id=:clinic AND p.is_active
            ORDER BY p.id LIMIT :limit OFFSET :offset''',clinic=user['clinic_id'],limit=limit,offset=offset)

    @router.get('/patients/{patient_id}',tags=['Pacientes'])
    def patient_get(patient_id:int,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR','RECEPTIONIST')
        return dict(m.patient_for(db,user['clinic_id'],patient_id))

    @router.patch('/patients/{patient_id}',tags=['Pacientes'])
    def patient_update(patient_id:int,body:PatientPatch,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR','RECEPTIONIST')
        return patch(db,'patients',patient_id,body,'clinic_id=:clinic AND is_active',user,'PATIENT_UPDATED','patient')

    @router.delete('/patients/{patient_id}',tags=['Pacientes'])
    def patient_deactivate(patient_id:int,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR')
        return write(db,'''UPDATE patients SET is_active=false WHERE id=:id AND clinic_id=:clinic AND is_active
            RETURNING id,is_active''',{'id':patient_id,'clinic':user['clinic_id']},user,'PATIENT_DEACTIVATED','patient',patient_id)

    @router.get('/appointments',tags=['Agendamentos'])
    def appointments(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),
                     patient_id:int|None=None,dentist_id:int|None=None,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR','RECEPTIONIST','DENTIST')
        if user['role']=='DENTIST':
            dentist_id=m.dentist_for(db,user)
        return [appointment_dto(row) for row in m.allrows(db,'''SELECT a.* FROM appointments a WHERE a.clinic_id=:clinic
            AND (CAST(:patient AS INTEGER) IS NULL OR a.patient_id=:patient)
            AND (CAST(:dentist AS INTEGER) IS NULL OR a.dentist_id=:dentist)
            ORDER BY a.scheduled_at DESC LIMIT :limit OFFSET :offset''',
            clinic=user['clinic_id'],patient=patient_id,dentist=dentist_id,limit=limit,offset=offset)]

    @router.get('/appointments/{appointment_id}',tags=['Agendamentos'])
    def appointment_get(appointment_id:int,user=Depends(m.access_user),db=Depends(m.db_dep)):
        row=m.one(db,'SELECT * FROM appointments WHERE id=:id AND clinic_id=:clinic',
                  id=appointment_id,clinic=user['clinic_id'])
        m.require(row is not None,404,'Agendamento não encontrado')
        if user['role']=='DENTIST':
            m.require(row['dentist_id']==m.dentist_for(db,user),403,'Sem acesso a este agendamento')
        return appointment_dto(row)

    @router.patch('/appointments/{appointment_id}',tags=['Agendamentos'])
    def appointment_update(appointment_id:int,body:AppointmentPatch,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR','RECEPTIONIST')
        # Atualizar consulta nunca altera vínculo clínico existente.
        return patch(db,'appointments',appointment_id,body,'clinic_id=:clinic',user,'APPOINTMENT_UPDATED','appointment')

    @router.delete('/appointments/{appointment_id}',tags=['Agendamentos'])
    def appointment_cancel(appointment_id:int,user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR','RECEPTIONIST')
        return write(db,'''UPDATE appointments SET status='CANCELED'
            WHERE id=:id AND clinic_id=:clinic AND status IN ('SCHEDULED','CONFIRMED') RETURNING *''',
            {'id':appointment_id,'clinic':user['clinic_id']},user,'APPOINTMENT_CANCELED','appointment',appointment_id)

    @router.get('/patients/{patient_id}/record/summary',tags=['Prontuários'])
    def record_summary(patient_id:int,user=Depends(m.clinical_user),db=Depends(m.db_dep)):
        m.allowed(db,user,patient_id)
        row=m.one(db,'SELECT * FROM medical_records WHERE patient_id=:id',id=patient_id)
        m.require(row is not None,404,'Prontuário não encontrado')
        return dict(row)

    @router.patch('/patients/{patient_id}/record',tags=['Prontuários'])
    def record_update(patient_id:int,body:RecordPatch,user=Depends(m.clinical_user),db=Depends(m.db_dep)):
        m.allowed(db,user,patient_id,lock=True)
        record_id=m.record_for(db,patient_id)
        return patch(db,'medical_records',record_id,body,
            'patient_id IN (SELECT id FROM patients WHERE clinic_id=:clinic)',user,'RECORD_UPDATED','medical_record')

    @router.get('/evolutions/{evolution_id}',tags=['Evoluções'])
    def evolution_get(evolution_id:int,user=Depends(m.clinical_user),db=Depends(m.db_dep)):
        row=m.one(db,'''SELECT e.*,r.patient_id FROM clinical_evolutions e JOIN medical_records r
            ON r.id=e.medical_record_id JOIN patients p ON p.id=r.patient_id
            WHERE e.id=:id AND p.clinic_id=:clinic''',id=evolution_id,clinic=user['clinic_id'])
        m.require(row is not None,404,'Evolução não encontrada')
        dentist=m.allowed(db,user,row['patient_id'])
        m.require(row['status']=='FINALIZED' or row['dentist_id']==dentist,403,'Rascunho privado')
        return dict(row)

    @router.get('/access-links',tags=['Acesso clínico'])
    def access_links(patient_id:int|None=None,dentist_id:int|None=None,
                     limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),
                     user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR')
        from app.clinical_patients_repository import read_administrative_links
        return read_administrative_links(
            db,clinic_id=user['clinic_id'],patient_id=patient_id,
            dentist_id=dentist_id,limit=limit,offset=offset)


    @router.get('/access-events',tags=['Acesso clínico'])
    def access_events(link_id:int|None=None,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),
                      user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR')
        return m.allrows(db,'''SELECT e.* FROM clinical_access_events e JOIN clinical_access_links l ON l.id=e.link_id
            WHERE l.clinic_id=:clinic AND (CAST(:link AS INTEGER) IS NULL OR e.link_id=:link)
            ORDER BY e.id DESC LIMIT :limit OFFSET :offset''',
            clinic=user['clinic_id'],link=link_id,limit=limit,offset=offset)

    @router.get('/audit-logs',tags=['Auditoria'])
    def audit_logs(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),
                   user=Depends(m.access_user),db=Depends(m.db_dep)):
        require_role(user,'ADMINISTRATOR')
        return m.allrows(db,'''SELECT a.* FROM audit_logs a JOIN users u ON u.id=a.user_id
            WHERE u.clinic_id=:clinic ORDER BY a.id DESC LIMIT :limit OFFSET :offset''',
            clinic=user['clinic_id'],limit=limit,offset=offset)

    app.include_router(router)
