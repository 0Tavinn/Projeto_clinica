# Reteste independente — prontuários e busca OpenCL

**Parecer: NÃO PRONTO PARA INTEGRAÇÃO DESTA CANDIDATA.** As correções principais passaram nas verificações exercitadas, mas permanece uma falha de privacidade nos logs da API. A resposta de validação foi sanitizada; o termo clínico na URL ainda é registrado pelo log padrão do servidor. Isso impede encerrar N05 e declarar a entrega pronta para uso integrado com conteúdo clínico.

**Executor: AGENTE DE QA**, com autorização de Paulo. Execução: **25/11/2026**, aproximadamente **20:21–20:43, America/Sao_Paulo (UTC−03)**; janela documentada de identificação até limpeza, cerca de 22 minutos, não tempo somado de CPU. Finalização documental: **26/11/2026**, após pausa solicitada por Paulo. Em 26/11 foram conciliadas evidências e hashes, sem nova execução funcional, sem reconstruir imagens e sem iniciar serviços.

**Pasta original das evidências:** /home/paulinho/Work/lumina-qa-evidence/2026-11-25-pacote-corrigido-987ee71999-bd315

## 1. Versão efetivamente examinada

| Item | Identificação |
|---|---|
| Fonte exclusiva | /home/paulinho/Work/lumina_odonto_corrigido_QA/lumina_odonto_atualizado |
| Tipo de entrega | Pacote de arquivos, **sem Git**; não há branch ou commit desta candidata |
| Proveniência | Recebido de Tarcísio **segundo Paulo**; não comprovada por autoria Git |
| SHA256 do manifesto da candidata | 987ee7199972977bc549346246d0ee5bf46d4611b9d15c3c8fc89fdfbd41fe40 |
| Inventário | 20 arquivos relevantes; 40 arquivos recebidos contando metadados Zone.Identifier |
| Comparação anterior | tata2005-patch-1, 4ccdc30a27143b6c022b7f8cae2e6ccf03860389, subpasta lumina_odonto/ |
| Ascendência da referência anterior | Pai f8f10c54a4a702b7d4feccbf5aeb98578db65909, entrega de banco PR18 |
| Schema recebido | SHA256 2ca830bda08ba3711f69408fe5848a5fd3304156373020f90310b04e746eda81, idêntico à referência PR18 informada e conferida |
| Imagem efetivamente executada | sha256:12b82a6b985742e7eb8a4e36b0aeb8f5d49280ace9a995c490e51d329ab5b9a6 |
| Branches de outros projetos | Apenas inventariadas/protegidas; não identificam este pacote |

A identidade é definida pelo mapa de caminhos e SHA256 em candidate-files-sha256.json; identity.json registra seu digest. Zone.Identifier foi excluído somente dessa identidade lógica e incluído na comparação integral de preservação. Todos os 40 arquivos permaneceram iguais antes/depois; uma nova leitura em 26/11 também confirmou igualdade. Não se atribui SHA de commit ao pacote. Um futuro commit só poderá herdar estas evidências após comparação verificável do conteúdo e das dependências.

Comparado ao conteúdo publicado anterior, changes.json registra 15 arquivos adicionados/modificados. Mudaram app/main.py, app/crud.py e app/opencl_search.py, além de Dockerfile, README e testes; foram incluídos arquivos de configuração e SQL antes ausentes da subpasta publicada. O kernel contains.cl não mudou nessa comparação. A lista integral e os hashes estão nos inventários. candidate-vs-4ccdc30.patch é um **diff sanitizado**, com três hashes fictícios de senha omitidos; artifact-sanitization.json guarda a declaração e o digest do diff original. O pacote original não foi sanitizado nem editado.

Os checkouts protegidos estavam em e49a3ce22f899ad64d971a50e8d7fd9c99cb5b3a: principal em feat/paralelismo-agendamento e alternativo com HEAD destacado. Não foram usados como fonte desta API nem receberam correções/importações.

## 2. Ambiente, dados e isolamento

| Componente | Versão/condição comprovada em 25/11 |
|---|---|
| Docker cliente/servidor | 29.9.3 / 29.9.3 |
| Compose | v5.7.0 |
| Python da imagem | 3.12.16 |
| PostgreSQL usado pela API | **16.16 (Debian 16.16-1.pgdg13+1)**, obtido por SHOW server_version no banco QA |
| FastAPI / Uvicorn | 0.165.0 / 0.54.0 |
| SQLAlchemy / psycopg | 2.1.9 / 3.3.9 |
| Pydantic / pytest | 2.14.4 / 9.2.0 |
| NumPy / PyOpenCL | 2.5.5 / 2026.1.5 |
| Plataforma OpenCL | Portable Computing Language, OpenCL 3.0 PoCL, driver 6.0+debian |
| Dispositivo | CPU Intel Core i5-13420H; device_type=2 |
| API ensaiada | Uvicorn HTTP real da aplicação recebida; não apenas TestClient |
| Banco | lumina_corrected_qa, novo e descartável |
| Prefixo exclusivo | lumina-corrected-qa-6ba8c93e83 |
| Rede / volume | prefixo-net / prefixo-data, exclusivos |
| Portas externas | Nenhuma publicada para API, PostgreSQL ou controle da instrumentação |
| Segredos | Gerados somente para QA; arquivo efêmero removido ao terminar |

O Dockerfile **original** construiu sem adaptar aplicação, testes ou dependências declaradas. As versões abertas foram resolvidas no build; dependencies.txt registra o ambiente efetivo. Isso não garante que um build futuro, sem fixação das versões, resulte no mesmo ambiente.

O Compose recebido publica 5432/8000 e depende de .env. Não foi iniciado diretamente. Um override externo removeu portas e forneceu configuração fictícia e nomes exclusivos; docker compose config --quiet passou. A execução efetiva foi por docker run, declarada em setup_and_core.py, com o mesmo Dockerfile/imagem e schema recebido montado somente para inicialização de banco vazio. Isso comprova o provisionamento dos artefatos recebidos nessa orquestração, não uma implantação diária pelo Compose original.

Dados: seed_demo.sql recebido, seguido de fixtures próprias com duas clínicas, administrador, recepção, dois dentistas locais, dentista externo, usuário inativo, dentista sem cadastro profissional, pacientes e consultas fictícios. Identidades-base e lotes grandes foram preparados por SQL somente no banco QA; operações clínicas, concessões administrativas e agenda foram exercitadas por HTTP. Lotes de paginação/bytes e falhas controladas são dados de teste declarados nos scripts. Nenhuma conta, token ou conteúdo real foi utilizado.

## 3. Critérios e método

A referência clínica desta entrega é a nova proposta de prontuários e especificação 1.1, confrontada com README.md, QA_CORRECOES.md, fonte e testes recebidos. Não se aplicaram automaticamente as antigas regras D02–D04 dependentes de consulta: nesta candidata, evolução manual não exige consulta e o vínculo é duradouro.

Distinções usadas:

- **Critério solicitado para revalidação:** revogação efetiva, isolamento, autoria, privacidade, transação e concorrência.
- **Comportamento implementado e executado:** registrado na matriz e nos logs, limitado às entradas e condições observadas.
- **Contrato candidato:** patient_id obrigatório, códigos 422/413 e paginação por candidatos, propostos pelo pacote e sujeitos a alinhamento.
- **Decisão pendente:** D05/D06, exportação/impressão, parte da política de inativos e limiares de rate limiting. Testes não substituem decisão de Paulo.

Conexões PostgreSQL independentes seguraram locks; pg_stat_activity comprovou wait_event_type=Lock antes de liberar transações. Não se usou apenas tempo de espera como prova. Parte das revogações determinísticas usa UPDATE SQL com commit na conexão controladora; esses casos comprovam ordenação/autorização, **não** auditoria administrativa ponta a ponta. Os cenários administrativos separados verificaram evento e auditoria por HTTP.

A instrumentação foi externa, em outro contêiner QA da mesma imagem, sem editar o pacote. O controle só existiu na rede exclusiva. O kernel original foi chamado; o fallback foi testado separadamente por injeção de OpenCLUnavailable. Não se apresenta essa injeção como falha real de driver.

## 4. Contagens sem duplicidade

| Grupo | Aprovados | Reprovados | Bloqueados | Não executados |
|---|---:|---:|---:|---:|
| Verificações independentes, incluindo 3 de preparo | **73** | **1** | 0 | 0 |
| Testes recebidos, contagem separada | **18** | 0 | 0 | 0 |
| Pendências de aceite/escopo | 0 | 0 | **7** | **2** |

São **74 IDs independentes**, dos quais 71 são sondagens de comportamento/integração e 3 verificam preparo. Os 18 testes recebidos se sobrepõem semanticamente às sondagens: **não se anuncia a soma como 92 cenários distintos**. A matriz tem 101 linhas de dados incluindo os grupos fornecido e pendente. Tentativas repetidas ficam em tentativas.csv, não aumentam a cobertura.

Distribuição das 74 verificações independentes segundo a camada principal da matriz:

| Camada principal | Aprovados | Reprovados |
|---|---:|---:|
| HTTP | 46 | 1 |
| HTTP/PostgreSQL | 22 | 0 |
| SQL | 1 | 0 |
| SQL/HTTP/infraestrutura | 1 | 0 |
| infraestrutura | 2 | 0 |
| servico/OpenCL real | 1 | 0 |

A classificação HTTP indica requisições ao servidor real; nem toda linha HTTP contém asserção direta do estado SQL. As comparações persistidas existem nos casos que as descrevem. Nenhum cenário de navegador foi executado. Os testes recebidos concluíram sem skips; provided-tests.xml e provided-tests.log são as evidências, não a informação de execução local contida em QA_CORRECOES.md.

O histórico de 23/11 permanece separado: **45 aprovados, 9 reprovados, 2 bloqueados, 7 não executados, 1 observação; 64 linhas**. Os nove resultados reprovados representavam oito defeitos. Não foram incorporados aos totais atuais. Migrações/restauração executadas no ensaio antigo não foram repetidas agora nem transferidas para este pacote.

## 5. Reteste dos oito defeitos

“Corrigido” significa aprovado nos cenários desta rodada e nesta identidade; não é aprovação irrestrita do módulo.

| Defeito / gravidade anterior | Situação no reteste | Esperado / observado / estado persistido | Evidência e reprodução |
|---|---|---|---|
| N01 — crítica; busca após revogação | **Corrigido no recorte exercitado** | Busca aguardando vínculo: CPU e OpenCL 403, vínculo REVOKED, sem results. Revogação durante kernel real:403 após commit, eventoRUNNING antes/depois. Edição/finalização após revogação:403, DRAFT v1, conteúdo/data final intactos. | concurrency-replay.log; instrumentation-probe.log; concurrency_replay.py e instrumentation_probe.py |
| N02 — alta; serialização da Agenda | **Corrigido** | POST 201; GET lista/detalhe/filtros, PATCH, DELETE200. scheduled_period ausente do DTO; após cancelamento o banco está CANCELED, coerente com HTTP 200. | N02-CRUD-DTO em core_probe.py.log; app/crud.py:66 e 76 |
| N03 — alta; preparo incompleto | **Corrigido para o pacote avulso e banco vazio ensaiado** | .env.example/schema/seed presentes; Dockerfile original constrói; config isolada válida; schema, seed e verificações SQL passam. Não comprova upgrade/migração nem corrige retroativamente o commit antigo. | build-exact.log; compose-config.log; seed.log; sql-constraints.log |
| N04 — alta; revogar alvos inelegíveis | **Corrigido nos alvos exercitados** | Paciente inativo, dentista inativo ou sem senha clínica:200, REVOKED, um evento novo e auditoria. Reativação de inativos recusada 404/422. Admin externo 404 sem alterar vínculo. Revogação preserva prontuário e 3 evoluções comparadas; leitura 403. | core_probe.py.log; final_probe.py.log; app/main.py:170–210 |
| N05 — alta; privacidade dos erros | **Parcial; pendência persiste nos logs** | Eco clínico do corpo 422 corrigido nas 5 entradas; resposta 422 da query também sem eco; update de usuário 200 sem hashes/campos de sessão. Entretanto termo de busca aparece no log de acesso da API original. Não foi comparado um snapshot SQL específico dessa requisição de leitura 422. | privacy-log-check.json; api-sanitized.log; core_probe.py.log; advanced_probe.py.log |
| N06 — média; escopo da busca | **Corrigido funcionalmente; contrato candidato** | Dois pacientes autorizados não misturam resultados; parâmetro ausente/inválido 422, sem vínculo 403, outra clínica negada. Rota não escreve; verificação focada em resultados e autorização. | N06-* em core_probe.py.log; openapi-differences.json; app/main.py:359 |
| N07 — média; coerção da versão | **Corrigido** | Texto, bool, null, zero, negativo, ausente:12 respostas 422 em PATCH/finalize, DRAFT v1 intacto. Atual 200; desatualizada 409. Disputa real 200/409, versão 2, conteúdo igual à edição aceita. | core_probe.py.log; concurrency-replay.log; app/main.py:63–69 |
| N08 — média; termo normalizado vazio | **Corrigido funcionalmente; 422 candidato** | Ausente, vazio, espaços e U+0301:422 nos 3 motores, sem busca ampla nem 503 técnico. Entradas Unicode válidas equivalentes à CPU no conjunto comparado. | core_probe.py.log; advanced_probe.py.log; app/main.py:359 e app/opencl_search.py |

As referências de linha pertencem ao pacote identificado, não a um commit publicado.

### N05-LOG — pendência de privacidade reproduzida

**Gravidade: alta (P1). Responsável proposto: Backend/Tarcísio, com revisão de configuração pela infraestrutura.**

**Pré-condições:** imagem construída do pacote original, Uvicorn iniciado pelo CMD do Dockerfile, dentista fictício ativo com token clínico. A demonstração usa uma sentinela fictícia em vez de dado clínico real.

**Passos:**

1. Autenticar e obter o token clínico pelo fluxo normal.
2. Fazer GET /api/v1/clinical/search?q=<sentinela-ficticia>, omitindo patient_id para provocar validação 422.
3. Conferir o corpo da resposta.
4. Conferir docker logs somente do contêiner exclusivo da API.

**Esperado:**422 útil, sem a entrada clínica no corpo nem em logs operacionais. **Encontrado:**corpo sem eco, mas o access log padrão registra a querystring. Extrato sanitizado efetivamente coletado:

~~~text
INFO: 172.22.0.4:45898 - "GET /api/v1/clinical/search?q=<query-sentinel> HTTP/1.1" 422 Unprocessable Entity
~~~

privacy-log-check.json registra body_sentinel_in_logs=false e query_sentinel_in_logs=true. O extrato acima foi coletado da API **original**, não do servidor instrumentado, que desabilitou somente seu próprio access log.

**Impacto fundamentado:**um termo de pesquisa potencialmente clínico pode ser retido em logs e disponibilizado a quem opera ou coleta esses logs, ampliando os locais de armazenamento além da resposta protegida. Foi comprovada a presença no log local do ensaio; **não há evidência de envio ou acesso por terceiros**, nem de exposição de pacientes reais.

**Local relevante:**Dockerfile:8 inicia Uvicorn sem política de redação; app/main.py:359–360 recebe q na URL. O handler de app/main.py:28–39 trata a resposta 422 e não remove a query do logger do servidor. Não basta trocar a mensagem de validação.

**Correção proposta, não implementada pelo QA:**definir registro de acesso que omita/redija valores clínicos de URLs, preservando método, rota, código e correlação úteis. Revisar também proxy/coletor quando existirem. Qualquer mudança no contrato de transporte da busca requer alinhamento. Retestar sentinelas nas respostas e logs em requisições válidas e inválidas. A proteção global dos logs não foi aprovada por este ensaio.

## 6. Regressões que passaram e limites das provas

- **Acesso:**sem autenticação 401; token de login não substitui clínico 401; admin não desbloqueia 403; recepção não obtém conteúdo pelo token de login 401; sem cadastro profissional 403; inativo não autentica 401; sem vínculo 403; outra clínica negada. Não são dois fatores independentes: são duas senhas com escopos de token.
- **Autoria/privacidade:**rascunho de outro autor ausente da lista e detalhe 403; escrita de terceiro 403; finalizada compartilhada com dentista vinculado 200; edição comum após finalização 403. Campos de autoria, estado e horário forjados não substituíram valores do servidor. Consulta opcional incompatível 422.
- **Vínculo duradouro:**novo agendamento concede/reativa; cancelamento, ausência e conclusão preservam acesso; alteração de consulta antiga não reativa vínculo revogado. Isso testa a nova política e não comprova o antigo fluxo de conclusão com care_occurred_at.
- **Transações:**falha intermediária de prontuário devolveu 500 e não deixou paciente residual; falha de auditoria ao editar devolveu 500 e preservou DRAFT v1, notes e finalized_at. Gatilhos de falha só existiram no banco QA e foram removidos. O 500 nesses casos é uma falha deliberadamente injetada; aprovação refere-se à atomicidade, não à qualidade de uma mensagem 500.
- **Concorrência:**espera real por lock, revogação 403, duas edições 200/409, edição versus finalização 200/403. Agendamentos concorrentes em horário inicialmente livre:201/409, uma consulta, um vínculo e um evento do vencedor. A origem SQL controlada da revogação é distinguida do fluxo administrativo.
- **Kernel real:**CPU e OpenCL retornaram os mesmos IDs/ordem nos conjuntos comparados; Unicode, acentos, caixa, textos longos, lista vazia e descrições vazias no motor foram exercitados. O dado de motor vazio não é aceite de descrição clínica vazia. Oito buscas HTTP concorrentes concluíram 200 com os mesmos IDs. Sem benchmark novo nem alegação de aceleração.
- **Busca grande:**1005 candidatos visíveis paginados1000/5, sem duplicidade e sem 3 rascunhos de outro autor. Página sem correspondência pode ter total 0 e next_offset1000, pois a paginação é de candidatos. Orçamento normalizado UTF8 de 2.000.000 bytes aceito; 2.000.004 recebeu 413 nos 3 motores.
- **Runtime indisponível:**injeção externa de OpenCLUnavailable produziu 503 em modo forçado e 200 com CPU em auto. Não foi retirada/avariada uma instalação real do driver.
- **Senhas/tokens:**distinção de senhas, reset por perfil/clínica, invalidação de token e senha antigos, expiração e assinatura inválida passaram. O aviso de chave curta no roteiro refere-se ao token propositalmente inválido do QA, não à chave efêmera da API.
- **Persistência:**contagens e digests de 10 tabelas idênticos antes/depois de reiniciar os mesmos contêineres API e PostgreSQL. IDs de contêiner e volume preservados; health/me 200 e novo login/desbloqueio funcionaram. Não foi recriação, backup/restauração ou teste de banco diário.

Na busca instrumentada OpenCL, o proxy chamou contains_bytes original, observou event.command_execution_status=1(RUNNING), confirmou a revogação SQL, voltou a observar 1 e aguardou conclusão real=0. A rota respondeu 403 sem results. Isso comprova a revogação dentro da janela de execução real registrada, sem gate artificial. Na CPU, a revogação foi **depois da comparação real e antes do retorno à rota**, não durante instruções da comparação.

A rechecagem ordena transações antes da resposta. Não permite retirar bytes já enviados e não demonstra ausência de todas as corridas possíveis. As verificações de usuário/clínica/paciente inativos durante lock observaram 401/403/404; a política clínica definitiva de inativação não foi aprovada pelo QA.

## 7. Tentativas e limitações de evidência

1. setup-attempt-1.py.txt contém um erro de sintaxe do roteiro QA, antes de criar recursos. Foi corrigido somente o auxiliar; não é falha da entrega nem teste aprovado.
2. final_probe.py usou id onde o POST de consulta devolve appointment_id. Esse caso ficou bloqueado na tentativa, preservada. status_probe.py usou o contrato correto e confirmou o vínculo duradouro. A matriz conserva um resultado final por ID.
3. A repetição de agenda em concurrency-replay.log atingiu o horário já ocupado pela primeira execução:409/409. A pré-condição de horário livre era inválida; appointment-race-final.log usa novos pacientes e outro intervalo e comprovou 201/409. Não é defeito de produto e não foi apagada a tentativa.
4. A primeira rodada de concorrência foi observada no console; a repetição gravada é a evidência arquivada usada no relatório. Não se contam as duas como cenários diferentes.
5. Os testes recebidos, alguns com mocks/TestClient, não substituíram as sondagens HTTP servidas em Uvicorn. Os logs independentes identificam a instrumentação quando usada.
6. Não há prints de navegador ou vídeos nesta rodada. As evidências reais são saídas HTTP resumidas, telemetria do kernel, SQL, digests e logs sanitizados. Não foram produzidas capturas ilustrativas para simular execução.
7. O diff distribuível omite hashes de senha do seed; a identificação integral do código vem dos digests por arquivo. Senhas fictícias dos roteiros são fixtures reproduzíveis, nunca credenciais reais.

## 8. Pendências para integração e implantação

| ID / situação | O que falta | Responsável proposto |
|---|---|---|
| N05-LOG — reprovado | Redação/omissão dos termos clínicos no log e reteste de respostas/logs | Backend + infraestrutura |
| P01 — não executado | Percurso no navegador com interface e API identificadas; login, senha clínica, paciente, vínculo, evolução, busca, 409 e erros | QA + Frontend |
| P02 — bloqueado | Referência publicada das correções e comparação com o pacote ensaiado | Backend + Paulo |
| P03 — bloqueado | Caminho suportado de upgrade/migrações versionadas; ensaiar em cópia descartável | Backend + DBA |
| P04 — bloqueado | Repositório/runner original completo e respectivas revisões para executar a suíte integral | Backend + DBA |
| P05 — não executado | Backup/restauração e eventual recriação com volume preservado | DBA + QA |
| P06 — bloqueado | Critérios/política de exportação e impressão | Paulo + Tech Lead |
| P07 — bloqueado | Decisões D05/D06 e limites clínicos de inativos | Paulo + Tech Lead |
| P08 — bloqueado | Limiar, janela, resposta e aceite de rate limiting | Paulo + Backend |
| P09 — bloqueado | Alinhar novos contratos de busca e consumidores | Backend + Frontend + Paulo |

Oito logins inválidos retornaram 401. Isso é uma observação, sem limiar aprovado para reprovar/aprovar rate limiting. O pacote não trouxe revisões Alembic históricas; não se inventou lineage nem se aplicou DDL em banco existente. Os arquivos SQL recebidos resolvem inicialização de **banco vazio**, não a transição de implantação da API antiga. Ausência de decisão não foi convertida em autorização ampla ou defeito aprovado.

## 9. Preservação, limpeza e parecer por camada

preservation.json confirma pacote byte a byte, HEAD/status/índice dos dois checkouts iguais e inventários de nomes/imagens/portas de contêineres, volumes e redes iguais antes/depois. Essa comparação de inventário não é checksum dos bancos diários; eles não foram acessados para escrita ou teste.

Foram criados e removidos **5 contêineres**, **1 volume**, **1 rede** e **1 imagem/tag QA**; cleanup.json registra verificação de propriedade por rótulo antes das remoções. Arquivo de segredo efêmero removido. Imagens-base/caches compartilhados não foram removidos. Nenhum recurso do Compose lumina_pr18_tarcisio, lumina_ui_*, lumina_execucao_* ou lumina_s07_* foi parado, recriado, migrado ou usado para escrita.

| Camada/objetivo | Parecer limitado |
|---|---|
| API clínica/integração desta candidata | **Não pronto:** N05-LOG aberto; correções exercitadas não equivalem a aceite global |
| Banco vazio e atomicidade no ensaio | **Aprovado no recorte executado** em PostgreSQL16.16; upgrade/restauração continuam sem prova atual |
| Busca OpenCL CPU | **Aprovada nos cenários executados** de execução/equivalência/reaquisição de autorização; sem alegação de velocidade |
| Interface/fluxo integrado | **Não executado; sem aceite** |
| Implantação/publicação | **Não pronta:** pacote sem commit, migrações/consumidores a alinhar |
| Produção/dados reais | **Sem homologação** nesta rodada |

## 10. Entrega e próximos passos

Artefatos nesta pasta: matriz.csv, tentativas.csv, totais.json, reproducao.md, comparativo-contratos.md, resumo-cassiano.md, manifesto-evidencias-sha256.json, além de scripts/logs e inventários citados. Cada linha da matriz contém pré-condição, ação, esperado, obtido, situação e caminho de evidência. Os logs originais das tentativas foram preservados; o access log de distribuição é explicitamente sanitizado.

Ordem sugerida: Backend corrigir N05-LOG e repetir sentinelas; alinhar contratos e publicar referência verificável; DBA/Backend fechar provisionamento/upgrade; QA executar o percurso com frontend identificado. Não é necessário repetir indiscriminadamente todos os testes já aprovados se o diff de correção não os afetar, mas a versão publicada deverá ser reconciliada.

**Resumo para Cassiano:** Em 25/11/2026, o AGENTE DE QA revalidou o pacote avulso de prontuários/OpenCL informado por Paulo como entrega corrigida de Tarcísio, manifesto 987ee71999…, em API HTTP real, PostgreSQL 16.16 descartável e CPU PoCL. Das 74 verificações independentes, 73 passaram e 1 reprovou; os 18 testes fornecidos passaram e ficam separados por sobreposição de cobertura. Sete defeitos anteriores passaram no recorte exercitado; N05 teve o eco da resposta corrigido, mas o termo clínico da URL permanece no log padrão. Não foi constatado acesso de terceiros. Parecer: não pronto para integração desta candidata até corrigir o log e concluir alinhamentos/publicação e validação com frontend. Recursos exclusivos removidos, originais e ambientes existentes preservados. Relatório finalizado em 26/11, sem novos testes funcionais nessa data.
