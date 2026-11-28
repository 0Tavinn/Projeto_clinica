"""Fixtures e verificações HTTP/SQL somente no banco exclusivo de vínculos."""

from pathlib import Path
import concurrent.futures
import datetime as dt
import json
import os
import time
import jwt
import httpx
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app import main as m

url=make_url(os.environ["DATABASE_URL"])
assert url.host=="pg" and url.database=="lumina_links_scratch" and url.username=="links_qa"
engine=create_engine(url,connect_args={"options":"-c statement_timeout=12000"})
BASE="http://api:8000"
results=[]
def case(name,condition,**facts):
    assert condition,name
    results.append({"id":name,"passed":True,**facts})
    Path("/tmp/access-results.json").write_text(json.dumps(results,indent=2))
def sql(statement,**params):
    with engine.begin() as db:
        value=db.execute(text(statement),params)
        return [dict(row) for row in value.mappings()] if value.returns_rows else []
def request(method,path,token=None,body=None,**kwargs):
    with httpx.Client(base_url=BASE,timeout=25) as client:
        return client.request(method,path,headers={"Authorization":"Bearer "+token} if token else {},
                              json=body,**kwargs)
for _ in range(100):
    try:
        if request("GET","/health").status_code==200:break
    except httpx.HTTPError:pass
    time.sleep(.1)
else:raise RuntimeError("API exclusiva indisponível")
clinics=[sql("INSERT INTO clinics(name,cnpj,email) VALUES(:name,:cnpj,:email) RETURNING id",
             name="Clínica QA",cnpj=f"{i+1:014d}",email=f"clinic{i}@qa.test")[0]["id"]
         for i in range(2)]
users={}
for i,(name,role,ci,professional) in enumerate([
    ("admin","ADMINISTRATOR",0,False),("recep","RECEPTIONIST",0,False),
    ("dent1","DENTIST",0,True),("dent2","DENTIST",0,True),
    ("foreign","DENTIST",1,True),("admin2","ADMINISTRATOR",1,False),
    ("noprof","DENTIST",0,False),("inactive","DENTIST",0,True)]):
    user=sql("""INSERT INTO users(clinic_id,full_name,email,cpf,role,password_hash,clinical_password_hash)
        VALUES(:clinic,:name,:email,:cpf,:role,:login,:clinical) RETURNING *""",
        clinic=clinics[ci],name="NAME_SENTINEL_"+name,email=name+"@qa.test",cpf=f"{i+1:011d}",
        role=role,login=m.hasher.hash("FicticioLogin2026!"),
        clinical=m.hasher.hash("FicticioClinical2026!"))[0]
    if professional:
        user["dentist_id"]=sql("INSERT INTO dentists(user_id,cro_number,cro_state) VALUES(:id,:cro,'PE') RETURNING id",
                               id=user["id"],cro=str(i+1))[0]["id"]
    login=request("POST","/api/v1/auth/login",body={"email":name+"@qa.test","password":"FicticioLogin2026!"})
    assert login.status_code==200
    user["access"]=login.json()["access_token"]
    user["clinical"]=m.token(user,"clinical",15) # Tokens QA para testar perfis inválidos também.
    if professional:
        unlock=request("POST","/api/v1/auth/clinical-unlock",user["access"],{"password":"FicticioClinical2026!"})
        assert unlock.status_code==200
        user["clinical"]=unlock.json()["clinical_token"]
    users[name]=user

counter=100
def patient(name,ci=0):
    global counter
    counter+=1
    admin=users["admin" if ci==0 else "admin2"]["access"]
    response=request("POST","/api/v1/patients",admin,{"full_name":name,"cpf":f"{counter:011d}",
        "medical_record_number":"REC-"+str(counter),"birth_date":"1990-01-01"})
    assert response.status_code==201
    return response.json()
def change(p,d="dent1",action="GRANTED",admin="admin"):
    return request("POST","/api/v1/admin/access",users[admin]["access"],
                   {"patient_id":p["patient_id"],"dentist_id":users[d]["dentist_id"],"action":action})
patients={}
for name in ("Alpha","Beta","Literal%_","Revoked","InactivePatient","OtherDentist","NoLink","InactiveDentist","Appointment"):
    patients[name]=patient("PATIENT_NAME_SENTINEL_"+name)
for name in ("Alpha","Beta","Literal%_","Revoked","InactivePatient"):
    assert change(patients[name]).status_code==200
assert change(patients["OtherDentist"],"dent2").status_code==200
assert change(patients["InactiveDentist"],"inactive").status_code==200
patients["Foreign"]=patient("PATIENT_NAME_SENTINEL_Foreign",1)
assert change(patients["Foreign"],"foreign",admin="admin2").status_code==200
assert change(patients["Revoked"],action="REVOKED").status_code==200
assert request("DELETE","/api/v1/patients/"+str(patients["InactivePatient"]["patient_id"]),users["admin"]["access"]).status_code==200
ct=users["dent1"]["clinical"]
prefix="/api/v1/clinical/patients"
expected={patients[n]["patient_id"] for n in ("Alpha","Beta","Literal%_")}
response=request("GET",prefix,ct)
case("own-active-manual-empty-records",response.status_code==200 and
     {x["patient_id"] for x in response.json()["items"]}==expected,http=response.status_code)
for item in response.json()["items"]:
    case("minimal-fields-"+str(item["patient_id"]),
         set(item)=={"patient_id","full_name","medical_record_number","medical_record_id","access_link_id"}
         and item["medical_record_id"] is not None)
case("manual-no-appointment-or-evolution",
     sql("SELECT count(*) n FROM appointments")[0]["n"]==0 and sql("SELECT count(*) n FROM clinical_evolutions")[0]["n"]==0)
detail=request("GET",prefix+"/"+str(patients["Alpha"]["patient_id"]),ct)
case("clinical-header",detail.status_code==200 and detail.json()["patient_id"]==patients["Alpha"]["patient_id"])
# Paginação por candidatos, sem total inventado.
seen=[];cursor=0;pages=0
while True:
    page=request("GET",prefix,ct,params={"limit":1,"after_id":cursor}).json()
    assert set(page)=={"items","limit","next_after_id"}
    seen.extend(x["patient_id"] for x in page["items"]);pages+=1
    if page["next_after_id"] is None:break
    cursor=page["next_after_id"]
    assert pages<10
case("pagination-no-duplicate",len(seen)==len(set(seen)) and set(seen)==expected,pages=pages)
for query,n in (("alpha","Alpha"),("REC-"+str(counter-8),"Alpha"),("%_","Literal%_")):
    page=request("GET",prefix,ct,params={"q":query})
    # Para número de prontuário usa o valor lido, sem assumir sequência de IDs.
    if n=="Alpha" and query.startswith("REC-"):
        query=detail.json()["medical_record_number"]
        page=request("GET",prefix,ct,params={"q":query})
    case("search-"+str(len(results)),page.status_code==200 and
         [x["patient_id"] for x in page.json()["items"]]==[patients[n]["patient_id"]])
for params in ({"limit":0},{"limit":101},{"after_id":-1},{"q":""},{"q":" "},{"q":"X"*129},{"limit":"QUERY_SENTINEL"}):
    res=request("GET",prefix,ct,params=params)
    case("invalid-parameters-"+str(len(results)),res.status_code==422 and "QUERY_SENTINEL" not in res.text)
selected=request("GET",prefix,ct,params={"dentist_id":users["dent2"]["dentist_id"]})
case("dentist-not-client-selected",{x["patient_id"] for x in selected.json()["items"]}==expected)
for name in ("OtherDentist","NoLink","Revoked","Foreign"):
    res=request("GET",prefix+"/"+str(patients[name]["patient_id"]),ct)
    case("guessed-id-"+name,res.status_code==403 and "PATIENT_NAME_SENTINEL" not in res.text)
inactive=request("GET",prefix+"/"+str(patients["InactivePatient"]["patient_id"]),ct)
case("inactive-patient-detail",inactive.status_code==404 and "PATIENT_NAME_SENTINEL" not in inactive.text)
other=request("GET",prefix,users["dent2"]["clinical"])
case("other-dentist-list",{x["patient_id"] for x in other.json()["items"]}=={patients["OtherDentist"]["patient_id"]})
foreign=request("GET",prefix,users["foreign"]["clinical"])
case("other-clinic-list",{x["patient_id"] for x in foreign.json()["items"]}=={patients["Foreign"]["patient_id"]})
for token,name in ((None,"absent"),("invalid-token","invalid"),(users["dent1"]["access"],"wrong-type"),
                   (users["admin"]["clinical"],"admin"),(users["recep"]["clinical"],"reception")):
    for path in (prefix,prefix+"/"+str(patients["Alpha"]["patient_id"])):
        case("token-"+name+"-"+str(len(results)),request("GET",path,token).status_code==401)
expired=jwt.encode({"sub":str(users["dent1"]["id"]),"clinic_id":clinics[0],"type":"clinical",
                   "session_version":1,"clinical_version":1,"iat":0,"exp":1},m.JWT_SECRET,algorithm="HS256")
case("expired-token",request("GET",prefix,expired).status_code==401)
case("no-professional",request("GET",prefix,users["noprof"]["clinical"]).status_code==403)
# Mutação existente é mantida; revogar inativos preserva conteúdo/evento/auditoria.
assert request("DELETE","/api/v1/users/"+str(users["inactive"]["id"]),users["admin"]["access"]).status_code==200
case("inactive-user-token",request("GET",prefix,users["inactive"]["clinical"]).status_code==401)
for name in ("InactivePatient","InactiveDentist"):
    p=patients[name];dent="dent1" if name=="InactivePatient" else "inactive"
    links=request("GET","/api/v1/access-links",users["admin"]["access"],params={"patient_id":p["patient_id"]})
    row=links.json()[0]
    case("admin-identifies-"+name,links.status_code==200 and isinstance(links.json(),list)
         and row["patient_full_name"].startswith("PATIENT_NAME_SENTINEL")
         and row["patient_is_active"]==(name!="InactivePatient")
         and row["dentist_is_active"]==(name!="InactiveDentist"))
    before=sql("SELECT count(*) n FROM clinical_access_events WHERE link_id=:id",id=row["id"])[0]["n"]
    audit=sql("SELECT count(*) n FROM audit_logs WHERE resource='clinical_access_link' AND details=:id",id=str(row["id"]))[0]["n"]
    case("admin-revokes-"+name,change(p,dent,"REVOKED").status_code==200)
    after=sql("SELECT count(*) n FROM clinical_access_events WHERE link_id=:id",id=row["id"])[0]["n"]
    audit_after=sql("SELECT count(*) n FROM audit_logs WHERE resource='clinical_access_link' AND details=:id",id=str(row["id"]))[0]["n"]
    case("revocation-event-audit-"+name,after==before+1 and audit_after==audit+1)
    assert sql("SELECT count(*) n FROM medical_records WHERE patient_id=:id",id=p["patient_id"])[0]["n"]==1
    case("inactive-reactivation-denied-"+name,change(p,dent,"REACTIVATED").status_code==(404 if name=="InactivePatient" else 422))
    case("inactive-grant-denied-"+name,change(p,dent,"GRANTED").status_code==(404 if name=="InactivePatient" else 422))
for name in ("recep","dent1"):
    case("admin-links-role-"+name,request("GET","/api/v1/access-links",users[name]["access"]).status_code==403)
case("admin-links-clinic-isolation",
     all(x["clinic_id"]==clinics[1] for x in request("GET","/api/v1/access-links",users["admin2"]["access"]).json()))
case("duplicate-grant-denied",change(patients["Beta"]).status_code==409)

# Confirma que atualização/cancelamento de consulta antiga não reabre acesso.
p=patients["Appointment"];when=dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=10)
appointment=request("POST","/api/v1/appointments",users["recep"]["access"],
    {"patient_id":p["patient_id"],"dentist_id":users["dent1"]["dentist_id"],"scheduled_at":when.isoformat()})
assert appointment.status_code==201
appointment_id=appointment.json()["appointment_id"]
assert request("DELETE","/api/v1/appointments/"+str(appointment_id),users["recep"]["access"]).status_code==200
case("cancel-keeps-link",request("GET",prefix+"/"+str(p["patient_id"]),ct).status_code==200)
assert change(p,action="REVOKED").status_code==200
patch=request("PATCH","/api/v1/appointments/"+str(appointment_id),users["recep"]["access"],{"notes":"Atualização fictícia"})
case("old-appointment-does-not-reopen",patch.status_code==200 and request("GET",prefix+"/"+str(p["patient_id"]),ct).status_code==403)

# Espera determinística: mesma ordem patient->link da mutação de produção.
for kind in ("list","detail"):
    victim=patient("PATIENT_NAME_SENTINEL_Race_"+kind)
    assert change(victim).status_code==200
    if kind=="list":
        tail=patient("PATIENT_NAME_SENTINEL_Race_list_tail")
        assert change(tail).status_code==200
    pid=victim["patient_id"];link=sql("SELECT id FROM clinical_access_links WHERE patient_id=:id",id=pid)[0]["id"]
    with Session(engine) as holder:
        holder.execute(text("SELECT id FROM patients WHERE id=:id FOR UPDATE"),{"id":pid}).all()
        path=prefix if kind=="list" else prefix+"/"+str(pid)
        params={"q":"Race_"+kind,"limit":1} if kind=="list" else None
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(request,"GET",path,ct,params=params)
            try:
                waiting=[]
                for _ in range(200):
                    waiting=sql("""SELECT pid,wait_event_type,wait_event FROM pg_stat_activity
                        WHERE datname=current_database() AND wait_event_type='Lock'
                          AND query ILIKE '%FOR SHARE%'""")
                    if waiting:break
                    time.sleep(.025)
                assert waiting,"Leitura não aguardou bloqueio real"
                m.change_link(holder,users["admin"],pid,users["dent1"]["dentist_id"],"ADMIN",action="REVOKED")
                holder.commit()
            finally:
                holder.rollback()
            response=future.result(timeout=20)
    if kind=="list":
        passed=response.status_code==200 and response.json()["items"]==[] and response.json()["next_after_id"]==pid
        following=request("GET",prefix,ct,params={"q":"Race_list","limit":1,"after_id":pid})
        case("cursor-after-concurrent-revocation",
             following.status_code==200 and [x["patient_id"] for x in following.json()["items"]]==[tail["patient_id"]])
    else:passed=response.status_code==403 and "PATIENT_NAME_SENTINEL" not in response.text
    case("revoked-during-wait-"+kind,passed,http=response.status_code,waiters=waiting)
    case("race-revocation-recorded-"+kind,
         sql("SELECT status FROM clinical_access_links WHERE id=:id",id=link)[0]["status"]=="REVOKED")
# A sessão também precisa ser atualizada depois da espera de leitura.
victim=patient("PATIENT_NAME_SENTINEL_ReaderRace")
assert change(victim).status_code==200
pid=victim["patient_id"]
with Session(engine) as holder:
    holder.execute(text("SELECT id FROM patients WHERE id=:id FOR UPDATE"),{"id":pid}).all()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(request,"GET",prefix,ct,params={"q":"ReaderRace"})
        try:
            waiting=[]
            for _ in range(200):
                waiting=sql("""SELECT pid,wait_event_type,wait_event FROM pg_stat_activity
                    WHERE datname=current_database() AND wait_event_type='Lock'
                      AND query ILIKE '%FOR SHARE%'""")
                if waiting:break
                time.sleep(.025)
            assert waiting
            holder.execute(text("UPDATE users SET session_version=session_version+1 WHERE id=:id"),
                           {"id":users["dent1"]["id"]})
            holder.commit()
        finally:
            holder.rollback()
        response=future.result(timeout=20)
case("session-invalidated-during-wait",response.status_code==401 and
     "PATIENT_NAME_SENTINEL" not in response.text,waiters=waiting)
login=request("POST","/api/v1/auth/login",body={"email":"dent1@qa.test","password":"FicticioLogin2026!"})
assert login.status_code==200
users["dent1"]["access"]=login.json()["access_token"]
unlock=request("POST","/api/v1/auth/clinical-unlock",users["dent1"]["access"],{"password":"FicticioClinical2026!"})
assert unlock.status_code==200
ct=unlock.json()["clinical_token"]
# Clínica e sessão continuam verificadas a cada requisição.
sql("UPDATE clinics SET is_active=false WHERE id=:id",id=clinics[0])
case("inactive-clinic",request("GET",prefix,ct).status_code==403)
sql("UPDATE clinics SET is_active=true WHERE id=:id",id=clinics[0])
sql("UPDATE users SET is_active=false,session_version=session_version+1 WHERE id=:id",id=users["dent1"]["id"])
case("inactive-reader",request("GET",prefix,ct).status_code==401)

# Contratos antigos permanecem arrays, e logging identifica as novas rotas.
paths=request("GET","/openapi.json").json()["paths"]
case("new-openapi-routes",prefix in paths and prefix+"/{patient_id}" in paths)
case("legacy-patients-array",isinstance(request("GET","/api/v1/patients",users["admin"]["access"]).json(),list))
case("legacy-dentists-array",isinstance(request("GET","/api/v1/dentists",users["admin"]["access"]).json(),list))
case("legacy-access-links-array",isinstance(request("GET","/api/v1/access-links",users["admin"]["access"]).json(),list))
Path("/tmp/access-results.json").write_text(json.dumps(results,indent=2))
print(json.dumps({"passed":len(results),"failed":0,"real_http":True}))
