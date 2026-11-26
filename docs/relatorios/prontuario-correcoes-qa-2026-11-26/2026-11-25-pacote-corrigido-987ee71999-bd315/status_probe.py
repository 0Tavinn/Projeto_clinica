
from qa_common import *
ids=json.load(open("/tmp/qa-fixture.json"));p=ids["patients"][0];dent=ids["users"]["dent1"]["dent"]
recep=login("recep");clinical=unlock(login("dent1"))
def run():
 codes=[];checks=[]
 for i,status_new in enumerate(["NO_SHOW","COMPLETED"]):
  stamp=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=52+i)).isoformat()
  a=req("POST","/api/v1/appointments",recep,{"patient_id":p,"dentist_id":dent,"scheduled_at":stamp})
  assert a.status_code==201
  aid=a.json()["appointment_id"]
  r=req("PATCH",f"/api/v1/appointments/{aid}",recep,{"status":status_new})
  state=q("SELECT status FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d",p=p,d=dent)[0]["status"]
  persisted=q("SELECT status FROM appointments WHERE id=:id",id=aid)[0]["status"]
  codes.append(r.status_code)
  checks.append({"appointment_state":persisted,"link_state":state,"read_http":req("GET",f"/api/v1/patients/{p}/record",clinical).status_code})
 return codes==[200,200] and all(x["link_state"]=="ACTIVE" and x["read_http"]==200 for x in checks),{"http":codes,"checks":checks,"criterion":"politica nova de vinculo duradouro; nao confirma fluxo antigo D02-D04"}
case("REG-status-durable-link","ausencia/conclusao preservam vinculo persistente",run)
