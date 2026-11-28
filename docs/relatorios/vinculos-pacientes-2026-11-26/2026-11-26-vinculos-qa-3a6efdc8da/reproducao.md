# Reprodução — pacientes clínicos e vínculos

Fonte exclusiva: /home/paulinho/Work/Projeto_clinica/lumina_odonto.
Branch: fix/prontuario-correcoes-qa.
HEAD base: 67068ac969cb7b34396b5d94e4ee09a7001ef8b4.
Manifesto local: 95fb2b8e2fd21f7a5a9e125fcbb7aaeb110e74d610eb150f3a4bb7f8d33bfcd7.

## Repetir sem sobrescrever esta evidência

O runner usa a pasta do próprio script para resultados. Copiar auxiliares e mapas para NOVA pasta, gerar prefixo exclusivo e conferir branch/HEAD/hashes. Não executar diretamente nesta pasta histórica. Se a versão divergir, parar e esclarecer; não alterar branch, arquivos ou índice para forçar correspondência.

A receita a seguir foi preparada após o ensaio; não acrescenta nova execução aos resultados.

~~~bash
export QA_TEMPLATE=/home/paulinho/Work/lumina-qa-evidence/2026-11-26-vinculos-qa-3a6efdc8da
export QA_OUTPUT="$(mktemp -d /home/paulinho/Work/lumina-qa-evidence/repro-vinculos-qa-XXXXXX)"

python3 - <<'PY'
from pathlib import Path
import os,json,hashlib,secrets,shutil,subprocess
s=Path("/home/paulinho/Work/Projeto_clinica/lumina_odonto")
r=s.parent
template=Path(os.environ["QA_TEMPLATE"])
target=Path(os.environ["QA_OUTPUT"])
def git(*args):
    return subprocess.check_output(["git","-C",str(r),*args],text=True).strip()
assert git("branch","--show-current")=="fix/prontuario-correcoes-qa"
assert git("rev-parse","HEAD")=="67068ac969cb7b34396b5d94e4ee09a7001ef8b4"
assert not git("diff","--cached","--raw")
actual={str(p.relative_to(s)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in s.rglob("*") if p.is_file()}
expected=json.loads((template/"source-before.json").read_text())
assert actual==expected
assert hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(",",":")).encode()).hexdigest()=="95fb2b8e2fd21f7a5a9e125fcbb7aaeb110e74d610eb150f3a4bb7f8d33bfcd7"
for name in ["run_links.py","probe_links.py","source-before.json","original-before.json"]:
    shutil.copyfile(template/name,target/name)
(target/"resource-prefix.txt").write_text("lumina-links-qa-"+secrets.token_hex(6))
print("Pasta exclusiva:",target)
PY

python3 "$QA_OUTPUT/run_links.py"
~~~

Requer Docker disponível no WSL e os caminhos de baseline referenciados no runner. Python global usa somente biblioteca padrão para orquestrar; dependências funcionais ficam na imagem. Não instalar pacotes no Python WSL global.

## O que o runner efetivamente fez em 26/11

1. Inventariou Git, fonte, pacotes protegidos e serviços existentes.
2. Conferiu fonte31, branch/HEAD e índice vazio.
3. Construiu o Dockerfile original, com label de propriedade e imagem própria.
4. Criou rede, volume e PostgreSQL 16 novos, sem portas publicadas; aplicou schema.sql e seed_demo.sql recebidos somente nesse banco vazio.
5. Iniciou a API sem argumento posterior à imagem: CMD original distribuído.
6. Iniciou cliente separado com PYTHONPATH=/app:/qa. Esse PYTHONPATH só permite o auxiliar importar as funções de produção; não muda a configuração da API.
7. Executou probe_links.py por HTTP real e conexões SQL independentes.
8. Comparou OpenAPI servido com a referência N05QA identificada.
9. Executou 32 testes recebidos, com network none, guardando JUnit.
10. Conferiu stdout/stderr em memória e salvou somente extratos sanitizados e booleanos.
11. Removeu apenas recursos próprios por label e identidade; removeu segredo efêmero; conferiu preservação.

O Compose recebido publica 5432/8000; não executá-lo diretamente. Não usar Compose diário, portas 18088/18089/55438, volume lumina_pr18_tarcisio_postgres_data ou banco da equipe. Não usar prune ou down-v.

## Comandos centrais observados

~~~text
docker build --label lumina.links.independent=<prefixo> -t <prefixo>:source <fonte>
docker run ... <prefixo>:source
docker exec <prefixo>-driver python /qa/probe_links.py
python -m pytest -v -ra --junitxml=/tmp/links-tests.xml --disable-warnings --tb=short
docker logs <prefixo>-api
~~~

As chamadas completas e seus argumentos de isolamento estão em run_links.py, sem segredo fixo. Conferir cada linhaQA_CASE e arquivos de resultado: um runner terminar não garante aprovação de todos os casos. Timeouts/ausência de saída/exceções de auxiliar não contam como aprovados.

## Como reproduzir a concorrência

No probe, C01-revocation-list/detail e C01-session-loss-list/detail:

- A conexão controladora segura o paciente em FOR UPDATE.
- Outra conexão envia a leitura porHTTP.
- waiters() consulta pg_stat_activity até demonstrar Lock emconsulta FOR SHARE.
- Revogação usa m.change_link de produção na mesma transação controladora, com commit antes de liberar. A prova de sessão usa outra conexão que confirma session_version antes da liberação.
- Conferir estado REVOKED e lista vazia/cursor útil ou detalhe 403. Para perda de sessão, conferir 401 sem identificação.
- No caso de lista, seguir o cursor e verificar o paciente remanescente.
- Os IDs/PID/eventos são salvos; nenhum conteúdo clínico real.

Não substituir o sinal de bloqueio por sleep. Não descrever a mutação de conexão SQL como duas chamadas HTTP simultâneas. Não generalizar para recolher bytes já enviados.

## Tentativa preservada

attempt-1/ parou por falta de PYTHONPATH antes de qualquer sondagem HTTP. A aplicação não foi alterada. A guarda contra token vazio em noecho também foi ajustada antes de ser exercitada.
A rodada funcional foi a segunda: 58 verificações aprovadas e 32 testes aprovados. Não somar a primeira tentativa. Não confundir os indicadores falsos por ausência de requests na primeira tentativa com defeito do produto.

## Evidências e limites

Matriz completa:matriz.csv. Resultados:http-results.json, privacy-log-check.json, tests.xml, openapi-comparison.json.
Logs:api-stdout-sanitized.log eapi-stderr-sanitized.log.
Identidade:source-before.json, source-after.json, identity.json, local-complete.patch.
Preservação/limpeza:preservation.json, cleanup.json e correspondentes em attempt-1/.
Não há navegador, PDF, implantação diária, migração ou repetição da matriz antiga 74.
