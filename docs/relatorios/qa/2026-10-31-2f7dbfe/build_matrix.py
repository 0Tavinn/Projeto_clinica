"""Consolida evidências desta execução sem contar testes repetidos duas vezes."""

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent
rows = []


def row(case, requirement, layer, pre, steps, expected, observed, result, evidence, defect="", impact="", next_action=""):
    rows.append({
        "id": case, "requisito": requirement, "camada": layer,
        "pre_condicoes_dados": pre, "passos_comando": steps,
        "esperado": expected, "obtido": observed, "situacao": result,
        "evidencia": evidence, "defeito": defect, "impacto": impact,
        "proxima_acao": next_action,
    })


for name, layer in (("pytest-sqlite.xml", "HTTP/serviço SQLite"), ("pytest-pg16.xml", "HTTP/PostgreSQL 16")):
    root = ET.parse(ROOT / name).getroot()
    testsuite = root if root.tag == "testsuite" else root.find("testsuite")
    for item in testsuite.findall("testcase"):
        if item.find("skipped") is not None:
            # Os cinco pulados em SQLite são precisamente os cinco executados
            # no PostgreSQL; o XML SQLite preserva a evidência desse skip.
            continue
        test_id = item.attrib["classname"] + "." + item.attrib["name"]
        failed = item.find("failure") is not None or item.find("error") is not None
        row(test_id, "contratos automatizados versionados", layer,
            "SQLite em memória" if "sqlite" in name else "PostgreSQL 16 descartável do script versionado",
            "pytest; consultar XML e log do mesmo nome", "asserções do teste passam",
            "passou" if not failed else "falhou", "reprovado" if failed else "aprovado", name)


for filename, evidence in (
    ("http-results.json", "http-results.json; http-probe.log; qa_http_probe.py"),
    ("concurrency-results.json", "concurrency-results.json; concurrency-probe.log; qa_concurrency.py"),
    ("additional-results.json", "additional-results.json; additional-probe.log; qa_additional.py"),
    ("second-clinic-results.json", "second-clinic-results.json; second-clinic-probe.log; qa_second_clinic_probe.py"),
):
    data = json.loads((ROOT / filename).read_text())
    cases = data["cases"] if isinstance(data, dict) else data
    for item in cases:
        defect = {
            "AUTH-configured-limit": "QA-04",
            "PG-loss-access-edit": "QA-01",
            "PG-loss-access-finalize": "QA-01",
            "PG-two-edits": "QA-02",
            "SPRINT-audit-events": "QA-05",
        }.get(item["id"], "")
        row(item["id"], item["requirement"], item["layer"],
            "Banco QA exclusivo; duas clínicas, sete contas e consultas fictícias controladas",
            f"Executar {evidence.split('; ')[-1]}; localizar ID {item['id']}",
            item["expected"], str(item["observed"]), item["result"], evidence,
            defect, item.get("note", ""), "Corrigir e repetir o cenário" if defect else "")


persist = json.loads((ROOT / "persistence-result.json").read_text())
row(persist["id"], persist["requirement"], persist["layer"],
    "Volume QA exclusivo com prontuário e evolução finalizada fictícios",
    "Executar qa_persistence.py; reiniciar apenas API e PostgreSQL QA",
    persist["expected"], json.dumps(persist["observed"], ensure_ascii=False),
    persist["result"], "persistence-result.json; persistence-probe.log; qa_persistence.py")


for case, expected, observed, evidence in (
    ("SQL-new-schema", "esquema novo íntegro", "PASSOU: new", "sql-pg16.log"),
    ("SQL-upgrade-25", "migração incremental íntegra", "PASSOU: upgrade", "sql-pg16.log"),
    ("SQL-base-upgrade", "cadeia de migrações íntegra", "PASSOU: base", "sql-pg16.log"),
    ("SQL-reapply-rejected", "migração não reaplicável", "PASSOU: reaplicação da migração recusada", "sql-pg16.log"),
    ("SQL-catalog-equivalent", "mesmo catálogo nas três rotas", "PASSOU: catálogo da concessão equivalente", "sql-pg16.log"),
    ("SQL-one-grant-concurrent", "uma concessão sob disputa", "PASSOU: concorrência, uma concessão por origem", "sql-pg16.log"),
):
    row(case, "RN-031/DBA", "SQL/PostgreSQL 16", "Três bancos temporários do script; somente dados fictícios",
        "bash backend/database/checks/run_20261025_clinical_access_pg16.sh",
        expected, observed, "aprovado", evidence)

row("PG-two-finalizations", "RF-024-CA10", "HTTP/PostgreSQL 16",
    "Evolução DRAFT fictícia com confirmação real da Agenda; dois clientes em conexões independentes",
    "bash docs/relatorios/qa/2026-10-31-2f7dbfe/qa_two_finalizations_pg16.sh",
    "uma finalização 200, outra 422; uma finalizada íntegra",
    "HTTP [200, 422]; estado FINALIZED; descrição original preservada",
    "aprovado", "two-finalizations-pg16.log; qa_two_finalizations_pg16.py")


features = json.loads((ROOT / "feature-inspection.json").read_text())
for case, requirement, layer, expected, observed, passed in (
    ("INFRA-health-api", "Docker Sprint 7", "HTTP", "API 200 e banco comunicante", "health 200; SELECT 1=1", True),
    ("INFRA-openapi", "contrato API", "HTTP", "rotas /api/v1 clínicas", f"{len(features['clinical_routes'])} caminhos clínicos", len(features["clinical_routes"]) == 9),
    ("INFRA-frontend-serving", "Docker Sprint 7", "HTTP", "HTML e bundle 200", f"HTML {features['frontend_http']}, bundle {features['bundle_http']}", features["frontend_http"] == 200 and features["bundle_http"] == 200),
    ("INFRA-frontend-api-url", "Docker Sprint 7", "HTTP", "bundle aponta à API QA", str(features["built_api_url_present"]), features["built_api_url_present"]),
    ("INFRA-cors", "Docker Sprint 7", "HTTP", "origem QA autorizada", str(features["cors_allow_origin"]), features["cors_allow_origin"] == "http://localhost:18129"),
    ("SPRINT-dashboard-appointments", "Sprint 7 dashboard", "código", "indicadores de consultas por situação/período", "dashboard só usa pacientes, perfil e equipe", features["dashboard_uses_appointment_aggregate"]),
    ("SPRINT-report-view", "Sprint 7 relatório", "código/API", "relatório de agendamentos", f"views/rotas ausentes: {not features['report_view_present']}/{not features['report_routes']}", bool(features["report_view_present"] or features["report_routes"])),
    ("FRONT-completion-payload", "RN-031", "código/HTTP", "enviar care_occurred_at com fuso", "frontend envia só status; API devolve 422", features["frontend_completion_sends_care_time"]),
):
    defect = {"SPRINT-dashboard-appointments": "QA-06", "SPRINT-report-view": "QA-07", "FRONT-completion-payload": "QA-03"}.get(case, "")
    row(case, requirement, layer, "Imagens QA reconstruídas da branch; bundle real servido",
        "qa_feature_scan.py; ler frontend/src/App.tsx e frontend/src/api.ts",
        expected, observed, "aprovado" if passed else "reprovado",
        "feature-inspection.json; feature-scan.log", defect,
        "Critério da Sprint 7 não atendido" if defect else "", "Implementar e repetir na interface" if defect else "")


row("PG-containers-recreated", "Docker Sprint 7", "PostgreSQL/HTTP",
    "Volume nomeado QA preservado", "docker compose up -d --force-recreate --no-build; comparar antes/depois e GET",
    "mesmas contagens e histórico após recriação", "contagens iguais; GET record/history 200 e mesmos IDs",
    "aprovado", "recreate-before.json; recreate-after.json; recreate-http.log")
row("SPRINT-export-csv", "Sprint 7 exportação condicional", "código/decisão",
    "Decisão de adoção ou justificativa não localizada", "Inspeção do código e planejamento",
    "CSV com filtros/permissões se adotado, ou justificativa no PDF", "não há implementação CSV no frontend nem rota de relatório",
    "bloqueado", "feature-inspection.json; docs/sprint/sprint-07.md",
    "", "Aceite depende da decisão documentada", "Paulo/equipe definirem aplicabilidade e Cassiano registrar no PDF")
for case in ("UI-flow-login-record-history", "UI-permissions-errors", "UI-search-filters"):
    row(case, "Sprint 7/interface", "interface", "Navegador automatizável indisponível nesta sessão",
        "Fluxo manual pelo navegador QA", "captura visual e comportamento funcional",
        "não observado", "não executado", "ver relatório: limites",
        "", "Build e HTML não comprovam interação visual", "Executar em navegador com capturas")


csv_path = ROOT / "matriz-testes.csv"
with csv_path.open("w", newline="", encoding="utf-8") as output:
    writer = csv.DictWriter(output, fieldnames=list(rows[0]), delimiter=";")
    writer.writeheader()
    writer.writerows(rows)

from collections import Counter, defaultdict
counts = Counter(item["situacao"] for item in rows)
by_layer = defaultdict(Counter)
for item in rows:
    by_layer[item["camada"]][item["situacao"]] += 1
print("rows", len(rows), "status", dict(counts))
print("layers", {layer: dict(count) for layer, count in by_layer.items()})
