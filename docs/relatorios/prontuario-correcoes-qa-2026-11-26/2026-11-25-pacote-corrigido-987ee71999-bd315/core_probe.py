
from qa_common import *
ids,tokens,ct=load();p=ids["patients"][0];users=ids["users"]
case("A-health","health200 conectado ao banco",lambda:status("GET","/health",None,None,200))
case("A-openapi","OpenAPI200",lambda:status("GET","/openapi.json",None,None,200))
case("REG-noauth","401",lambda:status("GET",f"/api/v1/patients/{p}/record",None,None,401))
case("REG-login-not-clinical","401",lambda:status("GET",f"/api/v1/patients/{p}/record",tokens["dent1"],None,401))
case("REG-admin-unlock","403",lambda:status("POST","/api/v1/auth/clinical-unlock",tokens["admin"],{"password":"ficticia"},403))
case("REG-reception-clinical","401",lambda:status("GET",f"/api/v1/patients/{p}/record",tokens["recep"],None,401))
case("REG-noprof","403",lambda:status("POST","/api/v1/auth/clinical-unlock",tokens["noprof"],{"password":"FicticioClinico2026!"},403))
case("REG-inactive-login","401",lambda:status("POST","/api/v1/auth/login",None,{"email":"inactive@qa.invalid","password":"FicticioLogin2026!"},401))
case("REG-foreign","nega outra clinica",lambda:(req("GET",f"/api/v1/patients/{p}/record",ct["foreign"]).status_code in [403,404],"acesso negado"))
case("REG-no-link","403",lambda:status("GET",f"/api/v1/patients/{ids['patients'][8]}/record",ct["dent1"],None,403))
def no_create():
 before=q("SELECT count(*) n FROM medical_records")[0]["n"]
 r=req("GET",f"/api/v1/patients/{p}/record",ct["dent1"])
 after=q("SELECT count(*) n FROM medical_records")[0]["n"]
 return r.status_code==200 and before==after,{"http":r.status_code,"count_before":before,"count_after":after}
case("REG-get-pure","GET nao cria",no_create)
e=create(ct["dent1"],p,"Clínica AÇÃO sensibilidade fictícia")
case("REG-private-list","rascunho ausente para outro dentista",lambda:(all(x["id"]!=e for x in req("GET",f"/api/v1/patients/{p}/evolutions",ct["dent2"]).json()),"rascunho privado na lista"))
case("REG-private-detail","403",lambda:status("GET",f"/api/v1/evolutions/{e}",ct["dent2"],None,403))
case("REG-other-author","403",lambda:status("PATCH",f"/api/v1/evolutions/{e}",ct["dent2"],{"version":1,"description":"tentativa ficticia"},403))
case("REG-empty-description","422",lambda:status("POST","/api/v1/evolutions",ct["dent1"],{"patient_id":p,"description":"   "},422))
case("REG-optional-appointment","422 para consulta incompatível",lambda:status("POST","/api/v1/evolutions",ct["dent1"],{"patient_id":p,"description":"teste","appointment_id":999999},422))
def invalid_versions():
 got=[]
 for endpoint in ["PATCH","FINALIZE"]:
  for v in ["1",True,None,0,-1,"missing"]:
   body={"version":v}
   if v=="missing":body={}
   if endpoint=="PATCH":body["notes"]="ficticia"
   method,path=("PATCH",f"/api/v1/evolutions/{e}") if endpoint=="PATCH" else ("POST",f"/api/v1/evolutions/{e}/finalize")
   r=req(method,path,ct["dent1"],body);got.append(r.status_code)
 row=q("SELECT version,status,notes FROM clinical_evolutions WHERE id=:id",id=e)[0]
 return all(c==422 for c in got) and row["version"]==1 and row["notes"] is None,{"http":got,"version":row["version"],"state":row["status"]}
case("N07-invalid-types","12 entradas invalidas422; sem mutacao",invalid_versions)
case("N07-current","200 versao atual",lambda:status("PATCH",f"/api/v1/evolutions/{e}",ct["dent1"],{"version":1,"notes":"nota ficticia"},200))
case("N07-stale-edit","409",lambda:status("PATCH",f"/api/v1/evolutions/{e}",ct["dent1"],{"version":1,"notes":"antiga"},409))
case("N07-stale-finalize","409",lambda:status("POST",f"/api/v1/evolutions/{e}/finalize",ct["dent1"],{"version":1},409))
case("REG-finalize","200 sem consulta obrigatoria",lambda:status("POST",f"/api/v1/evolutions/{e}/finalize",ct["dent1"],{"version":2},200))
case("REG-shared-finalized","200 dentista vinculado",lambda:status("GET",f"/api/v1/evolutions/{e}",ct["dent2"],None,200))
case("REG-finalized-edit","403",lambda:status("PATCH",f"/api/v1/evolutions/{e}",ct["dent1"],{"version":3,"notes":"indevida"},403))
def errors_private():
 sentinel="QA_PRIVATE_SENTINEL_20261125"
 cases=[
 ("POST","/api/v1/evolutions",ct["dent1"],{"description":sentinel,"notes":sentinel}),
 ("PATCH",f"/api/v1/evolutions/{e}",ct["dent1"],{"version":"bad","description":sentinel,"notes":sentinel}),
 ("POST","/api/v1/auth/login",None,{"password":sentinel}),
 ("POST","/api/v1/auth/clinical-unlock",tokens["dent1"],{"password":[sentinel]}),
 ("POST","/api/v1/users",tokens["admin"],{"full_name":sentinel,"password":sentinel,"unexpected_"+sentinel:sentinel})]
 stats=[]
 for method,path,t,body in cases:
  r=req(method,path,t,body)
  stats.append({"http":r.status_code,"echo":sentinel in r.text,"useful_loc":bool(r.json().get("detail"))})
 return all(x["http"]==422 and not x["echo"] and x["useful_loc"] for x in stats),stats
case("N05-validation-body","422 sem sentinela ou ctx/input indevidos",errors_private)
def user_public():
 r=req("PATCH",f"/api/v1/users/{users['dent2']['id']}",tokens["admin"],{"full_name":"Dentista QA alterado"})
 forbidden={"password_hash","clinical_password_hash","session_version","clinical_version"}
 found=sorted(forbidden&set(r.json()))
 return r.status_code==200 and not found,{"http":r.status_code,"forbidden_keys":found}
case("N05-user-update","200 sem hashes/sessao",user_public)
# Same text in two authorized patients, third unlinked.
p2=ids["patients"][1];create(ct["dent1"],p2,"Clínica AÇÃO sensibilidade fictícia")
case("N06-patient-scope","somente patient_id solicitado",lambda:(all(x["patient_id"]==p for x in req("GET","/api/v1/clinical/search",ct["dent1"],params={"patient_id":p,"q":"acao","engine_name":"cpu"}).json()["results"]),"ids restritos ao paciente"))
def bad_patient():
 codes=[]
 for v in [None,0,-1,"bad",ids["patients"][8]]:
  params={"q":"acao","engine_name":"cpu"}
  if v is not None:params["patient_id"]=v
  r=req("GET","/api/v1/clinical/search",ct["dent1"],params=params);codes.append(r.status_code)
 return codes==[422,422,422,422,403],codes
case("N06-invalid-or-unlinked","ausente/invalido422; semvinculo403",bad_patient)
case("N06-foreign","403ou404 sem outra clinica",lambda:(req("GET","/api/v1/clinical/search",ct["foreign"],params={"patient_id":p,"q":"acao"}).status_code in [403,404],"outra clinica negada"))
def bad_terms():
 codes=[]
 for mode in ["cpu","auto","opencl"]:
  for term in [None,"","   ","́"]:
   params={"patient_id":p,"engine_name":mode}
   if term is not None:params["q"]=term
   codes.append(req("GET","/api/v1/clinical/search",ct["dent1"],params=params).status_code)
 return all(c==422 for c in codes),codes
case("N08-empty-normalized","12 casos422 em todos motores; sem503",bad_terms)
def actual_opencl():
 a=req("GET","/api/v1/clinical/search",ct["dent1"],params={"patient_id":p,"q":"AÇÃO","engine_name":"cpu"})
 b=req("GET","/api/v1/clinical/search",ct["dent1"],params={"patient_id":p,"q":"AÇÃO","engine_name":"opencl"})
 return a.status_code==b.status_code==200 and b.json()["engine"]=="opencl" and a.json()["results"]==b.json()["results"],{"cpu_http":a.status_code,"opencl_http":b.status_code,"engine":b.json().get("engine"),"same_results":a.json().get("results")==b.json().get("results")}
case("REG-real-opencl","kernel real e igualdade CPU",actual_opencl)
# Agenda DTOs and link lifecycle. Future timezone-aware dates.
pa=ids["patients"][2]
def agenda():
 body={"patient_id":pa,"dentist_id":users["dent1"]["dent"],"scheduled_at":(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=10)).isoformat(),"duration_minutes":30}
 a=req("POST","/api/v1/appointments",tokens["recep"],body)
 assert a.status_code==201
 aid=a.json()["appointment_id"]
 responses=[a,req("GET","/api/v1/appointments",tokens["recep"]),req("GET",f"/api/v1/appointments/{aid}",tokens["recep"]),req("GET","/api/v1/appointments",tokens["recep"],params={"patient_id":pa,"dentist_id":users["dent1"]["dent"]}),req("PATCH",f"/api/v1/appointments/{aid}",tokens["recep"],{"notes":"administrativo ficticio"}),req("DELETE",f"/api/v1/appointments/{aid}",tokens["recep"])]
 codes=[x.status_code for x in responses]
 no_range=all("scheduled_period" not in x.text for x in responses)
 state=q("SELECT status FROM appointments WHERE id=:id",id=aid)[0]["status"]
 json.dump({"appointment":aid,"patient":pa},open("/tmp/qa-agenda.json","w"))
 return codes==[201,200,200,200,200,200] and no_range and state=="CANCELED",{"http":codes,"range_exposed":not no_range,"persisted":state}
case("N02-CRUD-DTO","201/200 coerentes, scheduled_period foraDTO",agenda)
def lifecycle():
 a=json.load(open("/tmp/qa-agenda.json"));aid=a["appointment"]
 preserved=req("GET",f"/api/v1/patients/{pa}/record",ct["dent1"]).status_code
 assert grant(tokens["admin"],pa,users["dent1"]["dent"],"REVOKED").status_code==200
 update=req("PATCH",f"/api/v1/appointments/{aid}",tokens["recep"],{"status":"CONFIRMED"})
 revoked=req("GET",f"/api/v1/patients/{pa}/record",ct["dent1"]).status_code
 new=req("POST","/api/v1/appointments",tokens["recep"],{"patient_id":pa,"dentist_id":users["dent1"]["dent"],"scheduled_at":(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=12)).isoformat()})
 after=req("GET",f"/api/v1/patients/{pa}/record",ct["dent1"]).status_code
 return [preserved,update.status_code,revoked,new.status_code,after]==[200,200,403,201,200],{"after_cancel":preserved,"old_update":update.status_code,"after_old":revoked,"new":new.status_code,"after_new":after}
case("REG-durable-link","cancelamento preserva; antiga nao reativa; nova reativa",lifecycle)
# Audit and revocation for inactive/no-password targets, restore fixture conditions.
def revoke_special():
 results=[]
 for mode in ["patient_inactive","dentist_inactive","no_clinical_password"]:
  patient=ids["patients"][3]
  link=q("SELECT id FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d",p=patient,d=users["dent1"]["dent"])[0]["id"]
  q("UPDATE patients SET is_active=true WHERE id=:id",id=patient)
  q("UPDATE users SET is_active=true WHERE id=:id",id=users["dent1"]["id"])
  if mode=="patient_inactive":q("UPDATE patients SET is_active=false WHERE id=:id",id=patient)
  if mode=="dentist_inactive":q("UPDATE users SET is_active=false WHERE id=:id",id=users["dent1"]["id"])
  oldhash=None
  if mode=="no_clinical_password":
   oldhash=q("SELECT clinical_password_hash h FROM users WHERE id=:id",id=users["dent1"]["id"])[0]["h"]
   q("UPDATE users SET clinical_password_hash=NULL WHERE id=:id",id=users["dent1"]["id"])
  before=q("SELECT count(*) n FROM clinical_access_events WHERE link_id=:id",id=link)[0]["n"]
  a=grant(tokens["admin"],patient,users["dent1"]["dent"],"REVOKED")
  row=q("SELECT status FROM clinical_access_links WHERE id=:id",id=link)[0]
  ev=q("SELECT count(*) n FROM clinical_access_events WHERE link_id=:id AND action='REVOKED'",id=link)[0]["n"]
  audit=q("SELECT count(*) n FROM audit_logs WHERE action='ACCESS_REVOKED' AND details=:id",id=str(link))[0]["n"]
  results.append({"mode":mode,"http":a.status_code,"state":row["status"],"events_total_delta":q("SELECT count(*) n FROM clinical_access_events WHERE link_id=:id",id=link)[0]["n"]-before,"revocation_events":ev,"audit":audit})
  q("UPDATE patients SET is_active=true WHERE id=:id",id=patient)
  q("UPDATE users SET is_active=true WHERE id=:id",id=users["dent1"]["id"])
  if oldhash:q("UPDATE users SET clinical_password_hash=:h WHERE id=:id",h=oldhash,id=users["dent1"]["id"])
  assert grant(tokens["admin"],patient,users["dent1"]["dent"],"REACTIVATED").status_code==200
 return all(x["http"]==200 and x["state"]=="REVOKED" and x["events_total_delta"]==1 and x["audit"]>=1 for x in results),results
case("N04-revoke-inactive-and-no-password","200;REVOKED;evento/auditoria atomicos",revoke_special)
def ineligible_grant():
 patient=ids["patients"][4]
 assert grant(tokens["admin"],patient,users["dent1"]["dent"],"REVOKED").status_code==200
 q("UPDATE patients SET is_active=false WHERE id=:id",id=patient)
 a=grant(tokens["admin"],patient,users["dent1"]["dent"],"REACTIVATED")
 q("UPDATE patients SET is_active=true WHERE id=:id",id=patient)
 q("UPDATE users SET is_active=false WHERE id=:id",id=users["dent1"]["id"])
 b=grant(tokens["admin"],patient,users["dent1"]["dent"],"REACTIVATED")
 q("UPDATE users SET is_active=true WHERE id=:id",id=users["dent1"]["id"])
 assert grant(tokens["admin"],patient,users["dent1"]["dent"],"REACTIVATED").status_code==200
 return a.status_code==404 and b.status_code==422,{"inactive_patient":a.status_code,"inactive_dentist":b.status_code}
case("N04-grant-eligibility","inativos nao recebem reativacao",ineligible_grant)
json.dump({"evolution":e,"patient":p},open("/tmp/qa-core.json","w"))
