# Reprodução focada e segura — N05-LOG

## Escopo e fonte

Candidata exclusiva:/home/paulinho/Work/lumina_odonto_correcao_N05_20261126.
Manifesto canônico: e3b28488163b174758f7e3782dbe916b0cc1cf8120cadf5a3cd5da79200e2825.
O pacote não é Git. Não substituir ou alterar arquivos para fazer um teste passar.

Execução independente original:26/11/2026. Os comandos abaixo descrevem o roteiro e uma futura repetição; não acrescem testes aos totais já registrados.

Arquivos de reprodução:
- run_focused.py: build exato, PostgreSQL16 novo, API com CMD original, clienteHTTP, testes, logs e limpeza.
- probe_independent.py: sentinelas fictícias e 25 objetivos iniciais, com retorno do resultado resumido.
- method_complement.py: TRACE reconhecido pelo parser, 405 eOTHER, em outra API original sem banco.
- candidate-before.json eoriginal-before.json: mapas de identidade usados pelo runner.

Não executar os runners diretamente na pasta histórica, pois eles escrevem artefatos junto ao próprio script.
Não executar docker compose up do pacote: publica5432/8000. O runner não o utiliza.
Não instalar dependências no Python global WSL; Python global usa apenas biblioteca padrão para orquestrarDocker.

## Conferência e execução em pasta nova

Conferir os 22 hashes antes dobuild. Digest canônico:

~~~python
hashlib.sha256(
    json.dumps(file_map, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
~~~

Receita preparada para repetir em outra pasta exclusiva, sem sobrescrever a evidência existente:

~~~bash
export QA_TEMPLATE=/home/paulinho/Work/lumina-qa-evidence/2026-11-26-n05-log-qa-4c930a5405
export QA_OUTPUT="$(mktemp -d /home/paulinho/Work/lumina-qa-evidence/repro-n05-log-XXXXXX)"

python3 - <<'PY'
from pathlib import Path
import os,json,hashlib,secrets,shutil
src=Path("/home/paulinho/Work/lumina_odonto_correcao_N05_20261126")
old=Path("/home/paulinho/Work/lumina_odonto_corrigido_QA/lumina_odonto_atualizado")
template=Path(os.environ["QA_TEMPLATE"])
target=Path(os.environ["QA_OUTPUT"])
def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}
expected=json.loads((template/"candidate-before.json").read_text())
assert hashes(src)==expected
assert hashlib.sha256(json.dumps(expected,sort_keys=True,separators=(",",":")).encode()).hexdigest()=="e3b28488163b174758f7e3782dbe916b0cc1cf8120cadf5a3cd5da79200e2825"
for name in ["run_focused.py","probe_independent.py","method_complement.py"]:
    shutil.copyfile(template/name,target/name)
(target/"candidate-before.json").write_text(json.dumps(expected,indent=2))
(target/"original-before.json").write_text(json.dumps(hashes(old),indent=2))
(target/"resource-prefix.txt").write_text("lumina-n05-independent-"+secrets.token_hex(5))
print("Pasta exclusiva:",target)
PY

python3 "$QA_OUTPUT/run_focused.py"
python3 "$QA_OUTPUT/method_complement.py"
~~~

Conferir resultados e códigos individuais, não apenas a saída do runner. case() pode registrar bloqueado/reprovado sem encerrar o processo. Umtimeout, exceção ou ausência de saída não é aprovação.

O runner principal não modifica CMD, loggers ou configurações da aplicação. Dockerfile e fontes são os recebidos. Os filtros vêm da candidata. O banco novo recebe schema e seed recebidos; credenciais são efêmeras. Nenhuma porta é publicada. A limpeza verifica rótulo **e** identidade dos recursos. Não usar prune, nem down-v, serviços diários oubanco existente.

O script de sondagem preserva a expectativa inicial405 para um método arbitrário. Em25 objetivos iniciais foram 24 aprovados e 1 falha de expectativa: o parser devolveu400. **Essa tentativa deve continuar visível em qualquer repetição**, não ser reclassificada silenciosamente como defeito ou aprovação. O complemento TRACE testa de fato o caminho 405/OTHER. Usar http-results-final.json eprivacy-log-check-final.json como referência de consolidação, não sobrescrever as capturas iniciais para fazê-las parecer diferentes.

## Provas importantes

### N05 original

Dentista fictício autenticado, token clínico válido:
GET /api/v1/clinical/search?q=<sentinela>, sem patient_id.
Esperado422 útil, sem a entrada no corpo nem no stdout/stderr.
No pacote antigo, o log continha o termo; nesta candidata, os streams reais não contiveram as sentinelas.

### Codificação e headers

As sondagens enviam termos Unicode, percent-encoded, double-encoded, nomes de parâmetros arbitrários, sentinelas em corpo e headers, token válido e inválido. O coletor verifica as formas originais e até três níveis de unquote em memória. Respostas de erro são verificadas no corpo; sentinelas de headers e tokens também são procuradas nos logs. Não houve auditoria completa de headers de resposta em todos os casos.

### Erro500 real

O script cria função/gatilho temporário em clinical_evolutions **somente no PostgreSQL QA**. A função lança uma exceção com NEW.description fictícia. Requisição válida de criação precisa retornar500 sem eco, logar server_error sem traceback e deixar a contagem de evoluções intacta. Função/gatilho removidos emfinally.
Não executar esse SQL em banco da equipe. Não interpretar esse500 deliberado como defeito de negócio.

### Streams e diagnóstico

docker logs é capturado com stdout/stderr separados em memória. Nenhum log clínico bruto é gravado no host. Em caso de entrada sensível, a linha de distribuição é omitida e identificada por digest; o booleano da falha é preservado.
Extratos reais: api-stdout-sanitized.log, api-stderr-sanitized.log, method-api-sanitized.log.
A redução de tracebacks é parte da política recebida; não ativar logs clínicos brutos para recuperar diagnóstico.

### MétodosHTTP

- Método inventado: F22 inicial recebeu 400 eevento invalid_http_request; não atingiu o roteamento/caminho OTHER.
- TRACE: parser aceitou, aplicação respondeu405, access log gerou OTHER /health.
- HTTP/1.0/1.1: requisições reais preservaram aversão noaccess log.
O complemento não usa banco porque o405 ocorre antes das dependências SQL; não é prova adicional de PostgreSQL.

## Leitura e limpeza

- relatorio.md: parecer ealcance.
- matriz.csv:75 linhas em grupos distintos, sem soma inflada.
- tentativas.csv: problemas do auxiliar/expectativas preservados.
- tests.xml/tests.log:26 testes recebidos, separados 18+8.
- openapi-comparison.json: igualdade com baselineQA identificado.
- cleanup.json emethod-cleanup.json: recursos exclusivos removidos.
- preservation.json/preservation-final.json: identidade, originais, Git eambientes preservados.

Na execução original, o total criado eremovido foi 6 contêineres, 1 volume, 2 redes e 2 imagens/tags próprios.
Não há necessidade de reiniciar ou remover qualquer serviço existente após esta entrega.
Se uma futura repetição for interrompida, consultar resources.json e verificar rótulo/ID antes de qualquer limpeza manual; não ampliar a remoção para outros nomes.
