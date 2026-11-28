"""Ensaios N05-LOG em imagem exata, CMD distribuído e recursos exclusivos."""

from pathlib import Path
import json,subprocess,tarfile,time,uuid
from urllib.parse import quote

OUT=Path(__file__).resolve().parent
SOURCE=Path(json.loads((OUT/"paths.json").read_text())["candidate"])
assert SOURCE==Path("/home/paulinho/Work/lumina_odonto_correcao_N05_20261126")
tag="lumina-n05-"+uuid.uuid4().hex[:12]
label="lumina.n05.qa"
names={"image":tag+":source","network":tag+"-net","volume":tag+"-data",
       "db":tag+"-db","api":tag+"-api","driver":tag+"-driver"}
(OUT/"resources.json").write_text(json.dumps({"label":label,"tag":tag,"names":names},indent=2))
owned=[]
def get(*args):return subprocess.check_output(args,text=True)
def run(*args,**kwargs):return subprocess.run(args,check=True,**kwargs)
def inventory():
    ids=get("docker","ps","-aq").split()
    result={"containers":[]}
    for id in ids:
        data=json.loads(get("docker","inspect",id))[0]
        result["containers"].append({k:v for k,v in {
            "id":data["Id"],"name":data["Name"],"image":data["Image"],
            "started":data["State"]["StartedAt"],"restarts":data["RestartCount"],
            "state":data["State"]["Status"],"ports":data["NetworkSettings"]["Ports"]}.items()})
    for kind in ("volume","network"):
        result[kind]=get("docker",kind,"ls","--format","{{.Name}}").splitlines()
    return result
before=inventory();(OUT/"inventory-before.json").write_text(json.dumps(before,indent=2))
for key,kind in (("image","image"),("network","network"),("volume","volume"),("db","container"),("api","container"),("driver","container")):
    assert subprocess.run(["docker",kind,"inspect",names[key]],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
def acquire(kind,key,args):
    run("docker",*args,stdout=subprocess.DEVNULL)
    owned.append((kind,names[key]))
markers=["N05_VALID_SENTINEL_4829","N05_QUERY_SENTINEL_7283","N05_UNICODE_acentuação_漢字",
         "N05_PARAMETER_SENTINEL_5821","N05_PATH_SENTINEL_9284","N05_BODY_SENTINEL_1529","N05_AUTH_SENTINEL_4253"]
def sanitize(text):
    for value in markers+["PRIVATE_LOG_SENTINEL"]:
        for encoded in (value,quote(value,safe=""),quote(value,safe="").lower()):
            text=text.replace(encoded,"[redacted-test-value]")
    return text
try:
    archive=OUT/"build-context.tar"
    with tarfile.open(archive,"w",format=tarfile.GNU_FORMAT) as tar:
        for path in SOURCE.iterdir():tar.add(path,arcname=path.name)
    with archive.open("rb") as data,(OUT/"build-exact.log").open("wb") as log:
        run("docker","build","--label",label+"="+tag,"-t",names["image"],"-",stdin=data,stdout=log,stderr=subprocess.STDOUT,timeout=420)
    owned.append(("image",names["image"]));archive.unlink()
    image=json.loads(get("docker","image","inspect",names["image"]))[0]
    assert image["Config"]["Cmd"]==["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
    (OUT/"image-identity.json").write_text(json.dumps({"id":image["Id"],"cmd":image["Config"]["Cmd"]},indent=2))
    acquire("network","network",["network","create","--label",label+"="+tag,names["network"]])
    acquire("volume","volume",["volume","create","--label",label+"="+tag,names["volume"]])
    acquire("container","db",["run","-d","--label",label+"="+tag,"--name",names["db"],"--network",names["network"],"--network-alias","pg",
        "--mount","type=volume,src="+names["volume"]+",dst=/var/lib/postgresql/data","-e","POSTGRES_DB=lumina_n05_scratch",
        "-e","POSTGRES_USER=n05_qa","-e","POSTGRES_PASSWORD=n05-exclusive-test-only","postgres:16"])
    for _ in range(90):
        if subprocess.run(["docker","exec",names["db"],"pg_isready","-h","127.0.0.1","-U","n05_qa","-d","lumina_n05_scratch"],
                          stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:break
        time.sleep(1)
    else:raise RuntimeError("PostgreSQL exclusivo indisponível")
    for name in ("schema.sql","seed_demo.sql"):
        result=subprocess.run(["docker","exec","-i",names["db"],"psql","-X","-q","-v","ON_ERROR_STOP=1","-U","n05_qa","-d","lumina_n05_scratch"],
                              input=(SOURCE/"sql"/name).read_bytes(),capture_output=True)
        (OUT/(name+".log")).write_bytes(result.stdout+result.stderr)
        assert result.returncode==0
    env=["-e","DATABASE_URL=postgresql+psycopg://n05_qa:n05-exclusive-test-only@pg/lumina_n05_scratch",
         "-e","JWT_SECRET=n05-exclusive-jwt-not-for-production-0000"]
    # Sem comando após a imagem: executa exatamente o CMD distribuído.
    acquire("container","api",["run","-d","--label",label+"="+tag,"--name",names["api"],"--network",names["network"],
        "--network-alias","api",*env,names["image"]])
    acquire("container","driver",["run","-d","--label",label+"="+tag,"--name",names["driver"],"--network",names["network"],
        *env,names["image"],"python","-c","import time;time.sleep(600)"])
    result=subprocess.run(["docker","exec","-i",names["driver"],"python","-"],input=(OUT/"probe_privacy.py").read_bytes(),capture_output=True,timeout=120)
    (OUT/"probe-execution.log").write_text(sanitize((result.stdout+result.stderr).decode(errors="replace")))
    assert result.returncode==0,"Sondagem HTTP falhou; consultar log sanitizado"
    result=get("docker","exec",names["driver"],"cat","/tmp/privacy-probe.json")
    (OUT/"http-results.json").write_text(result)
    # Induz erro real de conexão somente no banco descartável; não muda a API.
    run("docker","stop",names["db"],stdout=subprocess.DEVNULL)
    code="""import json,httpx
r=httpx.get('http://api:8000/api/v1/clinical/search?patient_id=1&q=N05_QUERY_SENTINEL_7283',
            headers={'Authorization':'Bearer N05_AUTH_SENTINEL_4253'},timeout=15)
assert r.status_code==401
print(json.dumps({'id':'401-invalid-while-db-off','http':r.status_code,'passed':True}))
"""
    result=subprocess.run(["docker","exec","-i",names["driver"],"python","-"],input=code.encode(),capture_output=True)
    assert result.returncode==0
    # Um token válido em memória é produzido usando o mesmo segredo QA, sem logá-lo.
    code="""import json,httpx,jwt,os,time
token=jwt.encode({'sub':'2','clinic_id':1,'type':'clinical','session_version':1,'clinical_version':1,
                 'iat':int(time.time()),'exp':int(time.time())+60},os.environ['JWT_SECRET'],algorithm='HS256')
r=httpx.get('http://api:8000/api/v1/clinical/search?patient_id=1&q=N05_QUERY_SENTINEL_7283',
           headers={'Authorization':'Bearer '+token},timeout=20)
assert r.status_code==500,r.status_code
assert 'N05_' not in r.text
print(json.dumps({'id':'500-database-unavailable','http':500,'error_body_no_echo':True,'passed':True}))
"""
    result=subprocess.run(["docker","exec","-i",names["driver"],"python","-"],input=code.encode(),capture_output=True,timeout=30)
    (OUT/"error-probe.log").write_text(sanitize((result.stdout+result.stderr).decode(errors="replace")))
    assert result.returncode==0
    run("docker","start",names["db"],stdout=subprocess.DEVNULL)
    result=subprocess.run(["docker","run","--rm","--label",label+"="+tag,"--network","none",
                          "-e","DATABASE_URL=postgresql+psycopg://qa:qa@localhost/qa",
                          "-e","JWT_SECRET=n05-only-unit-secret-not-for-production",
                          names["image"],"python","-m","pytest","-q","--disable-warnings","--tb=short"],
                         capture_output=True,timeout=120)
    (OUT/"tests.log").write_text(sanitize((result.stdout+result.stderr).decode(errors="replace")))
    assert result.returncode==0,"Testes falharam; consultar tests.log"
    code="import json,sys,importlib.metadata;from app.opencl_search import OpenCLSearch;s=OpenCLSearch();print(json.dumps({'python':sys.version.split()[0],'packages':{x:importlib.metadata.version(x) for x in ['fastapi','uvicorn','sqlalchemy','psycopg','pydantic','pytest','numpy','pyopencl']},'opencl_device':s.device.name if hasattr(s,'device') else str(s.ctx.devices[0].name)}))"
    result=subprocess.run(["docker","exec",names["driver"],"python","-c",code],capture_output=True)
    # Identificação de dependências não depende de atributos privados do motor.
    if result.returncode!=0:
        code="import json,sys,importlib.metadata,pyopencl as cl;print(json.dumps({'python':sys.version.split()[0],'packages':{x:importlib.metadata.version(x) for x in ['fastapi','uvicorn','sqlalchemy','psycopg','pydantic','pytest','numpy','pyopencl']},'devices':[d.name for p in cl.get_platforms() for d in p.get_devices()]}))"
        result=subprocess.run(["docker","exec",names["driver"],"python","-c",code],capture_output=True)
    assert result.returncode==0
    (OUT/"versions.json").write_bytes(result.stdout)
    log=subprocess.check_output(["docker","logs",names["api"]],stderr=subprocess.STDOUT).decode(errors="replace")
    forms=[]
    for value in markers:
        forms.extend([value,quote(value,safe=""),quote(value,safe="").lower()])
    checks={"query_values_absent":not any(value in log for value in forms),
            "access_logs_preserved":'GET /api/v1/clinical/search HTTP/1.1' in log,
            "status_422_present":'422 Unprocessable Entity' in log,
            "status_401_present":'401 Unauthorized' in log,
            "status_403_present":'403 Forbidden' in log,
            "status_500_present":'500 Internal Server Error' in log,
            "unknown_route_redacted":"[unmatched]" in log,
            "path_values_redacted":"/api/v1/patients/{patient_id}/record" in log,
            "error_event_preserved":"server_event=server_error" in log,
            "traceback_absent":"Traceback (most recent call last)" not in log,
            "original_cmd":True}
    (OUT/"privacy-log-check.json").write_text(json.dumps(checks,indent=2))
    (OUT/"api-sanitized.log").write_text(sanitize(log))
    assert all(checks.values()),checks
finally:
    cleanup=[]
    for kind,name in reversed(owned):
        data=json.loads(get("docker",kind,"inspect",name))[0]
        labels=data.get("Config",{}).get("Labels",{}) if kind in ("container","image") else data.get("Labels",{})
        assert (labels or {}).get(label)==tag
        result=subprocess.run(["docker",kind,"rm",*(["-f"] if kind=="container" else []),name],capture_output=True)
        cleanup.append({"kind":kind,"name":name,"removed":result.returncode==0})
    (OUT/"cleanup.json").write_text(json.dumps(cleanup,indent=2))
    after=inventory();(OUT/"inventory-after.json").write_text(json.dumps(after,indent=2))
    assert before==after
    assert all(row["removed"] for row in cleanup)
print("N05-LOG: testes/HTTP/logs concluídos; recursos próprios removidos.")
