
"""Executor QA independente. Nao altera candidata, bancos ou servicos preexistentes."""
from pathlib import Path
import os,json,subprocess,time,secrets,hashlib,datetime,re
from urllib.parse import quote,unquote
O=Path(__file__).resolve().parent
S=Path("/home/paulinho/Work/Projeto_clinica/lumina_odonto")
ORIGINAL=Path("/home/paulinho/Work/lumina_odonto_corrigido_QA/lumina_odonto_atualizado")
BASE=Path("/home/paulinho/Work/lumina-qa-evidence/2026-11-26-n05-log-qa-4c930a5405")
BACK=Path("/home/paulinho/Work/lumina-qa-evidence/2026-11-26-n05-log-backend-cfaac6e1")
P=(O/"resource-prefix.txt").read_text().strip()
assert P.startswith("lumina-links-qa-")
LABEL="lumina.links.independent"
N={"image":P+":source","network":P+"-net","volume":P+"-data","db":P+"-db","api":P+"-api","driver":P+"-driver","tests":P+"-tests"}
owned=[];secret_values=[];stage="initialization";failure=None
def get(cmd):return subprocess.check_output(cmd,text=True)
def hfiles(folder):return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob("*") if p.is_file()}
def gitstate():
 result={}
 for path in ["/home/paulinho/Work/Projeto_clinica","/home/paulinho/Work/Projeto_clinica_clinical_2fa"]:
  result[path]={"head":get(["git","-C",path,"rev-parse","HEAD"]).strip(),"branch":get(["git","-C",path,"branch","--show-current"]).strip(),
  "status":get(["git","-C",path,"status","--porcelain=v1"]),"index_sha256":hashlib.sha256(subprocess.check_output(["git","-C",path,"diff","--cached","--raw","-z"])).hexdigest()}
 return result
def inventory():
 ids=get(["docker","ps","-aq"]).split()
 result={"containers":[]}
 for id in ids:
  d=json.loads(get(["docker","inspect",id]))[0]
  result["containers"].append({"id":d["Id"],"name":d["Name"],"image":d["Image"],"started":d["State"]["StartedAt"],"restarts":d["RestartCount"],"state":d["State"]["Status"],"ports":d["NetworkSettings"]["Ports"]})
 result["containers"].sort(key=lambda x:x["id"])
 for kind in ["volume","network"]:result[kind]=sorted(get(["docker",kind,"ls","--format","{{.Name}}"]).splitlines())
 return result
def sensitive(text):
 decoded=text
 for _ in range(3):
  if any(v and v in decoded for v in secret_values):return True
  decoded=unquote(decoded)
 return bool(re.search(r"eyJ[A-Za-z0-9_-]+[.][A-Za-z0-9_-]+[.][A-Za-z0-9_-]+",text))
def safe(text):
 lines=[]
 for line in text.splitlines():
  if sensitive(line):line="[QA omitted sensitive line; sha256="+hashlib.sha256(line.encode()).hexdigest()+"]"
  line=re.sub(r"\$argon2(?:id|i|d)\$[^\s]+","[hash omitted]",line)
  lines.append(line)
 return chr(10).join(lines)+chr(10)
def run(cmd,name=None,stdin=None,timeout=120,check=True):
 r=subprocess.run(cmd,input=stdin,text=True,capture_output=True,timeout=timeout)
 if name:(O/name).write_text(safe(r.stdout+r.stderr))
 if check and r.returncode:raise RuntimeError("command failed: "+(name or stage))
 return r
def acquire(kind,name,cmd):
 run(cmd,"build-exact.log" if kind=="image" else "create-"+name+".log")
 info=json.loads(get(["docker",kind,"inspect",name]))[0]
 owned.append({"kind":kind,"name":name,"id":info.get("Id",info.get("Name"))})
 (O/"resources.json").write_text(json.dumps({"prefix":P,"label":LABEL,"resources":owned},indent=2))
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2))
git_before=gitstate();inv_before=inventory();base_before=hfiles(BASE);back_before=hfiles(BACK)
active=git_before["/home/paulinho/Work/Projeto_clinica"]
assert active["head"]=="67068ac969cb7b34396b5d94e4ee09a7001ef8b4" and active["branch"]=="fix/prontuario-correcoes-qa"
assert subprocess.check_output(["git","-C","/home/paulinho/Work/Projeto_clinica","diff","--cached","--raw","-z"])==b""
extra_protected=Path("/home/paulinho/Work/lumina_odonto_correcao_N05_20261126")
extra_before=hfiles(extra_protected)
old_qa=Path("/home/paulinho/Work/lumina-qa-evidence/2026-11-25-pacote-corrigido-987ee71999-bd315")
old_qa_before=hfiles(old_qa)
save("external-n05-before.json",extra_before)
stage_before=subprocess.check_output(["git","-C","/home/paulinho/Work/Projeto_clinica","ls-files","--stage","-z"])
save("index-state-before.json",{"ls_files_stage_sha256":hashlib.sha256(stage_before).hexdigest()})
save("git-before.json",git_before);save("inventory-before.json",inv_before)
save("historical-artifacts-before.json",{"qa":base_before,"backend":back_before})
assert hfiles(S)==json.loads((O/"source-before.json").read_text())
pwd=secrets.token_urlsafe(24);jwt=secrets.token_urlsafe(48);secret_values.extend([pwd,jwt])
db_name="links_qa_"+P.rsplit("-",1)[1]
env=O/".qa-secrets.env"
env.write_text(chr(10).join(["POSTGRES_USER=qa_n05","POSTGRES_DB="+db_name,"POSTGRES_PASSWORD="+pwd,"DATABASE_URL=postgresql+psycopg://qa_n05:"+pwd+"@pg:5432/"+db_name,"JWT_SECRET="+jwt])+chr(10));env.chmod(0o600)
save("environment.json",{"db_name":db_name,"db_user":"qa_n05","public_ports":[],"secrets":"ephemeral; not distributed"})
try:
 stage="build"
 for kind,key in [("image","image"),("network","network"),("volume","volume"),("container","db"),("container","api"),("container","driver"),("container","tests")]:
  assert subprocess.run(["docker",kind,"inspect",N[key]],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
 print("STAGE build",flush=True)
 acquire("image",N["image"],["docker","build","--label",LABEL+"="+P,"-t",N["image"],str(S)])
 # Exact build output separately if needed: acquire's run does not save; record metadata.
 image=json.loads(get(["docker","image","inspect",N["image"]]))[0]
 assert image["Config"]["Cmd"]==["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
 save("image-identity.json",{"id":image["Id"],"cmd":image["Config"]["Cmd"]})
 stage="provision"
 acquire("network",N["network"],["docker","network","create","--label",LABEL+"="+P,N["network"]])
 acquire("volume",N["volume"],["docker","volume","create","--label",LABEL+"="+P,N["volume"]])
 acquire("container",N["db"],["docker","run","-d","--label",LABEL+"="+P,"--name",N["db"],"--network",N["network"],"--network-alias","pg","--env-file",str(env),"--mount","type=volume,src="+N["volume"]+",dst=/var/lib/postgresql/data","postgres:16"])
 for _ in range(100):
  r=run(["docker","exec",N["db"],"pg_isready","-h","127.0.0.1","-U","qa_n05","-d",db_name],check=False)
  if r.returncode==0:break
  time.sleep(.3)
 else:raise RuntimeError("DB readiness timeout")
 for name in ["schema.sql","seed_demo.sql"]:
  run(["docker","exec","-i",N["db"],"psql","-X","-q","-v","ON_ERROR_STOP=1","-U","qa_n05","-d",db_name],name+".log",stdin=(S/"sql"/name).read_text())
 acquire("container",N["api"],["docker","run","-d","--label",LABEL+"="+P,"--name",N["api"],"--network",N["network"],"--network-alias","api","--env-file",str(env),N["image"]])
 acquire("container",N["driver"],["docker","run","-d","--label",LABEL+"="+P,"--name",N["driver"],"--network",N["network"],"--env-file",str(env),"-e","PYTHONPATH=/app:/qa","--mount","type=bind,src="+str(O)+",dst=/qa,readonly",N["image"],"python","-c","import time;time.sleep(3600)"])
 print("STAGE real_http",flush=True);stage="http"
 r=run(["docker","exec",N["driver"],"python","/qa/probe_links.py"],"probe-execution.log",check=False,timeout=180)
 secret=run(["docker","exec",N["driver"],"cat","/tmp/qa-sensitive.json"],check=False)
 if secret.returncode==0:
  info=json.loads(secret.stdout);secret_values.extend(info["markers"]+info["tokens"])
 # Do not persist raw HTTP/clinical output even on script exception.
 (O/"probe-execution.log").write_text(safe(r.stdout+r.stderr))
 for source,target in [("/tmp/qa-results.json","http-results.json"),("/tmp/qa-openapi.json","openapi-http.json"),("/tmp/qa-pg-version.txt","postgres-version.txt")]:
  z=run(["docker","exec",N["driver"],"cat",source],check=False)
  if z.returncode==0:(O/target).write_text(safe(z.stdout))
 if r.returncode:raise RuntimeError("HTTP probe aborted")
 stage="contracts"
 observed=json.loads((O/"openapi-http.json").read_text())
 baseline=json.loads((BASE/"openapi-http.json").read_text())
 added=sorted(set(observed["paths"])-set(baseline["paths"]))
 removed=sorted(set(baseline["paths"])-set(observed["paths"]))
 old_equal=all(observed["paths"][k]==v for k,v in baseline["paths"].items())
 save("openapi-comparison.json",{"added_paths":added,"removed_paths":removed,"prior_operations_equal":old_equal,"expected_added":["/api/v1/clinical/patients","/api/v1/clinical/patients/{patient_id}"]})
 stage="tests";print("STAGE supplied_tests",flush=True)
 # A named test container permits preserving JUnit; no network/DB writes from tests.
 z=run(["docker","run","--name",N["tests"],"--label",LABEL+"="+P,"--network","none","--env-file",str(env),N["image"],"python","-m","pytest","-v","-ra","--junitxml=/tmp/links-tests.xml","--disable-warnings","--tb=short"],"tests.log",check=False)
 info=json.loads(get(["docker","inspect",N["tests"]]))[0];owned.append({"kind":"container","name":N["tests"],"id":info["Id"]})
 save("resources.json",{"prefix":P,"label":LABEL,"resources":owned})
 junit=run(["docker","cp",N["tests"]+":/tmp/links-tests.xml",str(O/"tests.xml")],check=False)
 if (O/"tests.xml").exists():(O/"tests.xml").write_text(safe((O/"tests.xml").read_text()))
 save("test-process.json",{"exit":z.returncode})
 if z.returncode:raise RuntimeError("supplied tests failed")
 stage="versions"
 vcode="import json,sys,importlib.metadata,pyopencl as cl; print(json.dumps({'python':sys.version.split()[0],'packages':{n:importlib.metadata.version(n) for n in ['fastapi','uvicorn','sqlalchemy','psycopg','pydantic','pytest','numpy','pyopencl']},'devices':[{'platform':d.platform.name,'device':d.name,'type':d.type,'driver':d.driver_version,'version':d.version} for p in cl.get_platforms() for d in p.get_devices()]}))"
 vr=run(["docker","exec",N["driver"],"python","-c",vcode],"versions.json")
 run(["docker","version","--format","{{.Client.Version}} {{.Server.Version}}"],"docker-version.txt")
 run(["docker","compose","version"],"compose-version.txt")
except Exception as exc:
 failure={"stage":stage,"exception_type":type(exc).__name__}
 save("execution-failure.json",failure);print("QA_EXECUTION_FAILURE",json.dumps(failure),flush=True)
finally:
 stage="logs"
 if any(x["name"]==N["api"] for x in owned):
  logs=subprocess.run(["docker","logs",N["api"]],text=True,capture_output=True,timeout=30)
  # Sensitive metadata is recovered in memory, never copied to evidence.
  if any(x["name"]==N["driver"] for x in owned):
   z=run(["docker","exec",N["driver"],"cat","/tmp/qa-sensitive.json"],check=False)
   if z.returncode==0:
    data=json.loads(z.stdout);secret_values.extend(data["markers"]+data["tokens"])
  checks={"stdout_no_sensitive":not sensitive(logs.stdout),"stderr_no_sensitive":not sensitive(logs.stderr),
  "traceback_absent":"Traceback (most recent call last)" not in logs.stdout+logs.stderr,
  "formatter_error_absent":"--- Logging error ---" not in logs.stdout+logs.stderr}
  access=logs.stdout+logs.stderr
  entries=re.findall(r'"([A-Z]+) ([^" ]+) HTTP/([^" ]+)" ([0-9]{3})',access)
  checks.update({"method_route_status_present":bool(entries),
  "list_template_present":any(e[1]=="/api/v1/clinical/patients" and e[3]=="200" for e in entries),
  "detail_template_present":any(e[1]=="/api/v1/clinical/patients/{patient_id}" and e[3]=="200" for e in entries),
  "detail_denied_template_present":any(e[1]=="/api/v1/clinical/patients/{patient_id}" and e[3]=="403" for e in entries),
  "admin_links_template_present":any(e[1]=="/api/v1/access-links" and e[3]=="200" for e in entries),
  "legacy_search_template_present":any(e[1]=="/api/v1/clinical/search" and e[3]=="200" for e in entries),
  "path_id_not_logged":not bool(re.search(r"/api/v1/clinical/patients/[0-9]+",access)),
  "new_routes_not_unmatched":not any(e[1]=="[unmatched]" for e in entries),
  "no_query_in_access":all("?" not in e[1] for e in entries),
  "startup_event_present":"server_event=startup_complete" in access})
  for status in ["200","201","401","403","404","422"]:checks["status_"+status+"_present"]=any(e[3]==status for e in entries)
  save("privacy-log-check.json",checks)
  (O/"api-stdout-sanitized.log").write_text(safe(logs.stdout));(O/"api-stderr-sanitized.log").write_text(safe(logs.stderr))
 cleanup=[]
 for item in reversed(owned):
  kind,name=item["kind"],item["name"]
  z=subprocess.run(["docker",kind,"inspect",name],text=True,capture_output=True)
  if z.returncode:cleanup.append({**item,"removed":False,"reason":"unexpectedly absent"});continue
  meta=json.loads(z.stdout)[0];labels=meta.get("Config",{}).get("Labels",{}) if kind in ["container","image"] else meta.get("Labels",{})
  assert (labels or {}).get(LABEL)==P and meta.get("Id",meta.get("Name"))==item["id"],"ownership mismatch"
  cmd=["docker","rm","-f",name] if kind=="container" else ["docker",kind,"rm",name]
  z=subprocess.run(cmd,text=True,capture_output=True,timeout=90)
  cleanup.append({**item,"removed":z.returncode==0})
 save("cleanup.json",cleanup)
 if env.exists():env.unlink()
 candidate_after=hfiles(S);original_after=hfiles(ORIGINAL);save("candidate-after.json",candidate_after);save("original-after.json",original_after)
 git_after=gitstate();inv_after=inventory();save("git-after.json",git_after);save("inventory-after.json",inv_after)
 save("preservation.json",{"candidate_equal":candidate_after==json.loads((O/"source-before.json").read_text()),
 "original_all_40_equal":original_after==json.loads((O/"original-before.json").read_text()),
 "git_equal":git_before==git_after,"inventory_equal":inv_before==inv_after,
 "historical_qa_equal":base_before==hfiles(BASE),"backend_evidence_equal":back_before==hfiles(BACK),
 "external_n05_package_equal":hfiles(extra_protected)==extra_before,
 "historical_qa_25_equal":hfiles(old_qa)==old_qa_before,
 "tracked_index_entries_equal":subprocess.check_output(["git","-C","/home/paulinho/Work/Projeto_clinica","ls-files","--stage","-z"])==stage_before,
 "all_owned_removed":all(x["removed"] for x in cleanup),"ephemeral_secrets_file_removed":not env.exists()})
 (O/"finished-utc.txt").write_text(datetime.datetime.now(datetime.timezone.utc).isoformat())
print("QA_RUN_FINISHED",json.dumps({"failure":failure,"evidence":str(O)}),flush=True)
