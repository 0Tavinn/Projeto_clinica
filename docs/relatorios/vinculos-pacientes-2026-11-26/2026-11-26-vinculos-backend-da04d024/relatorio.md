# Backend — pacientes clínicos e vínculos

Data: 26/11/2026. Implementação e ensaio pelo Backend; revisão independente de QA ainda pendente.

## Identidade da revisão

- Checkout exclusivo: /home/paulinho/Work/Projeto_clinica.
- Branch: fix/prontuario-correcoes-qa.
- HEAD de referência: 67068ac969cb7b34396b5d94e4ee09a7001ef8b4.
- Entrega funcional LOCAL, sem commit: nove arquivos rastreados modificados e seis novos.
- Fonte ativa: lumina_odonto/. Não houve uso de backend/ como fonte nem integração de outro checkout.
- Imagem final ensaiada: sha256:25b497084577a0d394332f7b5f5a54e19d6984adf4fe2d64f567bc8a50dfb6dd, depois removida pela limpeza própria.
- source-after.json identifica os31 arquivos lógicos da fonte. SHA256 canônico do JSON ordenado e compacto: 95fb2b8e2fd21f7a5a9e125fcbb7aaeb110e74d610eb150f3a4bb7f8d33bfcd7. SHA256 dos bytes do próprio arquivo JSON: 41dac68bcfefe98cf42227fb614e3d93f7528ca19e113a0ab1596ee200f52eca.
- Na retomada, os31 arquivos foram comparados novamente: nenhuma diferença nem arquivo adicional na fonte. Nenhuma mudança funcional ou documental posterior ao manifesto associado ao ensaio final foi encontrada. A construção usou o Dockerfile e o contexto dessa fonte; não foi feita nova execução dos testes na retomada.
- final-file-hashes.json inclui também o README documental externo à fonte; local-complete.patch inclui os15 arquivos, inclusive os novos. Identificadores adicionais em resume-verification.json.

## O que já existia e foi mantido

clinical_access_links e eventos persistentes, POST /api/v1/admin/access para conceder/revogar/reativar e GET administrativo de vínculos/eventos já existiam. Novo agendamento concede/reativa; cancelamento, ausência e conclusão não retiram o vínculo. Revogação preserva prontuário, evoluções e histórico. Alterar consulta antiga não reabre acesso revogado.

Não foram criadas mutações duplicadas, DDL ou migração. O schema existente foi suficiente. O provisionamento de schema.sql ocorreu somente no PostgreSQL descartável recém-criado. Não houve alteração de frontend, RF/RN, regras clínicas, recuperação de senha ou impressão.

## Contratos acrescentados

| Operação | Autorização/entrada | Resposta e restrição |
|---|---|---|
| GET /api/v1/clinical/patients | clinical_token do próprio dentista; limit1–100 padrão50; after_id>=0 padrão0; q opcional1–128 caracteres com conteúdo após trim | 200, objeto items/limit/next_after_id; somente pacientes ativos vinculados na clínica. |
| GET /api/v1/clinical/patients/{patient_id} | Mesmo token; patient_id inteiro positivo | 200, identificação mínima; nova verificação de vínculo no servidor. |
| GET /api/v1/access-links | access_token de ADMIN; filtros existentes patient_id/dentist_id, limit/offset preservados | Mesmo array e campos anteriores, enriquecidos com nomes e situação dos participantes. |

Cada item clínico tem exatamente cinco campos: patient_id, full_name, medical_record_number, medical_record_id e access_link_id. medical_record_id pode ser null no legado sem prontuário. Nenhuma dessas leituras cria prontuário. Incluem vínculos administrativos sem consulta/evolução. Não expõem CPF, contatos, notas, rascunhos ou credenciais.

q usa ILIKE por parte do nome/número; caixa é ignorada, acentos não são normalizados. %, _ e ! recebem escape literal. O filtro sem q foi exercitado no PostgreSQL; CAST explícito de search para TEXT evita ambiguidade do parâmetro NULL.

A paginação ordena patient_id crescente e usa limit+1 candidatos. next_after_id é o último candidato examinado quando há outro candidato. Revogação concorrente pode produzir página menor/vazia com cursor: continuar até null, sem total global ou snapshot estável entre páginas. dentist_id não é um seletor aceito dessas novas rotas; o profissional vem da identidade autenticada.

A leitura administrativa acrescenta patient_full_name, patient_medical_record_number, patient_is_active, dentist_full_name, dentist_is_active, dentist_user_id, dentist_cro_number e dentist_cro_state. Inclui inativos/revogados para identificação e revogação. dentist_is_active representa o usuário profissional. Os nomes/CRO são atuais, sem fotografia histórica. Concessão/reativação de inativos permanece recusada; recepção não administra vínculos. GET /dentists continua incluindo inativos com flag.

Erros preservam o envelope detail existente, sem eco clínico: 401 token/sessão inválida, 403 inelegibilidade/vínculo/profissional, 404 nos contextos de paciente indisponível definidos pelo helper existente e422 parâmetros inválidos. Sem modificação dos contratos anteriores de prontuário/evolução.

## Organização, concorrência e logging

Os quatro módulos clinical_patients separam rotas, DTOs, consulta/bloqueios e serviço. main.py apenas instala as rotas antes da política de logs; crud.py reaproveita a consulta administrativa enriquecida.

As leituras bloqueiam pacientes em ordem crescente e depois vínculos com FOR SHARE, seguindo patient -> link de change_link. Após a espera, novas consultas em READ COMMITTED conferem autorização e elegibilidade. Não reutilizam a projeção identificadora de antes do bloqueio. No detalhe, a autenticação clínica ocorre na dependency; get_patient resolve o dentista e chama allowed antes dos bloqueios e novamente após a espera. A lista reconfere usuário/sessão/clínica/profissional e projeta novamente só vínculos ativos. Fechar a sessão da dependency encerra a transação; não há commit/escrita nova nem locks mantidos durante navegação.

A revogação concorrente foi sincronizada por bloqueio real observado em pg_stat_activity. A prova usa HTTP para leitura e change_link de produção na conexão independente que detém o bloqueio. Não se afirma que duas chamadas HTTP concorrentes de revogação foram executadas. Proteção demonstrada para essa ordem de locks e isolamento; não se promete congelar todas as mudanças futuras de identidade ou recolher bytes enviados.

Uma falha de identificação operacional foi encontrada nos testes: FastAPI0.165.0 não expunha as rotas incluídas no snapshot anterior do logger; quatro casos exibiam [unmatched]. Não foi observado vazamento nessa falha. logging_policy.py agora complementa rotas diretas pelos caminhos públicos de app.openapi() e os compila com starlette.routing.compile_path. A remoção de query/IDs/args/exceções continua vigente. Não se usaram atributos privados nem se relaxaram os testes. Proxy/coletor/SQL echo externos não foram fornecidos nem validados.

## Resultados efetivamente executados

Ambiente Docker exclusivo, Python3.12.16, PostgreSQL imagem postgres:16, FastAPI0.165.0, Uvicorn0.54.0, SQLAlchemy2.1.9, psycopg3.3.9, Pydantic2.14.4, pytest9.2.0. Bibliotecas/dispositivo em versions.json. A versão menor do servidor PostgreSQL não foi capturada neste runner; não atribuir uma versão menor de ensaios históricos.

| Evidência final | Resultado | Limite |
|---|---|---|
| tests.log: python -m pytest -q --disable-warnings --tb=short | 32 passed,1 warning,1.87s | Suíte distribuída e novos testes de contrato/logging; contagem separada do HTTP. |
| http-results.json/probe_access.py | 66 verificações aprovadas, nenhuma reprovada | HTTP real Uvicorn e SQL independente; não navegador. |
| privacy-log-check.json e api-sanitized.log | Todos os nove indicadores verdadeiros | Rotas estáticas corretas, sentinelas ausentes,401/403/422 e ausência de traceback nos caminhos exercitados. |
| resume-verification.json | Hashes31/31, AST dos Python alterados, links relativos e git diff --check aprovados | Conferência de retomada; não é nova rodada de testes. |
| cleanup.json e inventários | Recursos próprios removidos; inventário anterior/final igual | Somente recursos criados e rotulados pelo ensaio. |

HTTP/SQL cobriu vínculo manual e prontuário vazio; dados mínimos; paginação/busca com e sem q; limites inválidos; clínica/dentista alheios e IDs adivinhados; revogação; usuários/pacientes/clínica inativos; falta de profissional; tokens ausentes/errados/expirados/perfis indevidos; gestão de inativos com evento/auditoria; recusa de concessão/reativação; arrays antigos; cancelamento preservando vínculo e atualização antiga sem reabertura.

Concorrência: espera real seguida de revogação deixou a lista sem o paciente e com cursor válido; detalhe403; página seguinte alcançou o candidato remanescente. Invalidação da sessão durante a espera retornou401. IDs e wait_event_type=Lock estão no JSON, sem conteúdo clínico real.

Tentativas preservadas: attempt-1 foi interrompida por NameError no auxiliar (Path não importado), sem resultado final aprovado. attempt-2 produziu66 verificações HTTP e4 falhas/28 aprovações de testes de logging; a política foi corrigida antes da rodada final. Não somar tentativas como novas aprovações. Os32 testes não equivalem a reexecutar a antiga matriz independente de74 casos. Não houve novo benchmark nem teste SQLite nesta entrega.

## Preservação e reprodução

preservation.json registra HEAD/índice intactos e vazio no stage;40 arquivos do original externo,22 do pacote N05 corrigido e114 artefatos de QA preservados; checkout alternativo e recursos preexistentes iguais ao inventário anterior. O índice tem SHA256 d475703f26f13c8e1f6b915f5ba422be3054eb53e97ccd9615818beeeca0abcd para git ls-files --stage -z. Nenhum commit, push, merge, implantação, restart ou alteração de banco existente.

Os recursos temporários tinham prefixo lumina-links-56e432f28d8f, rede/volume/imagem exclusivos, três contêineres, rótulo de propriedade e nenhuma porta publicada. Todos removidos. O ambiente lumina_pr18_tarcisio e ambientes históricos foram preservados.

O comando completo de repetição está em reproducao.md. Ele confere branch/HEAD/hashes e copia apenas os dois auxiliares para NOVA pasta de evidências; verify_candidate.py constrói a fonte, provisiona banco descartável, executa CMD original sem override, roda HTTP/testes e limpa por propriedade. Não executar o runner nesta pasta histórica, pois seus arquivos de saída seriam sobrescritos. Dependências com faixas abertas podem produzir versões diferentes no próximo build.

A explicação do manifesto antigo agora confere os blobs do commit21cefa608327fa157938308a4c9e16fbfa3a6eb4;22 arquivos históricos foram conferidos. O parecer N05 antigo não é transferido automaticamente à revisão funcional nova.

## Arquivos criados ou alterados

- /home/paulinho/Work/Projeto_clinica/docs/relatorios/prontuario-correcoes-qa-2026-11-26/README.md
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/FRONTEND.md
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/README.md
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/app/clinical_patients.py
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/app/clinical_patients_repository.py
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/app/clinical_patients_schemas.py
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/app/clinical_patients_service.py
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/app/crud.py
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/app/logging_policy.py
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/app/main.py
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/docs/frontend/authentication-and-search.md
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/docs/frontend/clinical-patients-and-links.md
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/docs/frontend/records-and-evolutions.md
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/tests/test_clinical_patients.py
- /home/paulinho/Work/Projeto_clinica/lumina_odonto/tests/test_logging_policy.py

## Repasse e limites

Frontend: consumir o clinical_token, paginação por cursor e os cinco campos mínimos; usar detalhe para cabeçalho; não interpretar flags administrativas como autorização de conceder. Guias atualizados em lumina_odonto/docs/frontend/. O frontend não foi alterado nem validado no navegador.

DBA: sem DDL/migração nova; a entrega depende do schema de vínculos existente da API avulsa. Não foi ensaiada migração do backend diário para esse schema. Compatibilidade de dados anômalos/corrompidos fora das constraints não foi prometida.

QA independente: conferir HEAD + final-file-hashes.json/local-complete.patch, executar reproducao.md em recursos próprios, repetir isolamento/tokens/gestão de inativos, cursores após revogação, espera real de lista/detalhe e N05 nas rotas novas. Comparar versões de dependências e registrar novos resultados sem sobrescrever os atuais. A integração/implantação diária e aceite global continuam pendentes.

Conclusão: implementação mínima concluída e exercitada pelo Backend na fonte local identificada, pronta para revisão do Tech Lead e reteste independente de QA. Sem aprovação independente desta revisão, publicação ou aceite integral da Sprint.

## Reconciliação documental — 26/11/2026

Uma orientação intermediária do Tech Lead levou à descrição incorreta de uma única chamada de allowed no detalhe. A reconferência do QA e a leitura da fonte final congelada confirmaram duas chamadas, uma antes e outra depois de lock_patients_and_links. O arquivo clinical_patients_service.py mantém SHA256 52b2de0a70f08482ec3187dca765f101957caef47232c7e88e5241b169caaf55. A descrição acima foi reconciliada com essa fonte; a observação histórica do QA permanece preservada. Foram alterados somente este relatório externo e seu hash no manifesto documental, sem mudança nos31 arquivos, guias ou testes e sem nova execução de testes.
