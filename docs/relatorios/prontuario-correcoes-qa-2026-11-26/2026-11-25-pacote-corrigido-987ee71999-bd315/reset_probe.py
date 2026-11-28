
from qa_common import *
import jwt,os
ids,tokens,ct=load();users=ids["users"];p=ids["patients"][0]
case("REG-passwords-distinct-create","422 se senhas de login/clinica iguais",lambda:status("POST","/api/v1/users",tokens["admin"],{"full_name":"Usuario QA ficticio","email":"equal@qa.invalid","cpf":"99999990003","role":"DENTIST","password":"MesmoFicticio2026!","clinical_password":"MesmoFicticio2026!"},422))
case("REG-reset-login-equals-clinical","422",lambda:status("POST",f"/api/v1/admin/users/{users['dent2']['id']}/reset-login-password",tokens["admin"],{"new_password":"FicticioClinico2026!"},422))
case("REG-reset-clinical-equals-login","422",lambda:status("POST","/api/v1/auth/reset-clinical-password",tokens["dent2"],{"new_password":"FicticioLogin2026!"},422))
case("REG-reset-foreign-target","404",lambda:status("POST",f"/api/v1/admin/users/{users['foreign']['id']}/reset-login-password",tokens["admin"],{"new_password":"NovoFicticio2026!"},404))
case("REG-reset-nonadmin","403",lambda:status("POST",f"/api/v1/admin/users/{users['dent2']['id']}/reset-login-password",tokens["recep"],{"new_password":"NovoFicticio2026!"},403))
def reset_login_flow():
 uid=users["dent2"]["id"]
 before=q("SELECT session_version FROM users WHERE id=:id",id=uid)[0]["session_version"]
 r=req("POST",f"/api/v1/admin/users/{uid}/reset-login-password",tokens["admin"],{"new_password":"NovoFicticioLogin2026!"})
 access=req("GET","/api/v1/auth/me",tokens["dent2"])
 clinical=req("GET",f"/api/v1/patients/{p}/record",ct["dent2"])
 old=req("POST","/api/v1/auth/login",body={"email":"dent2@qa.invalid","password":"FicticioLogin2026!"})
 new=login("dent2","NovoFicticioLogin2026!");newclinical=unlock(new)
 after=q("SELECT session_version FROM users WHERE id=:id",id=uid)[0]["session_version"]
 json.dump({"dent2_login_changed":True},open("/tmp/qa-reset-state.json","w"))
 return r.status_code==200 and access.status_code==401 and clinical.status_code==401 and old.status_code==401 and after==before+1 and bool(newclinical),{"reset":r.status_code,"old_access":access.status_code,"old_clinical":clinical.status_code,"old_password":old.status_code,"session_increment":after-before,"new_login_unlock":True}
case("REG-reset-login-invalidates","reset invalida tokens e senha antigos; novo login funciona",reset_login_flow)
def reset_clinical_flow():
 access=login("dent2","NovoFicticioLogin2026!");oldclinical=unlock(access)
 before=q("SELECT clinical_version FROM users WHERE id=:id",id=users["dent2"]["id"])[0]["clinical_version"]
 r=req("POST","/api/v1/auth/reset-clinical-password",access,{"new_password":"NovaFicticiaClinica2026!"})
 old=req("GET",f"/api/v1/patients/{p}/record",oldclinical)
 valid=req("GET","/api/v1/auth/me",access)
 new=unlock(access,"NovaFicticiaClinica2026!")
 after=q("SELECT clinical_version FROM users WHERE id=:id",id=users["dent2"]["id"])[0]["clinical_version"]
 return r.status_code==200 and old.status_code==401 and valid.status_code==200 and after==before+1 and bool(new),{"reset":r.status_code,"old_clinical":old.status_code,"login_still_valid":valid.status_code,"clinical_increment":after-before,"new_unlock":True}
case("REG-reset-clinical-invalidates","reset clinico invalida somente liberacao correspondente",reset_clinical_flow)
user=q("SELECT id,clinic_id,session_version,clinical_version FROM users WHERE id=:id",id=users["dent1"]["id"])[0]
payload={**user,"sub":str(user["id"]),"type":"clinical","exp":int(time.time())-60};payload.pop("id")
expired=jwt.encode(payload,os.environ["JWT_SECRET"],algorithm="HS256")
case("REG-expired-clinical","401",lambda:status("GET",f"/api/v1/patients/{p}/record",expired,None,401))
payload["exp"]=int(time.time())+60
invalid=jwt.encode(payload,"other-fictitious-key-only-qa",algorithm="HS256")
case("REG-invalid-token","401",lambda:status("GET",f"/api/v1/patients/{p}/record",invalid,None,401))
# Observation, no invented rate threshold.
codes=[req("POST","/api/v1/auth/login",body={"email":"dent1@qa.invalid","password":"errada"}).status_code for _ in range(8)]
print("QA_OBSERVATION "+json.dumps({"id":"RATE-policy","observed_http":codes,"criterion":"limiar nao aprovado; sem aceite/reprovacao inferidos"}),flush=True)
