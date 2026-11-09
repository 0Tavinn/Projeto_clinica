"""Inspeção HTTP do frontend/API de QA e leitura da implementação da Sprint 7."""

import json
import re
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
with httpx.Client(timeout=8, trust_env=False) as client:
    api = client.get("http://127.0.0.1:18128/openapi.json")
    html = client.get("http://127.0.0.1:18129/")
    asset = re.search(r'src="(/assets/[^\"]+\.js)"', html.text)
    bundle = client.get("http://127.0.0.1:18129" + asset.group(1)) if asset else None
    cors = client.options("http://127.0.0.1:18128/api/v1/auth/login", headers={
        "Origin": "http://localhost:18129", "Access-Control-Request-Method": "POST",
    })

source = (ROOT / "frontend/src/App.tsx").read_text()
api_source = (ROOT / "frontend/src/api.ts").read_text()
paths = list(api.json()["paths"]) if api.status_code == 200 else []
result = {
    "frontend_http": html.status_code,
    "frontend_title": "Lumina Odonto" in html.text,
    "bundle_http": bundle.status_code if bundle else None,
    "built_api_url_present": "http://localhost:18128/api/v1" in bundle.text if bundle else False,
    "cors_http": cors.status_code,
    "cors_allow_origin": cors.headers.get("access-control-allow-origin"),
    "openapi_http": api.status_code,
    "route_count": len(paths),
    "clinical_routes": [p for p in paths if "/appointments" in p or "/record" in p or "/evolution" in p],
    "report_routes": [p for p in paths if "report" in p.lower() or "relat" in p.lower()],
    "audit_routes": [p for p in paths if "audit" in p.lower() or "histor" in p.lower()],
    "dashboard_uses_appointment_aggregate": "function Dashboard" in source and "appointmentCount" in source[source.index("function Dashboard"):source.index("function Stat")],
    "report_view_present": "'reports'" in source or "'relatorios'" in source,
    "frontend_completion_sends_care_time": "body: JSON.stringify({ status, care_occurred_at" in api_source,
    "frontend_get_or_open": "getOrOpen: (patientId" in api_source,
    "frontend_csv_export_marker": "text/csv" in source or "text/csv" in api_source,
    "frontend_patient_search": "Pesquisar por nome, CPF ou telefone" in source,
}
(OUT / "feature-inspection.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(result, ensure_ascii=False))
