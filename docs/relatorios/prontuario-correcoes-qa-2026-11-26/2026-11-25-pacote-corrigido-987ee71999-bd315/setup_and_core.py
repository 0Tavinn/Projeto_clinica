
from pathlib import Path
import subprocess,json,secrets,os,time
O=Path(__file__).parent
SOURCE=Path("/home/paulinho/Work/lumina_odonto_corrigido_QA/lumina_odonto_atualizado")
prefix=(O/"resource-prefix.txt").read_text().strip()
image=prefix+":source";db=prefix+"-db";api=prefix+"-api";network=prefix+"-net";volume=prefix+"-data";label="lumina.corrected.qa="+prefix
resources=[]
pwd=secrets.token_urlsafe(20);secret=secrets.token_urlsafe(48)
envfile=O/".qa-ephemeral.env"
envfile.write_text("DATABASE_URL=postgresql+psycopg://qa:"+pwd+"@pg:5432/lumina_corrected_qa"+chr(10)+"JWT_SECRET="+secret+chr(10))
envfile.chmod(0o600)
def run(cmd,name,stdin=None,check=True,timeout=180):
 p=subprocess.run(cmd,input=stdin,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 output=p.stdout.replace(secret,"<redacted>").replace(pwd,"<redacted>")
 (O/name).write_text(output)
 if check and p.returncode:raise RuntimeError(name+" exit="+str(p.returncode))
 return p
def save(): (O/"resources.json").write_text(json.dumps(resources,indent=2))
override="""services:
  api:
    env_file: !override
      - %s
    image: %s
    ports: !reset []
  db:
    ports: !reset []
volumes:
  pgdata:
    name: %s
networks:
  default:
    name: %s
"""%(envfile,image,volume,network)
(O/"compose.qa.override.yml").write_text(override)
run(["docker","compose","-p",prefix,"-f",str(SOURCE/"docker-compose.yml"),"-f",str(O/"compose.qa.override.yml"),"config","--quiet"],"compose-config.log")
for kind,name in [("network",network),("volume",volume),("container",db),("container",api)]:
 if subprocess.run(["docker",kind,"inspect",name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:raise RuntimeError("resource already exists")
for kind,name in [("network",network),("volume",volume)]:
 run(["docker",kind,"create","--label",label,name],"create-"+kind+".log")
 resources.append({"kind":kind,"name":name});save()
run(["docker","run","-d","--label",label,"--name",db,"--network",network,"--network-alias","pg","--mount","type=volume,src="+volume+",dst=/var/lib/postgresql/data","--mount","type=bind,src="+str(SOURCE/"sql/schema.sql")+",dst=/docker-entrypoint-initdb.d/001-schema.sql,readonly","-e","POSTGRES_USER=qa","-e","POSTGRES_DB=lumina_corrected_qa","-e","POSTGRES_PASSWORD="+pwd,"postgres:16"],"db-start.log")
resources.append({"kind":"container","name":db});save()
for _ in range(100):
 logs=subprocess.run(["docker","logs",db],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout
 ready=subprocess.run(["docker","exec",db,"pg_isready","-U","qa","-d","lumina_corrected_qa"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
 if "PostgreSQL init process complete" in logs and ready:break
 time.sleep(.3)
else:raise RuntimeError("DB init timeout")
run(["docker","exec",db,"psql","-X","-At","-U","qa","-d","lumina_corrected_qa","-c","SHOW server_version"],"postgres-version.txt")
run(["docker","exec","-i",db,"psql","-X","-v","ON_ERROR_STOP=1","-U","qa","-d","lumina_corrected_qa"],"seed.log",stdin=(SOURCE/"sql/seed_demo.sql").read_text())
run(["docker","exec","-i",db,"psql","-X","-v","ON_ERROR_STOP=1","-U","qa","-d","lumina_corrected_qa"],"sql-constraints.log",stdin=(SOURCE/"sql/check_clinical_schema.sql").read_text())
run(["docker","run","-d","--label",label,"--name",api,"--network",network,"--network-alias","qa-api","--env-file",str(envfile),image],"api-start.log")
resources.append({"kind":"container","name":api});save()
# Run unchanged supplied tests and preserve JUnit before removing their container.
test=prefix+"-provided-tests"
p=run(["docker","run","--label",label,"--name",test,"--network",network,"--env-file",str(envfile),image,"python","-m","pytest","-v","-ra","--junitxml=/tmp/provided.xml","--disable-warnings","--tb=short"],"provided-tests.log",check=False)
resources.append({"kind":"container","name":test});save()
run(["docker","cp",test+":/tmp/provided.xml",str(O/"provided-tests.xml")],"copy-junit.log",check=False)
print("provided_tests_exit",p.returncode,flush=True)
# QA driver runs as a peer HTTP client. Fixture ids persist in /tmp across phases.
driver=prefix+"-driver"
run(["docker","run","-d","--label",label,"--name",driver,"--network",network,"--env-file",str(envfile),"--mount","type=bind,src="+str(O)+",dst=/qa,readonly","-e","PYTHONPATH=/app:/qa",image,"python","-c","import time; time.sleep(36000)"],"driver-start.log")
resources.append({"kind":"container","name":driver});save()
for script in ["fixture.py","core_probe.py"]:
 p=run(["docker","exec",driver,"python","/qa/"+script],script+".log",check=False)
 print(script,"exit",p.returncode,flush=True)
run(["docker","exec",api,"python","-m","pip","freeze"],"dependencies.txt")
run(["docker","exec",api,"python","--version"],"python-version.txt")
run(["docker","inspect","--format","{{.Image}}",api],"image-id.txt")
run(["docker","exec",driver,"python","-c","import json; from app.opencl_search import OpenCLSearch; import pyopencl as cl,numpy; e=OpenCLSearch(); d=e.ctx.devices[0];print(json.dumps({'platform':d.platform.name,'device':d.name.strip(),'type':str(d.type),'driver':d.driver_version,'opencl':d.version,'pyopencl':cl.VERSION_TEXT,'numpy':numpy.__version__}))"],"opencl-device.json")
print("SETUP_AND_CORE_DONE",flush=True)
