
"""Preparo e limpeza exclusivos das sondagens QA adicionais."""
import subprocess,pathlib,json,time,secrets,hashlib,os
R=pathlib.Path("/home/paulinho/Work/Projeto_clinica_clinical_2fa")
O=pathlib.Path(__file__).parent
suffix=(O/"independent-id.txt").read_text().strip()
label="lumina.opencl.qa="+suffix
app="lumina-opencl-independent-app:"+suffix
qa="lumina-opencl-independent-tests:"+suffix
net="lumina_agenda_"+suffix
vol=net+"_data"
db=net+"_db";api=net+"_api"
pwd=secrets.token_urlsafe(18);secret=secrets.token_urlsafe(40)
url="postgresql+psycopg://opencl_qa:"+pwd+"@pg/lumina_opencl_scratch"
created=[]
def run(cmd,file,stdin=None,check=True,timeout=180):
    p=subprocess.run(cmd,input=stdin,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
    data=p.stdout.replace(pwd,"<qa-credential-redacted>").replace(secret,"<qa-secret-redacted>")
    (O/file).write_text(data,encoding="utf8")
    if check and p.returncode:raise RuntimeError(file+" exit="+str(p.returncode))
    return p.returncode,data
def docker_run(args,file,check=True):
    return run(["docker","run","--rm","--label",label]+args,file,check=check)
try:
    for kind,name in [("network",net),("volume",vol),("container",db),("container",api)]:
        p=subprocess.run(["docker",kind,"inspect",name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if p.returncode==0:raise RuntimeError("resource exists")
    run(["docker","network","create","--label",label,net],"independent-network.log");created.append(("network",net))
    run(["docker","volume","create","--label",label,vol],"independent-volume.log");created.append(("volume",vol))
    run(["docker","run","-d","--label",label,"--name",db,"--network",net,"--network-alias","pg",
         "--mount","type=volume,src="+vol+",dst=/var/lib/postgresql/data","-e","POSTGRES_DB=lumina_opencl_scratch",
         "-e","POSTGRES_USER=opencl_qa","-e","POSTGRES_PASSWORD="+pwd,"postgres:16-alpine"],"independent-db.log")
    created.append(("container",db))
    for _ in range(90):
        p=subprocess.run(["docker","exec",db,"pg_isready","-h","127.0.0.1","-U","opencl_qa","-d","lumina_opencl_scratch"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if p.returncode==0:break
        time.sleep(.3)
    else:raise RuntimeError("PostgreSQL timeout")
    run(["docker","exec","-i",db,"psql","-X","-v","ON_ERROR_STOP=1","-U","opencl_qa","-d","lumina_opencl_scratch"],"independent-schema.log",stdin=(R/"backend/database/schema.sql").read_text())
    run(["docker","exec",db,"psql","-X","-At","-U","opencl_qa","-d","lumina_opencl_scratch","-c","SHOW server_version"],"independent-postgres-version.txt")
    run(["docker","run","-d","--label",label,"--name",api,"--network",net,"--network-alias","qa-api",
         "-e","ENVIRONMENT=test","-e","DATABASE_URL="+url,"-e","SECRET_KEY="+secret,app],"independent-api-start.log")
    created.append(("container",api))
    run(["docker","inspect","--format","{{.Image}}",api],"independent-api-image.txt")
    common=["--network",net,"--mount","type=bind,src="+str(O)+",dst=/qa,readonly","-e","DATABASE_URL="+url,"-e","SECRET_KEY="+secret]
    docker_run(common+[qa,"python","/qa/probe_http.py"],"independent-http.log",check=False)
    docker_run(["--mount","type=bind,src="+str(O)+",dst=/qa,readonly",qa,
                "python","-m","pytest","-v","-s","-p","no:cacheprovider","--junitxml=/tmp/qa.xml",
                "/qa/test_independent_opencl.py","--disable-warnings","--tb=short"],"independent-opencl.log",check=False)
    # Collect nodeids to deduplicate official targeted/full runs.
    docker_run([qa,"python","-m","pytest","--collect-only","-q","-p","no:cacheprovider"],"full-collection.txt")
    docker_run([qa,"python","-m","pytest","--collect-only","-q","-p","no:cacheprovider",
                "tests/test_opencl_conflicts.py","tests/test_appointments.py","tests/test_opencl_repository.py","tests/test_opencl_pg.py"],"targeted-collection.txt")
    # Compare OpenAPI with source extracted directly from the PR18 commit.
    baseline="import sys,json; from app.main import app; from sqlalchemy.orm import configure_mappers; configure_mappers(); print(json.dumps(app.openapi(),sort_keys=True))"
    docker_run(["--mount","type=bind,src="+str(O/"baseline-pr18")+",dst=/baseline,readonly","-e","PYTHONPATH=/baseline/backend","-w","/tmp",qa,"python","-c",baseline],"baseline-source-openapi.json")
    docker_run([qa,"python","-c",baseline],"local-source-openapi.json")
    def document(name):
        raw=(O/name).read_text()
        (O/(name+".raw.log")).write_text(raw)
        value=json.loads(next(line for line in raw.splitlines() if line.startswith("{")))
        (O/name).write_text(json.dumps(value,sort_keys=True))
        return value
    one=document("baseline-source-openapi.json")
    two=document("local-source-openapi.json")
    canon=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    (O/"independent-openapi-comparison.json").write_text(json.dumps({"baseline_commit":"f8f10c54a4a702b7d4feccbf5aeb98578db65909","baseline_sha256":canon(one),"local_sha256":canon(two),"identical":one==two,"baseline_paths":len(one["paths"]),"local_paths":len(two["paths"])},indent=2))
    package="""import importlib.metadata as m,hashlib,json,sys; from importlib.resources import files; import app; p=files('app.appointments').joinpath('kernels/check_overlap.cl'); d=m.distribution('dental-clinic-api'); print(json.dumps({'python':sys.version,'app_location':app.__file__,'kernel_location':str(p),'kernel_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'kernel_in_distribution':any(str(x).endswith('kernels/check_overlap.cl') for x in d.files),'versions':{n:m.version(n) for n in ['numpy','pyopencl','fastapi','sqlalchemy','psycopg','pydantic','pytest']}}))"""
    docker_run(["-w","/tmp",qa,"python","-c",package],"installed-package.json")
    docker_run([qa,"python","-m","pip","freeze"],"independent-dependencies.txt")
    docker_run([qa,"python","-m","scripts.benchmark_conflicts"],"independent-benchmark.json")
    # Sanitized server logs only; no headers or settings dump.
    _,logs=run(["docker","logs",api],"independent-api-log.tmp",check=False)
    safe=[l for l in logs.splitlines() if l.startswith(("INFO:","WARNING:","ERROR:"))]
    (O/"independent-api.log").write_text("\n".join(safe));(O/"independent-api-log.tmp").unlink()
    print("supplement completed",flush=True)
finally:
    cleanup=[]
    for kind,name in reversed(created):
        labelarg="{{index .Config.Labels \"lumina.opencl.qa\"}}" if kind=="container" else "{{index .Labels \"lumina.opencl.qa\"}}"
        p=subprocess.run(["docker",kind,"inspect","--format",labelarg,name],capture_output=True,text=True)
        if p.returncode==0 and p.stdout.strip()==suffix:
            args=["docker","rm","-f",name] if kind=="container" else ["docker",kind,"rm",name]
            p=subprocess.run(args,capture_output=True,text=True)
            cleanup.append({"type":kind,"name":name,"removed":p.returncode==0})
        else:cleanup.append({"type":kind,"name":name,"removed":False,"reason":"ownership not verified"})
    for name in [qa,app]:
        p=subprocess.run(["docker","image","inspect","--format","{{index .Config.Labels \"lumina.opencl.qa\"}}",name],capture_output=True,text=True)
        if p.returncode==0 and p.stdout.strip()==suffix:
            p=subprocess.run(["docker","image","rm",name],capture_output=True,text=True)
            cleanup.append({"type":"image","name":name,"removed":p.returncode==0})
    (O/"independent-cleanup.json").write_text(json.dumps(cleanup,indent=2))
