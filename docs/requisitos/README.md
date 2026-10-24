# Requisitos do sistema — detalhamento clínico

**Revisão:** 23/10/2026. **Área:** `chore/sprint-07-docker-integration`, base `ab129d7`, com alterações Docker ainda sem commit.

Os IDs vêm do [catálogo geral](../requirements.md); esta revisão os preserva. Cada RF possui arquivo próprio. As regras estão em [regras de negócio](../regras-de-negocio/README.md).

| Requisito | Situação |
|---|---|
| [RF-023 — Consultar prontuários clínicos](RF-023-prontuario-do-paciente.md) | Implementação parcial; refinamento de fluxo e acesso para revisão |
| [RF-024 — Registrar evoluções clínicas](RF-024-evolucoes-clinicas.md) | Implementação parcial; correções e preservação de autoria pendentes |
| [RF-025 — Resumos de apoio por IA](RF-025-resumo-clinico-por-ia.md) | Proposta de produto, sem implementação nem inclusão automática na entrega de sábado |

## Diretrizes e evidências

**Definido por Paulo nesta conversa:** o prontuário acompanha o paciente; diferentes dentistas podem atendê-lo; cada evolução identifica seu responsável. Não haverá associação permanente e exclusiva paciente–dentista para representar o prontuário. O cadastro e a Agenda mantêm suas próprias permissões.

**Proposta discutida, ainda para aprovação operacional:** painel com atendimentos do dia; tela que reúne histórico e rascunho do atendimento; resumo de apoio por IA quando disponível. A ausência de vínculo exclusivo não concede, por si só, leitura a todos os profissionais. As decisões abaixo continuam abertas.

**Implementação encontrada:** API e tela de prontuário/evoluções existem, com autoria obtida da sessão e bloqueio de edição comum após finalização. Há falhas de validação de conteúdo/agendamento e acesso amplo a rascunhos. O número cadastral do paciente não representa, sozinho, a existência de prontuário clínico (RN-015).

**Validação executada:** Docker, login e recuperação de 50 pacientes após reinício foram demonstrados; isso não é aceite clínico. Em ensaio isolado do serviço com SQLite em memória, descrição vazia foi finalizada, uma consulta cancelada de outro paciente/dentista foi aceita e outro dentista da clínica leu o rascunho. Esses casos ainda precisam integrar os testes HTTP em PostgreSQL. Ver [registro da integração](../sprint/sprint-07-docker-integration.md).

## Decisões abertas antes da implementação dependente

| Código local | Questão | Recomendação para discussão | Quem fecha |
|---|---|---|---|
| D01 | Quem lê o histórico finalizado e por quanto tempo? | Definir política para dentistas da mesma clínica, admitindo continuidade por outro profissional sem vínculo exclusivo. | Paulo, equipe e professor |
| D02 | Quem abre o prontuário e quando? | Leitura sem criação; abertura explícita autorizada, com resposta consistente para registro existente. | Paulo/equipe; backend fecha contrato HTTP |
| D03 | Quais estados autorizam leitura, rascunho e finalização? Como registrar atendimento avulso? | Separar preparação, registro durante o atendimento e confirmação do que foi realizado; definir evidência e horário do atendimento. | Paulo, equipe e professor |
| D04 | Quais campos são obrigatórios? Pode registrar por outro profissional? | Descrição não vazia ao finalizar; procedimento opcional quando não realizado; cada profissional registra sua própria atuação neste MVP. | Paulo, equipe e professor |
| D05 | Quando preservar nome/CRO e quem retifica? | Cópia histórica identificada; retificação vinculada ao original com motivo e autoria. | Equipe/professor; DBA avalia dados e esquema |
| D06 | Como obter acesso quando o paciente está inativo ou deixa de ter consultas com o profissional? | Preservar histórico e definir autorização específica; não deduzir exclusão ou acesso irrestrito. | Paulo, equipe e professor |
| D07 | A IA entra nesta entrega? Quais dados, processamento e atualização são autorizados? | Tratar RF-025 como incremento após o núcleo; definir origem dos dados, atualização e revisão humana antes de integrar. | Gestor/equipe/professor, com revisão técnica |

Esses códigos D identificam questões locais de decisão, não novos requisitos nem regras aprovadas. A privacidade de rascunhos, o contrato de abertura e a retificação estão especificados como propostas; as decisões clínicas dependem do fechamento acima.

## Impactos e redefinições necessárias

| Parte existente | Alteração ou revisão esperada |
|---|---|
| RF-023 / RN-031 | Atualizar acesso e abertura; comprovar autorização por ação sem criar um dono exclusivo do prontuário. |
| RF-024 / RN-032 | Validar entradas, preservar autoria e garantir transações e finalização diante de concorrência. |
| RF-012 | Refinar painel do dentista para consultas do dia; hoje o painel conta pacientes da clínica inteira. Definir o recorte antes de chamar a lista de “meus pacientes”. |
| RF-017, RF-022 / RN-021, RN-024, RN-025 | Rever o momento em que a consulta libera leitura, rascunho e finalização. Hoje a tela só oferece “Registrar evolução” após `COMPLETED`. |
| RF-025 / RN-033 | Detalhar resumo de apoio e dependências; ainda sem serviço, modelo de IA ou processamento escolhido. |
| RF-026 / RN-034 | Definir eventos e leitura autorizada do histórico de operações, preservando sigilo do conteúdo clínico. |
| API e interface | Trocar o GET que cria dados exige mudança coordenada em `recordsApi.getOrOpen`; ajustar botões, erros e recuperação do rascunho. |
| Banco / ORM | Avaliar cópia histórica de nome/CRO, momento real do atendimento e vínculo de retificação. Preservar um prontuário por paciente. |
| Banco existente | O DBA deve inspecionar e preparar atualização reproduzível; editar `schema.sql` não atualiza volumes existentes. Não preencher CRO antigo como comprovadamente histórico sem evidência. |
| Unicidade de evolução por consulta | A regra atual permite no máximo uma evolução por consulta. Retificação precisa de modelagem que preserve essa regra ou de revisão explícita dela. |

## Encaminhamento

Paulo fecha as decisões com equipe/professor; backend define contrato e validações; DBA avalia integridade e atualização de bancos existentes; frontend ajusta o fluxo; João executa a matriz de perfis, clínicas, estados e concorrência no PostgreSQL. A atribuição aqui é um repasse técnico, não comunicação automática aos responsáveis.

O escopo atual é prontuário/evoluções do MVP acadêmico. Anamnese, odontograma, anexos e consentimentos não são declarados entregues por estes documentos. Para a referência profissional mais ampla, consultar o [manual e modelos do CFO](https://website.cfo.org.br/modelos-de-prontuarios/).
