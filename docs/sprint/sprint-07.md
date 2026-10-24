# Sprint 7 — Manutenção e Consolidação | Lumina Odonto

**Período de trabalho:** 19 a 24 de outubro de 2026  
**Prazo da disciplina:** 24/10/2026, às 23h59  
**Prioridade de 19/10:** reunir a versão atual do projeto e executá-la em Docker  
**Situação deste documento:** instruções de Paulo Sérgio para alinhamento e execução da equipe

## 1. Objetivo

Consolidar o Lumina Odonto por meio da correção dos defeitos encontrados após a Sprint 6 e da entrega demonstrável dos itens da Sprint 7: dashboard, relatórios, pesquisa, filtros, exportação quando aplicável e histórico de operações.

O dashboard de consultas será o destaque da Sprint. As melhorias deverão aproveitar Agenda, pacientes e prontuário já desenvolvidos. O foco desta semana é fazer o sistema integrado funcionar de forma consistente e apresentar evidências reais, usando dados fictícios.

## 2. Decisões e limites do trabalho

### 2.1 Integração e Docker primeiro

Nesta **segunda-feira, 19/10**, Luiz Otávio terá como primeira tarefa reunir a versão atual acordada pela equipe e preparar o ambiente Docker com **frontend React/Vite, API FastAPI e PostgreSQL**. O Compose presente na base consultada ainda usa MySQL e não contém o frontend; portanto, sua execução atual não comprova o ambiente desejado.

Otávio deverá começar com um banco descartável e dados fictícios, conferir as variáveis de ambiente, a comunicação entre serviços, o armazenamento persistente do PostgreSQL e a inicialização da API. O estado das migrações deve ser conferido antes de automatizar qualquer aplicação de esquema. Nenhum procedimento novo será executado em banco compartilhado sem a avaliação do responsável pelo banco.

**Resultado esperado hoje:** ambiente integrado executável e instruções curtas para reproduzi-lo, ou um bloqueio concreto informado a Paulo com o ponto de falha, evidência e próxima ação. A conclusão do Docker depende de iniciar os três serviços e exercitar um fluxo real, não apenas de os contêineres subirem.

### 2.2 Nome do projeto

Otávio verificará os nomes ainda antigos e padronizará a apresentação como **Lumina Odonto** na interface, API, configuração de ambiente e documentação afetada. O plano anterior recomenda `lumina-odonto` como nome do repositório GitHub. Se a mudança do repositório remoto fizer parte desta tarefa, Otávio alinhará o endereço com Paulo, fará a alteração caso tenha a permissão necessária e conferirá os links, branches e acesso da equipe. O nome da pasta local não precisa mudar para o produto ser apresentado como Lumina Odonto.

### 2.3 Correções clínicas e escopo da Sprint 7

**Detalhamento revisado em 23/10/2026:** [RFs clínicos, decisões e impactos](../requisitos/README.md) e [regras clínicas](../regras-de-negocio/README.md). Os arquivos distinguem direção de produto, propostas e implementação encontrada.

Paulo coordenará as correções de backend e as regras que ainda precisem de decisão. O contrato de abertura do prontuário merece prioridade: na base `ab129d7`, o `GET` cria o prontuário quando ausente e o frontend depende desse comportamento. A proposta de separar leitura e abertura exige mudança coordenada da API e da interface. A equipe deverá definir a operação de criação e testar o fluxo completo no PostgreSQL e pela interface antes de marcar a pendência como resolvida.

A pesquisa de OpenCL fica com Tarcísio nesta semana. Seu resultado será uma proposta revisável para o paralelismo do projeto; não se presume implementação integrada nem aceleração comprovada antes de um experimento medido e de decisão da equipe.

## 3. Entregas obrigatórias da Sprint 7

1. **Dashboard:** indicadores úteis de consultas por situação e período, calculados sobre dados reais da Agenda e coerentes com a listagem.
2. **Relatórios:** consulta organizada de agendamentos, com resumo pertinente ao acompanhamento da clínica.
3. **Pesquisa:** localização de registros por critérios definidos pela equipe, integrada aos dados da aplicação.
4. **Filtros:** combinação funcional de período, dentista e situação; acrescentar busca por paciente no recorte acordado.
5. **Exportação:** produzir CSV administrativo, se adotado pela equipe, com os mesmos filtros e permissões do relatório. Caso não seja aplicável, justificar a decisão no PDF.
6. **Logs ou histórico:** registrar as principais operações realizadas, indicando quem agiu, quando, em qual recurso e com qual resultado. O histórico deve ter leitura autorizada e não armazenar senhas, tokens ou conteúdo clínico integral.

Cada item deve ser demonstrado no sistema executável. A tabela `audit_logs` já prevista no banco não constitui, sozinha, histórico funcional. O dashboard atual possui contagens de pacientes e equipe, mas ainda precisa dos indicadores de consultas previstos para esta Sprint.

## 4. Divisão de atividades

### 4.1 Luiz Otávio — Docker, identidade do projeto e frontend

- **Hoje, 19/10:** reunir a versão integrada acordada, substituir o Compose antigo baseado em MySQL e executar frontend, API e PostgreSQL no Docker.
- Validar acesso ao frontend, à API e ao banco; conferir persistência após reiniciar os serviços com dados fictícios.
- Registrar comandos de inicialização, configuração necessária, resultado obtido e bloqueios de ambiente.
- Padronizar o nome apresentado como **Lumina Odonto** e encaminhar a atualização do nome do repositório e dos links conforme o item 2.2.
- Depois de estabilizar o ambiente, assumir com Caio uma parte definida do frontend: relatório/listagem, pesquisa, filtros e exportação, conforme o contrato acordado com Paulo.
- Compartilhar com a equipe a versão integrada e comunicar cedo qualquer conflito entre backend e frontend.

**Aceite:** `docker compose up --build` inicia PostgreSQL, API e frontend no ambiente definido; o fluxo de autenticação e uma consulta real funcionam; a documentação permite reproduzir a execução; nome e links afetados foram conferidos ou tiveram bloqueio registrado.

### 4.2 Caio Cesar — Correções clínicas e dashboard no frontend

- Corrigir com Otávio os defeitos de integração do frontend, começando pelo fluxo Agenda → consulta → prontuário → evolução.
- Ajustar a interface ao contrato aprovado para consultar ou criar o prontuário e tratar erros de permissão, ausência de registro e falha de conexão.
- Melhorar o dashboard para mostrar consultas por situação no período selecionado, usando dados reais e permissões corretas.
- Alinhar com Otávio a divisão de componentes e arquivos para evitar alterações concorrentes na mesma tela.
- Fornecer capturas e passos de demonstração a João e Cassiano.

**Aceite:** fluxo clínico e indicadores demonstráveis pela interface, com valores conferidos contra a Agenda e mensagens compreensíveis em caso de erro.

### 4.3 Paulo Sérgio — Backend, regras e coordenação

- Manter a lista de defeitos com reprodução, impacto, responsável, versão e próxima ação.
- Definir com a equipe o contrato de abertura do prontuário e as regras de acesso ainda pendentes, antes de alterar o fluxo clínico.
- Corrigir ou coordenar as correções de backend necessárias ao fluxo integrado.
- Acordar com Caio e Otávio os dados do dashboard, relatório, pesquisa, filtros e exportação, preservando isolamento por clínica e perfil.
- Definir com João quais operações entram no histórico e quem poderá consultar os eventos.
- Validar no PostgreSQL, com dados fictícios, os resultados apresentados como concluídos.

**Aceite:** decisões registradas; defeitos prioritários demonstrados como corrigidos na versão identificada; consultas e permissões verificadas; pendências restantes classificadas.

### 4.4 Tarcísio — Pesquisa e proposta de paralelismo

- Investigar aplicações concretas de OpenCL relacionadas ao Lumina Odonto e selecionar até duas candidatas para comparação.
- Descrever entrada, saída, necessidade de processamento, equipamento disponível e dependências de instalação.
- Preparar, se viável, um experimento pequeno com dados fictícios, versão sequencial e versão OpenCL; conferir saídas equivalentes e medir tempo total.
- Identificar os limites da proposta, incluindo suporte no computador de apresentação e relação com o sigilo do prontuário.
- Entregar a Paulo e a todos os integrantes uma recomendação curta para discussão antes de iniciar a integração ao sistema.

**Aceite:** proposta escrita e revisável, com problema, justificativa, evidências disponíveis, limitações e próximo passo; qualquer desempenho ainda não medido deve ser indicado como hipótese.

### 4.5 João Vitor — Testes e verificação das correções

- Reproduzir os defeitos comunicados pela equipe e registrar passos, resultado esperado e resultado obtido.
- Testar o fluxo clínico no ambiente integrado, incluindo dentista responsável, outro dentista, recepção, administrador e outra clínica.
- Conferir criação do prontuário pela operação aprovada, rascunho, finalização, bloqueio de edição e recuperação após reinício.
- Testar indicadores, relatório, pesquisa, filtros combinados, exportação e histórico em dados reais de teste.
- Executar a suíte automatizada aplicável e registrar resultado, ambiente e commit; testar também o fluxo em PostgreSQL, pois os testes com SQLite não substituem esse ensaio.

**Aceite:** resultados vinculados à versão testada; falhas reproduzíveis comunicadas a Paulo e aos responsáveis; demonstração de que permissões e dados entre clínicas não vazam.

### 4.6 Cassiano Augusto — Documentação e PDF cumulativo

- Preparar a seção da Sprint 7 no **PDF único com todas as Sprints anteriores**, identificando número do grupo, projeto e todos os integrantes.
- Registrar as correções da Sprint 6 executadas nesta semana, inclusive mudanças de planejamento, arquitetura ou modelagem, com justificativa e evidência.
- Documentar dashboard, relatório, pesquisa, filtros, exportação ou sua justificativa, histórico e integração com os módulos anteriores.
- Receber de cada integrante commit, testes, capturas, dificuldades e pendências; diferenciar funcionalidades demonstradas de propostas futuras, inclusive OpenCL.
- Conferir o link atualizado do GitHub, a numeração das figuras e a legibilidade do PDF antes da revisão final.

**Aceite:** PDF cumulativo revisável pela equipe, com cada entrega da Sprint 7 comprovada ou pendência declarada; versão final pronta para envio pelo Scrum Master.

## 5. Plano de execução

| Data | Marco verificável |
| --- | --- |
| **19/10, segunda** | Otávio prioriza Docker com frontend, API e PostgreSQL e padronização do nome. Paulo fecha a lista de defeitos e o contrato clínico. Caio divide as tarefas de frontend com Otávio. João inicia os cenários de teste; Tarcísio inicia a pesquisa; Cassiano abre a seção da Sprint 7. |
| **20/10, terça** | Corrigir e ensaiar os defeitos que bloqueiam o fluxo clínico no ambiente integrado. Otávio informa o resultado do Docker e eventuais pendências. Tarcísio apresenta a primeira seleção de problemas para OpenCL. |
| **21/10, quarta** | Demonstrar dashboard de consultas, relatório, pesquisa e filtros com dados reais da API; João compara os resultados com a Agenda. |
| **22/10, quinta** | Completar e verificar histórico de operações; conferir exportação CSV ou registrar a decisão fundamentada sobre sua aplicabilidade. Revisar a proposta de paralelismo com Paulo e toda a equipe. |
| **23/10, sexta** | João executa o roteiro de aceite na versão integrada. Corrigir falhas prioritárias, entregar evidências a Cassiano e revisar o PDF cumulativo. |
| **24/10, sábado** | Fazer apenas as verificações necessárias após correções e enviar a Sprint 7 até **23h59**, com comprovante de entrega. |

Os marcos intermediários são metas de organização desta semana, não conclusões antecipadas. Se um item não puder ser demonstrado, registrar o bloqueio, o impacto e a próxima ação no mesmo dia.

## 6. Roteiro mínimo de demonstração

1. Iniciar os serviços no Docker e entrar no Lumina Odonto com uma conta de teste.
2. Demonstrar o fluxo clínico corrigido com PostgreSQL e dados fictícios; reiniciar os serviços e recuperar os dados.
3. Conferir no dashboard consultas por período e situação, comparando totais com os registros da Agenda.
4. Consultar o relatório, pesquisar e combinar filtros; repetir com outro perfil para verificar a autorização.
5. Mostrar o CSV administrativo com os mesmos filtros e sem dados clínicos, se a equipe o implementar.
6. Executar uma operação relevante e localizar seu evento no histórico com acesso autorizado.
7. Mostrar o nome Lumina Odonto na aplicação e conferir a documentação e o endereço do repositório usados na entrega.

## 7. Evidências e pendências a registrar

- Versão integrada, commits e ambiente usados em cada ensaio.
- Resultado do Docker: serviços, inicialização, persistência após reinício e instruções de reprodução.
- Defeitos da Sprint 6 corrigidos, com reprodução anterior e resultado após a correção.
- Telas e dados de dashboard, relatório, pesquisa, filtros, exportação e histórico.
- Testes por perfil e clínica, resultados da suíte automatizada e ensaio em PostgreSQL.
- Proposta de OpenCL com hipóteses claramente separadas de resultados medidos.
- Situação da padronização do nome e do endereço do repositório.
- PDF cumulativo revisado, link correto do GitHub e comprovante de envio.

Uma tarefa só será marcada como concluída depois de demonstração ou teste na versão identificada. O envio acadêmico da Sprint 7 deve ser realizado por **um único integrante, o Scrum Master**, conforme a atividade da disciplina.

## 8. Decisões pendentes para Paulo e toda a equipe

1. Qual commit ou branch será a referência integrada de Docker, testes e entrega?
2. Qual operação criará o prontuário quando ele ainda não existir e qual autorização será exigida?
3. Como serão divididos os arquivos e as telas do frontend entre Otávio e Caio após a prioridade do Docker?
4. O identificador do repositório GitHub será atualizado para `lumina-odonto` nesta semana? Quem possui acesso para executar a mudança e atualizar os links?
5. Quais operações serão auditadas e quais perfis poderão consultar o histórico?
6. O CSV administrativo será implementado? Se a equipe concluir que exportação não se aplica, qual justificativa entrará no PDF?
7. Qual problema OpenCL deverá resolver no projeto e que resultado acadêmico será esperado da proposta de Tarcísio?

Este documento distribui o trabalho solicitado por Paulo. Ajustes de escopo, responsabilidades e regras serão confirmados com ele e com todos os integrantes, sem presumir aprovação individual ou conclusão antes das evidências.
