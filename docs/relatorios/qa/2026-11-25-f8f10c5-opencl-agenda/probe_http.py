
"""HTTP real para API exclusiva QA. Nunca usa servicos diarios."""
import os,json,time,datetime as dt
from concurrent.futures import ThreadPoolExecutor
import httpx
from sqlalchemy import create_engine,text,select
from sqlalchemy.orm import Session
import app.main  # Registra modelos relacionados na fixture QA.
from app.users.models import Clinic,User
from app.patients.models import Patient
from app.dentists.models import Dentist
from app.security.auth import create_access_token
from app.security.roles import Role
from app.security.hashing import hash_password
E=create_engine(os.environ["DATABASE_URL"],connect_args={"options":"-c statement_timeout=15000"})
BASE="http://qa-api:8000"
R=[]
def emit(id,expected,obtained,ok):
 R.append({"id":id,"expected":expected,"obtained":obtained,"status":"aprovado" if ok else "reprovado"})
 print("QA_HTTP "+json.dumps(R[-1],sort_keys=True),flush=True)
with httpx.Client(base_url=BASE,timeout=20) as c:
 for _ in range(60):
  try:
   r=c.get("/health")
   if r.status_code==200:break
  except Exception:pass
  time.sleep(.2)
 else:raise RuntimeError("API QA nao iniciou")
 emit("HTTP-health","200",r.status_code,r.status_code==200)
 r=c.get("/openapi.json");emit("HTTP-openapi","200 contrato disponivel",r.status_code,r.status_code==200)
 r=c.get("/api/v1/appointments");emit("HTTP-unauth","401",r.status_code,r.status_code==401)
with Session(E,expire_on_commit=False) as db:
 cl=Clinic(name="QA HTTP Agenda",cnpj="00000000009991",email="qa-http@example.test")
 db.add(cl);db.flush()
 users=[User(clinic_id=cl.id,full_name="Recepcao QA "+str(i),email=f"qa-recep{i}@example.test",cpf=f"{300+i:011d}",password_hash=hash_password("FicticiaAgenda2026!"),role=Role.RECEPTIONIST) for i in range(2)]
 dentist_user=User(clinic_id=cl.id,full_name="Dentista QA",email="qa-dent@example.test",cpf="00000000302",password_hash=hash_password("FicticiaAgenda2026!"),role=Role.DENTIST)
 db.add_all(users+[dentist_user]);db.flush()
 dentist=Dentist(user_id=dentist_user.id,cro_number="888888",cro_state="PE")
 pats=[Patient(clinic_id=cl.id,full_name="Paciente QA "+str(i),cpf=f"{400+i:011d}",medical_record_number=f"QA-HTTP-{i}",birth_date=dt.date(1990,1,1)) for i in range(2)]
 db.add_all([dentist]+pats);db.commit()
 clinic_id,dentist_id=cl.id,dentist.id
 patient_ids=[p.id for p in pats]
 headers=[{"Authorization":"Bearer "+create_access_token(u)} for u in users]
 # A real login response also works with the same fixture credential; do not print it.
with httpx.Client(base_url=BASE,timeout=20) as c:
 r=c.post("/api/v1/auth/login",data={"username":users[0].email,"password":"FicticiaAgenda2026!"})
 emit("HTTP-login","200 access_token presente",{"http":r.status_code,"access_token_present":bool(r.json().get("access_token"))},r.status_code==200 and bool(r.json().get("access_token")))
start=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=20)).replace(microsecond=123456)
payload={"patient_id":patient_ids[0],"dentist_id":dentist_id,"scheduled_at":start.isoformat(),"duration_minutes":30}
def post(i,body=None):
 with httpx.Client(base_url=BASE,timeout=20) as c:return c.post("/api/v1/appointments",json=body or dict(payload,patient_id=patient_ids[i]),headers=headers[i])
with E.connect() as holder:
 holder.execute(text("SELECT pg_advisory_xact_lock(:k)"),{"k":clinic_id*1_000_000+dentist_id})
 with ThreadPoolExecutor(max_workers=2) as pool:
  futures=[pool.submit(post,i) for i in range(2)]
  try:
   deadline=time.monotonic()+10
   while time.monotonic()<deadline:
    with E.connect() as monitor:
     waits=monitor.execute(text("SELECT pid,wait_event_type,wait_event FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'SELECT pg_advisory_xact_lock%'")).mappings().all()
    if len(waits)>=2:break
    time.sleep(.04)
   assert len(waits)>=2,"Duas chamadas HTTP nao aguardaram lock"
  finally:holder.commit()
  responses=[f.result(timeout=20) for f in futures]
winner=next((r for r in responses if r.status_code==201),None)
with E.connect() as c:
 rows=c.execute(text("SELECT id,patient_id,scheduled_at FROM appointments")).mappings().all()
codes=sorted(r.status_code for r in responses)
ok=codes==[201,409] and len(rows)==1 and winner is not None and rows[0]["patient_id"]==winner.json()["patient_id"]
emit("HTTP-PG-race","duas esperas reais;201/409;uma gravacao correta",{"http":codes,"waiters":[dict(x) for x in waits],"persisted_count":len(rows),"winner_patient_matches":winner is not None and rows[0]["patient_id"]==winner.json()["patient_id"]},ok)
assert winner is not None,"sem vencedor para continuar smoke"
aid=winner.json()["id"]
with httpx.Client(base_url=BASE,timeout=20) as c:
 same={"scheduled_at":start.astimezone(dt.timezone(dt.timedelta(hours=-3))).isoformat()}
 r=c.patch(f"/api/v1/appointments/{aid}",json=same,headers=headers[0])
 emit("HTTP-self-update-timezone","200 ao atualizar proprio slot com fuso equivalente",r.status_code,r.status_code==200)
 adjacent=dict(payload,scheduled_at=(start+dt.timedelta(minutes=30)).isoformat())
 r=post(0,adjacent)
 emit("HTTP-adjacent","201 para intervalo adjacente",r.status_code,r.status_code==201)
 after_id=r.json().get("id")
 r=c.patch(f"/api/v1/appointments/{aid}",json={"scheduled_at":(start+dt.timedelta(microseconds=1)).isoformat()},headers=headers[0])
 emit("HTTP-one-microsecond-overlap","409 sobreposicao com consulta adjacente",r.status_code,r.status_code==409)
 with E.connect() as db:unchanged=db.scalar(text("SELECT scheduled_at FROM appointments WHERE id=:id"),{"id":aid})==start
 emit("HTTP-rollback-update","horario original preservado",unchanged,unchanged)
# Force no precheck by SQL insert only: persistent GiST independently rejects it.
with E.connect() as db:
 transaction=db.begin()
 try:
  db.execute(text("INSERT INTO appointments(clinic_id,patient_id,dentist_id,scheduled_at,duration_minutes) VALUES(:c,:p,:d,:t,30)"),{"c":clinic_id,"p":patient_ids[1],"d":dentist_id,"t":start})
  code=None
 except Exception as e:code=getattr(getattr(e,"orig",None),"sqlstate",None)
 finally:transaction.rollback()
emit("SQL-GiST-authority","23P01 mesmo sem precheck",code,code=="23P01")
with E.connect() as db:count=db.scalar(text("SELECT count(*) FROM appointments"))
emit("SQL-GiST-rollback","duas gravacoes apos tentativa rejeitada",count,count==2)
if not all(x["status"]=="aprovado" for x in R):raise SystemExit(1)
