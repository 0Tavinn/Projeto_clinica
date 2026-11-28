
"""QA independente das leituras clinicas/vinculos. Somente DB descartavel."""
from pathlib import Path
import os,json,time,datetime,concurrent.futures as cf
import httpx
from sqlalchemy import create_engine,text
from sqlalchemy.orm import Session
from sqlalchemy.engine import make_url
from app import main as m
U=make_url(os.environ["DATABASE_URL"])
assert U.host=="pg" and U.database.startswith("links_qa_") and U.username=="qa_n05"
E=create_engine(U,connect_args={"options":"-c statement_timeout=12000"})
BASE="http://api:8000"
PREFIX="/api/v1/clinical/patients"
FIELDS={"patient_id","full_name","medical_record_number","medical_record_id","access_link_id"}
MARKERS=["QA Sensitive ","QA-MR-","QA_QUERY_PRIVATE_7832","QA_PATH_PRIVATE_9371","QA_HEADER_PRIVATE_5826","QA CLINICAL PRIVATE 6391"]
tokens=[];R=[]
def secret_save():
 p=Path("/tmp/qa-sensitive.json");p.write_text(json.dumps({"markers":MARKERS,"tokens":tokens}));p.chmod(0o600)
def sql(statement,**params):
 with E.begin() as db:
  x=db.execute(text(statement),params)
  return [dict(r) for r in x.mappings()] if x.returns_rows else []
def req(method,path,t=None,body=None,**kw):
 headers={"X-QA-Sensitive":MARKERS[4],"Connection":"close"}
 if t:headers["Authorization"]="Bearer "+t
 with httpx.Client(base_url=BASE,timeout=25,headers=headers) as c:
  return c.request(method,path,json=body,**kw)
def case(id,expected,fn):
 try:ok,got=fn();row={"id":id,"expected":expected,"obtained":got,"status":"aprovado" if ok else "reprovado"}
 except Exception as ex:row={"id":id,"expected":expected,"obtained":{"qa_exception_type":type(ex).__name__},"status":"bloqueado"}
 R.append(row);Path("/tmp/qa-results.json").write_text(json.dumps(R,indent=2));print("QA_CASE "+json.dumps(row),flush=True)
def noecho(r):return not any(v and v in r.text for v in MARKERS+tokens)
def status(method,path,t,body,expected,**kw):
 r=req(method,path,t,body,**kw)
 return r.status_code==expected and noecho(r),{"http":r.status_code,"no_echo":noecho(r)}
for _ in range(100):
 try:
  if req("GET","/health").status_code==200:break
 except httpx.HTTPError:pass
 time.sleep(.1)
else:raise RuntimeError("QA API readiness")
secret_save()
clinics=[sql("INSERT INTO clinics(name,cnpj,email) VALUES(:n,:c,:e) RETURNING id",n="QA Clinica "+str(i),c=str(83000000000000+i),e=f"clinic{i}@qa.invalid")[0]["id"] for i in [0,1]]
US={}
def login(name):
 r=req("POST","/api/v1/auth/login",body={"email":name+"@qa.invalid","password":"FicticioLogin2026!"});assert r.status_code==200
 t=r.json()["access_token"];tokens.append(t);secret_save();return t
def refresh():
 US["d1"]["access"]=login("d1")
 r=req("POST","/api/v1/auth/clinical-unlock",US["d1"]["access"],{"password":"FicticioClinical2026!"});assert r.status_code==200
 US["d1"]["clinical"]=r.json()["clinical_token"];tokens.append(US["d1"]["clinical"]);secret_save();return US["d1"]["clinical"]
for i,(name,role,ci,prof,pw) in enumerate([("admin","ADMINISTRATOR",0,False,True),("recep","RECEPTIONIST",0,False,True),("d1","DENTIST",0,True,True),("d2","DENTIST",0,True,True),("foreign","DENTIST",1,True,True),("admin2","ADMINISTRATOR",1,False,True),("inactive","DENTIST",0,True,True),("noprof","DENTIST",0,False,True),("nopwd","DENTIST",0,True,False)]):
 u=sql("INSERT INTO users(clinic_id,full_name,email,cpf,role,password_hash,clinical_password_hash) VALUES(:c,:n,:e,:cpf,:r,:ph,:ch) RETURNING *",c=clinics[ci],n="QA Sensitive "+name,e=name+"@qa.invalid",cpf=str(81000000000+i),r=role,ph=m.hasher.hash("FicticioLogin2026!"),ch=m.hasher.hash("FicticioClinical2026!") if pw else None)[0]
 if prof:u["dent"]=sql("INSERT INTO dentists(user_id,cro_number,cro_state) VALUES(:u,:cro,'PE') RETURNING id",u=u["id"],cro=str(81000+i))[0]["id"]
 US[name]=u;u["access"]=login(name)
 if prof and pw:
  r=req("POST","/api/v1/auth/clinical-unlock",u["access"],{"password":"FicticioClinical2026!"});assert r.status_code==200;u["clinical"]=r.json()["clinical_token"]
 else:u["clinical"]=m.token(u,"clinical",15) # QA-signed token for ineligible role/professional checks.
 tokens.append(u["clinical"]);secret_save()
CT=US["d1"]["clinical"];ADMIN=US["admin"]["access"]
count=0;PS={}
def newpatient(label,ci=0):
 global count
 count+=1
 r=req("POST","/api/v1/patients",US["admin" if ci==0 else "admin2"]["access"],{"full_name":"QA Sensitive "+label,"cpf":str(82000000000+count),"medical_record_number":"QA-MR-"+str(1000+count),"birth_date":"1990-01-01"})
 assert r.status_code==201
 return r.json()["patient_id"]
def change(p,d="d1",action="GRANTED",admin="admin"):
 return req("POST","/api/v1/admin/access",US[admin]["access"],{"patient_id":p,"dentist_id":US[d]["dent"],"action":action})
for label in ["Alpha","Beta","Percent%Name","Under_score","Bang!Name","InactivePatient","Revoked","OtherDentist","NoLink","Legacy","InactiveDentist","Appointment"]:
 PS[label]=newpatient(label)
for label in ["Alpha","Beta","Percent%Name","Under_score","Bang!Name","InactivePatient","Revoked","Legacy"]:assert change(PS[label]).status_code==200
assert change(PS["OtherDentist"],"d2").status_code==200
assert change(PS["InactiveDentist"],"inactive").status_code==200
PS["Foreign"]=newpatient("Foreign",1);assert change(PS["Foreign"],"foreign",admin="admin2").status_code==200
assert change(PS["Revoked"],action="REVOKED").status_code==200
sql("UPDATE patients SET is_active=false WHERE id=:id",id=PS["InactivePatient"])
sql("DELETE FROM medical_records WHERE patient_id=:p",p=PS["Legacy"])
VISIBLE={PS[x] for x in ["Alpha","Beta","Percent%Name","Under_score","Bang!Name","Legacy"]}
def listing(t=CT,**params):return req("GET",PREFIX,t,params=params)
def main_list():
 r=listing();b=r.json()
 return r.status_code==200 and {x["patient_id"] for x in b["items"]}==VISIBLE and b["limit"]==50 and b["next_after_id"] is None,{"http":r.status_code,"visible_count":len(b["items"]),"default_limit":b["limit"]}
case("L01-own-active-scope","somente6 ativos vinculados do proprio dentista",main_list)
def dto():
 rs=[listing(),req("GET",PREFIX+"/"+str(PS["Alpha"]),CT)]
 items=rs[0].json()["items"]+[rs[1].json()]
 return all(set(x)==FIELDS for x in items),{"all_exactly_five_fields":all(set(x)==FIELDS for x in items),"items_checked":len(items)}
case("L02-minimal-dto","cinco campos;sem CPF/contato/notas/credenciais",dto)
def empty_manual():
 p=PS["Beta"]
 facts=sql("SELECT (SELECT count(*) FROM appointments WHERE patient_id=:p) a,(SELECT count(*) FROM clinical_evolutions e JOIN medical_records r ON r.id=e.medical_record_id WHERE r.patient_id=:p) e,(SELECT count(*) FROM medical_records WHERE patient_id=:p) r",p=p)[0]
 r=req("GET",PREFIX+"/"+str(p),CT)
 return r.status_code==200 and facts=={"a":0,"e":0,"r":1},{"http":r.status_code,"appointments":facts["a"],"evolutions":facts["e"],"records":facts["r"]}
case("L03-admin-link-empty-record","vinculo manual sem consulta/evolucao aparece",empty_manual)
def nullable_legacy():
 before=sql("SELECT count(*) n FROM medical_records")[0]["n"]
 r=req("GET",PREFIX+"/"+str(PS["Legacy"]),CT);l=listing()
 after=sql("SELECT count(*) n FROM medical_records")[0]["n"]
 x=next(i for i in l.json()["items"] if i["patient_id"]==PS["Legacy"])
 return r.status_code==200 and r.json()["medical_record_id"] is None and x["medical_record_id"] is None and before==after,{"http":r.status_code,"nullable":r.json().get("medical_record_id") is None,"record_count_unchanged":before==after}
case("L04-read-no-create-nullable","legado sem prontuario retorna null;GET nao cria",nullable_legacy)
for name,token,expected in [("other-dentist",US["d2"]["clinical"],{PS["OtherDentist"]}),("other-clinic",US["foreign"]["clinical"],{PS["Foreign"]})]:
 def f(token=token,expected=expected):
  r=listing(token);return r.status_code==200 and {x["patient_id"] for x in r.json()["items"]}==expected,{"http":r.status_code,"scope_matches":{x["patient_id"] for x in r.json()["items"]}==expected}
 case("L05-"+name,"lista restrita ao proprio contexto",f)
for label in ["Revoked","OtherDentist","NoLink","Foreign"]:
 case("L06-guessed-"+label,"403 sem identificacao",lambda label=label:status("GET",PREFIX+"/"+str(PS[label]),CT,None,403))
case("L07-inactive-patient","404;paciente inativo sem identificacao",lambda:status("GET",PREFIX+"/"+str(PS["InactivePatient"]),CT,None,404))
def tamper_selector():
 r=listing(dentist_id=US["d2"]["dent"]);ids={x["patient_id"] for x in r.json()["items"]}
 return r.status_code==200 and ids==VISIBLE,{"http":r.status_code,"client_selector_did_not_change_scope":ids==VISIBLE}
case("L08-client-dentist-ignored","dentista derivado da sessao;query nao amplia escopo",tamper_selector)
def cursor():
 seen=[];after=0;pages=0
 while True:
  r=listing(limit=2,after_id=after);assert r.status_code==200
  b=r.json();assert set(b)=={"items","limit","next_after_id"} and b["limit"]==2
  seen += [x["patient_id"] for x in b["items"]];pages+=1
  nxt=b["next_after_id"]
  if nxt is None:break
  assert nxt>after;after=nxt;assert pages<12
 return seen==sorted(VISIBLE) and len(seen)==len(set(seen)),{"pages":pages,"unique_count":len(set(seen)),"ascending_no_duplicates":seen==sorted(VISIBLE) and len(seen)==len(set(seen))}
case("P01-cursor","cursor crescente;sem duplicar;sem total/offset inventados",cursor)
case("P02-after-last","pagina vazia terminal",lambda:(listing(after_id=999999).json()=={"items":[],"limit":50,"next_after_id":None},"terminal empty"))
number=sql("SELECT medical_record_number FROM patients WHERE id=:id",id=PS["Alpha"])[0]["medical_record_number"]
for name,query,expected in [("name","aLpHa",PS["Alpha"]),("record-number",number,PS["Alpha"]),("percent","%",PS["Percent%Name"]),("underscore","_",PS["Under_score"]),("escape-bang","!",PS["Bang!Name"])]:
 def f(query=query,expected=expected):
  r=listing(q=query);ids=[x["patient_id"] for x in r.json()["items"]]
  return r.status_code==200 and ids==[expected],{"http":r.status_code,"exact_expected_id_set":ids==[expected]}
 case("P03-search-"+name,"busca literal em nome/numero",f)
for name,params in [("limit-zero",{"limit":0}),("limit-over",{"limit":101}),("limit-text",{"limit":MARKERS[2]}),("after-negative",{"after_id":-1}),("q-empty",{"q":""}),("q-space",{"q":" "}),("q-long",{"q":"x"*129})]:
 case("P04-invalid-"+name,"422 sem eco",lambda params=params:status("GET",PREFIX,CT,None,422,params=params))
for name,t in [("absent",None),("wrong-type",US["d1"]["access"]),("invalid",MARKERS[2]),("admin-access",ADMIN),("reception-access",US["recep"]["access"]),("admin-clinical",US["admin"]["clinical"]),("reception-clinical",US["recep"]["clinical"]),("expired",m.token(US["d1"],"clinical",-1)),("no-professional",US["noprof"]["clinical"])]:
 if t:tokens.append(t)
 secret_save()
 def f(t=t,name=name):
  codes=[req("GET",path,t).status_code for path in [PREFIX,PREFIX+"/"+str(PS["Alpha"])]]
  expected=403 if name=="no-professional" else 401
  return codes==[expected,expected],{"http":codes}
 case("A01-"+name,"ambas rotas recusam perfil/token",f)
for kind in ["user","clinic"]:
 def f(kind=kind):
  statement="UPDATE "+("users" if kind=="user" else "clinics")+" SET is_active=:v WHERE id=:id"
  id=US["d1"]["id"] if kind=="user" else clinics[0]
  sql(statement,v=False,id=id)
  try:rs=[req("GET",p,CT) for p in [PREFIX,PREFIX+"/"+str(PS["Alpha"])]];codes=[r.status_code for r in rs];private=all(noecho(r) for r in rs)
  finally:sql(statement,v=True,id=id)
  expected=401 if kind=="user" else 403
  return codes==[expected,expected] and private,{"http":codes,"no_echo":private}
 case("A02-inactive-"+kind,"ambas rotas negam estado inativo atual",f)
# Administrative DTO and retained filters.
OLD={"id","clinic_id","patient_id","dentist_id","status","version","created_at","updated_at"}
NEW={"patient_full_name","patient_medical_record_number","patient_is_active","dentist_full_name","dentist_is_active","dentist_user_id","dentist_cro_number","dentist_cro_state"}
def admin_array():
 r=req("GET","/api/v1/access-links",ADMIN,params={"patient_id":PS["Alpha"],"dentist_id":US["d1"]["dent"]})
 b=r.json();x=b[0]
 return r.status_code==200 and isinstance(b,list) and len(b)==1 and OLD|NEW<=set(x) and x["dentist_user_id"]==US["d1"]["id"],{"http":r.status_code,"array":isinstance(b,list),"legacy_fields_retained":OLD<=set(x),"enriched_fields":NEW<=set(x)}
case("M01-admin-enriched-array","array legado com campos antigos e nomes/flags",admin_array)
def admin_paging():
 r=req("GET","/api/v1/access-links",ADMIN,params={"dentist_id":US["d1"]["dent"],"limit":1,"offset":0})
 r2=req("GET","/api/v1/access-links",ADMIN,params={"dentist_id":US["d1"]["dent"],"limit":1,"offset":1})
 return r.status_code==r2.status_code==200 and len(r.json())==len(r2.json())==1 and r.json()[0]["id"]!=r2.json()[0]["id"],{"http":[r.status_code,r2.status_code],"offset_preserved":True}
case("M02-admin-filters-offset","filtros antigos;limit/offset mantidos",admin_paging)
for name in ["recep","d1"]:
 case("M03-admin-only-"+name,"403",lambda name=name:status("GET","/api/v1/access-links",US[name]["access"],None,403))
def admin_isolation():
 r=req("GET","/api/v1/access-links",US["admin2"]["access"])
 foreign_change=change(PS["Alpha"],action="REVOKED",admin="admin2")
 return r.status_code==200 and all(x["clinic_id"]==clinics[1] for x in r.json()) and foreign_change.status_code==404,{"http":r.status_code,"foreign_mutation":foreign_change.status_code,"rows_own_clinic":all(x["clinic_id"]==clinics[1] for x in r.json())}
case("M04-clinic-isolation","lista e mutacao administrativa isoladas",admin_isolation)
# Preserve clinical data on inactive target revocation.
sql("UPDATE users SET is_active=false WHERE id=:id",id=US["inactive"]["id"])
for label,dentname in [("InactivePatient","d1"),("InactiveDentist","inactive")]:
 def f(label=label,dentname=dentname):
  pid=PS[label]
  rec=sql("SELECT * FROM medical_records WHERE patient_id=:p",p=pid)
  # Controlled fictional legacy content only in scratch database.
  if not sql("SELECT id FROM clinical_evolutions WHERE medical_record_id=:r",r=rec[0]["id"]):
   sql("INSERT INTO clinical_evolutions(medical_record_id,dentist_id,description) VALUES(:r,:d,:s)",r=rec[0]["id"],d=US[dentname]["dent"],s=MARKERS[5])
  before=sql("SELECT * FROM clinical_evolutions WHERE medical_record_id=:r ORDER BY id",r=rec[0]["id"])
  r=req("GET","/api/v1/access-links",ADMIN,params={"patient_id":pid});row=r.json()[0]
  event=sql("SELECT count(*) n FROM clinical_access_events WHERE link_id=:id",id=row["id"])[0]["n"]
  audit=sql("SELECT count(*) n FROM audit_logs WHERE resource='clinical_access_link' AND details=:id",id=str(row["id"]))[0]["n"]
  mutation=change(pid,dentname,"REVOKED")
  current=sql("SELECT status FROM clinical_access_links WHERE id=:id",id=row["id"])[0]["status"]
  ec=sql("SELECT count(*) n FROM clinical_access_events WHERE link_id=:id",id=row["id"])[0]["n"]-event
  ac=sql("SELECT count(*) n FROM audit_logs WHERE resource='clinical_access_link' AND details=:id",id=str(row["id"]))[0]["n"]-audit
  same=rec==sql("SELECT * FROM medical_records WHERE patient_id=:p",p=pid) and before==sql("SELECT * FROM clinical_evolutions WHERE medical_record_id=:r ORDER BY id",r=rec[0]["id"])
  expected_flags=(label!="InactivePatient",label!="InactiveDentist")
  return mutation.status_code==200 and current=="REVOKED" and ec==ac==1 and same and (row["patient_is_active"],row["dentist_is_active"])==expected_flags,{"http":mutation.status_code,"flags":[row["patient_is_active"],row["dentist_is_active"]],"state":current,"event_increment":ec,"audit_increment":ac,"clinical_data_unchanged":same}
 case("M05-revoke-"+label,"inativo identificavel;revogacao200 com evento/auditoria;dados preservados",f)
 for action in ["GRANTED","REACTIVATED"]:
  expected=404 if label=="InactivePatient" else 422
  case("M06-inactive-"+label+"-"+action,"concessao/reativacao inativa recusada",lambda label=label,dentname=dentname,action=action,expected=expected:status("POST","/api/v1/admin/access",ADMIN,{"patient_id":PS[label],"dentist_id":US[dentname]["dent"],"action":action},expected))
case("M07-no-clinical-password-grant","regra atual permite conceder a profissional ativo sem senha clinica",lambda:(change(PS["NoLink"],"nopwd").status_code==200,{"http_expected":200,"criterion":"comportamento implementado;nao nova decisao clinica"}))
# Existing appointment origin lifecycle, no old D02/D04 rule imposed.
def appointment_lifecycle():
 p=PS["Appointment"];stamp=datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=15)
 a=req("POST","/api/v1/appointments",US["recep"]["access"],{"patient_id":p,"dentist_id":US["d1"]["dent"],"scheduled_at":stamp.isoformat()});assert a.status_code==201
 aid=a.json()["appointment_id"]
 cancel=req("DELETE","/api/v1/appointments/"+str(aid),US["recep"]["access"])
 aftercancel=req("GET",PREFIX+"/"+str(p),CT)
 rev=change(p,action="REVOKED")
 old=req("PATCH","/api/v1/appointments/"+str(aid),US["recep"]["access"],{"status":"CONFIRMED","notes":"QA administrative"})
 oldcancel=req("DELETE","/api/v1/appointments/"+str(aid),US["recep"]["access"])
 denied=req("GET",PREFIX+"/"+str(p),CT)
 new=req("POST","/api/v1/appointments",US["recep"]["access"],{"patient_id":p,"dentist_id":US["d1"]["dent"],"scheduled_at":(stamp+datetime.timedelta(days=1)).isoformat()})
 allowed=req("GET",PREFIX+"/"+str(p),CT)
 codes=[cancel.status_code,aftercancel.status_code,rev.status_code,old.status_code,oldcancel.status_code,denied.status_code,new.status_code,allowed.status_code]
 return codes==[200,200,200,200,200,403,201,200],{"http_sequence":codes,"scheduled_at_timezone":"+00:00;fixture"}
case("M08-appointment-lifecycle","cancelamento preserva;consulta antiga nao reabre;novo agendamento reativa",appointment_lifecycle)
# PostgreSQL independent connections and real waiters, no sleeps-only proof.
def waiters():
 for _ in range(240):
  r=sql("SELECT pid,wait_event_type,wait_event FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query ILIKE '%FOR SHARE%'")
  if r:return r
  time.sleep(.025)
 raise RuntimeError("lock wait not proven")
def concurrent_read(kind,session_loss=False):
 global CT
 label=("Session " if session_loss else "Revoke ")+kind
 victim=newpatient("Race "+label+" First");assert change(victim).status_code==200
 tail=None
 if kind=="list":
  tail=newpatient("Race "+label+" Tail");assert change(tail).status_code==200
 path=PREFIX if kind=="list" else PREFIX+"/"+str(victim)
 params={"q":"Race "+label,"limit":1} if kind=="list" else None
 with Session(E) as holder:
  holder.execute(text("SELECT id FROM patients WHERE id=:p FOR UPDATE"),{"p":victim}).all()
  with cf.ThreadPoolExecutor(1) as pool:
   f=pool.submit(req,"GET",path,CT,params=params)
   try:
    ws=waiters()
    if session_loss:
     sql("UPDATE users SET session_version=session_version+1 WHERE id=:id",id=US["d1"]["id"])
     holder.commit()
    else:
     m.change_link(holder,US["admin"],victim,US["d1"]["dent"],"ADMIN",action="REVOKED")
     holder.commit()
   finally:holder.rollback()
   r=f.result(timeout=20)
 if session_loss:
  good=r.status_code==401 and noecho(r);result={"http":r.status_code,"waiters":ws,"no_echo":noecho(r)}
  CT=refresh()
 else:
  if kind=="list":
   b=r.json();nxt=req("GET",PREFIX,CT,params={"q":"Race "+label,"limit":1,"after_id":b["next_after_id"]})
   got=[x["patient_id"] for x in nxt.json()["items"]]
   good=r.status_code==200 and b["items"]==[] and b["next_after_id"]==victim and got==[tail]
   result={"http":r.status_code,"empty_page":b["items"]==[],"cursor_advanced":b["next_after_id"]==victim,"following_tail_found":got==[tail],"waiters":ws}
  else:good=r.status_code==403 and noecho(r);result={"http":r.status_code,"no_echo":noecho(r),"waiters":ws}
  result["link_state"]=sql("SELECT status FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d",p=victim,d=US["d1"]["dent"])[0]["status"]
  good=good and result["link_state"]=="REVOKED"
 return good,result
for session_loss in [False,True]:
 for kind in ["list","detail"]:
  case("C01-"+("session-loss" if session_loss else "revocation")+"-"+kind,"espera real;revalidacao apos commit;sem identificacao indevida",lambda kind=kind,session_loss=session_loss:concurrent_read(kind,session_loss))
# N05 and legacy search OpenCL. No concurrency history or benchmark repeated.
def opencl_search():
 r=req("POST","/api/v1/evolutions",CT,{"patient_id":PS["Alpha"],"description":MARKERS[5]});assert r.status_code==201
 cpu=req("GET","/api/v1/clinical/search",CT,params={"patient_id":PS["Alpha"],"q":MARKERS[5],"engine_name":"cpu"})
 cl=req("GET","/api/v1/clinical/search",CT,params={"patient_id":PS["Alpha"],"q":MARKERS[5],"engine_name":"opencl"})
 denied=req("GET","/api/v1/clinical/search",CT,params={"patient_id":PS["OtherDentist"],"q":MARKERS[5],"engine_name":"opencl"})
 return cpu.status_code==cl.status_code==200 and cl.json()["engine"]=="opencl" and cpu.json()["results"]==cl.json()["results"] and denied.status_code==403,{"cpu_http":cpu.status_code,"opencl_http":cl.status_code,"engine":cl.json().get("engine"),"equal_results":cpu.json().get("results")==cl.json().get("results"),"denied_http":denied.status_code}
case("N01-legacy-opencl-search","busca antiga realOpenCL e permissao preservadas",opencl_search)
for path in [PREFIX,PREFIX+"/"+str(PS["Alpha"])]:
 case("N02-minimal-after-content-"+("list" if path==PREFIX else "detail"),"conteudo clinico/rascunhos continuam foraDTO",lambda path=path:(all(set(x)==FIELDS for x in (req("GET",path,CT).json()["items"] if path==PREFIX else [req("GET",path,CT).json()])),"exact_fields_only"))
case("N03-new-route-error","422 sem eco dequery/nome/id sensivel",lambda:status("GET",PREFIX+"/"+MARKERS[3],CT,None,422,params={"q":MARKERS[2],MARKERS[2]:MARKERS[5]}))
doc=req("GET","/openapi.json");assert doc.status_code==200
Path("/tmp/qa-openapi.json").write_text(json.dumps(doc.json()))
with E.connect() as db:Path("/tmp/qa-pg-version.txt").write_text(db.scalar(text("SHOW server_version")))
secret_save()
print(json.dumps({"final_cases":len(R),"counts":{s:sum(x["status"]==s for x in R) for s in ["aprovado","reprovado","bloqueado"]}}),flush=True)
