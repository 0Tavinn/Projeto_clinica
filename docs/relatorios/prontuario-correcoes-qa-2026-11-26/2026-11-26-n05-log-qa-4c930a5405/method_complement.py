
"""Complemento restrito: TRACE reconhecido pelo parser e redacao OTHER.
Sem banco; apenas roteamento HTTP405 da mesma candidata, sem dependencia SQL.
"""
from pathlib import Path
import subprocess,json,secrets,hashlib
O=Path(__file__).resolve().parent
S=Path("/home/paulinho/Work/lumina_odonto_correcao_N05_20261126")
P="lumina-n05-method-"+secrets.token_hex(5);LABEL="lumina.n05.independent"
image=P+":source";net=P+"-net";api=P+"-api";driver=P+"-driver"
owned=[]
marker="QA_TRACE_PRIVATE_SENTINEL_7642"
def run(args,**kw):return subprocess.run(args,text=True,capture_output=True,timeout=120,**kw)
def acquire(kind,name,args):
 r=run(args);assert r.returncode==0
 d=json.loads(subprocess.check_output(["docker",kind,"inspect",name],text=True))[0]
 owned.append({"kind":kind,"name":name,"id":d.get("Id",d.get("Name"))})
def inventory():
 data={}
 for kind in ["container","volume","network"]:
  if kind=="container":
   ids=subprocess.check_output(["docker","ps","-aq"],text=True).split()
   data[kind]=[{"id":d["Id"],"started":d["State"]["StartedAt"],"restart":d["RestartCount"]} for id in ids for d in json.loads(subprocess.check_output(["docker","inspect",id],text=True))]
   data[kind].sort(key=lambda x:x["id"])
  else:data[kind]=sorted(subprocess.check_output(["docker",kind,"ls","--format","{{.Name}}"],text=True).splitlines())
 return data
before=inventory()
try:
 r=run(["docker","build","--label",LABEL+"="+P,"-t",image,str(S)])
 (O/"method-build.log").write_text(r.stdout+r.stderr);assert r.returncode==0
 d=json.loads(subprocess.check_output(["docker","image","inspect",image],text=True))[0]
 owned.append({"kind":"image","name":image,"id":d["Id"]})
 assert d["Config"]["Cmd"]==["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
 (O/"method-image.json").write_text(json.dumps({"id":d["Id"],"cmd":d["Config"]["Cmd"],"database":"nao usado; somente HTTP405 antes de dependencias"},indent=2))
 acquire("network",net,["docker","network","create","--label",LABEL+"="+P,net])
 acquire("container",api,["docker","run","-d","--label",LABEL+"="+P,"--name",api,"--network",net,"--network-alias","method-api",
 "-e","DATABASE_URL=postgresql+psycopg://qa@127.0.0.1:5432/unused","-e","JWT_SECRET="+secrets.token_urlsafe(48),image])
 acquire("container",driver,["docker","run","-d","--label",LABEL+"="+P,"--name",driver,"--network",net,image,"python","-c","import time;time.sleep(120)"])
 code="""import httpx,time,json
for _ in range(80):
 try:
  if httpx.get('http://method-api:8000/openapi.json',timeout=1).status_code==200:break
 except httpx.HTTPError:pass
 time.sleep(.2)
else:raise RuntimeError('readiness')
r=httpx.request('TRACE','http://method-api:8000/health?q=QA_TRACE_PRIVATE_SENTINEL_7642',headers={'X-QA-Secret':'QA_TRACE_PRIVATE_SENTINEL_7642'},timeout=10)
print(json.dumps({'id':'F22-recognized-trace','http':r.status_code,'no_echo':'QA_TRACE_PRIVATE_SENTINEL_7642' not in r.text}))
"""
 r=run(["docker","exec","-i",driver,"python","-"],input=code);assert r.returncode==0
 observed=json.loads(r.stdout)
 logs=run(["docker","logs",api])
 all_logs=logs.stdout+logs.stderr
 leak=marker in all_logs
 result={"id":"F22-recognized-trace","expected":"TRACE aceito pelo parser;405;log OTHER /health;sem eco",
 "obtained":{**observed,"other_method_logged":'"OTHER /health HTTP/1.1" 405' in all_logs,"log_no_echo":not leak},
 "status":"aprovado" if observed["http"]==405 and observed["no_echo"] and not leak and '"OTHER /health HTTP/1.1" 405' in all_logs else "reprovado"}
 (O/"method-result.json").write_text(json.dumps(result,indent=2))
 safe=all_logs if not leak else chr(10).join("[QA omitted sensitive line]" if marker in x else x for x in all_logs.splitlines())
 (O/"method-api-sanitized.log").write_text(safe)
 print(json.dumps(result))
finally:
 cleanup=[]
 for item in reversed(owned):
  kind,name=item["kind"],item["name"]
  meta=json.loads(subprocess.check_output(["docker",kind,"inspect",name],text=True))[0]
  labels=meta["Config"].get("Labels",{}) if kind in ["container","image"] else meta.get("Labels",{})
  assert labels.get(LABEL)==P and meta.get("Id",meta.get("Name"))==item["id"]
  z=run(["docker","rm","-f",name] if kind=="container" else ["docker",kind,"rm",name])
  cleanup.append({**item,"removed":z.returncode==0})
 (O/"method-cleanup.json").write_text(json.dumps(cleanup,indent=2))
 after=inventory()
 (O/"method-preservation.json").write_text(json.dumps({"inventory_equal":before==after,"all_own_removed":all(x["removed"] for x in cleanup)},indent=2))
