# Agenda OpenCL — relatório Backend/DBA — 25/11/2026

## Versão e preservação do stage

Checkout exclusivo: `/home/paulinho/Work/Projeto_clinica_clinical_2fa`.
Branch: `feat/paralelismo-agendamento`.
HEAD: `f8f10c54a4a702b7d4feccbf5aeb98578db65909` (base PR18).
Implementação e evidências desta tarefa estão no working tree.

Os 17 caminhos que já estavam no stage conservam os mesmos blobs, modos e
nomes. `index-before.txt` e `index-after.txt` são idênticos.
O SHA-256 do diff staged bruto antes/depois é
`41f728d17e0dcc8729b81db0f5abcf7ab900e8fd8249fa65dff173a07e8a4932`.
Não houve stage, commit, stash, reset, push, merge ou criação de PR.

## Implementação

Um work-item compara um intervalo existente ao solicitado usando
`existing_start < requested_end && requested_start < existing_end`.
Flags individuais são reduzidas no host. UTC e microssegundos int64
preservam limites exatos e adjacência. Buffers possuem no máximo o tamanho
de lote configurado, até 65536 intervalos; todos os lotes necessários são
processados. Fim do intervalo segue o timedelta do cálculo existente.

O repositório mantém clínica, dentista, situações excluídas e excluding_id.
O cursor é fechado no finally, inclusive quando o conflito encerra a leitura.
O service, advisory lock, transações, tratamento 23P01 e GiST foram preservados.
Não há migração, alteração de RN/RF ou de módulos clínicos.

OpenCL CPU é inicializado sob demanda. Contexto/programa ficam em cache,
mas fila, kernel e buffers são locais a cada chamada. Falhas de biblioteca,
plataforma, dispositivo, compilação ou execução usam a mesma referência
sequencial, inclusive para o lote que falhou. Resultado interno registra
`opencl`, `sequential` ou `mixed`; não integra o contrato HTTP.
Logs técnicos registram somente a classe do erro.

## Arquivos da entrega

Modificados no working tree:

- `backend/app/appointments/repository.py`: integração e fechamento do cursor.
- `backend/app/core/config.py`: motor auto/sequential e tamanho de lote validado.
- `backend/pyproject.toml`: NumPy/PyOpenCL e inclusão do kernel no pacote.
- `backend/Dockerfile`: PoCL/ICD CPU.
- `compose.yml`: repasse de configurações do comparador.
- `.env.example`: opções públicas de configuração.

Novos:

- `backend/app/appointments/conflict_detection.py`: normalização, referência e fallback.
- `backend/app/appointments/opencl_conflicts.py`: runtime CPU e execução por chamada.
- `backend/app/appointments/kernels/check_overlap.cl`: comparação paralela.
- `backend/scripts/benchmark_conflicts.py`: medição educativa.
- `backend/tests/test_opencl_conflicts.py`: bordas, lotes, falhas e threads.
- `backend/tests/test_opencl_repository.py`: filtros e exclusão do próprio ID.
- `backend/tests/test_opencl_pg.py`: corrida HTTP e autoridade GiST.
- `backend/tests/opencl-qa.Dockerfile`: dependências de testes na imagem exclusiva.
- `backend/tests/run_opencl_qa.sh`: ensaio reproduzível e limpeza por propriedade.
- `docs/paralelismo-agendamento.md`: arquitetura, configuração e uso.
- Esta pasta e logs das duas tentativas anteriores, mantidos para transparência.

As três alterações em arquivos compartilhados de infraestrutura existem apenas
no working tree; o stage DBA continua com os conteúdos originais.
Os comentários novos explicam em português UTC, limites, buffers, threads,
fallback, cursor e transações. Nomes de código permanecem em inglês.
`file-hashes.txt` identifica os 16 arquivos de implementação/guia ensaiados.

## Ambiente e execução comprovada

Ubuntu WSL orquestrou imagens Docker exclusivas, sem instalar pacotes no host
ou no venv existente. Imagem da API derivada de Python 3.12 slim/Debian trixie.
PoCL 6.0+debian, OpenCL 3.0, plataforma Portable Computing Language,
dispositivo CPU `13th Gen Intel Core i5-13420H`, NumPy 2.2.6,
PyOpenCL 2025.2.7. O kernel instalado no pacote foi compilado/executado,
com profiling e afirmação de motor OpenCL, sem fallback nos testes reais.

As versões fixadas possuem metadados e distribuições compatíveis com Python
3.11 e 3.12 no PyPI. A execução real desta tarefa foi em Python 3.12.
Python 3.11 não foi executado.
Fontes: https://pypi.org/project/pyopencl/2025.2.7/
e https://pypi.org/project/numpy/2.2.6/.

Comando executado a partir da raiz:

```bash
bash backend/tests/run_opencl_qa.sh
```

O runner fez build das imagens próprias, criou rede, volume e PostgreSQL
16.15 com nomes aleatórios/rótulo exclusivo e aplicou somente ali o schema
PR18. Não publicou portas. A API foi exercitada via TestClient, com sessões
SQL independentes por requisição. Nenhum Uvicorn de produção foi substituído.

### Resultados finais

- `targeted.log`: **65 aprovados**, 9 warnings, 10,59 s.
  Inclui os 14 testes existentes da Agenda, testes de filtros, OpenCL CPU real,
  precisão temporal, fusos, passagem da meia-noite, adjacência, lista vazia,
  conflito no último lote, falhas e 64 chamadas concorrentes com 8 threads.
- `postgres-version.txt`: **16.15**.
- `test_http_race_and_gist_authority`, parte dos 65: duas recepcionistas com
  pacientes diferentes e mesmo intervalo/dentista aguardam o advisory lock.
  pg_stat_activity confirma duas esperas reais. Após liberação, respostas
  **201/409**, envelope APPOINTMENT_TIME_CONFLICT e uma linha persistida,
  com patient_id do vencedor. Contornar has_conflict apenas na sondagem
  continua produzindo **409** pela exclusão GiST, sem segunda linha.
  A reserva adjacente posterior recebe **201** e deixa duas linhas,
  demonstrando também recuperação após rollback.
- `full-suite.log`: **97 aprovados, 1 pulado**, 10 warnings, 19,98 s.
  A única execução da suíte completa ocorreu após finalizar o código.
  O teste PostgreSQL é pulado nessa execução sem URL, pois já foi exercitado
  no ensaio dirigido com destino exclusivo.
- `http-contract-diff.txt` vazio: rotas, schemas e frontend/src idênticos ao HEAD.
- `openapi-check.txt`: OpenAPI com **18 paths**, hash canônico
  `b959aa6f36ddcd38c350eac94d34ba3a51fa177f8fb3b0ff1f1084bd2290dba3`,
  igual ao baseline PR18 obtido pelo Tech Lead por GET em 25/11.
- `git diff --check` e `bash -n backend/tests/run_opencl_qa.sh` passaram.

A exclusão GiST e a corrida foram exercitadas em PostgreSQL real. Os testes
de edição, cancelamento e reagendamento existentes integram a regressão
SQLite; esta tarefa não afirma ter revalidado todos esses fluxos em PostgreSQL.
Warnings são de dependências/deprecações existentes, sem falha de teste.

### Tentativas anteriores

1. `opencl-1795632915_6782`: o build concluiu, mas uma revisão do runner
   durante a execução causou erro de leitura/sintaxe. Não houve teste aprovado
   nessa tentativa. O recurso de imagem exclusivo foi removido.
2. `opencl-1795633113_7ecc7819-fc4`: 65 testes dirigidos passaram, mas a
   verificação de compatibilidade incluiu indevidamente os Dockerfiles de
   frontend já preparados pela DBA. O runner parou antes do benchmark e da
   suíte completa. A seleção foi corrigida para frontend/src.
3. A repetição final nesta pasta terminou com código de saída zero.
   As duas tentativas anteriores não contam como suítes completas aprovadas.

## Medição educativa

`benchmark.json` registra cinco repetições, medianas e lote 4096.
Inicialização conjunta de imports, contexto e build: **1.092,4 ms**.
O cache do driver pode existir; essa medida não isola o compilador.
Cada chamada mede preparação de arrays, transferências, execução e redução,
além do kernel por profiling. Exclui banco, ORM, HTTP, rede e interface.

| Intervalos | Sequencial total (ms) | OpenCL total (ms) | Kernel (ms) |
|---|---:|---:|---:|
| 32 | 0,0060 | 1,2720 | 0,1070 |
| 4096 | 0,2327 | 2,3043 | 0,0483 |
| 65536 | 6,5457 | 44,6566 | 1,0732 |

OpenCL foi mais lento no tempo completo em todos esses tamanhos. A entrega
demonstra paralelismo real e equivalência, sem prometer ganho da aplicação.
Lista vazia não lança kernel.

## Recursos e repasse

`cleanup.txt` vazio comprova a ausência dos recursos temporários finais.
`containers-before.txt` e `containers-after.txt` mostram os mesmos três
contêineres lumina_pr18_tarcisio saudáveis. Não foi executado comando de
DDL, seed, backup, restauração, reinício ou implantação nesses recursos.
O banco principal e seu volume não foram usados para os testes.

Revisão independente de QA ainda é necessária sobre o diff resultante.
O DBA pode revisar a adição de PoCL à imagem e as duas variáveis de Compose,
preservando o commit de infraestrutura preparado.
O frontend conserva seu contrato, sem novos campos, endpoints ou ações.
A adoção em imagem compartilhada exige uma etapa de implantação autorizada.
Não foi emitido aceite global do PR18 ou dos módulos clínicos.
