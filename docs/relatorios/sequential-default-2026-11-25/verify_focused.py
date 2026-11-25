"""Valida defaults e reutiliza o runner oficial sem benchmark nem suíte ampla."""

import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def inventory():
    result={}
    ids=subprocess.check_output(["docker","ps","-aq"],text=True).split()
    items=json.loads(subprocess.check_output(["docker","inspect",*ids])) if ids else []
    result["containers"]=[{"id":x["Id"],"image":x["Image"],"name":x["Name"],
                          "started":x["State"]["StartedAt"],"status":x["State"]["Status"],
                          "restarts":x["RestartCount"],"ports":x["NetworkSettings"]["Ports"]}
                         for x in items]
    for kind in ("volume","network"):
        result[kind]=subprocess.check_output(["docker",kind,"ls","--format","{{.ID}}" if kind=="network" else "{{.Name}}"],text=True).splitlines()
    return result

before=inventory()
(OUT/"inventory-before.json").write_text(json.dumps(before,indent=2))
# Renderiza apenas configurações fictícias, sem carregar o .env existente.
checks=[]
with tempfile.TemporaryDirectory(prefix="lumina-default-") as temporary:
    fake=Path(temporary)/"fake.env"
    fake.write_text("POSTGRES_DB=qa_default\nPOSTGRES_USER=qa_default\nPOSTGRES_PASSWORD=qa-only-fake\nSECRET_KEY=qa-only-fake\nCOMPOSE_PROJECT_NAME=qa_default\n")
    for supplied,expected in ((None,"sequential"),("","sequential"),("auto","auto"),("sequential","sequential")):
        environment=dict(os.environ)
        environment.pop("APPOINTMENT_CONFLICT_ENGINE",None)
        if supplied is not None: environment["APPOINTMENT_CONFLICT_ENGINE"]=supplied
        document=json.loads(subprocess.check_output([
            "docker","compose","--env-file",str(fake),"-f",str(ROOT/"compose.yml"),
            "config","--format","json"],env=environment))
        actual=document["services"]["api"]["environment"]["APPOINTMENT_CONFLICT_ENGINE"]
        assert actual==expected
        checks.append({"supplied":supplied,"effective":actual,"passed":True})
    # Testa o gerador em cópia temporária, preservando o .env de Paulo.
    test_root=Path(temporary)/"generator";(test_root/"scripts").mkdir(parents=True)
    script=test_root/"scripts/setup_dev.py";script.write_bytes((ROOT/"scripts/setup_dev.py").read_bytes())
    subprocess.run(["python3",str(script),"--project","qa_default"],check=True,capture_output=True)
    generated=(test_root/".env").read_text()
    assert "APPOINTMENT_CONFLICT_ENGINE=sequential" in generated.splitlines()
    (test_root/".env").write_text("APPOINTMENT_CONFLICT_ENGINE=auto\n")
    old=(test_root/".env").read_bytes()
    result=subprocess.run(["python3",str(script)],capture_output=True)
    assert result.returncode==1 and (test_root/".env").read_bytes()==old
    checks.append({"setup_new_default":"sequential","existing_auto_preserved":True,"passed":True})
(OUT/"configuration-checks.json").write_text(json.dumps(checks,indent=2))

source=(ROOT/"backend/tests/run_opencl_qa.sh").read_text()
for line in (
    'docker run --rm "$qa_image" python -m scripts.benchmark_conflicts > "$report/benchmark.json"',
    'docker run --rm "$qa_image" python -m pytest -q -p no:cacheprovider --disable-warnings --tb=short | tee "$report/full-suite.log"',
):
    assert source.count(line)==1
    source=source.replace(line,"# Omitido nesta verificação proporcional de configuração.")
source=source.replace('cd "$(dirname "$0")/.."','cd '+str(ROOT/"backend"))
with (OUT/"focused-runner.log").open("w") as log:
    result=subprocess.run(["bash","-c",source],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=480)
after=inventory()
(OUT/"inventory-after.json").write_text(json.dumps(after,indent=2))
assert before==after
assert result.returncode==0
print("Configurações e ensaio dirigido aprovados; inventário preservado.")
