
from qa_common import *
ids=json.load(open("/tmp/qa-fixture.json"));p=ids["patients"][0];dent=ids["users"]["dent1"]["dent"]
admin=login("admin");recep=login("recep");clinical=unlock(login("dent1"))
def preserve_revocation():
 before=q("SELECT id,general_notes FROM medical_records WHERE patient_id=:p",p=p)
 evol_before=q("SELECT e.* FROM clinical_evolutions e JOIN medical_records r ON e.medical_record_id=r.id WHERE r.patient_id=:p ORDER BY e.id",p=p)
 row=q("SELECT id,status FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d",p=p,d=dent)[0]
 if row["status"]=="REVOKED":assert grant(admin,p,dent,"REACTIVATED").status_code==200
 ev_before=q("SELECT count(*) n FROM clinical_access_events WHERE link_id=:id",id=row["id"])[0]["n"]
 r=grant(admin,p,dent,"REVOKED")
 after=q("SELECT id,general_notes FROM medical_records WHERE patient_id=:p",p=p)
 evol_after=q("SELECT e.* FROM clinical_evolutions e JOIN medical_records r ON e.medical_record_id=r.id WHERE r.patient_id=:p ORDER BY e.id",p=p)
 events=q("SELECT count(*) n FROM clinical_access_events WHERE link_id=:id",id=row["id"])[0]["n"]-ev_before
 denied=req("GET",f"/api/v1/patients/{p}/record",clinical)
 reactivated=grant(admin,p,dent,"REACTIVATED")
 return r.status_code==200 and before==after and evol_before==evol_after and events==1 and denied.status_code==403 and reactivated.status_code==200,{"http":r.status_code,"record_equal":before==after,"evolutions_equal":evol_before==evol_after,"evolutions_count":len(evol_after),"event_increment":events,"revoked_read_http":denied.status_code,"reactivated_http":reactivated.status_code}
case("N04-preserve-clinical-history","revogacao administrativa preserva prontuario e evolucoes;um evento;leitura403",preserve_revocation)
def status_preserves():
 ids_appt=[]
 codes=[]
 checks=[]
 for i,status_new in enumerate(["NO_SHOW","COMPLETED"]):
  stamp=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=50+i)).isoformat()
  a=req("POST","/api/v1/appointments",recep,{"patient_id":p,"dentist_id":dent,"scheduled_at":stamp})
  assert a.status_code==201
  r=req("PATCH",f"/api/v1/appointments/{a.json()['id']}",recep,{"status":status_new})
  state=q("SELECT status FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d",p=p,d=dent)[0]["status"]
  codes.append(r.status_code)
  checks.append({"appointment_state":status_new,"link_state":state,"read_http":req("GET",f"/api/v1/patients/{p}/record",clinical).status_code})
 return codes==[200,200] and all(x["link_state"]=="ACTIVE" and x["read_http"]==200 for x in checks),{"http":codes,"checks":checks,"criterion":"politica nova de vinculo duradouro; nao confirma fluxo antigo D02-D04"}
case("REG-status-durable-link","ausencia/conclusao preservam vinculo persistente",status_preserves)
def wrong_clinic_admin():
 uid=q("INSERT INTO users(clinic_id,full_name,email,cpf,role,password_hash) VALUES(:c,'Admin externo QA','adminforeign@qa.invalid','99999990004','ADMINISTRATOR',:h) RETURNING id",c=ids["clinics"][1],h=hasher.hash("FicticioLogin2026!"))[0]["id"]
 other=login("adminforeign")
 before=q("SELECT * FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d",p=p,d=dent)
 rs=[grant(other,p,dent,a) for a in ["REVOKED","GRANTED","REACTIVATED"]]
 after=q("SELECT * FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d",p=p,d=dent)
 return all(x.status_code==404 for x in rs) and before==after,{"http":[x.status_code for x in rs],"link_unchanged":before==after}
case("N04-cross-clinic-admin","admin de outra clinica nao concede/revoga/reativa",wrong_clinic_admin)
