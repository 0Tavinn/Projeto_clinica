# Sprint 5 — Segundo Módulo Funcionando | Lumina Odonto

## Objetivo da Sprint

Implementar e demonstrar o segundo módulo completo do sistema Lumina Odonto: a Agenda e o Agendamento de Consultas.

O módulo deverá permitir o cadastro, a consulta, a atualização, o reagendamento, o cancelamento e a alteração da situação das consultas, integrando frontend, API FastAPI e banco de dados PostgreSQL.

A solução deverá aplicar regras de negócio, validações, controle de acesso por perfil, persistência no banco de dados, testes das funcionalidades, correção de bugs e commits organizados no GitHub.

Também será realizada a padronização da identidade do projeto no repositório, adotando o nome **Lumina Odonto** e o identificador `lumina-odonto`.

### Meta interna

Até **01/10**, o fluxo principal da Agenda deverá estar funcionando de ponta a ponta:

**Frontend → API → PostgreSQL**

Os dias **02/10 e 03/10** serão destinados a testes, correção de bugs, validação pelo Docker, coleta de evidências, elaboração do relatório e revisão da entrega.

O prazo oficial da Sprint 5 é **03/10 às 23h59**.

---

## Entrega individual no Drive

Cada integrante deverá elaborar um relatório individual referente à sua participação na Sprint 5 e enviá-lo ao Drive do projeto.

O relatório servirá de apoio para Cassiano elaborar o documento final da Sprint.

### Conteúdo mínimo do relatório individual

1. Nome do integrante;
2. Responsabilidade assumida na Sprint;
3. Atividades realizadas;
4. Arquivos, telas ou funcionalidades desenvolvidas;
5. Branches, commits ou Pull Requests relacionados;
6. Testes realizados e resultados obtidos;
7. Evidências, como prints das telas, Swagger, terminal, Docker ou PostgreSQL;
8. Dificuldades encontradas;
9. Soluções adotadas;
10. Pendências e próximos passos.

### Organização sugerida no Drive

```text
Sprint 05/
├── Relatórios Individuais/
│   ├── Caio Cesar/
│   ├── Cassiano Augusto/
│   ├── João Vitor/
│   ├── Luiz Otávio/
│   ├── Paulo Sérgio/
│   └── Tarcísio Alves/
├── Evidências/
├── Bugs e Testes/
└── Relatório Final/
```

### Padrão sugerido para os arquivos

```text
S05_NomeDoIntegrante_RelatorioIndividual
```

Exemplo:

```text
S05_PauloSergio_RelatorioIndividual
```

O relatório deverá ser entregue em formato editável, como Google Docs ou Word, para facilitar a consolidação da documentação.

---

## Padrão para criação de branches

Cada integrante deverá criar sua branch somente quando iniciar a atividade correspondente.

Antes de criar a branch, deverá confirmar que não existem arquivos pendentes:

```bash
git status --short
```

Em seguida, deverá atualizar a branch principal:

```bash
git switch main
git pull --ff-only origin main
```

A branch da atividade deverá ser criada e enviada ao GitHub:

```bash
git switch -c nome-da-branch
git push -u origin nome-da-branch
```

Ao finalizar uma parte relevante da atividade, o integrante deverá criar commits descritivos e enviar as alterações para o GitHub.

As alterações deverão passar por revisão antes de serem incorporadas à `main`.

---

## Padronização do nome do projeto e do repositório

O nome oficial do produto deverá ser apresentado como:

```text
Lumina Odonto
```

O nome recomendado para o repositório no GitHub será:

```text
lumina-odonto
```

O endereço esperado após a alteração será:

```text
https://github.com/0Tavinn/lumina-odonto
```

A alteração do nome do repositório deverá ser realizada pelo responsável que possua permissão administrativa no GitHub.

Depois da alteração, cada integrante deverá atualizar o endereço remoto do repositório local:

```bash
git remote set-url origin https://github.com/0Tavinn/lumina-odonto.git
git remote -v
```

A equipe deverá confirmar que os seguintes comandos continuam funcionando:

```bash
git fetch origin
git pull --ff-only origin main
git push
```

O nome da pasta local `Projeto_clinica` não precisa ser alterado para que o Git continue funcionando. A mudança necessária é no nome do repositório remoto e nos links da documentação.

Os links antigos presentes no `README.md`, nos documentos da pasta `docs/`, no Drive e no relatório final deverão ser atualizados.

---

## Paulo Sérgio — Banco de dados, regras de negócio, validação e evidências

### Branches sugeridas

```text
docs/system-requirements-and-rules
feat/demo-seed-data
```

### Atividades

- Revisar a estrutura atual da tabela `appointments`.
- Validar as relações entre consultas, pacientes, dentistas e clínica.
- Conferir a relação entre `users`, `dentists` e `appointments`.
- Registrar os ajustes necessários no banco de dados para o módulo de Agenda.
- Elaborar e manter o documento `docs/requirements.md`.
- Elaborar e manter o documento `docs/business-rules.md`.
- Preparar a proposta das regras de negócio de agendamento.
- Validar com a equipe as regras definidas antes da implementação.
- Registrar as decisões que ainda dependem de confirmação da equipe.
- Definir os dados fictícios necessários para a demonstração.
- Criar, com apoio técnico, o script `seed_demo.py`.
- Executar o script no PostgreSQL local.
- Conferir que o script não duplica dados quando executado novamente.
- Validar no PostgreSQL os agendamentos criados, atualizados, cancelados e concluídos.
- Elaborar o roteiro de testes da Agenda.
- Testar os fluxos como administrador, recepcionista e dentista.
- Registrar os bugs encontrados e acompanhar as correções.
- Conferir branches, commits e Pull Requests antes da versão final.
- Confirmar com Otávio a alteração do nome do repositório.
- Verificar se os integrantes atualizaram o endereço remoto local.
- Conferir se o README, a documentação e o quadro da Sprint utilizam o novo link.
- Organizar prints e evidências no Drive.
- Repassar a Cassiano as informações necessárias para o relatório final.

### Relatório individual

- Descrever a revisão realizada no banco de dados.
- Registrar os requisitos e as regras de negócio propostas e aprovadas.
- Informar os testes de persistência realizados no PostgreSQL.
- Incluir evidências do script de dados fictícios, caso seja concluído.
- Informar os bugs identificados e as correções validadas.
- Registrar a conferência das branches, dos Pull Requests e do novo link do repositório.
- Enviar o relatório individual ao Drive.

---

## Caio Cesar — Frontend da Agenda e integração

### Branch sugerida

```text
feat/appointments-frontend
```

### Atividades

- Criar ou adaptar a tela de Agenda para utilizar dados reais da API.
- Integrar a listagem de consultas.
- Criar o formulário para cadastro de agendamento.
- Permitir selecionar paciente, dentista, data, horário, duração e observações.
- Exibir consultas por data, dentista e situação.
- Integrar a consulta dos detalhes de um agendamento.
- Integrar a atualização e o reagendamento de consultas.
- Integrar o cancelamento de consultas conforme as permissões do usuário.
- Exibir a situação da consulta conforme os estados aprovados pela equipe.
- Aplicar validações para campos obrigatórios, data, horário e duração.
- Exibir mensagens claras para sucesso, conflito de horário, dados inválidos, permissão negada e falha de conexão.
- Atualizar a Agenda após cadastro, alteração, cancelamento ou mudança de situação.
- Restringir visualmente as ações de acordo com o perfil autenticado.
- Confirmar que o dentista visualiza somente as consultas autorizadas.
- Aplicar no formulário de pacientes, se houver tempo disponível, máscaras de CPF e telefone.
- Organizar os campos de endereço do paciente para futura integração com consulta de CEP.
- Capturar prints das telas integradas.
- Atualizar o endereço remoto local após a alteração do nome do repositório.

### Relatório individual

- Descrever as telas da Agenda desenvolvidas.
- Explicar a integração do frontend com a API de agendamentos.
- Informar as validações e mensagens apresentadas.
- Incluir prints do cadastro, da listagem, da edição e do cancelamento de consultas.
- Registrar os testes feitos com os diferentes perfis.
- Informar branches, commits ou Pull Requests.
- Enviar o relatório individual ao Drive.

---

## Tarcísio Alves Viana Costa Filho e João Vitor Lima Rocha — API, regras de negócio e testes técnicos

### Branches sugeridas

```text
feat/appointments-api
test/appointments-api
```

### Organização das branches

Tarcísio deverá iniciar a implementação na branch:

```text
feat/appointments-api
```

Quando os endpoints iniciais estiverem disponíveis, João poderá criar a branch de testes a partir da branch de Tarcísio:

```bash
git fetch origin
git switch -c test/appointments-api --track origin/feat/appointments-api
git push -u origin test/appointments-api
```

João deverá abrir Pull Request da branch `test/appointments-api` para a branch `feat/appointments-api`.

Após a revisão e a incorporação dos testes, Tarcísio deverá abrir a Pull Request final de `feat/appointments-api` para a `main`.

### Atividades

- Revisar a tabela `appointments`.
- Alinhar o modelo ORM ao banco PostgreSQL.
- Revisar a relação entre contas com perfil dentista e a tabela `dentists`.
- Definir o fluxo de cadastro dos dados profissionais do dentista necessários para o agendamento.
- Conferir os estados aceitos pela tabela de agendamentos.
- Validar com a equipe as transições permitidas entre os estados.
- Implementar as regras documentadas em `docs/business-rules.md`.
- Criar os schemas, serviços, repositórios e rotas necessários para agendamentos.
- Implementar a listagem de consultas por período, dentista, paciente e situação.
- Implementar o cadastro de consulta.
- Implementar a consulta dos detalhes de um agendamento.
- Implementar atualização e reagendamento.
- Implementar cancelamento por alteração de situação, sem exclusão física do histórico.
- Implementar atualização da situação para consulta concluída ou ausência do paciente.
- Garantir que paciente, dentista e consulta pertençam à mesma clínica.
- Impedir agendamento para paciente ou dentista inativo.
- Impedir agendamentos em horários passados.
- Impedir conflito de horário para o mesmo dentista.
- Garantir proteção contra duas reservas simultâneas do mesmo horário.
- Definir permissões para administrador, recepcionista e dentista.
- Garantir que o dentista altere somente os atendimentos sob sua responsabilidade.
- Garantir que as respostas de erro possam ser apresentadas pelo frontend.
- Criar ou atualizar os testes automatizados da API.
- Criar testes para conflito de horário, permissões, cancelamento, transições e persistência.
- Criar testes para impedir acesso a dados de outra clínica.
- Apoiar Caio durante a integração da Agenda.
- Revisar Pull Requests relacionados ao backend.
- Atualizar o endereço remoto local após a alteração do nome do repositório.

### Relatório individual

- Descrever as rotas e regras de negócio implementadas.
- Informar os campos e situações utilizados no agendamento.
- Registrar os testes automatizados executados.
- Incluir evidências dos testes e dos erros tratados.
- Informar branches, commits ou Pull Requests.
- Registrar dificuldades e soluções técnicas.
- Enviar o relatório individual ao Drive.

---

## Luiz Otávio de Souza Azevedo — Docker, ambiente, repositório e integração

### Branches sugeridas

```text
chore/docker-postgresql
chore/update-project-links
```

A alteração do nome do repositório no GitHub não exige uma branch. A branch `chore/update-project-links` deverá ser utilizada somente se for necessário modificar links e nomes dentro dos arquivos versionados.

### Atividades de Docker e ambiente

- Criar ou atualizar a configuração Docker do projeto atual.
- Remover a configuração antiga baseada em MySQL.
- Configurar PostgreSQL, API FastAPI e frontend no Docker Compose.
- Configurar volume para preservar os dados do PostgreSQL.
- Garantir que o banco seja inicializado com a estrutura PostgreSQL atual.
- Conferir se os scripts SQL e as migrações representam o banco atual antes de automatizar a inicialização.
- Configurar a comunicação entre frontend, API e banco de dados.
- Validar CORS e variáveis de ambiente no ambiente Docker.
- Garantir que o projeto possa ser iniciado pelo comando:

```bash
docker compose up --build
```

- Validar o acesso ao frontend, à documentação da API e ao PostgreSQL.
- Apoiar a execução do script `seed_demo.py` dentro do ambiente Docker.
- Conferir os logs da API e dos containers durante falhas de integração.
- Atualizar o README com as instruções de execução local e por Docker.
- Revisar branches, commits e Pull Requests.
- Apoiar Caio, Tarcísio e João em problemas de integração.

### Atividades de padronização do repositório

- Confirmar que possui permissão administrativa no repositório.
- Alterar o nome do repositório de `Projeto_clinica` para `lumina-odonto`.
- Manter o nome de apresentação do produto como **Lumina Odonto**.
- Confirmar o novo endereço:

```text
https://github.com/0Tavinn/lumina-odonto
```

- Atualizar links antigos presentes no `README.md` e na pasta `docs/`.
- Comunicar à equipe quando a alteração estiver concluída.
- Enviar à equipe o comando para atualização do endereço remoto.
- Confirmar que `fetch`, `pull` e `push` continuam funcionando.
- Verificar se as branches e os Pull Requests continuam acessíveis.
- Informar o novo endereço a Paulo e Cassiano.

### Relatório individual

- Descrever a configuração criada para Docker.
- Registrar os serviços executados no Docker Compose.
- Informar os ajustes de PostgreSQL, CORS e variáveis de ambiente.
- Incluir evidências dos containers em funcionamento.
- Registrar a alteração do nome do repositório e a atualização dos links.
- Informar branches, commits ou Pull Requests.
- Enviar o relatório individual ao Drive.

---

## Cassiano Augusto Brito de Souza — Documentação da Sprint

### Branch sugerida

```text
docs/sprint-05-report
```

> Esta branch será necessária somente se Cassiano atualizar documentos Markdown dentro do repositório. Para documentos mantidos apenas no Drive, não será necessário criar branch.

### Atividades

- Definir o padrão dos relatórios individuais.
- Acompanhar o recebimento dos relatórios no Drive.
- Organizar as evidências, os testes e os registros de bugs recebidos.
- Elaborar a seção da Sprint 5 no documento final.
- Descrever o módulo de Agenda implementado.
- Apresentar evidências do agendamento funcionando.
- Apresentar evidências da persistência das consultas no PostgreSQL.
- Registrar as regras de negócio implementadas ou atualizadas.
- Registrar os testes realizados e seus resultados.
- Registrar os bugs identificados e as correções efetuadas.
- Inserir no relatório o link atualizado do GitHub.
- Confirmar que o link inserido no documento abre corretamente.
- Utilizar o nome oficial **Lumina Odonto** em toda a documentação.
- Registrar as dificuldades encontradas e os próximos passos.
- Identificar corretamente todos os integrantes.
- Revisar a formatação conforme as normas ABNT.
- Conferir a qualidade e a legibilidade das imagens.
- Revisar a numeração sequencial das figuras das Sprints anteriores e da Sprint 5.
- Exportar a versão final em PDF.
- Disponibilizar o PDF para revisão da equipe antes do envio.

### Relatório individual

- Descrever as atividades de organização e documentação.
- Registrar os documentos, as evidências e os testes recebidos.
- Informar os ajustes realizados na formatação.
- Registrar a atualização do nome e do link do repositório.
- Registrar as dificuldades encontradas durante a consolidação.
- Enviar o relatório individual ao Drive.

---

## Critérios para considerar a Sprint pronta

- A Agenda utiliza dados reais da API.
- Administrador e recepcionista conseguem cadastrar agendamentos.
- O dentista consegue visualizar as consultas autorizadas.
- O dentista consegue atualizar a situação dos atendimentos permitidos.
- Os agendamentos são persistidos no PostgreSQL.
- Os dados continuam disponíveis após reiniciar a aplicação.
- As consultas podem ser consultadas, atualizadas, remarcadas e canceladas.
- O cancelamento preserva o registro no banco de dados.
- O sistema impede conflito de horário para o mesmo dentista.
- O sistema impede agendamento para paciente ou dentista inativo.
- O sistema impede agendamentos em horários passados.
- O sistema impede acesso a registros pertencentes a outra clínica.
- O sistema apresenta mensagens claras de sucesso e erro.
- As permissões por perfil são respeitadas.
- Os testes automatizados da API foram executados.
- Os principais fluxos foram testados pela interface.
- Os bugs encontrados foram registrados e corrigidos ou classificados como pendência.
- O sistema funciona localmente e no Docker.
- O script de dados fictícios pode ser executado sem criar duplicidades indevidas.
- Os commits estão organizados e enviados ao GitHub.
- O repositório está identificado como `lumina-odonto`.
- Os integrantes atualizaram o endereço remoto local.
- O README, a documentação e o relatório utilizam o endereço atualizado.
- As branches e os Pull Requests continuam acessíveis após a alteração.
- Cada integrante enviou seu relatório individual ao Drive.
- As evidências foram organizadas para o relatório final.
- O relatório final foi revisado pela equipe.

---

## Fora do escopo da Sprint 5

- Prontuário clínico completo;
- Evoluções clínicas;
- Integração funcional de Inteligência Artificial;
- Métricas financeiras avançadas;
- Relatórios gerenciais avançados;
- Portal de autoatendimento do paciente.

---

## Preparação para Inteligência Artificial

Nesta Sprint, a equipe poderá definir o objetivo futuro da Inteligência Artificial, os dados que ela poderá utilizar e as regras de privacidade necessárias.

A integração funcional da IA deverá ocorrer após a implementação do prontuário clínico e das evoluções dos pacientes, pois esses dados serão a base para qualquer recurso de apoio ao dentista.

O conteúdo gerado futuramente por IA deverá ser apresentado como apoio ao profissional. Ele não deverá registrar automaticamente diagnósticos, prescrições ou evoluções clínicas sem revisão e confirmação do dentista responsável.

---

## Resultado esperado da Sprint 5

Ao final da Sprint 5, o Lumina Odonto deverá possuir dois módulos funcionais integrados:

1. Autenticação, gestão da equipe e gestão de pacientes;
2. Agenda e agendamento de consultas.

O segundo módulo deverá operar com dados reais, respeitar as permissões dos usuários, persistir os agendamentos no PostgreSQL e possuir testes e evidências de funcionamento.

O projeto também deverá possuir ambiente Docker atualizado para PostgreSQL, documentação revisada, requisitos e regras de negócio registrados, dados fictícios para demonstração e identidade padronizada no GitHub como **Lumina Odonto**.