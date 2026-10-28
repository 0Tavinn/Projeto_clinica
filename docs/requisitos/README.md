# Requisitos do sistema — detalhamento clínico

**Revisão:** 24/10/2026. **Área:** `chore/sprint-07-docker-integration`, base atual `9b26c81`. Docker já está incorporado a esse commit; as alterações documentais locais ainda não têm commit.

Os IDs vêm do [catálogo geral](../requirements.md); esta revisão os preserva. Cada RF possui arquivo próprio. As regras estão em [regras de negócio](../regras-de-negocio/README.md).

| Requisito | Situação |
|---|---|
| [RF-023 — Consultar prontuários clínicos](RF-023-prontuario-do-paciente.md) | Concessão e permanência da leitura aprovadas por Paulo em 24/10; autorização persistente ainda não implementada. |
| [RF-024 — Registrar evoluções clínicas](RF-024-evolucoes-clinicas.md) | Implementação parcial; correções e preservação de autoria pendentes |
| [RF-025 — Resumos de apoio por IA](RF-025-resumo-clinico-por-ia.md) | Proposta de produto, sem implementação nem inclusão automática na entrega de sábado |

## Diretrizes e evidências

**Definido por Paulo nesta conversa:** o prontuário acompanha o paciente; diferentes dentistas podem atendê-lo; cada evolução identifica seu responsável. Não haverá associação permanente e exclusiva paciente–dentista para representar o prontuário. O cadastro e a Agenda mantêm suas próprias permissões.

**Política de leitura aprovada em 24/10:** a confirmação de uma consulta pela operação autorizada da Agenda concede acesso ao dentista responsável pelo paciente na mesma clínica, e a concessão permanece após conclusão, ausência ou cancelamento posteriores. Rascunhos continuam privados ao autor. A aprovação foi dada por Paulo neste fluxo; não comprova implementação ou testes. Painel com atendimentos do dia, abertura do prontuário, condições de escrita e resumo de apoio por IA conservam as pendências próprias. A ausência de vínculo exclusivo não concede, por si só, leitura a todos os profissionais.

**Implementação encontrada:** API e tela de prontuário/evoluções existem, com autoria obtida da sessão e bloqueio de edição comum após finalização. Há falhas de validação de conteúdo/agendamento e acesso amplo a rascunhos. O número cadastral do paciente não representa, sozinho, a existência de prontuário clínico (RN-015).

**Validação executada:** Docker, login e recuperação de 50 pacientes após reinício foram demonstrados; isso não é aceite clínico. Em ensaio isolado do serviço com SQLite em memória, descrição vazia foi finalizada, uma consulta cancelada de outro paciente/dentista foi aceita e outro dentista da clínica leu o rascunho. Esses casos ainda precisam integrar os testes HTTP em PostgreSQL. Ver [registro da integração](../sprint/sprint-07-docker-integration.md).

## Decisões parcialmente fechadas e pendentes

| Código local | Situação e objeto | Próxima ação | Responsabilidade pela aprovação |
|---|---|---|---|
| D01 | Concessão por confirmação e permanência da leitura aprovadas por Paulo em 24/10; implementação, persistência, legado e alteração dos participantes ainda pendentes de desenho. | Propor mecanismo persistente e atômico, tratamento de consultas antigas e de mudanças posteriores de paciente ou dentista, sem deduzir concessão pelo estado atual isolado. | Paulo aprovou a política; DBA e backend propõem o desenho técnico. |
| D02 | Abertura do prontuário e consulta sem criação ainda não decididas. | Definir quem abre, quando e o contrato HTTP/frontend para prontuário inexistente. | Paulo decide; backend e frontend detalham o contrato. |
| D03 | Estados para criar rascunho e finalizar, momento do atendimento e atendimento avulso ainda não decididos. | Separar a leitura duradoura das condições para registrar um atendimento específico. | Paulo decide; backend e DBA avaliam impactos. |
| D04 | Conteúdo mínimo e registro em nome de outro profissional ainda não decididos. | Avaliar descrição não vazia na finalização, procedimento opcional e autoria própria. | Paulo decide; backend define validações após a decisão. |
| D05 | Momento da cópia de nome/CRO, dados antigos e retificação ainda não decididos. | Definir preservação histórica, vínculo com o original e responsabilidade pela retificação. | Paulo decide; DBA e backend avaliam o desenho. |
| D06 | Política clínica para paciente inativo ainda não decidida. | Definir leitura e escrita sem apagar histórico nem presumir acesso irrestrito. | Paulo decide; backend aplica a regra aprovada. |
| D07 | Escopo, fontes, revisão humana e processamento da IA ainda não decididos. | Tratar RF-025 como incremento futuro, sem declarar funcionalidade implementada. | Paulo decide o escopo; a equipe revisa a solução. |

Esses códigos D identificam decisões locais, não novos requisitos ou regras. D01 está parcialmente fechada quanto à concessão e à permanência da leitura; sua execução técnica continua pendente. A privacidade dos rascunhos segue RN-031. D02–D06 permanecem abertas nos pontos indicados, e a proposta de IA depende de D07. A aprovação das decisões de produto neste fluxo cabe a Paulo; contribuições técnicas ou acadêmicas podem orientar revisões posteriores.

## Impactos e redefinições necessárias

| Parte existente | Alteração ou revisão esperada |
|---|---|
| RF-023 / RN-031 | Implementar a concessão persistente aprovada e comprovar autorização por ação, sem criar um dono exclusivo do prontuário; abertura segue D02. |
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

Paulo aprova as decisões de produto neste fluxo; backend define contrato e validações após as decisões pertinentes; DBA avalia integridade e atualização de bancos existentes; frontend ajusta o fluxo; João executa a matriz de perfis, clínicas, estados e concorrência no PostgreSQL. A atribuição aqui é um repasse técnico, não comunicação automática aos responsáveis.

O escopo atual é prontuário/evoluções do MVP acadêmico. Anamnese, odontograma, anexos e consentimentos não são declarados entregues por estes documentos. Para a referência profissional mais ampla, consultar o [manual e modelos do CFO](https://website.cfo.org.br/modelos-de-prontuarios/).
