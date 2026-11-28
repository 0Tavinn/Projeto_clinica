# QA independente — pacientes clínicos e vínculos

**Pronto com ressalvas para integrar estas novas rotas em ambiente de teste.** Não foi reproduzido defeito de produto no recorte executado. A conclusão vale para a fonte local identificada abaixo; não é aceite de frontend, implantação ou Sprint.

**Executor:** agente de QA. **Data:** 26/11/2026. Janela documentada de identificação até limpeza: aproximadamente 10:35–10:43, America/Sao_Paulo, incluindo preparo e uma tentativa interrompida do auxiliar.

## Versão efetivamente testada

| Campo | Identificação |
|---|---|
| Fonte exclusiva | /home/paulinho/Work/Projeto_clinica/lumina_odonto |
| Branch | fix/prontuario-correcoes-qa |
| HEAD de referência | 67068ac969cb7b34396b5d94e4ee09a7001ef8b4 |
| Estado | **Alterações locais, sem commit; índice vazio** |
| Manifesto canônico dos 31 arquivos | **95fb2b8e2fd21f7a5a9e125fcbb7aaeb110e74d610eb150f3a4bb7f8d33bfcd7** |
| Imagem efetivamente usada | sha256:21e602ec72e70b83c71d9a3d5727e7025b7f14d0fd30521077dafd05b617c6b5 |
| Origem das alterações | Implementação local do agente de Backend, conforme repasse do Tech Lead |
| Guia consultado | lumina_odonto/docs/frontend/clinical-patients-and-links.md |
| Evidências desta rodada | /home/paulinho/Work/lumina-qa-evidence/2026-11-26-vinculos-qa-3a6efdc8da |

O HEAD isoladamente **não representa a funcionalidade ensaiada**: a versão é HEAD mais o diff local e o manifesto. Foram encontrados nove arquivos rastreados modificados e seis novos, incluindo o README de consolidação fora de lumina_odonto/. source-before.json e candidate-after.json identificam a fonte; local-complete.patch registra os 15 caminhos alterados, inclusive arquivos não rastreados. git-status-before.txt identifica quais são locais. Nenhum desses arquivos foi preparado no índice pelo QA.

Os 31 hashes conferiram com source-after.json do Backend antes do build e continuaram iguais depois. O manifesto é SHA256 do mapa de arquivos em JSON ordenado e compacto. Os pacotes avulsos de prontuário e N05 não foram usados como fonte funcional desta revisão.

## Ambiente e isolamento

- **PostgreSQL 16.16 (Debian 16.16-1.pgdg13+1)**, identificado por SHOW server_version no banco descartável.
- Python 3.12.16; FastAPI 0.165.0; Uvicorn 0.54.0; SQLAlchemy 2.1.9; psycopg 3.3.9; Pydantic 2.14.4; pytest 9.2.0; NumPy 2.5.5; PyOpenCL 2026.1.5.
- OpenCL real em CPU Intel i5-13420H, Portable Computing Language, OpenCL 3.0 PoCL, driver 6.0+debian.
- Docker cliente/servidor 29.9.3; Compose v5.7.0. Não foi iniciado o Compose recebido.
- Build com Dockerfile original e API Uvicorn HTTP real pelo CMD distribuído, sem --no-access-log ou instrumentação da aplicação.
- Banco final links_qa_3a6efdc8dar2, rede, volume e contêineres próprios. **Nenhuma porta publicada**.
- Dados fictícios: duas clínicas, admin de cada clínica, recepção, dois dentistas locais, dentista externo, usuário inativo, usuário sem cadastro profissional e profissional ativo sem senha clínica. Pacientes com vínculos administrativos, revogados, inativos, sem vínculo e legado sem prontuário.
- Cadastro de pacientes, concessões, revogações, agenda e leitura usaram HTTP. SQL direto preparou fixtures e controlou estados e bloqueios somente no banco QA. Nenhuma instalação no Python global WSL.

Build, versões e identidade: build-exact.log, versions.json, postgres-version.txt, image-identity.json, environment.json.

## Resultados desta execução

| Grupo | Aprovados | Reprovados | Bloqueados | Não executados no grupo |
|---|---:|---:|---:|---:|
| Verificações independentes HTTP/SQL | **58** | 0 | 0 | 0 |
| Asserções transversais sobre os mesmos logs | **20** | 0 | 0 | 0 |
| Comparação de contrato OpenAPI | **1** | 0 | 0 | 0 |
| Testes distribuídos atuais | **32** | 0 | 0 | 0 |

Os 32 testes concluíram sem skips, com um warning: 2 de contrato/autenticação das novas rotas, 12 de logging, 5 do motor OpenCL/CPU e 13 dos contratos anteriores. O warning não impediu os testes. A contagem foi obtida nesta execução, não herdada do Backend. Alguns tokens de QA foram assinados com o segredo efêmero para exercitar perfis inelegíveis, expiração e falta de cadastro; não são evidência de que a API emita esses tokens para tais perfis. Os dentistas elegíveis autenticaram e desbloquearam por HTTP.

As 20 asserções de logs analisam as requisições dos mesmos casos; não são 20 percursos adicionais. Os testes distribuídos se sobrepõem às verificações independentes. **Não somar essas linhas como cenários distintos.** A matriz tem 111 linhas, com grupos explícitos. Nenhuma das 74 sondagens antigas foi anunciada como repetida. Os 66 resultados HTTP/SQL informados pelo Backend e suas tentativas não entram nos totais do QA.

| Categoria dos 58 casos | Quantidade | Resultado exercitado | Evidência |
|---|---:|---|---|
| Lista, detalhe e identificação mínima | 12 | Só ativos vinculados do próprio dentista/clínica; cinco campos exatos; IDs adivinhados recusados; prontuário vazio e legado null | Casos L em http-results.json |
| Cursor, busca e parâmetros | 14 | Paginação crescente, sem duplicidade; nome/número; %, _ e ! literais; parâmetros inválidos422 | Casos P |
| Autenticação e elegibilidade | 11 | Duas rotas recusam tokens/perfis indevidos; usuário/clínica inativos; falta de cadastro profissional | Casos A |
| Administração e origem do vínculo | 13 | Array/campos anteriores preservados; nomes/flags; revogação de inativos; eventos/auditoria; agenda não reabre por atualização antiga | Casos M |
| Esperas concorrentes | 4 | Revogação e perda de sessão em lista/detalhe após lock real | Casos C |
| N05 e busca clínica anterior | 4 | DTO mínimo após existir rascunho; erro sem eco; busca antiga com OpenCL e autorização | Casos N |

A matriz CSV contém, por ID, pré-condição, ação, esperado, obtido, situação e caminho da evidência.

## Principais provas

**Identificação e privacidade.** A lista omitiu pacientes de outro dentista, outra clínica, revogados, inativos e sem vínculo. Detalhes de IDs adivinhados retornaram 403 sem identificação; paciente inativo retornou 404 no contexto autorizado. Lista e detalhe tiveram exatamente patient_id, full_name, medical_record_number, medical_record_id eaccess_link_id. CPF, contatos, general_notes, rascunhos e credenciais não fizeram parte do DTO, inclusive depois de existir uma evolução fictícia.

Um vínculo concedido administrativamente apareceu sem consulta ou evolução. Prontuário vazio foi retornado; legado sem prontuário teve medical_record_id=null na lista e no detalhe. A contagem de prontuários não mudou nessas leituras.

**Paginação e pesquisa.** limit padrão 50, cursor crescente e páginas sem duplicidade foram observados. A resposta teve apenas items, limit, next_after_id, sem total global. Busca por nome sem diferença de caixa e por número funcionou. %, _ e ! corresponderam literalmente, sem ampliar a consulta como curingas. limit 0/101/textual, after_id negativo, q vazio/espaços/maior que 128 receberam 422. Não se impôs offset, total global ou normalização de acentos que o contrato não promete.

**Administração.** GET /access-links permaneceu array, conservando campos anteriores e acrescentando nomes, flags e identificação profissional. Filtros patient_id/dentist_id e limit/offset continuaram operando. Recepção e dentista com access_token receberam 403; o admin externo ficou limitado à própria clínica e não pôde revogar vínculo alheio.

Paciente e dentista inativos foram identificados com flags corretas. A revogação retornou 200, persistiu REVOKED, acrescentou um evento e uma auditoria e manteve prontuário/evolução comparados. Concessão/reativação de inativos foi recusada 404/422. Concessão a profissional ativo sem senha clínica foi aceita conforme implementação atual; **isso é comportamento verificado, não nova aprovação de regra clínica**.

**Agenda.** Novo agendamento concedeu vínculo; cancelamento conservou acesso. Depois de revogar, atualizar e cancelar novamente a consulta antiga não reabriu o vínculo. Outro agendamento novo reativou o acesso. Isso não é teste do antigo fluxo de confirmação/conclusão clínica.

## Concorrência em PostgreSQL real

Foram usadas conexões independentes e requisições HTTP reais. A conexão controladora bloqueou o paciente; pg_stat_activity comprovou wait_event_type=Lock e wait_event=transactionid na leitura FOR SHARE antes da liberação. Não foi apenas uma espera por tempo.

| Caso | Operação confirmada antes de liberar | Obtido e estado |
|---|---|---|
| C01-revocation-list | change_link de produção, na transação SQL independente, revogou e confirmou | HTTP 200, items vazio, next_after_id avançou; página seguinte encontrou o paciente remanescente; vínculo REVOKED |
| C01-revocation-detail | Mesma ordenação de revogação | HTTP 403, sem identificação; vínculo REVOKED |
| C01-session-loss-list | Outra conexão confirmou incremento de session_version | HTTP 401, sem identificação |
| C01-session-loss-detail | Mesma invalidação | HTTP 401, sem identificação |

O PID 101 e os eventos de espera estão no JSON. As revogações concorrentes usaram a função de produção na conexão controladora: **não se afirma uma prova de duas chamadas HTTP simultâneas de revogação**. Eventos/auditoria por HTTP foram verificados nos casos administrativos separados.

A evidência demonstra essa ordem transacional; não promete snapshot estável entre páginas nem recolher bytes enviados antes de uma revogação posterior. Após perda de sessão foi feito novo login/desbloqueio para continuar as verificações restantes.

## N05 e contrato das rotas novas

Os stdout/stderr reais foram conferidos em memória antes de salvar extratos sanitizados. Nenhuma sentinela de query, nome, número, ID arbitrário, header ou token foi encontrada nos streams. Erros exercitados não ecoaram identificação. Os logs conservaram método, template e status:

~~~text
INFO:     - - "GET /api/v1/clinical/patients HTTP/1.1" 200 OK
INFO:     - - "GET /api/v1/clinical/patients/{patient_id} HTTP/1.1" 403 Forbidden
INFO:     - - "GET /api/v1/clinical/patients/{patient_id} HTTP/1.1" 401 Unauthorized
INFO:     - - "GET /api/v1/clinical/patients/{patient_id} HTTP/1.1" 422 Unprocessable Entity
~~~

As rotas conhecidas **não** foram aceitas como [unmatched]. privacy-log-check.json tem 20 indicadores verdadeiros. Não se desligou o access log por configuração de QA. Não se repetiu o erro 500 do reteste N05 anterior nem se transferiu sua prova para todas as novas rotas.

A busca clínica anterior respondeu200 em CPU e OpenCL real, com resultados iguais e engine=opencl; paciente sem autorização recebeu 403. Sem benchmark novo. O OpenAPI servido acrescentou exatamente as duas rotas clínicas, não removeu rotas e manteve iguais as operações anteriores ao compará-las com a referência N05QA identificada. Isso não equivale a teste de frontend.

## Tentativa interrompida e divergência documental

A primeira tentativa terminou antes de qualquer sondagem HTTP por ModuleNotFoundError:app no cliente de QA. Foram removidos seus recursos e preservados seus arquivos em attempt-1/. Corrigiu-se somente PYTHONPATH=/app:/qa no cliente. Também se corrigiu preventivamente o auxiliar noecho para ignorar token vazio antes de suas asserções serem exercitadas. Não houve correção da aplicação. Essa tentativa não é aprovação nem defeito de produto; as verificações falsas por ausência de requisições no log inicial não são falhas do logger.

A nota de coordenação sobre o detalhe e a descrição do relatório externo destacaram allowed após os locks. **No arquivo efetivamente congelado, get_patient contém uma chamada de allowed antes e outra depois de lock_patients_and_links.** Essa observação foi reconferida com o mesmo manifesto de 31 arquivos; a fonte não foi alterada. O relatório usa o código executado como evidência. A redação externa deve ser reconciliada com essa sequência, sem necessidade de inferir uma falha clínica. Ver source-reconciliation.json e app/clinical_patients_service.py.

O relatório externo do Backend estava sendo finalizado, e foi informada uma edição documental coordenada. Não se declara preservação byte a byte desse relatório durante sua redação. Os arquivos congelados identity/source-after e a aplicação conferiram; os relatórios históricos já concluídos permaneceram protegidos.

## Preservação, limpeza e limites

Fonte de 31 arquivos, pacote original com 40 arquivos incluindo metadados, pacote N05 externo com 22 arquivos e evidências históricas conferidas permaneceram iguais. Git HEAD, branch, status, alterações preparadas e saída de git ls-files --stage -z permaneceram iguais. O QA não fez add, stash, reset, switch, commit, push oumerge.

Foram removidos os recursos próprios de ambas as tentativas: **7 contêineres, 2 volumes, 2 redes e2 imagens/tags**. Rótulo e identidade foram conferidos antes de remover. Inventários de serviços preexistentes, imagens em uso, portas, inícios e reinícios permaneceram iguais. O Compose lumina_pr18_tarcisio e os ambientes históricos não foram usados para escrita, rebuild ou reinício. Não houve prune. Arquivos efêmeros de segredo removidos.

Evidências:preservation.json, attempt-1/preservation.json, cleanup.json, attempt-1/cleanup.json, git-before/after.json e inventory-before/after.json. A comparação de inventário não é checksum do banco diário; ele não foi alvo deste ensaio.

Continuam **não executados neste escopo**: navegador/frontend, implantação diária, upgrade/migrações, backup/restauração e regressão completa das74 provas antigas. D05/D06, exportação e outras decisões clínicas anteriores não foram decididas aqui. A política de logging não foi homologada para proxy, coletor, SQL echo, configurações externas ou futuras fontes de saída.

**Próximo passo:** publicar referência verificável das alterações locais, conferir o conteúdo publicado contra o manifesto e executar a integração com frontend identificado em ambiente de teste. Se o conteúdo mudar, avaliar o diff e repetir os casos afetados. Os resultados não devem ser atribuídos ao HEAD 67068ac sem seu diff.

Não foi criado PDF nem houve publicação externa. Não existem prints ou vídeos de navegador nesta rodada; as provas são saídas HTTP/SQL, JUnit, logs e metadados reais.
