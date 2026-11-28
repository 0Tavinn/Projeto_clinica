"""Sondagem HTTP real, sem gravar nem imprimir tokens; só usa o seed fictício."""

import json
import urllib.error
import urllib.request


class SessionProbe:
    def __init__(self, base):
        self.base, self.results = base, []

    def request(self, label, method, path, expected, token=None, body=None, origin=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        if origin:
            headers.update(Origin=origin, **{"Access-Control-Request-Method": "POST",
                                           "Access-Control-Request-Headers": "authorization,content-type"})
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            response = urllib.request.urlopen(request, timeout=15)
        except urllib.error.HTTPError as error:
            response = error
        raw = response.read()
        self.results.append({"case": label, "status": response.status, "expected": expected})
        assert response.status == expected, (label, response.status, expected)
        if expected == 204:
            assert not raw
        if origin:
            assert response.headers.get("Access-Control-Allow-Origin") == origin
        return json.loads(raw) if raw and "json" in response.headers.get("Content-Type", "") else None

    def login(self, role):
        body = self.request("login_" + role, "POST", "/api/v1/auth/login", 200,
                            body={"email": role + ".demo@example.com", "password": "DemoLumina2026!"})
        assert body["expires_in"] == 1800
        return body["access_token"]

    def unlock(self, token):
        body = self.request("clinical_unlock", "POST", "/api/v1/auth/clinical-unlock", 200,
                            token, {"password": "ClinicaDemo2026!"})
        assert body["expires_in"] == 900
        return body["clinical_token"]

    def exercise(self, restart):
        self.request("health", "GET", "/health", 200)
        for origin in ["http://localhost:5173", "http://localhost:3000"]:
            for path in ["/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/clinical-lock"]:
                self.request("cors_" + path, "OPTIONS", path, 200, origin=origin)
        admin, access = self.login("admin"), self.login("dentista")
        self.request("create_reception_fixture", "POST", "/api/v1/users", 201, admin,
                     {"full_name": "Recepção Fictícia Sessão", "email": "recepcao.sessao@example.test",
                      "cpf": "99999999991", "role": "RECEPTIONIST", "password": "DemoRecepcao2026!"})
        reception = self.request("reception_login", "POST", "/api/v1/auth/login", 200,
                                 body={"email": "recepcao.sessao@example.test", "password": "DemoRecepcao2026!"})["access_token"]
        self.request("reception_cannot_manage_links", "GET", "/api/v1/access-links", 403, reception)
        self.request("reception_cannot_lock_clinical", "POST", "/api/v1/auth/clinical-lock", 403, reception)
        self.request("reception_logout", "POST", "/api/v1/auth/logout", 204, reception)
        self.request("reception_logout_effective", "GET", "/api/v1/auth/me", 401, reception)
        clinical = self.unlock(access)
        self.request("admin_links", "GET", "/api/v1/access-links", 200, admin)
        self.request("dentist_list", "GET", "/api/v1/clinical/patients", 200, clinical)
        self.request("token_kind_separation", "GET", "/api/v1/access-links", 401, clinical)
        self.request("clinical_lock", "POST", "/api/v1/auth/clinical-lock", 204, access)
        self.request("login_survives_clinical_lock", "GET", "/api/v1/auth/me", 200, access)
        self.request("old_clinical_token_revoked", "GET", "/api/v1/clinical/patients", 401, clinical)
        clinical = self.unlock(access)
        self.request("logout", "POST", "/api/v1/auth/logout", 204, access)
        self.request("old_login_revoked", "GET", "/api/v1/auth/me", 401, access)
        self.request("old_unlock_revoked", "GET", "/api/v1/clinical/patients", 401, clinical)
        # O token fica somente em memória durante o reinício da API de ensaio.
        restart()
        self.request("logout_persists_after_restart", "GET", "/api/v1/auth/me", 401, access)
        self.request("other_user_survives_restart", "GET", "/api/v1/access-links", 200, admin)
        fresh = self.login("dentista")
        self.request("new_login_after_logout", "GET", "/api/v1/auth/me", 200, fresh)
        clinical = self.unlock(fresh)
        self.request("clinical_after_new_login", "GET", "/api/v1/clinical/patients", 200, clinical)

        patients = self.request("admin_patient_selection", "GET", "/api/v1/patients", 200, admin)
        patient = next(row for row in patients if row["medical_record_number"] == "DEMO-003")
        dentists = self.request("admin_dentist_selection", "GET", "/api/v1/dentists", 200, admin)
        pair = {"patient_id": patient["id"], "dentist_id": dentists[0]["id"]}
        for action, status in [("GRANTED", 200), ("REVOKED", 200), ("REACTIVATED", 200)]:
            self.request("link_" + action, "POST", "/api/v1/admin/access", status, admin, {**pair, "action": action})
        self.request("logout_admin", "POST", "/api/v1/auth/logout", 204, admin)
        self.request("admin_list_rejects_revoked_session", "GET", "/api/v1/access-links", 401, admin)
        return self.results
