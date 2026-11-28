
from qa_common import *
ids=json.load(open("/tmp/qa-fixture.json"));tokens={n:login(n) for n in ["admin","recep","dent1"]};ct={"dent1":unlock(tokens["dent1"])};users=ids["users"];p=ids["patients"][5];dent=users["dent1"]["dent"];admin=tokens["admin"]
create(ct["dent1"],p,"AÇÃO corrida de autorização fictícia")
def ensure_active():
 row=q("SELECT status FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d",p=p,d=dent)[0]
 if row["status"]=="REVOKED":assert grant(admin,p,dent,"REACTIVATED").status_code==200
def search_lock(mode):
 ensure_active()
 with E.begin() as holder:
  link=holder.execute(text("SELECT id FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d FOR UPDATE"),{"p":p,"d":dent}).scalar_one()
  with cf.ThreadPoolExecutor(1) as pool:
   future=pool.submit(req,"GET","/api/v1/clinical/search",ct["dent1"],None,params={"patient_id":p,"q":"acao","engine_name":mode})
   waits=waitlocks()
   holder.execute(text("UPDATE clinical_access_links SET status='REVOKED',version=version+1 WHERE id=:id"),{"id":link})
   holder.commit()
   response=future.result(timeout=20)
 state=q("SELECT status FROM clinical_access_links WHERE id=:id",id=link)[0]["status"]
 return response.status_code==403 and state=="REVOKED" and "results" not in response.json(),{"engine_requested":mode,"http":response.status_code,"state":state,"waiters":waits,"results_exposed":"results" in response.json()}
for mode in ["cpu","opencl"]:
 case("N01-lock-"+mode,"403 apos revogacao confirmada durante espera real",lambda mode=mode:search_lock(mode))
ensure_active()
def inactive_wait(kind):
 updates={"user":("UPDATE users SET is_active=:active WHERE id=:id",users["dent1"]["id"],401),"clinic":("UPDATE clinics SET is_active=:active WHERE id=:id",ids["clinics"][0],403),"patient":("UPDATE patients SET is_active=:active WHERE id=:id",p,404)}
 sql,id,code=updates[kind]
 response=None
 try:
  with E.begin() as holder:
   holder.execute(text("SELECT id FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d FOR UPDATE"),{"p":p,"d":dent})
   with cf.ThreadPoolExecutor(1) as pool:
    future=pool.submit(req,"GET","/api/v1/clinical/search",ct["dent1"],None,params={"patient_id":p,"q":"acao","engine_name":"opencl"})
    waits=waitlocks()
    q(sql,active=False,id=id)
    holder.commit()
    response=future.result(timeout=20)
 finally:q(sql,active=True,id=id)
 return response.status_code==code and "results" not in response.json(),{"kind":kind,"http":response.status_code,"waiters":waits,"policy":"implementacao observada; D06/limites clinicos nao aprovados por este teste"}
for kind in ["user","clinic","patient"]:
 case("REG-inactivation-wait-"+kind,"nega segundo estado atual apos espera",lambda kind=kind:inactive_wait(kind))
# Revocation while mutation waits; compare all sensitive persisted fields by equality.
def revoke_mutation(action):
 ensure_active();eid=create(ct["dent1"],p)
 before=q("SELECT description,notes,status,version,finalized_at FROM clinical_evolutions WHERE id=:id",id=eid)[0]
 with E.begin() as holder:
  link=holder.execute(text("SELECT id FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d FOR UPDATE"),{"p":p,"d":dent}).scalar_one()
  with cf.ThreadPoolExecutor(1) as pool:
   method,path,body=("PATCH",f"/api/v1/evolutions/{eid}",{"version":1,"description":"não persistir"}) if action=="edit" else ("POST",f"/api/v1/evolutions/{eid}/finalize",{"version":1})
   future=pool.submit(req,method,path,ct["dent1"],body)
   waits=waitlocks()
   holder.execute(text("UPDATE clinical_access_links SET status='REVOKED',version=version+1 WHERE id=:id"),{"id":link})
   holder.commit();response=future.result(timeout=20)
 after=q("SELECT description,notes,status,version,finalized_at FROM clinical_evolutions WHERE id=:id",id=eid)[0]
 ensure_active()
 return response.status_code==403 and before==after,{"http":response.status_code,"unchanged":before==after,"state":after["status"],"version":after["version"],"waiters":waits}
for action in ["edit","finalize"]:
 case("REG-revoke-"+action,"403 e conteudo/estado/versao intactos",lambda action=action:revoke_mutation(action))
def two_edits():
 eid=create(ct["dent1"],p)
 with E.begin() as holder:
  holder.execute(text("SELECT id FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d FOR UPDATE"),{"p":p,"d":dent})
  with cf.ThreadPoolExecutor(2) as pool:
   fs=[pool.submit(req,"PATCH",f"/api/v1/evolutions/{eid}",ct["dent1"],{"version":1,"description":"Texto fictício "+s}) for s in ["A","B"]]
   waits=waitlocks(2);holder.commit();responses=[f.result(timeout=20) for f in fs]
 codes=sorted(r.status_code for r in responses)
 winner=next((r for r in responses if r.status_code==200),None)
 row=q("SELECT description,status,version FROM clinical_evolutions WHERE id=:id",id=eid)[0]
 matched=winner is not None and row["description"]==winner.json()["description"]
 return codes==[200,409] and row["version"]==2 and matched,{"http":codes,"version":row["version"],"winner_content_matches":matched,"waiters":waits}
case("N07-two-edits-winner","200/409;um incremento;texto igual ao vencedor",two_edits)
def edit_finalization():
 eid=create(ct["dent1"],p)
 with E.begin() as holder:
  holder.execute(text("SELECT id FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d FOR UPDATE"),{"p":p,"d":dent})
  with cf.ThreadPoolExecutor(2) as pool:
   fin=pool.submit(req,"POST",f"/api/v1/evolutions/{eid}/finalize",ct["dent1"],{"version":1});waitlocks()
   edit=pool.submit(req,"PATCH",f"/api/v1/evolutions/{eid}",ct["dent1"],{"version":1,"notes":"não persistir"})
   waits=waitlocks(2);holder.commit();a,b=fin.result(timeout=20),edit.result(timeout=20)
 row=q("SELECT status,version,notes,finalized_at FROM clinical_evolutions WHERE id=:id",id=eid)[0]
 return a.status_code==200 and b.status_code==403 and row["status"]=="FINALIZED" and row["version"]==2 and row["notes"] is None and row["finalized_at"] is not None,{"finalize_http":a.status_code,"edit_http":b.status_code,"version":row["version"],"state":row["status"],"notes_unchanged":row["notes"] is None,"waiters":waits}
case("REG-edit-versus-finalize","FINALIZED versao2;edicao403 sem sobrescrever",edit_finalization)
# Concurrent scheduling, database exclusion and link event atomicity.
# Replay uses fresh patients: original fixture patients already have links after first race.
for i in range(2):
 r=req("POST","/api/v1/patients",tokens["recep"],{"full_name":"Paciente repeticao concorrente ficticio","cpf":str(99999990100+i),"medical_record_number":"REPLAY-RACE-"+str(i),"birth_date":"1990-01-01"})
 assert r.status_code==201
 ids["patients"][7+i]=r.json()["patient_id"]

def appointment_race():
 patient_ids=ids["patients"][7:9]
 stamp=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=30)).isoformat()
 def post(patient):return req("POST","/api/v1/appointments",tokens["recep"],{"patient_id":patient,"dentist_id":dent,"scheduled_at":stamp})
 with cf.ThreadPoolExecutor(2) as pool:responses=list(pool.map(post,patient_ids))
 codes=sorted(r.status_code for r in responses)
 rows=q("SELECT id,patient_id FROM appointments WHERE dentist_id=:d AND scheduled_at=:s",d=dent,s=stamp)
 links=q("SELECT patient_id FROM clinical_access_links WHERE dentist_id=:d AND patient_id=ANY(:ps)",d=dent,ps=patient_ids)
 events=q("SELECT e.id FROM clinical_access_events e WHERE appointment_id=ANY(:ids)",ids=[r["id"] for r in rows])
 winner=rows[0]["patient_id"] if rows else None
 return codes==[201,409] and len(rows)==1 and len(links)==1 and len(events)==1 and links[0]["patient_id"]==winner,{"http":codes,"appointments":len(rows),"links":len(links),"events":len(events),"link_matches_winner":len(links)==1 and links[0]["patient_id"]==winner}
case("REG-appointment-race","201/409;uma consulta/vinculo/evento",appointment_race)
