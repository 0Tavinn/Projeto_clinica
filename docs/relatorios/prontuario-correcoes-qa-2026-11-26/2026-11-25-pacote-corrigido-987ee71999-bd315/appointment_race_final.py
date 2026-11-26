from qa_common import *
ids=json.load(open("/tmp/qa-fixture.json"));users=ids["users"];dent=users["dent1"]["dent"];tokens={"recep":login("recep")}

for i in range(2):
 r=req("POST","/api/v1/patients",tokens["recep"],{"full_name":"Paciente corrida final ficticio","cpf":str(99999990200+i),"medical_record_number":"FINAL-RACE-"+str(i),"birth_date":"1990-01-01"})
 assert r.status_code==201
 ids["patients"][7+i]=r.json()["patient_id"]
def appointment_race():
 patient_ids=ids["patients"][7:9]
 stamp=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=32)).isoformat()
 def post(patient):return req("POST","/api/v1/appointments",tokens["recep"],{"patient_id":patient,"dentist_id":dent,"scheduled_at":stamp})
 with cf.ThreadPoolExecutor(2) as pool:responses=list(pool.map(post,patient_ids))
 codes=sorted(r.status_code for r in responses)
 rows=q("SELECT id,patient_id FROM appointments WHERE dentist_id=:d AND scheduled_at=:s",d=dent,s=stamp)
 links=q("SELECT patient_id FROM clinical_access_links WHERE dentist_id=:d AND patient_id=ANY(:ps)",d=dent,ps=patient_ids)
 events=q("SELECT e.id FROM clinical_access_events e WHERE appointment_id=ANY(:ids)",ids=[r["id"] for r in rows])
 winner=rows[0]["patient_id"] if rows else None
 return codes==[201,409] and len(rows)==1 and len(links)==1 and len(events)==1 and links[0]["patient_id"]==winner,{"http":codes,"appointments":len(rows),"links":len(links),"events":len(events),"link_matches_winner":len(links)==1 and links[0]["patient_id"]==winner}
case("REG-appointment-race","201/409;uma consulta/vinculo/evento",appointment_race)
