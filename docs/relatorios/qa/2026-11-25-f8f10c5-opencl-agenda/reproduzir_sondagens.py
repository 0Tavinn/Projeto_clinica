
"""Reproducao em NOVA pasta de evidencias. Nao sobrescreve a rodada original."""
import pathlib,sys,subprocess,uuid,tarfile,io,json,hashlib,shutil
r=pathlib.Path("/home/paulinho/Work/Projeto_clinica_clinical_2fa")
source=pathlib.Path(__file__).parent
expected=json.loads((source/"tested-source-hashes.json").read_text())
for p,h in expected.items():
 if hashlib.sha256((r/p).read_bytes()).hexdigest()!=h:
  raise SystemExit("Fonte diverge da versao auditada: "+p+". Identifique uma nova candidata antes do reteste.")
o=r/"docs/relatorios/qa"/("repro-opencl-"+uuid.uuid4().hex[:12])
o.mkdir(parents=True)
for name in ["probe_http.py","test_independent_opencl.py","run_independent.py"]:
 shutil.copy2(source/name,o/name)
suffix="qa-independent-"+uuid.uuid4().hex[:10]
(o/"independent-id.txt").write_text(suffix)
baseline=o/"baseline-pr18";baseline.mkdir()
data=subprocess.check_output(["git","archive","f8f10c54a4a702b7d4feccbf5aeb98578db65909","backend"],cwd=r)
with tarfile.open(fileobj=io.BytesIO(data)) as t:t.extractall(baseline,filter="data")
app="lumina-opencl-independent-app:"+suffix
qa="lumina-opencl-independent-tests:"+suffix
cmds=[
 (["Dockerfile","pyproject.toml","README.md","alembic.ini","app","alembic","scripts","tests","database"],
 ["docker","build","--label","lumina.opencl.qa="+suffix,"-t",app,"-"],"build-app.log"),
 (["tests","database","scripts"],
 ["docker","build","--label","lumina.opencl.qa="+suffix,"-f","tests/opencl-qa.Dockerfile","--build-arg","APP_IMAGE="+app,"-t",qa,"-"],"build-tests.log")]
for paths,cmd,filename in cmds:
 data=subprocess.check_output(["tar","-cf","-",*paths],cwd=r/"backend")
 p=subprocess.run(cmd,input=data,capture_output=True,timeout=360)
 (o/filename).write_bytes(p.stdout+p.stderr)
 if p.returncode:raise SystemExit("Build falhou: "+str(o/filename))
print("Evidencias novas em "+str(o),flush=True)
p=subprocess.run([sys.executable,str(o/"run_independent.py")],timeout=480)
raise SystemExit(p.returncode)
