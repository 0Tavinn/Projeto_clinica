# Reprodução segura das sondagens QA

Este roteiro é para **outro banco descartável vazio** na mesma branch/commit. Execute em uma **cópia desta pasta de evidências** sob `docs/relatorios/qa/` para não sobrescrever os resultados de 31/10. Os scripts têm nomes, banco e portas específicos desta execução; se algum já existir, escolha outra identidade de ensaio e atualize os scripts copiados antes de executar. Nunca aponte para o banco da equipe.

1. Confirme `git rev-parse HEAD` igual a `2f7dbfe6d0d7a747f57dbeeede3a716938adc5fa`, ausência de mudanças funcionais locais, Docker/Compose disponíveis e portas `18128/18129` livres. A primeira configuração do Compose deve usar volume **vazio**. Não aplique `schema.sql` nem migrações em volume anterior.
2. Crie `/tmp/lumina_qa_20261031_2f7dbfe.env` com `POSTGRES_DB=lumina_qa_20261031_2f7dbfe_db`, `POSTGRES_USER=qa_clinic`, `POSTGRES_PASSWORD` e `SECRET_KEY` temporários gerados localmente, `CORS_ORIGINS=http://localhost:18129`, `VITE_API_URL=http://localhost:18128/api/v1`, `API_PORT=127.0.0.1:18128`, `FRONTEND_PORT=127.0.0.1:18129` e `LOGIN_RATE_LIMIT=100/minute`. Mantenha permissão `0600` e não publique o arquivo. Gere também uma senha fictícia de testes em `/tmp/lumina_qa_20261031_2f7dbfe.test_password`, igualmente protegida.
3. Crie `/tmp/lumina_qa_20261031_2f7dbfe.override.yml`:

   ```yaml
   volumes:
     postgres_data:
       name: lumina_qa_20261031_2f7dbfe_pg16_data
   networks:
     app_network:
       name: lumina_qa_20261031_2f7dbfe_network
   ```

4. Confira `docker volume inspect` e `docker network inspect` para garantir que esses nomes ainda **não** existem. Inspecione `docker compose ... config` antes de iniciar: volume, rede, portas, URL da API no bundle e caminho do schema devem ser os exclusivos esperados. A linha de comando Compose usada foi:

   ```bash
   docker compose -p lumina_qa_20261031_2f7dbfe \
     --env-file /tmp/lumina_qa_20261031_2f7dbfe.env \
     -f docker-compose.yml \
     -f /tmp/lumina_qa_20261031_2f7dbfe.override.yml \
     up -d --build --force-recreate
   ```

5. No banco exclusivo já inicializado pelo entrypoint, envie `qa_fixture.py` por stdin para `docker exec -i -e QA_TEST_PASSWORD=... lumina_qa_20261031_2f7dbfe-api-1 python -` e guarde a saída em `fixture-ids.json` da **cópia**. O script recusa nome de banco inesperado. Com `QA_TEST_PASSWORD` no ambiente do processo local, execute `qa_http_probe.py`, `qa_concurrency.py`, `qa_additional.py`, `qa_persistence.py` e `qa_feature_scan.py` nessa ordem. Para a prova adicional da clínica B, execute `qa_second_clinic_fixture.py` no contêiner API com `QA_CLINIC_B_ID` obtido do fixture, depois `qa_second_clinic_probe.py`. Os scripts de HTTP recusam URL de API diferente da exclusiva; não registram senha ou token.
6. O ensaio SQL independente é `bash backend/database/checks/run_20261025_clinical_access_pg16.sh`; a suíte clínica PostgreSQL é `cd backend && bash tests/run_clinical_pg16.sh`; a disputa de duas finalizações é `bash docs/relatorios/qa/2026-10-31-2f7dbfe/qa_two_finalizations_pg16.sh`. Cada runner cria e remove seu próprio PostgreSQL 16 temporário. O último caminho absoluto no script de finalizações deve ser ajustado se a pasta de evidências for copiada para outro nome.
7. Ao terminar, use `docker compose ... down` **sem `-v`**, confira que os três contêineres são os seus e remova somente o volume, a rede eventualmente residual e as duas imagens criadas sob o prefixo QA. Exclua os arquivos temporários com senhas. Nunca remova os volumes `lumina_execucao_20261029_postgres_data` ou `lumina_s07_docker_review_20261023`.

Os logs e JSON deste relatório mostram as respostas observadas na execução original. A pasta de cópia deve ter seus próprios arquivos de evidência, hora, commit e IDs de imagens; não reutilize os resultados antigos como prova de uma nova versão.
