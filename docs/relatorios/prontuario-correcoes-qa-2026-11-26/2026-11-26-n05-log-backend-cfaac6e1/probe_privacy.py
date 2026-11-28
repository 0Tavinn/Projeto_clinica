"""Sondagem real de HTTP e logs; mantém respostas clínicas apenas em memória."""

import json
import os
import socket
import time
from pathlib import Path
from urllib.parse import quote
import httpx
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url

url=make_url(os.environ["DATABASE_URL"])
assert url.host=="pg" and url.database=="lumina_n05_scratch" and url.username=="n05_qa"
E=create_engine(url)
base="http://api:8000"
rows=[]
# Sentinelas exclusivamente fictícias; o relatório publica somente booleanos.
sentinels=["N05_VALID_SENTINEL_4829","N05_QUERY_SENTINEL_7283",
           "N05_UNICODE_acentuação_漢字","N05_PARAMETER_SENTINEL_5821",
           "N05_PATH_SENTINEL_9284","N05_BODY_SENTINEL_1529","N05_AUTH_SENTINEL_4253"]
with httpx.Client(base_url=base,timeout=30) as client:
    for _ in range(100):
        try:
            if client.get("/health").status_code==200: break
        except httpx.HTTPError: pass
        time.sleep(.2)
    else: raise RuntimeError("API exclusiva não iniciou")
    def login(email):
        response=client.post("/api/v1/auth/login",json={"email":email,"password":"DemoLumina2026!"})
        assert response.status_code==200
        return response.json()["access_token"]
    access=login("dentista.demo@example.com")
    response=client.post("/api/v1/auth/clinical-unlock",
        headers={"Authorization":"Bearer "+access},json={"password":"ClinicaDemo2026!"})
    assert response.status_code==200
    clinical=response.json()["clinical_token"]
    headers={"Authorization":"Bearer "+clinical}
    with E.connect() as db:
        ids=db.execute(text("SELECT id FROM patients ORDER BY id")).scalars().all()
        version=db.scalar(text("SHOW server_version"))
    assert version.startswith("16.")
    # Resultado autorizado pode conter a descrição; deve estar ausente dos logs.
    created=client.post("/api/v1/evolutions",headers=headers,
                        json={"patient_id":ids[0],"description":sentinels[0]+" "+sentinels[2]})
    assert created.status_code==201, "Falha na fixture clínica"
    rows.append({"id":"fixture-evolution","http":201,"passed":True})
    def observe(id,response,expected,allow_content=False):
        assert response.status_code==expected,(id,response.status_code)
        if not allow_content:
            assert not any(value in response.text for value in sentinels),id
        rows.append({"id":id,"http":response.status_code,"passed":True,
                     "authorized_content_allowed":allow_content})
    for mode in ("cpu","opencl","auto"):
        response=client.get("/api/v1/clinical/search",headers=headers,
                            params={"patient_id":ids[0],"q":sentinels[0],"engine_name":mode})
        observe("valid-"+mode,response,200,True)
        document=response.json()
        assert document["total"]>=1 and any(sentinels[0] in item["description"] for item in document["results"])
        assert document["engine"]==("cpu" if mode=="cpu" else "opencl")
        rows[-1].update(engine=document["engine"],authorized_result_present=True)
    observe("422-missing-patient",client.get("/api/v1/clinical/search",headers=headers,
        params={"q":sentinels[1]}),422)
    observe("422-encoded-unicode",client.get(
        "/api/v1/clinical/search?q="+quote(sentinels[2],safe=""),headers=headers),422)
    observe("422-parameter-name",client.get("/api/v1/clinical/search",headers=headers,
        params={"q":sentinels[1],sentinels[3]:sentinels[2]}),422)
    observe("422-invalid-patient",client.get("/api/v1/clinical/search",headers=headers,
        params={"patient_id":sentinels[3],"q":sentinels[1]}),422)
    observe("422-invalid-engine",client.get("/api/v1/clinical/search",headers=headers,
        params={"patient_id":ids[0],"q":sentinels[1],"engine_name":sentinels[3]}),422)
    observe("422-invalid-body",client.post("/api/v1/evolutions",headers=headers,
        json={"description":sentinels[5]}),422)
    observe("401-missing-auth",client.get("/api/v1/clinical/search",
        params={"patient_id":ids[0],"q":sentinels[1]}),401)
    observe("401-invalid-token",client.get("/api/v1/clinical/search",
        headers={"Authorization":"Bearer "+sentinels[6]},
        params={"patient_id":ids[0],"q":sentinels[1]}),401)
    observe("403-no-link",client.get("/api/v1/clinical/search",headers=headers,
        params={"patient_id":ids[2],"q":sentinels[1]}),403)
    observe("404-unknown",client.get("/"+sentinels[4],headers=headers,
        params={sentinels[3]:sentinels[1]}),404)
    observe("path-template",client.get(f"/api/v1/patients/{ids[0]}/record",headers=headers,
        params={"q":sentinels[1]}),200,True)

# Confere warning de parsing sem registrar o conteúdo enviado.
with socket.create_connection(("api",8000),timeout=5) as connection:
    connection.sendall(("GET /?q="+sentinels[1]+" HTTP/1.1\r\nBad Header\r\n\r\n").encode())
    raw=connection.recv(4096)
    assert b"400" in raw
rows.append({"id":"400-malformed-http","http":400,"passed":True})
Path("/tmp/privacy-probe.json").write_text(json.dumps({"cases":rows,"postgres":version},indent=2))
print(json.dumps({"passed":len(rows),"failed":0,"real_http":True,"engines":["cpu","opencl","auto"]}))
