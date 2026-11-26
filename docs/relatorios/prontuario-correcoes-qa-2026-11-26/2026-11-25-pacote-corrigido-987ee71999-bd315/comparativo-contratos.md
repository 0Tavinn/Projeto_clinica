# Comparativo de contratos — pacote corrigido

Finalizado em 26/11/2026. Resultados funcionais executados em 25/11/2026 pelo AGENTE DE QA.
Fonte: manifesto 987ee7199972977bc549346246d0ee5bf46d4611b9d15c3c8fc89fdfbd41fe40, sem Git.
Comparação: app da subpasta lumina_odonto/ em 4ccdc30a27143b6c022b7f8cae2e6ccf03860389.

| Aspecto | Referência publicada anterior | Pacote ensaiado | Efeito/decisão |
|---|---|---|---|
| Busca por paciente | patient_id não declarado; parâmetro era ignorado | patient_id obrigatório epositivo; filtro de um paciente | Corrige escopo solicitado; frontend deve enviar o ID. Contrato candidato a alinhar. |
| Paginação da busca | Limite/truncamento sem navegação demonstrada | offset>=0, candidate_limit1000, next_offset; total por página de resultados | Consumidor deve percorrer candidatos; total não significa total global. Página vazia pode ter next_offset. |
| Termo inválido | Normalização vazia gerava CPU 200/OpenCL 503 | Ausente/vazio/espaços/U+0301 recebem 422 nos 3 motores | Recusa consistente comprovada; código 422 proposto pelo pacote, sem decisão nova inventada. |
| Orçamento | Cobertura anterior insuficiente | Limite normalizado UTF8 de 2.000.000 bytes por página; acima 413 | Limite2.000.000 aceito e2.000.004 recusado; contrato/UX a alinhar. |
| Versão de evolução | int com coerção de texto | Inteiro estrito positivo emPATCH/finalize | Texto/bool/null/zero/negativo/ausente 422; versão velha 409; frontend deve enviar número JSON atual. |
| Erro 422 | Padrão ecoava input clínico | detail com loc permitida, mensagem genérica evalidation_error; sem input/ctx | Revalidado em 5 entradas equery; consumidor deve tratar o envelope. Access log ainda registra q. |
| Agenda | scheduled_period do banco chegava ao DTO e causava 500 | Campo interno removido; casts de filtros opcionais | CRUD/lista/filtros exercitados com 201/200 e estado coerente. scheduled_period não é DTO público proposto. |
| Atualização de usuário | Risco de devolver campos internos da linha | Resposta sem hashes eversões de sessão | HTTP 200 verificado eforbidden_keys vazio. |
| Revogação administrativa | Elegibilidade ativa bloqueava revogação | Revogação aceita alvos inativos/sem senha clínica da mesma clínica | Não concede automaticamente elegibilidade paraGRANTED/REACTIVATED. |
| Autorização da busca | Não revalidava depois do processamento | Lock/rechecagem antes de selecionar eantes de devolver; rollback libera durante cálculo | Revogação emespera edurante kernel real resultou 403. |
| Provisionamento | Subpasta publicada não continha os caminhos de.env/schema/seed | Pacote traz esses arquivos ebuild passa | Corrige o pacote recebido; Git antigo continua inalterado. Não comprova upgrade. |

## OpenAPI e limites

openapi-baseline.json eopenapi-candidate.json foram gerados por importação das duas fontes em processos isolados da imagem de QA, sem escrita em banco. A diferença estrutural de operações encontrada foi GET /api/v1/clinical/search, com patient_id obrigatório eoffset. openapi-differences.json guarda os parâmetros antes/depois.

A igualdade de outras operações no OpenAPI não prova igualdade de comportamento: coerção estrita, sanitização da resposta, campos dinâmicos eautorização precisam da fonte/das sondagens. Não foi comparado o esquema de um servidor diário com fonte diferente.

## Integração e aprovações

Este serviço avulso usa login JSON, token clínico separado e/api/v1/evolutions. O backend/ herdado efrontends deoutros checkouts não foram substituídos. Esta rodada não comprova compatibilidade com as chamadas efetivas da interface.
Antes de integrar, Backend/Frontend/Paulo precisam alinhar transporte da busca, paginação, códigos 422/413, envelope de erro, version eestratégia de transição. O QA verificou implementação econtratos propostos; estabelecer critérios clínicos continua responsabilidade de Paulo/TechLead.
