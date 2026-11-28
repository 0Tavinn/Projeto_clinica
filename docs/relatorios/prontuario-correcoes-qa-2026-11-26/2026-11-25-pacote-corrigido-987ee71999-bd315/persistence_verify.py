
"""Auxiliar de reproducao preparado em26/11; nao reexecutado nesta data."""
from pathlib import Path
import subprocess,json,time
O=Path(__file__).parent
p=(O/"resource-prefix.txt").read_text().strip()
assert p.startswith("lumina-corrected-qa-")
def snapshot(name):
 r=subprocess.run(["docker","exec",p+"-driver","python","/qa/snapshot_db.py"],text=True,capture_output=True,timeout=40)
 r.check_returncode();value=json.loads(r.stdout)
 (O/name).write_text(json.dumps(value,indent=2));return value
before=snapshot("persistence-reproduced-before.json")
proof=[]
for suffix in ["-api","-db"]:
 name=p+suffix
 item=json.loads(subprocess.check_output(["docker","inspect",name],text=True))[0]
 assert item["Config"]["Labels"]["lumina.corrected.qa"]==p
 proof.append({"name":name,"id":item["Id"],"before_started":item["State"]["StartedAt"]})
 subprocess.run(["docker","restart",name],check=True,timeout=90,stdout=subprocess.DEVNULL)
for _ in range(100):
 r=subprocess.run(["docker","exec",p+"-db","pg_isready","-U","qa","-d","lumina_corrected_qa"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if r.returncode==0:break
 time.sleep(.2)
else:raise RuntimeError("PostgreSQL indisponivel")
after=snapshot("persistence-reproduced-after.json")
result={"all_table_snapshots_equal":before==after,"tables":len(before),"type":"restart dos mesmos containers"}
(O/"persistence-reproduced-result.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result))
assert before==after
