# Vínculos de pacientes — entrega consolidada

Consolidado em **26/11/2026**, sob responsabilidade de Paulo Sérgio,
com implementação pelo agente de Backend, revisão do Tech Lead e QA independente.

## Referência versionada

Branch: `fix/prontuario-correcoes-qa`.
O guia inicial foi registrado em `67068ac969cb7b34396b5d94e4ee09a7001ef8b4`.
As novas rotas e seus guias estão no commit `00e67dc425a3390b9803a250d76fab00dd0c3535`.

Os **31 arquivos** de `lumina_odonto/` nesse commit correspondem à fonte
funcional e documental efetivamente ensaiada pelo Backend e pelo QA.
Manifesto canônico: `95fb2b8e2fd21f7a5a9e125fcbb7aaeb110e74d610eb150f3a4bb7f8d33bfcd7`.
Mapa: [manifesto-fonte-aprovada.json](manifesto-fonte-aprovada.json).

Os relatórios descrevem o estado real de suas execuções: HEAD de referência
67068ac mais alterações locais, antes destes commits. Não foram alterados
para simular testes sobre um commit que ainda não existia. A conferência de
blobs Git descrita abaixo vincula os mesmos bytes ao commit atual.

## Rotas e funcionamento

| Operação | Finalidade |
|---|---|
| GET `/api/v1/clinical/patients` | Lista mínima dos pacientes ativos vinculados ao próprio dentista; token clínico, pesquisa literal e paginação por cursor. |
| GET `/api/v1/clinical/patients/{patient_id}` | Identificação mínima autorizada para o cabeçalho do prontuário. |
| GET `/api/v1/access-links` | Mantém array/admin e filtros anteriores; acrescenta nomes e flags para gerir também alvos inativos. |

Concessão, revogação e reativação continuam em POST `/api/v1/admin/access`.
O schema, as mutações e o histórico de vínculos existentes foram reutilizados.
Não há migração nova ou alteração de regras clínicas nesta entrega.

O vínculo administrativo sem consulta aparece na lista. Prontuário vazio
aparece; registro legado sem prontuário pode ter `medical_record_id: null`.
As leituras não criam registros nem retornam CPF, contatos, notas ou rascunhos.
Os cinco campos mínimos e os exemplos estão no
[guia para Otávio](../../../lumina_odonto/FRONTEND.md) e no
[contrato de pacientes e vínculos](../../../lumina_odonto/docs/frontend/clinical-patients-and-links.md).

A lista usa `limit`, `after_id` e `q`, retornando `items`, `limit` e
`next_after_id`, sem total global. Uma revogação concorrente pode esvaziar
a página e ainda deixar cursor para continuar. Não se promete snapshot entre
páginas. A autorização é verificada novamente após esperar pelos bloqueios;
a fonte final do detalhe contém verificação antes e depois desses locks.

## Validação e evidências

| Executor | Resultado | Relatório |
|---|---|---|
| Backend | 32 testes e 66 verificações HTTP/SQL aprovados no ensaio final. | [Backend](2026-11-26-vinculos-backend-da04d024/relatorio.md) |
| QA independente | 58 verificações independentes, 32 testes distribuídos, 20 asserções transversais de logs e 1 comparação de contrato aprovados. | [QA](2026-11-26-vinculos-qa-3a6efdc8da/relatorio.md) |

Os grupos se sobrepõem. Não somá-los como cenários únicos nem incorporar as
74 sondagens históricas que não foram repetidas. O QA usou HTTP real da imagem
pelo CMD distribuído, PostgreSQL **16.16** descartável e OpenCL real em CPU.

Parecer do QA: **pronto com ressalvas para integrar estas novas rotas em
ambiente de teste**, sem defeito de produto reproduzido no recorte executado.
Navegador, implantação diária, upgrade/migração e aceite global não foram validados.

A tentativa de QA interrompida por importação do cliente foi preservada e
não contabilizada. O Backend também preservou as tentativas anteriores:
erro do auxiliar ao salvar resultados e falha de identificação das rotas
nos logs, corrigida antes da imagem final. A política passou a incluir os
caminhos públicos do OpenAPI; os logs não expuseram termos ou IDs nos casos
exercitados. Não se promete proteção de loggers/proxies externos não ensaiados.

O QA identificou uma divergência na descrição do número de chamadas de
autorização. A orientação intermediária do Tech Lead usou uma versão anterior
do método. A fonte final foi reconferida e o relatório do Backend reconciliado
para duas chamadas, antes e depois dos locks. A observação histórica foi
preservada. Foi somente correção documental, sem mudança funcional ou novo teste.

[Matriz independente](2026-11-26-vinculos-qa-3a6efdc8da/matriz.csv),
[resumo para Cassiano](2026-11-26-vinculos-qa-3a6efdc8da/resumo-cassiano.md) e
[reprodução](2026-11-26-vinculos-qa-3a6efdc8da/reproducao.md) acompanham os logs,
mapas de hashes e inventários nas subpastas. Os originais externos permanecem
preservados. Artefatos históricos podem conter caminhos absolutos do ambiente
ensaiado; adaptar somente a orquestração e criar saída nova ao repetir.

## Conferência dos bytes versionados

A partir da raiz do repositório:

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib, json, subprocess
root = Path.cwd()
manifest = json.loads((root / 'docs/relatorios/vinculos-pacientes-2026-11-26/manifesto-fonte-aprovada.json').read_text())
commit = '00e67dc425a3390b9803a250d76fab00dd0c3535'
for name, expected in manifest.items():
    blob = subprocess.check_output(['git', 'show', f'{commit}:lumina_odonto/{name}'], cwd=root)
    assert hashlib.sha256(blob).hexdigest() == expected, name
print(f'{len(manifest)} arquivos do commit correspondem à fonte testada.')
PY
```

Esta conferência foi executada na consolidação; não é nova execução funcional.
Os ambientes/pacotes originais e o banco diário permaneceram preservados.
Os recursos descartáveis dos ensaios foram removidos pelos respectivos agentes.
Não houve push, merge ou implantação na consolidação. O próximo passo é publicar
uma referência verificável e conectar o frontend em ambiente de teste identificado.
