# Lumina Odonto — Relatório Parcial da Reunião de 29/10/2026

**Fonte:** relato de Paulo Sérgio sobre a reunião de 29/10/2026. **Registro sujeito à revisão da equipe.**

**Natureza do documento:** registro parcial de encaminhamentos e propostas discutidas em 29/10/2026. Decisões posteriores poderão complementá-lo ou revisá-lo. Este texto não registra lista de presença, aprovação coletiva, implementação ou resultado de testes.

## 1. Objetivo e prioridade

A reunião tratou dos refinamentos necessários para finalizar o Lumina Odonto. A prioridade apresentada foi consolidar o fluxo de consultas e prontuários utilizado pelo dentista. Cada integrante deve acompanhar suas responsabilidades em frontend, backend, banco de dados, testes e documentação. Problemas encontrados devem ser comunicados à equipe com informações suficientes para orientar a correção.

**Encaminhamento imediato registrado:** Luiz Otávio preparará o protótipo das seções **Prontuários**, **Consultas** e **Consultas realizadas**. O protótipo servirá para a equipe refinar regras e contratos antes dos ajustes correspondentes. O relato não fixa data individual de entrega.

## 2. Proposta funcional discutida

As seções abaixo descrevem a organização discutida para a área do dentista, além de dashboard, pacientes vinculados e agenda. Sua descrição não comprova implementação nem aprovação de regra técnica.

### 2.1 Prontuários

Foi proposta uma seção para consultar o histórico dos pacientes aos quais o dentista tenha acesso autorizado e registrar atualizações clínicas em texto.

Discutiu-se uma **segunda senha** para abrir essa área, além da senha principal de login. A intenção relatada é que uma autenticação adicional permita ao dentista consultar os prontuários já autorizados, sem uma senha diferente por paciente. Criação, recuperação, duração do acesso e momento de nova autenticação ainda exigem definição técnica. A senha adicional **não substitui** a verificação do vínculo e da autorização de acesso entre dentista e paciente.

O registro das atualizações clínicas também requer refinamento: é preciso distinguir novo registro, edição de rascunho e eventual retificação de informação finalizada. Nenhum desses detalhes foi definido como operação pronta nesta reunião.

### 2.2 Consultas

A seção **Consultas** foi discutida como área principal para acompanhar atendimentos agendados e confirmados. Ao selecionar uma consulta, a proposta é abrir uma janela com informações do paciente, acesso ao prontuário, opção de registrar atualização clínica, campo para descrever o atendimento realizado e informações de procedimentos e valores destinadas ao encaminhamento à recepção.

Uma tabela de preços foi mencionada como possibilidade. Seu funcionamento, abrangência e manutenção não foram definidos.

**Fluxo proposto para refinamento:**

1. O dentista seleciona a consulta e consulta as informações do paciente e o prontuário.
2. Registra uma atualização clínica quando aplicável e informa o que foi realizado e os valores pertinentes.
3. Confirma a conclusão do atendimento.
4. O sistema registra a consulta como finalizada, salva as informações correspondentes e disponibiliza à recepção os dados necessários para cobrança e registro do pagamento.

A atualização do prontuário foi descrita como **opcional na proposta**. A equipe ainda precisa confirmar essa condição e definir o conteúdo mínimo para finalizar um atendimento. A conclusão clínica **não confirma automaticamente o pagamento**: a recepção tratará a cobrança e o registro do pagamento. Os estados da Agenda, as operações da API, as informações compartilhadas com a recepção e o tratamento de falhas permanecem sujeitos a alinhamento.

### 2.3 Consultas realizadas

Foi proposta uma seção de histórico dos atendimentos concluídos pelo dentista, com visão geral dos pacientes atendidos e do que foi realizado em cada consulta. Os campos exibidos, os detalhes acessíveis, a pesquisa e os filtros ainda precisam ser refinados.

## 3. Encaminhamentos e responsabilidades registrados

| Responsável mencionado no relato | Encaminhamento registrado | Situação |
| --- | --- | --- |
| Luiz Otávio | Preparar o protótipo das três seções: Prontuários, Consultas e Consultas realizadas. | **Encaminhamento imediato definido no relato.** |
| Caio Cesar | Participar da elaboração do frontend com Otávio, a partir do protótipo e dos contratos alinhados. | Participação prevista; implementação depende do alinhamento. |
| Paulo Sérgio — backend e banco de dados | Avaliar os requisitos apresentados no protótipo e preparar contratos de API e ajustes de banco necessários após esclarecer as regras pendentes com a equipe. | Encaminhamento condicionado ao refinamento das regras. |
| Tarcísio | Apresentar contribuição sobre a padronização do que será desenvolvido. | Pendente esclarecer objeto e resultado esperado dessa padronização. |
| João Vitor | Continuar os testes, registrar resultados e comunicar falhas e bloqueios à equipe. | Continuidade dos testes; este relato não traz novos resultados. |
| Cassiano Augusto | Continuar a documentação e incorporar este registro parcial, separando propostas, implementações e resultados demonstrados. | Continuidade da documentação. |
| Toda a equipe | Revisar sua parte, comunicar problemas e alinhar alterações que afetem outras áreas. | Orientação geral registrada. |

O relato não informa prazos individuais nem confirma conclusões dessas atividades.

## 4. Próximos passos registrados

1. Otávio prepara os protótipos das três seções.
2. A equipe revisa os protótipos e esclarece as regras pendentes.
3. Paulo, Caio e Otávio alinham os dados, as operações e os estados necessários à integração.
4. Backend, banco de dados e frontend executam os ajustes que forem acordados.
5. João testa as funcionalidades disponíveis e registra as evidências.
6. Cassiano atualiza a documentação conforme os resultados efetivamente demonstrados.

A preparação do protótipo pode ocorrer enquanto os testes e a documentação da versão atual continuam. A entrega em que as novas mudanças entrarão e seu impacto no fechamento pendente da Sprint 7 ainda precisam ser definidos.

## 5. Perguntas pendentes para refinamento

1. Como funcionará a segunda senha: criação, recuperação, duração do acesso e novas solicitações de autenticação?
2. Quais critérios vinculam paciente e dentista e autorizam a leitura do histórico?
3. Como serão preservadas e, se necessário, retificadas as informações clínicas finalizadas?
4. Quando a atualização clínica será opcional e qual conteúdo mínimo será exigido para concluir a consulta?
5. Quais situações da Agenda permitem iniciar e finalizar o atendimento?
6. Como procedimentos e preços serão cadastrados, selecionados e alterados? Haverá tabela de preços?
7. Quais dados de cobrança a recepção receberá, mantendo separado o conteúdo clínico?
8. Como o pagamento será registrado e acompanhado pela recepção?
9. Como serão tratadas falhas ao salvar ou finalizar o atendimento?
10. O que Tarcísio deverá padronizar e qual resultado se espera?
11. Em qual entrega entrarão essas mudanças e como afetarão o fechamento pendente da Sprint 7?
