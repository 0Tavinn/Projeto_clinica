# Diagnóstico de latência HTTP da Agenda OpenCL — 25/11/2026

## Resultado e recomendação para decisão

O maior custo atribuível ao OpenCL neste ensaio foi a primeira utilização
com candidatos em processo novo. As três primeiras criações não vazias em
auto levaram 1,44–1,78 s no HTTP, com 0,95–1,40 s dentro da inicialização
do runtime (imports, contexto e build). No sequencial, as primeiras chamadas
correspondentes levaram 0,25–0,39 s. São três observações de processos novos,
não uma distribuição estatística de partidas frias.

Nas chamadas aquecidas com 32 candidatos, o custo adicional do comparador
OpenCL no host foi em média 1,83 ms para criação aceita; o kernel levou
0,093 ms. A mediana HTTP dessa operação foi 40,45 ms em auto e 33,84 ms em
sequential. A dispersão foi considerável, inclusive no cenário vazio que
não lança kernel. Não é correto atribuir toda diferença HTTP ao OpenCL
nem afirmar que a aplicação inteira ficou proporcionalmente mais lenta.

Recomendo, para aprovação do Tech Lead e de Paulo, **sequential como padrão
de uso diário e auto configurável para demonstração educativa**. É uma
proposta de configuração, ainda não aplicada. Ela elimina o custo de
inicialização OpenCL no primeiro agendamento cotidiano e mantém o objetivo
educativo disponível. Exigiria alinhar o default de Settings e os defaults
de Compose/template em futura tarefa, com regressões e implantação próprias.
Não exige alteração HTTP, frontend, migração ou remoção de fallback/locks.
Não foi estabelecido limiar de crossover. Os dados não demonstram ganho
de latência da aplicação por OpenCL.

Alternativamente, manter auto e aquecer o runtime antes da prontidão moveria
essa espera para o startup, com tratamento de falha e teste de readiness a
definir. Isso não resolve o custo de carregar milhares de objetos ORM.
Não implementei nenhuma dessas alternativas.

## Versão, escopo e fontes

Checkout exclusivo `/home/paulinho/Work/Projeto_clinica_clinical_2fa`.
Branch `feat/paralelismo-agendamento`.
Base `f8f10c54a4a702b7d4feccbf5aeb98578db65909`.
Feature OpenCL ainda local, sem commit. Fonte inspecionada preservada em
`working-before.patch` (rastreados) e `preservation-before.json` (hashes).
`stage-before.bin`, `stage-after.bin`, `stage-blobs-before.txt` e
`preservation.json` identificam o índice e sua preservação.
SHA-256 dos bytes staged raw:
`41f728d17e0dcc8729b81db0f5abcf7ab900e8fd8249fa65dff173a07e8a4932`.

Foram lidos guia, comparador, backend da Agenda e evidências independentes
de QA em `docs/relatorios/qa/2026-11-25-f8f10c5-opencl-agenda/`,
especialmente relatorio.md e independent-http.log. O QA aprovou com ressalvas
o snapshot local e não reproduziu defeito de produto. As contagens do QA
e o benchmark comparador anterior são históricos, sem soma aos resultados
desta investigação. Esta medição é diagnóstico do Backend, sem novo aceite
independente de QA.

## Ambiente e método

Python 3.12.16, PostgreSQL 16.15, NumPy 2.2.6, PyOpenCL 2025.2.7,
PoCL 6.0+debian/OpenCL 3.0 CPU Intel i5-13420H.
FastAPI 0.141.1, SQLAlchemy 2.0.52, Uvicorn 0.52.4, HTTPX 0.28.1.
Versões efetivas em `versions.json`.

API servida por Uvicorn real em subprocessos no contêiner de medição;
HTTPX envia HTTP a 127.0.0.1:8000 nesse contêiner. PostgreSQL fica em outro
contêiner da rede exclusiva. Não houve TestClient. Um worker Uvicorn;
handlers síncronos usam o pool padrão de threads do FastAPI.
A imagem instala o código local sem bind mount do host.

As únicas fontes novas são instrumentação/artefatos nesta pasta:
`instrumented_app.py`, `measure_http.py`, `run_measurement.py` e Dockerfile.
A instrumentação importa o aplicativo instalado e envolve funções em memória
apenas no processo de QA. Não modifica fontes funcionais ou defaults.
Relógio do cliente e durações do servidor usam perf_counter_ns por processo;
tempos de kernel usam profiling OpenCL. Não se alinham timestamps absolutos
entre processos ou relógios.

Rotas exercitadas:
- POST /api/v1/appointments — patient_id, dentist_id, scheduled_at com fuso,
  duration_minutes=30. Aceita201 ou conflito409.
- PATCH /api/v1/appointments/{id} — scheduled_at e duration_minutes.
  Aceita200 ou conflito409, com exclusão do próprio ID.

Fixtures SQL com dados fictícios criam slots de 30 minutos separados por
uma hora, sem sobreposição. Tokens válidos de recepcionista são gerados
na fixture, sem cronometrar login, senha ou autenticação clínica.
O rate limit de login permanece intacto e não é atingido; não há login
repetido nesta medição. Não houve401/429 nem outra falha de roteiro entre
as 360 amostras válidas.

0 candidatos é o caminho vazio. 32 é uma hipótese de pequena Agenda ativa
para o profissional, sem alegar representar dados reais de Paulo. 512 e,
principalmente,8192 são estresse. O filtro atual considera todos os slots
ativos da dupla clínica/dentista, sem janela temporal. A fixture de8192
espalha slots por cerca de341 dias, a cada hora, inclusive fora de horário
comercial; não modela a distribuição cotidiana de uma clínica.

Cada tentativa usa a mesma quantidade de candidatos por motor. Inserções
aceitas são removidas por SQL fora da medição. Atualizações aceitas preservam
o horário do próprio slot e exercitam excluir o próprio ID. Após conflitos
de atualização, o horário persistido é verificado. Contagens de linhas são
conferidas após cada operação para impedir acúmulo enviesado. O conflito
é no último slot cronológico da fixture; a consulta SQL não promete ordem
de entrega. Número de lotes efetivamente consumidos consta dos logs.

Foram336 chamadas aquecidas,8 primeiras chamadas e16 sondagens concorrentes,
totalizando360. São12 amostras aquecidas por célula/motor. Mediana e p95
por interpolação linear, mais IQR, mínimo e máximo em `summary.json`.
É amostragem exploratória limitada, não ensaio de carga/capacidade nem
estimativa estável de caudas raras. A ordem entre motores foi alternada
por tamanho, mas não houve múltiplos blocos randomizados de todo o ensaio.
Não se pode inferir ganho causal a partir das células negativas.

## HTTP aquecido

Diferença positiva significa auto com mediana maior.
Cada célula tem12 amostras. Os tempos incluem autenticação Bearer, SQL,
ORM, validações, serialização e tráfego HTTP local. Não incluem preparo
da fixture e verificação SQL externa.

| Candidatos | Operação | Sequential mediana / p95 (ms) | Auto mediana / p95 (ms) | Diferença das medianas (ms) | IQR seq / auto (ms) |
|---:|---|---:|---:|---:|---:|
| 0 | POST aceito 201 | 21.28 / 33.61 | 25.93 / 46.02 | +4.64 | 4.22 / 14.33 |
| 0 | PATCH aceito 200 | 24.73 / 39.45 | 18.32 / 38.61 | -6.41 | 8.37 / 11.42 |
| 32 | POST aceito 201 | 33.84 / 47.37 | 40.45 / 67.02 | +6.61 | 4.65 / 18.01 |
| 32 | POST conflito 409 | 28.16 / 35.27 | 27.24 / 45.90 | -0.91 | 5.50 / 15.04 |
| 32 | PATCH aceito 200 | 24.35 / 36.14 | 30.95 / 52.93 | +6.60 | 6.26 / 16.59 |
| 32 | PATCH conflito 409 | 17.36 / 26.38 | 23.58 / 40.69 | +6.21 | 3.45 / 17.08 |
| 512 | POST aceito 201 | 56.84 / 122.97 | 49.38 / 93.83 | -7.47 | 36.53 / 31.02 |
| 512 | POST conflito 409 | 39.54 / 65.06 | 42.11 / 64.55 | +2.57 | 15.92 / 14.13 |
| 512 | PATCH aceito 200 | 67.11 / 84.48 | 56.33 / 71.10 | -10.78 | 18.69 / 15.16 |
| 512 | PATCH conflito 409 | 60.10 / 103.24 | 51.47 / 95.43 | -8.64 | 23.46 / 12.46 |
| 8192 | POST aceito 201 | 342.47 / 413.53 | 357.30 / 472.12 | +14.83 | 83.30 / 91.34 |
| 8192 | POST conflito 409 | 337.62 / 407.77 | 341.39 / 525.02 | +3.77 | 83.53 / 122.73 |
| 8192 | PATCH aceito 200 | 365.65 / 425.09 | 477.57 / 522.36 | +111.92 | 71.65 / 151.78 |
| 8192 | PATCH conflito 409 | 338.32 / 464.42 | 414.00 / 528.15 | +75.68 | 38.93 / 72.37 |


## Primeiro uso e cache

| Candidatos | Sequential primeira chamada (ms) | Auto primeira chamada (ms) | Runtime auto (ms) |
|---:|---:|---:|---:|
| 0 | 148.39 | 148.97 | 0.00 |
| 32 | 268.23 | 1775.24 | 1399.81 |
| 512 | 253.18 | 1442.06 | 1119.72 |
| 8192 | 390.42 | 1548.83 | 949.18 |

Cada linha usa um processo Uvicorn novo para cada motor. Health foi usado
para aguardar startup e não chamou o comparador. Antes da primeira chamada,
os diretórios exclusivos XDG_CACHE_HOME e POCL_CACHE_DIR tinham zero entradas,
verificado pela instrumentação. A contagem final de entradas está em
`processes.json`. Isso comprova esses diretórios vazios e runtime em novo
processo, mas não demonstra que todo cache do sistema operacional,
LLVM ou outro cache externo estava frio. Compilação e imports foram
medidos juntos, sem decomposição exclusiva do compilador.

O caso vazio não inicializou OpenCL; ambos os primeiros HTTP ficaram em
aproximadamente149 ms. Assim, esse custo inicial de API/SQL é distinto da
inicialização OpenCL observada nos casos não vazios.

## Parcelas observadas

Médias em milissegundos para criação aceita em auto:

| Candidatos | Repositório total (ms) | OpenCL host total (ms) | Arrays (ms) | Enfileirar/leitura com espera (ms) | Kernel (ms) |
|---:|---:|---:|---:|---:|---:|
| 0 | 5.223 | 0.000 | 0.000 | 0.000 | 0.000 |
| 32 | 11.909 | 1.827 | 0.044 | 0.358 | 0.093 |
| 512 | 30.305 | 1.440 | 0.157 | 0.262 | 0.052 |
| 8192 | 348.078 | 5.615 | 2.629 | 0.688 | 0.207 |

Essas parcelas são **aninhadas e não devem ser somadas**. Repositório inclui
consulta, consumo do cursor, ORM, conversões e comparador. detect_ns também
inclui consumo/fetch do gerador de candidatos. sql_execute_ns mede chamadas
DBAPI, sem isolar todo fetch de cursor e materialização ORM. array_prepare_ns
envolve np.asarray; cópia inicial COPY_HOST_PTR, alocação de buffers,
fila e redução não foram isoladas individualmente. A leitura inclui
enfileiramento e espera, sobrepondo-se ao kernel quando ele ainda executa.
server_ns termina no retorno de call_next, não após todo consumo do corpo
pelo cliente. A medida principal de latência é o HTTP completo do cliente.

No cenário8192 aquecido, o repositório consumiu em média348 ms para POST
aceito em auto, contra5,62 ms na função OpenCL do host e0,207 ms no kernel.
A busca/materialização de candidatos domina essa escala. As diferenças
HTTP de até112 ms observadas em PATCH nessa rodada são maiores que a
parcela OpenCL medida e convivem com IQR alto. Não há base para atribuí-las
integralmente ao kernel ou propor um limiar automático de troca de motor.

Instrumentar cada conversão e chamada também adiciona overhead. Não foi
executada réplica sem instrumentação, logo os tempos absolutos representam
a API instrumentada. Esse limite importa especialmente nos lotes grandes.
Não foram tomadas medidas de rede externa, navegador, máquina diferente
ou tráfego do ambiente diário.

## Inicialização e requisições simultâneas

Quatro primeiras criações simultâneas por motor usaram **dentistas
diferentes**,32 candidatos para cada um, isolando a espera do runtime da
serialização deliberada pelo advisory lock do mesmo profissional.
Todas receberam201 e a contagem voltou à fixture128 após limpeza das
criações. Uma segunda rodada de4 chamadas foi aquecida.

- Sequential, primeiras4:346–362 ms. Aquecidas:125–140 ms.
- Auto, primeiras4:1389–1396 ms. Uma thread inicializou o runtime por1077 ms;
  as outras3 esperaram aproximadamente1069–1073 ms no lock de inicialização.
- Auto aquecido:130–138 ms. Espera do lock de runtime de até cerca de0,01 ms
  nessa pequena sondagem.

O lock do runtime pode concentrar espera no primeiro uso simultâneo,
mesmo com dentistas diferentes. Depois de aquecido, não foi um gargalo
relevante nessas4 chamadas. Código de comparação e transferências roda
em handlers síncronos de threads; a inicialização ocupa essas threads.
Não foi medido esgotamento do pool nem responsividade do event loop
sob carga alta. A proteção de reservas concorrentes do mesmo dentista
permanece necessária e não é candidata a remoção.

## Interpretação para Paulo e proposta

Com uma pequena quantidade de candidatos e runtime aquecido, os HTTP
ficaram na ordem de dezenas de milissegundos neste ambiente local.
Uma diferença de poucos milissegundos provavelmente não seria uma espera
claramente percebida isoladamente na tela. Já a primeira utilização
OpenCL não vazia, próxima de1,5 s ou mais, provavelmente seria percebida
como espera se coincidisse com a ação de salvar.

Essas são inferências a partir do HTTP. Não houve observação de navegador.
Outras ações, renderização, latência de rede e máquina do usuário podem
alterar a experiência. No estresse8192, tempos de centenas de milissegundos
apareceram em ambos os motores. Isso recomenda investigar a projeção SQL
e materialização de candidatos somente se houver necessidade real nesse
volume, em tarefa própria e com preservação da regra. Não foi projetada
nem implementada uma otimização de consulta nesta etapa.

A opção proporcional proposta é deixar sequential no uso diário e oferecer
auto explicitamente na demonstração. Manter auto é também possível se a
equipe aceitar o primeiro uso observado e o objetivo educativo; não existe
um requisito aprovado de latência usado aqui para declarar reprovação.

## Preservação, limpeza, falhas de roteiro e reprodução

`inventory-before.json` e `inventory-after.json` são idênticos, incluindo
IDs, imagens, início, reinícios e portas dos contêineres preexistentes,
além de redes e volumes. `cleanup.json` confirma remoção dos recursos com
rótulo exclusivo deste ensaio. Não houve acesso SQL ao banco diário,
rebuild do Compose diário ou instalação no Python global WSL3.14.
O PostgreSQL exclusivo recebeu schema PR18 apenas em banco vazio.

A primeira tentativa de build falhou porque o tar PAX foi interpretado
como Dockerfile pelo CLI Windows. O harness foi corrigido para formato GNU
e o Dockerfile de instrumentação foi corrigido. Nenhuma amostra HTTP foi
produzida nessa tentativa; registros em `attempt-1/`.
A execução válida terminou sem falhas e com código zero.

Reprodução, a partir do checkout autorizado:

~~~bash
python3 docs/relatorios/performance-opencl-http-2026-11-25/run_measurement.py
~~~

Esse comando recria recursos próprios e sobrescreve saídas desta pasta.
Para preservar a rodada, copie somente a pasta de instrumentação para
uma nova pasta irmã antes de reproduzir, mantenha o ROOT exclusivo e
identifique os novos hashes. Não o use como teste do banco existente.

`raw.json` contém360 amostras e metadados anônimos; `summary.json` contém
estatísticas completas; dez arquivos <motor>-<cenário>.log têm os tempos
do servidor. `execution.log`, `versions.json`, `processes.json`, logs
de build e inventários permitem reproduzir e auditar. Nenhum payload,
token ou conteúdo clínico é registrado nos logs de requisição.
