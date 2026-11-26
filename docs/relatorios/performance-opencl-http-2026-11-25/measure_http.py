"""Experimento HTTP reproduzível em processo Uvicorn e banco exclusivos."""

import datetime as dt
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import httpx
from sqlalchemy import create_engine, text, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
import app.main
from app.users.models import Clinic, User
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.security.roles import Role
from app.security.auth import create_access_token

url = os.environ["DATABASE_URL"]
parsed = make_url(url)
assert parsed.host == "pg" and parsed.database == "lumina_perf_scratch"
assert parsed.username == "perf_qa"
db_engine = create_engine(url)
anchor = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)+dt.timedelta(days=10)
output = Path("/tmp/measure-output")
output.mkdir()
with Session(db_engine) as db:
    assert str(db.scalar(text("SHOW server_version_num"))).startswith("16")
    clinic = Clinic(name="Clínica fictícia", cnpj="12345678000199", email="perf@example.test")
    db.add(clinic); db.flush()
    user = User(clinic_id=clinic.id, full_name="Recepção fictícia", cpf="12345678901",
                email="perf@example.test", role=Role.RECEPTIONIST, password_hash="not-used")
    db.add(user)
    professionals = [
        User(clinic_id=clinic.id, full_name="Profissional fictício", cpf=f"{i+2:011d}",
             email=f"dentist{i}@example.test", role=Role.DENTIST, password_hash="not-used")
        for i in range(4)
    ]
    db.add_all(professionals); db.flush()
    dentists = [Dentist(user_id=u.id, cro_number=str(i+1), cro_state="PE")
                for i,u in enumerate(professionals)]
    patient = Patient(clinic_id=clinic.id, full_name="Paciente fictício", cpf="99999999999",
                      medical_record_number="PERF", birth_date=dt.date(1990,1,1))
    db.add_all(dentists+[patient]); db.commit()
    clinic_id, patient_id = clinic.id, patient.id
    dentist_ids = [d.id for d in dentists]
    token = create_access_token(user)
records = []
processes = []

def execute(query, parameters=None):
    with db_engine.begin() as db:
        return db.execute(text(query), parameters or {})

def count_rows():
    with db_engine.connect() as db:
        return db.scalar(text("SELECT count(*) FROM appointments"))

def reset_fixture(count, ids):
    """Insere slots não sobrepostos; sem gerar milhares de requisições HTTP."""
    execute("TRUNCATE appointments RESTART IDENTITY CASCADE")
    for dentist_id in ids:
        if count:
            execute(
                "INSERT INTO appointments(clinic_id,patient_id,dentist_id,scheduled_at,duration_minutes,status) "
                "SELECT :clinic,:patient,:dentist,CAST(:anchor AS timestamptz)+i*interval '1 hour',30,'SCHEDULED' "
                "FROM generate_series(0,:last) AS i",
                {"clinic":clinic_id,"patient":patient_id,"dentist":dentist_id,
                 "anchor":anchor,"last":count-1},
            )

def start_api(mode, label):
    """Processo novo e diretórios de cache próprios; health não inicializa OpenCL."""
    directory = Path(tempfile.mkdtemp(prefix="perf-cache-"))
    log = (output/(label+".log")).open("w")
    env = dict(os.environ, APPOINTMENT_CONFLICT_ENGINE=mode, XDG_CACHE_HOME=str(directory/"xdg"),
               POCL_CACHE_DIR=str(directory/"pocl"), PYTHONPATH="/measurement")
    process = subprocess.Popen(
        [sys.executable,"-m","uvicorn","instrumented_app:app","--host","127.0.0.1","--port","8000",
         "--no-access-log","--log-level","warning"], env=env, stdout=log, stderr=log,
    )
    for _ in range(200):
        try:
            if httpx.get("http://127.0.0.1:8000/health",timeout=1).status_code==200:
                break
        except httpx.HTTPError:
            pass
        if process.poll() is not None:
            raise RuntimeError("Uvicorn encerrou; consultar log de processo")
        time.sleep(.05)
    else:
        process.terminate(); process.wait(timeout=10)
        raise RuntimeError("API não iniciou")
    assert len(list(directory.rglob("*")))==0, "Cache deve estar vazio antes da primeira chamada"
    return process,log,directory

def stop_api(process, log, directory, label):
    process.terminate(); process.wait(timeout=20); log.close()
    info = {"label":label,"exit":process.returncode,"new_process":True,
            "cache_empty_before_first_request":True,"cache_entries_after":len(list(directory.rglob("*")))}
    processes.append(info)
    parsed_metrics = {}
    for line in (output/(label+".log")).read_text().splitlines():
        if line.startswith("PERF "):
            row=json.loads(line[5:])
            parsed_metrics[row["sample"]]=row
    for row in records:
        if row["process"]==label:
            row["server"]=parsed_metrics.get(row["id"])
            assert row["server"] is not None, row["id"]
            assert row["server"]["status"]==row["status"]
            assert row["server"]["fallback"] is False
            expected = "opencl" if row["mode"]=="auto" and row["candidate_count"] else "sequential"
            assert row["server"]["engine"]==expected, row

def request(client, mode, count, operation, label, ordinal, phase, subject=None, dentist=None, barrier=None):
    dentist = dentist or dentist_ids[0]
    free = anchor+dt.timedelta(hours=count+10)
    conflict = operation.endswith("conflict")
    when = anchor+dt.timedelta(hours=count-1) if conflict else free
    payload = {"patient_id":patient_id,"dentist_id":dentist,"scheduled_at":when.isoformat(),
               "duration_minutes":30}
    method = "POST" if operation.startswith("create") else "PATCH"
    path = "/api/v1/appointments" if method=="POST" else f"/api/v1/appointments/{subject}"
    if method=="PATCH":
        payload={"scheduled_at":when.isoformat(),"duration_minutes":30}
    sample=f"{label}-{phase}-{operation}-{ordinal}"
    if barrier: barrier.wait(timeout=10)
    start=time.perf_counter_ns()
    response=client.request(method,path,json=payload,headers={"X-Perf-Case":sample},timeout=60)
    elapsed=time.perf_counter_ns()-start
    expected=409 if conflict else (201 if method=="POST" else 200)
    assert response.status_code==expected, (sample,response.status_code)
    body=response.json()
    if conflict: assert body["error"]["code"]=="APPOINTMENT_TIME_CONFLICT"
    row={"id":sample,"process":label,"mode":mode,"candidate_count":count,
         "operation":operation,"phase":phase,"status":response.status_code,"http_ns":elapsed}
    records.append(row)
    if method=="POST" and not conflict:
        execute("DELETE FROM appointments WHERE id=:id",{"id":body["id"]})
    return row

for count in (0,32,512,8192):
    # Alterna a ordem para reduzir viés temporal entre os motores.
    for mode in (("sequential","auto") if count in (0,512) else ("auto","sequential")):
        reset_fixture(count,[dentist_ids[0]])
        label=f"{mode}-{count}"
        process,log,directory=start_api(mode,label)
        try:
            with httpx.Client(base_url="http://127.0.0.1:8000",
                              headers={"Authorization":"Bearer "+token}) as client:
                request(client,mode,count,"create_accept",label,0,"first")
                assert count_rows()==count
                operations=["create_accept"]+(["create_conflict"] if count else [])
                # Requisições aquecidas sequenciais, sem concorrência ou espera intencional.
                for i in range(12):
                    for operation in operations:
                        request(client,mode,count,operation,label,i,"warm")
                        assert count_rows()==count
                free=anchor+dt.timedelta(hours=count+10)
                with db_engine.begin() as db:
                    subject=db.scalar(text(
                        "INSERT INTO appointments(clinic_id,patient_id,dentist_id,scheduled_at,duration_minutes,status) "
                        "VALUES(:clinic,:patient,:dentist,:when,30,'SCHEDULED') RETURNING id"),
                        {"clinic":clinic_id,"patient":patient_id,"dentist":dentist_ids[0],"when":free})
                operations=["update_accept"]+(["update_conflict"] if count else [])
                for i in range(12):
                    for operation in operations:
                        request(client,mode,count,operation,label,i,"warm",subject=subject)
                        assert count_rows()==count+1
                        with db_engine.connect() as db:
                            assert db.scalar(text("SELECT scheduled_at FROM appointments WHERE id=:id"),
                                             {"id":subject})==free
        finally:
            stop_api(process,log,directory,label)

# Sondagens concorrentes separadas, dentistas diferentes para isolar o lock do runtime.
for mode in ("sequential","auto"):
    reset_fixture(32,dentist_ids)
    label=f"{mode}-parallel"
    process,log,directory=start_api(mode,label)
    try:
        for phase in ("parallel_first","parallel_warm"):
            barrier=Barrier(4)
            clients=[httpx.Client(base_url="http://127.0.0.1:8000",
                                 headers={"Authorization":"Bearer "+token}) for _ in dentist_ids]
            try:
                with ThreadPoolExecutor(max_workers=4) as pool:
                    futures=[pool.submit(request,client,mode,32,"create_accept",label,i,phase,
                                         dentist=dentist,barrier=barrier)
                             for i,(client,dentist) in enumerate(zip(clients,dentist_ids))]
                    [future.result(timeout=65) for future in futures]
            finally:
                for client in clients: client.close()
            assert count_rows()==128
    finally:
        stop_api(process,log,directory,label)

groups=[]
for mode in ("sequential","auto"):
    for count in (0,32,512,8192):
        for operation in ("create_accept","create_conflict","update_accept","update_conflict"):
            data=[r for r in records if r["mode"]==mode and r["candidate_count"]==count
                  and r["operation"]==operation and r["phase"]=="warm"]
            if not data: continue
            values=[r["http_ns"]/1e6 for r in data]
            ordered=sorted(values)
            # Percentil por interpolação linear, explícito para as 12 amostras.
            def percentile(p):
                index=(len(ordered)-1)*p
                low=int(index); high=min(low+1,len(ordered)-1)
                return ordered[low]+(ordered[high]-ordered[low])*(index-low)
            groups.append({"mode":mode,"candidate_count":count,"operation":operation,"n":len(data),
                           "median_ms":statistics.median(values),"p95_ms":percentile(.95),
                           "min_ms":min(values),"max_ms":max(values),"iqr_ms":percentile(.75)-percentile(.25),
                           "mean_components_ms":{k:statistics.mean(r["server"].get(k,0)/1e6 for r in data)
                               for k in ("sql_execute_ns","repository_conflict_ns","detect_ns",
                                         "datetime_normalize_ns","opencl_host_total_ns","runtime_ns",
                                         "runtime_lock_wait_ns","runtime_lock_hold_ns","array_prepare_ns",
                                         "read_enqueue_wait_ns","kernel_ns","server_ns")}})
(output/"raw.json").write_text(json.dumps(records,indent=2))
(output/"summary.json").write_text(json.dumps(groups,indent=2))
(output/"processes.json").write_text(json.dumps(processes,indent=2))
# A identificação ocorre fora das amostras e não aquece os processos medidos.
from app.appointments.opencl_conflicts import runtime_info
import importlib.metadata
with db_engine.connect() as db:
    version=db.scalar(text("SHOW server_version"))
(output/"versions.json").write_text(json.dumps({"python":platform.python_version(),"postgres":version,
      "packages":{p:importlib.metadata.version(p) for p in ("numpy","pyopencl","fastapi","sqlalchemy","uvicorn","httpx")},
      "opencl":runtime_info()},indent=2))
print(json.dumps({"status":"completed","samples":len(records),"warm":len([r for r in records if r["phase"]=="warm"]),
                  "processes":len(processes),"integrity_checks":"passed","http_auth_errors":0},indent=2))
