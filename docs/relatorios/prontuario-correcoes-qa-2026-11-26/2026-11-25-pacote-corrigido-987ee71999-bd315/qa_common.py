
import os,json,time,datetime,concurrent.futures as cf
import httpx
from sqlalchemy import create_engine,text
from app.main import hasher
E=create_engine(os.environ["DATABASE_URL"],connect_args={"options":"-c statement_timeout=12000"})
BASE=os.environ.get("QA_API_URL","http://qa-api:8000")
R=[]
def req(method,path,t=None,body=None,**kwargs):
    with httpx.Client(base_url=BASE,timeout=20,headers={"Connection":"close"}) as c:
        return c.request(method,path,headers={"Authorization":"Bearer "+t} if t else {},json=body,**kwargs)
def q(sql,**p):
    with E.begin() as c:
        r=c.execute(text(sql),p)
        return [dict(x) for x in r.mappings()] if r.returns_rows else []
def case(id,expected,fn):
    try:
        val=fn()
        ok,obtained=val if isinstance(val,tuple) else (bool(val),str(val))
        rec={"id":id,"expected":expected,"obtained":obtained,"status":"aprovado" if ok else "reprovado"}
    except Exception as exc:
        rec={"id":id,"expected":expected,"obtained":{"script_exception_type":type(exc).__name__},"status":"bloqueado"}
    R.append(rec)
    with open("/tmp/qa-extra-cases.jsonl","a") as stream:stream.write(json.dumps(rec,ensure_ascii=True,default=str)+chr(10))
    print("QA_CASE "+json.dumps(rec,ensure_ascii=True,default=str),flush=True)
    return rec
def status(method,path,t,body,n):
    r=req(method,path,t,body);return r.status_code==n,{"http":r.status_code}
def login(name,pw="FicticioLogin2026!"):
    r=req("POST","/api/v1/auth/login",body={"email":name+"@qa.invalid","password":pw})
    assert r.status_code==200,"login fixture falhou"
    return r.json()["access_token"]
def unlock(t,pw="FicticioClinico2026!"):
    r=req("POST","/api/v1/auth/clinical-unlock",t,{"password":pw})
    assert r.status_code==200,"unlock fixture falhou"
    return r.json()["clinical_token"]
def load():
    ids=json.load(open("/tmp/qa-fixture.json"))
    tokens={n:login(n) for n in ["admin","recep","dent1","dent2","foreign","noprof"]}
    ct={n:unlock(tokens[n]) for n in ["dent1","dent2","foreign"]}
    return ids,tokens,ct
def grant(t,patient,dent,action="GRANTED"):
    return req("POST","/api/v1/admin/access",t,{"patient_id":patient,"dentist_id":dent,"action":action})
def create(ct,p,desc="Clinica sensibilidade ficticia",appointment=None):
    body={"patient_id":p,"description":desc}
    if appointment is not None:body["appointment_id"]=appointment
    r=req("POST","/api/v1/evolutions",ct,body)
    assert r.status_code==201,"fixture evolution nao criada"
    return r.json()["id"]
def waitlocks(count=1):
    for _ in range(200):
        rows=q("SELECT pid,wait_event_type,wait_event FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query ILIKE '%clinical_access_links%'")
        if len(rows)>=count:return rows
        time.sleep(.025)
    raise AssertionError("espera por lock nao comprovada")
