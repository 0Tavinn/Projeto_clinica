
from qa_common import *
ids,tokens,ct=load();u=ids["users"];p=ids["patients"][6];d=u["dent1"]["dent"]
# Bulk fixture, authorized drafts plus hidden third-party drafts.
record=q("SELECT id FROM medical_records WHERE patient_id=:p",p=p)[0]["id"]
with E.begin() as db:
 db.execute(text("INSERT INTO clinical_evolutions(medical_record_id,dentist_id,description) SELECT :r,:d,'Ação página fictícia '||i FROM generate_series(1,1005) i"),{"r":record,"d":d})
 db.execute(text("INSERT INTO clinical_evolutions(medical_record_id,dentist_id,description) SELECT :r,:d,'Ação rascunho privado fictício' FROM generate_series(1,3)"),{"r":record,"d":u["dent2"]["dent"]})
def pages():
 all_ids={}
 stats=[]
 hidden={x["id"] for x in q("SELECT id FROM clinical_evolutions WHERE medical_record_id=:r AND dentist_id=:d",r=record,d=u["dent2"]["dent"])}
 for engine in ["cpu","opencl"]:
  results=[]
  for offset in [0,1000]:
   r=req("GET","/api/v1/clinical/search",ct["dent1"],params={"patient_id":p,"q":"AÇÃO","engine_name":engine,"offset":offset})
   assert r.status_code==200
   body=r.json()
   stats.append({"engine":body["engine"],"offset":offset,"total_page":body["total"],"next_offset":body["next_offset"],"count":len(body["results"])})
   assert body["total"]==len(body["results"])
   assert body["next_offset"]==(1000 if offset==0 else None)
   results.extend(x["id"] for x in body["results"])
  all_ids[engine]=results
 return len(all_ids["cpu"])==1005 and len(set(all_ids["cpu"]))==1005 and all_ids["cpu"]==all_ids["opencl"] and not hidden.intersection(all_ids["cpu"]),{"pages":stats,"unique_visible":len(set(all_ids["cpu"])),"hidden_drafts_returned":bool(hidden.intersection(all_ids["cpu"]))}
case("REG-pagination-1005","paginas1000/5;next_offset;IDs iguais;rascunhos ocultos",pages)

def concurrent_search():
    def run(_):
        return req("GET","/api/v1/clinical/search",ct["dent1"],params={"patient_id":p,"q":"acao","engine_name":"opencl"})
    with cf.ThreadPoolExecutor(4) as pool:responses=list(pool.map(run,range(8)))
    arrays=[[x["id"] for x in r.json().get("results",[])] for r in responses]
    return all(r.status_code==200 and r.json()["engine"]=="opencl" for r in responses) and all(x==arrays[0] for x in arrays),{"http":[r.status_code for r in responses],"equal_ids":all(x==arrays[0] for x in arrays),"count_per_page":len(arrays[0])}
case("REG-concurrent-opencl-http","8 buscas OpenCL concorrentes iguais",concurrent_search)
def empty_match_page():
    r=req("GET","/api/v1/clinical/search",ct["dent1"],params={"patient_id":p,"q":"nunca-corresponde","engine_name":"opencl"})
    b=r.json()
    return r.status_code==200 and b["total"]==0 and b["next_offset"]==1000 and b["results"]==[],{"http":r.status_code,"total_page":b.get("total"),"next_offset":b.get("next_offset")}
case("REG-page-total-semantics","total=0 e proxima pagina de candidatos explicita",empty_match_page)
def kernel_unicode():
    from app.opencl_search import OpenCLSearch,sequential_search
    engine=OpenCLSearch()
    texts=["","AÇÃO Clínica","Straße","café","😀 texto","a"*10000+"fim"]
    for term in ["acao","CLÍNICA","strasse","café","😀","fim","inexistente"]:
        assert engine.search(texts,term)==sequential_search(texts,term)
    assert engine.search([], "teste")==[]
    assert engine.search(["",""], "teste")==[]
    return True,{"device":engine.device_name,"terms_compared":7,"empty_lists_and_strings":True}
case("REG-kernel-unicode","CPU/OpenCL iguais, vazios validos sem erro de buffer",kernel_unicode)

# Exact normalized UTF8 budget with emoji.
pb=ids["patients"][4];rb=q("SELECT id FROM medical_records WHERE patient_id=:p",p=pb)[0]["id"]
with E.begin() as db:
 eb=db.execute(text("INSERT INTO clinical_evolutions(medical_record_id,dentist_id,description) VALUES(:r,:d,:s) RETURNING id"),{"r":rb,"d":d,"s":"😀"*500000}).scalar_one()
def budget():
 codes=[]
 for mode in ["cpu","opencl"]:
  r=req("GET","/api/v1/clinical/search",ct["dent1"],params={"patient_id":pb,"q":"naoexiste","engine_name":mode});codes.append(r.status_code)
 q("UPDATE clinical_evolutions SET description=:s WHERE id=:id",s="😀"*500001,id=eb)
 over=[req("GET","/api/v1/clinical/search",ct["dent1"],params={"patient_id":pb,"q":"naoexiste","engine_name":mode}).status_code for mode in ["cpu","auto","opencl"]]
 return codes==[200,200] and over==[413,413,413],{"at_2000000_bytes":codes,"at_2000004_bytes":over}
case("REG-byte-budget-unicode","limiteaceito;acima413 em todos motores",budget)
# Rollback patient+record failure, source unchanged.
q("CREATE FUNCTION qa_record_failure() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'QA forced failure'; END $$")
q("CREATE TRIGGER qa_record_failure BEFORE INSERT ON medical_records FOR EACH ROW EXECUTE FUNCTION qa_record_failure()")
before=q("SELECT count(*) n FROM patients")[0]["n"]
try:
 r=req("POST","/api/v1/patients",tokens["recep"],{"full_name":"Rollback ficticio","cpf":"99999990001","medical_record_number":"ROLLBACK-QA","birth_date":"1990-01-01"})
finally:
 q("DROP TRIGGER qa_record_failure ON medical_records");q("DROP FUNCTION qa_record_failure()")
after=q("SELECT count(*) n FROM patients")[0]["n"]
case("REG-patient-rollback","falha sem paciente ou prontuario residual",lambda:(r.status_code==500 and before==after,{"http":r.status_code,"patients_before":before,"patients_after":after}))
# Unique patient/record under two HTTP creations.
def duplicate_patient():
 body={"full_name":"Concorrente ficticio","cpf":"99999990002","medical_record_number":"CONCURRENT-QA","birth_date":"1990-01-01"}
 with cf.ThreadPoolExecutor(2) as pool:rs=list(pool.map(lambda _:req("POST","/api/v1/patients",tokens["recep"],body),range(2)))
 rows=q("SELECT p.id,r.id record FROM patients p JOIN medical_records r ON r.patient_id=p.id WHERE p.cpf='99999990002'")
 return sorted(x.status_code for x in rs)==[201,409] and len(rows)==1,{"http":sorted(x.status_code for x in rs),"records":len(rows)}
case("REG-patient-duplicate","201/409 umpaciente/prontuario",duplicate_patient)
# Evolution rollback when related audit insertion fails.
pr=ids["patients"][0];er=create(ct["dent1"],pr)
q("CREATE FUNCTION qa_audit_failure() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.action='EVOLUTION_EDITED' THEN RAISE EXCEPTION 'QA forced failure'; END IF; RETURN NEW; END $$")
q("CREATE TRIGGER qa_audit_failure BEFORE INSERT ON audit_logs FOR EACH ROW EXECUTE FUNCTION qa_audit_failure()")
try:r=req("PATCH",f"/api/v1/evolutions/{er}",ct["dent1"],{"version":1,"notes":"não persistir"})
finally:q("DROP TRIGGER qa_audit_failure ON audit_logs");q("DROP FUNCTION qa_audit_failure()")
row=q("SELECT version,status,notes,finalized_at FROM clinical_evolutions WHERE id=:id",id=er)[0]
case("REG-evolution-rollback","estado/versao/conteudo intactos apos falha relacionada",lambda:(r.status_code==500 and row["version"]==1 and row["status"]=="DRAFT" and row["notes"] is None and row["finalized_at"] is None,{"http":r.status_code,"state":row["status"],"version":row["version"],"notes_unchanged":row["notes"] is None}))
# Current-state fields are server-defined, ignore forged extras.
r=req("POST","/api/v1/evolutions",ct["dent1"],{"patient_id":pr,"description":"Autoria ficticia","dentist_id":u["dent2"]["dent"],"status":"FINALIZED","recorded_at":"2000-01-01T00:00:00Z","finalized_at":"2000-01-01T00:00:00Z"})
body=r.json()
case("REG-server-authorship-time","autor e horarios do servidor",lambda:(r.status_code==201 and body["dentist_id"]==d and body["status"]=="DRAFT" and body["finalized_at"] is None and not body["recorded_at"].startswith("2000-01-01"),{"http":r.status_code,"correct_author":body.get("dentist_id")==d,"state":body.get("status"),"forged_time_used":str(body.get("recorded_at")).startswith("2000-01-01")}))
# N05 query sentinel: response and default access logs are checked separately by orchestrator.
sentinel="QA_QUERY_PRIVATE_SENTINEL_20261125"
r=req("GET","/api/v1/clinical/search",ct["dent1"],params={"q":sentinel}) # missing patient_id ->422
case("N05-validation-query-response","422 sem eco do termo clinico",lambda:(r.status_code==422 and sentinel not in r.text,{"http":r.status_code,"echo":sentinel in r.text}))
