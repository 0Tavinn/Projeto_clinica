
from pathlib import Path
import subprocess,json
O=Path(__file__).parent
prefix=(O/"resource-prefix.txt").read_text().strip()
assert prefix.startswith("lumina-corrected-qa-")
resources=json.loads((O/"resources.json").read_text())
entries=[]
for kind in ["container","volume","network"]:
 for r in resources:
  if r["kind"]!=kind:continue
  name=r["name"];assert name.startswith(prefix+"-")
  proc=subprocess.run(["docker",kind,"inspect",name],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if proc.returncode:
   entries.append({"kind":kind,"name":name,"result":"already absent"});continue
  meta=json.loads(proc.stdout)[0]
  labels=meta.get("Config",{}).get("Labels",{}) if kind=="container" else meta.get("Labels",{})
  assert labels.get("lumina.corrected.qa")==prefix,"ownership mismatch"
  cmd=["docker","rm","-f",name] if kind=="container" else ["docker",kind,"rm",name]
  p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
  entries.append({"kind":kind,"name":name,"exit":p.returncode})
  assert p.returncode==0
image=prefix+":source"
p=subprocess.run(["docker","image","inspect",image],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if p.returncode==0:
 meta=json.loads(p.stdout)[0];assert meta["Config"]["Labels"]["lumina.corrected.qa"]==prefix
 p=subprocess.run(["docker","image","rm",image],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
 entries.append({"kind":"image","name":image,"exit":p.returncode});assert p.returncode==0
env=O/".qa-ephemeral.env"
if env.exists():env.unlink()
(O/"cleanup.json").write_text(json.dumps(entries,indent=2))
print(json.dumps(entries))
