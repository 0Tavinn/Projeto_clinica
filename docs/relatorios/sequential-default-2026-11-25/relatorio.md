# Padrão sequencial da Agenda — 25/11/2026

## Entrega

Aplicado localmente o ajuste aprovado por Paulo: sequential é o padrão
cotidiano, e auto continua disponível para OpenCL CPU educativo com fallback.

Checkout: /home/paulinho/Work/Projeto_clinica_clinical_2fa
Branch: feat/paralelismo-agendamento
Base: f8f10c54a4a702b7d4feccbf5aeb98578db65909
Alterações ainda no working tree.

## Defaults e arquivos alterados nesta etapa

| Arquivo | Alteração |
|---|---|
| backend/app/core/config.py | Settings passa a sequential quando não configurado; mantém Literal auto/sequential e lote4096. |
| compose.yml | Fallback da interpolação passa a sequential; auto explícito continua sendo encaminhado. |
| .env.example | Exemplo cotidiano sequential e comentário sobre auto/fallback. |
| scripts/setup_dev.py | Ambiente novo recebe sequential. O_EXCL continua preservando .env já existente. |
| backend/tests/test_opencl_conflicts.py | Casos de kernel/fallback selecionam auto explicitamente; novo teste de default e override por ambiente. |
| backend/tests/test_opencl_pg.py | Sondagem que exige kernel real configura auto explicitamente. |
| backend/tests/run_opencl_qa.sh | Contêiner dirigido recebe auto explicitamente. A suíte completa continua sem override do motor. |
| docs/paralelismo-agendamento.md | Padrão cotidiano, demonstração isolada, precedência dos helpers e motivo da decisão. |

O setup_dev não tinha default próprio do motor anteriormente: omitia a
variável e dependia do fallback do Compose. Agora gera o valor explicitamente.
Nenhum arquivo .env existente ou compose.local.yml foi modificado.
O helper Environment carrega os valores do .env sobre os do shell; por isso
a demonstração recomendada usa o runner isolado e não depende de prefixar
auto a um comando do helper diário.

Implementação/kernel/dependências OpenCL, tamanho do lote, algoritmo,
repositório, regras, rotas, schemas, frontend e SQL não mudaram nesta etapa.
Os oito arquivos acima são as únicas diferenças sobre os bytes preexistentes
registrados antes do trabalho. Novos artefatos desta rodada estão nesta pasta
e na pasta opencl-1795642186_d870cfbd-c6a.

## Verificação executada

Ambiente de teste Docker derivado de Python3.12-slim, com NumPy/PyOpenCL/PoCL
instalados pela imagem do projeto. PostgreSQL16.15 em contêiner e volume
exclusivos. Não houve instalação de pacotes no Python global WSL3.14.

1. Compose renderizado com --env-file temporário fictício e sem serviços
   iniciados: opção ausente => sequential; vazia => sequential;
   auto explícito => auto; sequential explícito => sequential.
   Somente o resultado sanitizado foi persistido em configuration-checks.json.
2. setup_dev executado em cópia temporária: novo .env contém sequential.
   Nova execução diante de .env fictício com auto retornou1 e manteve os
   mesmos bytes. O .env real permaneceu idêntico ao snapshot anterior.
3. Processo independente da imagem recém-construída, sem override do motor:
   get_settings retornou sequential; detect_conflict encontrou o conflito,
   engine=sequential, fallback=false, sem importar pyopencl.
   Evidência em default-process.log.
4. Ensaio dirigido: **66 aprovados,0 reprovados,0 pulados**,9 warnings,
   10,58 s. Inclui default novo, configuração inválida, equivalência,
   OpenCL CPU real com profiling, lotes, precisão temporal, fallback,
   concorrência, filtros do repositório,14 regressões existentes da Agenda
   e corrida HTTP/TestClient em PostgreSQL com autoridade GiST.
   Log em ../opencl-1795642186_d870cfbd-c6a/targeted.log.
5. OpenAPI permaneceu com18 caminhos e hash canônico
   b959aa6f36ddcd38c350eac94d34ba3a51fa177f8fb3b0ff1f1084bd2290dba3,
   igual ao baseline PR18 já identificado. Routers/schemas/frontend/src
   continuaram sem diff contra o HEAD.
6. git diff --check e bash -n backend/tests/run_opencl_qa.sh passaram.

Comando executado nesta rodada:

~~~bash
cd /home/paulinho/Work/Projeto_clinica_clinical_2fa
python3 docs/relatorios/sequential-default-2026-11-25/verify_focused.py
~~~

O wrapper reutilizou o runner oficial, omitindo apenas benchmark e suíte
ampla. A mudança afetou a seleção do motor no harness; por isso foi repetido
o conjunto dirigido completo, incluindo o PostgreSQL e kernel real.
Não foi repetida a investigação de performance nem a suíte geral nesta etapa.
Os resultados gerais e o parecer independente anteriores continuam associados
aos seus snapshots históricos. Não são apresentados como reteste desta revisão.

Para demonstrar OpenCL com o runner oficial em recursos descartáveis:

~~~bash
cd /home/paulinho/Work/Projeto_clinica_clinical_2fa
bash backend/tests/run_opencl_qa.sh
~~~

Esse runner fornece auto explicitamente ao contêiner dirigido, monta seu
próprio PostgreSQL e remove seus recursos por rótulo. Também executa suas
demais verificações e benchmark educativo. Não altera o .env diário.
A imagem de QA mantém LUMINA_REQUIRE_OPENCL=1: ausência do runtime provoca
falha nos testes reais, evitando falso positivo por sequential/fallback.

## Preservação e limite do aceite

Índice byte a byte idêntico, incluindo os17 arquivos de infraestrutura.
stage-before.bin/stage-after.bin e index-before.txt/index-after.txt
registram a comparação. SHA-256 dos bytes staged raw antes/depois:
41f728d17e0dcc8729b81db0f5abcf7ab900e8fd8249fa65dff173a07e8a4932.

preservation.json compara414 arquivos preexistentes e identifica somente
os oito arquivos esperados como alterados. Inclui preservação dos relatórios
históricos de QA/Backend/performance e dos arquivos locais de ambiente.
change-hashes.txt identifica a revisão atual desses oito arquivos.

inventory-before.json e inventory-after.json são idênticos para contêineres,
imagens em uso, horários de início, reinícios, portas, redes e volumes
preexistentes. A limpeza do runner deixou cleanup.txt vazio para os recursos
temporários. O Compose lumina_pr18_tarcisio e seu banco não foram utilizados
para escrita ou implantação. Não houve commit, publicação ou alteração do stage.

A decisão se apoia no diagnóstico HTTP anterior, que não demonstrou ganho
consistente com OpenCL CPU e identificou custo no primeiro uso. Os números
daquele diagnóstico não foram recalculados nesta rodada. Esta entrega está
testada pelo Backend no recorte descrito e ainda pode receber revisão
independente do QA/Tech Lead. Uma implantação futura exige decisão própria.
