
from qa_common import *
ids,tokens,ct=load();users=ids["users"]
CONTROL="http://qa-instrumented:9010"
def control(mode,p):
    with httpx.Client(timeout=10) as c:
        r=c.post(CONTROL,json={"mode":mode,"patient_id":p,"dentist_id":users["dent1"]["dent"]});assert r.status_code==200
def telemetry():
    with httpx.Client(timeout=10) as c:return c.get(CONTROL).json()
def search(p,qterm,engine):
    with httpx.Client(timeout=30) as c:
        return c.get("http://qa-instrumented:8000/api/v1/clinical/search",params={"patient_id":p,"q":qterm,"engine_name":engine},headers={"Authorization":"Bearer "+ct["dent1"]})
def reactivate(p):
    row=q("SELECT status FROM clinical_access_links WHERE patient_id=:p AND dentist_id=:d",p=p,d=users["dent1"]["dent"])[0]
    if row["status"]=="REVOKED":assert grant(tokens["admin"],p,users["dent1"]["dent"],"REACTIVATED").status_code==200
p=ids["patients"][5]
def cpu_revoke():
    reactivate(p);control("cpu_revoke",p)
    r=search(p,"acao","cpu");t=telemetry()
    return r.status_code==403 and t["events"][0]["revoked_rows"]==1 and "results" not in r.json(),{"http":r.status_code,"telemetry":t,"results_exposed":"results" in r.json()}
case("N01-compute-cpu","403 apos revogacao no fim do calculo real antes da rechecagem",cpu_revoke)
reactivate(p)
# Bounded pathological text forces enough real device work to observe RUNNING.
pheavy=ids["patients"][3]
record=q("SELECT id FROM medical_records WHERE patient_id=:p",p=pheavy)[0]["id"]
with E.begin() as db:
    db.execute(text("INSERT INTO clinical_evolutions(medical_record_id,dentist_id,description) SELECT :r,:d,repeat('a',1999) FROM generate_series(1,1000)"),{"r":record,"d":users["dent1"]["dent"]})
def kernel_revoke():
    reactivate(pheavy);control("kernel_revoke",pheavy)
    r=search(pheavy,"a"*127+"b","opencl");t=telemetry()
    events=t["events"]
    running=bool(events) and events[0]["revocation_committed_while_event_running"]
    return r.status_code==403 and running and events[0]["kernel_really_completed"] and "results" not in r.json(),{"http":r.status_code,"telemetry":t,"inflight_proven":running,"results_exposed":"results" in r.json()}
case("N01-compute-real-opencl","revogacao commit com evento RUNNING e resposta403",kernel_revoke)
reactivate(pheavy)
def unavailable():
    control("unavailable",p)
    a=search(p,"acao","opencl");b=search(p,"acao","auto")
    control("normal",p)
    return a.status_code==503 and b.status_code==200 and b.json()["engine"]=="cpu",{"forced_http":a.status_code,"auto_http":b.status_code,"auto_engine":b.json().get("engine")}
case("REG-unavailable-external","forcado503;automaticoCPU;harness declarado",unavailable)
