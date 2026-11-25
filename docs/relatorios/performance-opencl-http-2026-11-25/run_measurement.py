"""Orquestra recursos próprios com inventário e limpeza por rótulo."""

import hashlib
import json
import subprocess
import tarfile
import time
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
assert ROOT == Path("/home/paulinho/Work/Projeto_clinica_clinical_2fa")
def command(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)
def capture(*args):
    return subprocess.check_output(args,text=True).strip()
assert capture("git","-C",str(ROOT),"branch","--show-current")=="feat/paralelismo-agendamento"
assert capture("git","-C",str(ROOT),"rev-parse","HEAD")=="f8f10c54a4a702b7d4feccbf5aeb98578db65909"
staged=subprocess.check_output(["git","-C",str(ROOT),"diff","--cached","--raw","-z"])
assert hashlib.sha256(staged).hexdigest()=="41f728d17e0dcc8729b81db0f5abcf7ab900e8fd8249fa65dff173a07e8a4932"

def inventory():
    ids=capture("docker","ps","-aq").split()
    containers=[]
    for item in ids:
        data=json.loads(capture("docker","inspect",item))[0]
        containers.append({"id":data["Id"],"name":data["Name"],"image":data["Image"],
                           "started":data["State"]["StartedAt"],"restart_count":data["RestartCount"],
                           "status":data["State"]["Status"],"ports":data["NetworkSettings"]["Ports"]})
    return {"containers":containers,"volumes":capture("docker","volume","ls","--format","{{.Name}}").splitlines(),
            "networks":capture("docker","network","ls","--format","{{.ID}} {{.Name}}").splitlines()}

before=inventory()
(OUT/"inventory-before.json").write_text(json.dumps(before,indent=2))
suffix="perf-"+uuid.uuid4().hex[:12]
label="lumina.opencl.perf"
names={"app":"lumina-perf-app:"+suffix,"lab":"lumina-perf-lab:"+suffix,
       "network":"lumina_"+suffix,"volume":"lumina_"+suffix,"db":"lumina_db_"+suffix,
       "probe":"lumina_probe_"+suffix}
(OUT/"resources.json").write_text(json.dumps({"suffix":suffix,"label":label,"names":names},indent=2))
owned=[]
def acquire(kind,name,args):
    command("docker",*args)
    owned.append((kind,name))
def check_absent(kind,name):
    result=subprocess.run(["docker",kind,"inspect",name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    assert result.returncode!=0
for key,kind in (("app","image"),("lab","image"),("network","network"),("volume","volume"),("db","container"),("probe","container")):
    check_absent(kind,names[key])

def build(context, members, image, logfile, build_args=()):
    archive=OUT/"build-context.tar"
    with tarfile.open(archive,"w",format=tarfile.GNU_FORMAT) as tar:
        for name in members: tar.add(context/name,arcname=name)
    with archive.open("rb") as stream, (OUT/logfile).open("wb") as log:
        command("docker","build","--label",label+"="+suffix,"-t",image,*build_args,"-",
                stdin=stream,stdout=log,stderr=subprocess.STDOUT,timeout=420)
    owned.append(("image",image))
    archive.unlink()

try:
    build(ROOT/"backend",["Dockerfile","pyproject.toml","README.md","alembic.ini","app","alembic","scripts"],
          names["app"],"build-app.log")
    build(OUT,["Dockerfile","instrumented_app.py","measure_http.py"],names["lab"],"build-lab.log",
          ("--build-arg","BASE="+names["app"]))
    acquire("network",names["network"],["network","create","--label",label+"="+suffix,names["network"]])
    acquire("volume",names["volume"],["volume","create","--label",label+"="+suffix,names["volume"]])
    acquire("container",names["db"],["run","-d","--name",names["db"],"--label",label+"="+suffix,
            "--network",names["network"],"--network-alias","pg","--mount",
            "type=volume,src="+names["volume"]+",dst=/var/lib/postgresql/data",
            "-e","POSTGRES_DB=lumina_perf_scratch","-e","POSTGRES_USER=perf_qa",
            "-e","POSTGRES_PASSWORD=perf-qa-only","postgres:16-alpine"])
    for _ in range(90):
        result=subprocess.run(["docker","exec",names["db"],"pg_isready","-h","127.0.0.1","-U","perf_qa","-d","lumina_perf_scratch"],
                              stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if result.returncode==0: break
        time.sleep(1)
    else: raise RuntimeError("Banco exclusivo não ficou disponível")
    with (ROOT/"backend/database/schema.sql").open("rb") as source, (OUT/"schema.log").open("wb") as log:
        command("docker","exec","-i",names["db"],"psql","-X","-q","-v","ON_ERROR_STOP=1",
                "-U","perf_qa","-d","lumina_perf_scratch",stdin=source,stdout=log,stderr=subprocess.STDOUT)
    acquire("container",names["probe"],["create","--name",names["probe"],"--label",label+"="+suffix,
            "--network",names["network"],"-e","ENVIRONMENT=test",
            "-e","DATABASE_URL=postgresql+psycopg://perf_qa:perf-qa-only@pg/lumina_perf_scratch",
            "-e","SECRET_KEY=isolated-performance-only",names["lab"]])
    with (OUT/"execution.log").open("wb") as log:
        command("docker","start","-a",names["probe"],stdout=log,stderr=subprocess.STDOUT,timeout=300)
    status=json.loads(capture("docker","inspect",names["probe"]))[0]["State"]["ExitCode"]
    # Extrai resultados inclusive quando a instrumentação falhar.
    extract=subprocess.Popen(["docker","cp",names["probe"]+":/tmp/measure-output/.","-"],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=extract.stdout,mode="r|") as tar:
        # Saídas produzidas pela própria instrumentação, sem caminhos externos.
        for member in tar:
            assert member.name.startswith("./") or "/" not in member.name
            assert ".." not in Path(member.name).parts
            if member.isfile():
                (OUT/Path(member.name).name).write_bytes(tar.extractfile(member).read())
    assert extract.wait()==0
    assert status==0, "Instrumentação falhou; consultar execution.log"
finally:
    results=[]
    for kind,name in reversed(owned):
        data=json.loads(capture("docker",kind,"inspect",name))[0]
        labels=data.get("Config",{}).get("Labels",{}) if kind in {"container","image"} else data.get("Labels",{})
        assert (labels or {}).get(label)==suffix
        args=["docker",kind,"rm"]
        if kind=="container": args.append("-f")
        result=subprocess.run([*args,name],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        results.append({"kind":kind,"name":name,"removed":result.returncode==0})
    (OUT/"cleanup.json").write_text(json.dumps(results,indent=2))
    after=inventory()
    (OUT/"inventory-after.json").write_text(json.dumps(after,indent=2))
    after_stage=subprocess.check_output(["git","-C",str(ROOT),"diff","--cached","--raw","-z"])
    (OUT/"stage-after.bin").write_bytes(after_stage)
    assert staged==after_stage
    assert before==after, "Inventário mudou; revisar antes/depois"
    assert all(row["removed"] for row in results)
print("Diagnóstico HTTP concluído; inventário e índice preservados.")
