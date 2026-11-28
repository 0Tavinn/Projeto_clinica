
from qa_common import *
for _ in range(100):
    try:
        if req("GET","/health").status_code==200:break
    except Exception:pass
    time.sleep(.2)
else:raise RuntimeError("API QA nao pronta")
cids=[]
for n in (1,2):
    cids.append(q("INSERT INTO clinics(name,cnpj,email) VALUES(:n,:c,:e) RETURNING id",n="QA Reteste "+str(n),c=f"99999999999{n}00",e=f"clinic{n}@qa.invalid")[0]["id"])
users={}
for i,(name,role,ci,active) in enumerate([("admin","ADMINISTRATOR",0,True),("recep","RECEPTIONIST",0,True),("dent1","DENTIST",0,True),("dent2","DENTIST",0,True),("foreign","DENTIST",1,True),("inactive","DENTIST",0,False),("noprof","DENTIST",0,True)]):
    uid=q("INSERT INTO users(clinic_id,full_name,email,cpf,role,is_active,password_hash,clinical_password_hash) VALUES(:c,:n,:e,:p,:r,:a,:h,:ch) RETURNING id",c=cids[ci],n=name,e=name+"@qa.invalid",p=f"{500+i:011d}",r=role,a=active,h=hasher.hash("FicticioLogin2026!"),ch=hasher.hash("FicticioClinico2026!"))[0]["id"]
    users[name]={"id":uid}
    if role=="DENTIST" and name!="noprof":
        users[name]["dent"]=q("INSERT INTO dentists(user_id,cro_number,cro_state) VALUES(:u,:c,'PE') RETURNING id",u=uid,c=str(99000+i))[0]["id"]
at=login("admin");rt=login("recep")
pids=[]
for i in range(9):
    p=req("POST","/api/v1/patients",rt,{"full_name":"Paciente reteste "+str(i),"cpf":f"{700+i:011d}","medical_record_number":"MANUAL-RETESTE-"+str(i),"birth_date":"1990-01-01"})
    assert p.status_code==201
    pids.append(p.json()["patient_id"])
for p in pids[:7]:
    assert grant(at,p,users["dent1"]["dent"]).status_code==200
assert grant(at,pids[0],users["dent2"]["dent"]).status_code==200
json.dump({"clinics":cids,"users":users,"patients":pids},open("/tmp/qa-fixture.json","w"))
print("QA fixture criada: duas clinicas; perfis ficticios; pacientes e vinculos proprios",flush=True)
