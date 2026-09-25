# Sprint 4 — Primeiro Módulo Completo | Lumina Odonto

## Objetivo da Sprint

Implementar e demonstrar o primeiro módulo completo do sistema Lumina Odonto, integrando o front-end, a API e o banco de dados PostgreSQL.

O módulo deverá permitir que os usuários realizem um fluxo real de utilização, incluindo autenticação, controle de acesso, cadastro da equipe e gestão de pacientes.

A solução deverá apresentar persistência de dados, validações, mensagens claras de sucesso e erro, navegação entre telas e commits organizados no GitHub.

### Meta interna

Até **24/09**, o fluxo principal deverá estar funcionando de ponta a ponta:

**Front-end → API → PostgreSQL**

Os dias **25/09 e 26/09** serão destinados a correções, Docker, atualização do README, coleta de evidências, elaboração do relatório e revisão da entrega.

O prazo oficial da Sprint 4 é **26/09 às 23h59**.

---

## Entrega individual no Drive

Cada integrante deverá elaborar um relatório individual referente à sua participação na Sprint 4 e enviá-lo ao Drive do projeto.

O relatório servirá de apoio para Cassiano elaborar o documento final da Sprint.

### Conteúdo mínimo do relatório individual

1. Nome do integrante;
2. Responsabilidade assumida na Sprint;
3. Atividades realizadas;
4. Arquivos, telas ou funcionalidades desenvolvidas;
5. Branches, commits ou Pull Requests relacionados;
6. Testes realizados e resultados obtidos;
7. Evidências, como prints das telas, Swagger, terminal ou PostgreSQL;
8. Dificuldades encontradas;
9. Soluções adotadas;
10. Pendências e próximos passos.

### Organização sugerida no Drive

```text
Sprint 04/
├── Relatórios Individuais/
│   ├── Caio Cesar/
│   ├── Cassiano Augusto/
│   ├── João Vitor/
│   ├── Luiz Otávio/
│   ├── Paulo Sérgio/
│   └── Tarcísio Alves/
├── Evidências/
└── Relatório Final/
```

### Padrão sugerido para os arquivos

```
S04_NomeDoIntegrante_RelatorioIndividual
```

```
Exemplo: S04_PauloSergio_RelatorioIndividual
```

---

O relatório deverá ser entregue em formato editável, como Google Docs ou Word, para facilitar a consolidação da documentação.

## Paulo Sérgio — Coordenação, validação e evidências

### Atividades

- Criar e manter o quadro de tarefas da Sprint atualizado.
- Acompanhar o andamento das atividades de cada integrante.
- Compartilhar com Caio o guia de integração da API.
- Disponibilizar as contas locais de teste.
- Validar no Swagger os endpoints utilizados pelo front-end.
- Conferir no PostgreSQL se os usuários cadastrados pelo front-end foram persistidos.
- Conferir no PostgreSQL se os pacientes cadastrados pelo front-end foram persistidos.
- Testar o fluxo completo como administrador.
- Testar o fluxo completo como recepcionista.
- Testar o fluxo completo como dentista.
- Conferir branches, commits e Pull Requests antes da versão final.
- Registrar prints e evidências do sistema funcionando.
- Organizar as evidências no Drive.
- Repassar a Cassiano as informações necessárias para o relatório final.

### Relatório individual

- Descrever o trabalho de coordenação realizado.
- Registrar os testes executados no Swagger e no sistema integrado.
- Incluir evidências da persistência no PostgreSQL.
- Informar as dificuldades encontradas durante a integração.
- Enviar o relatório individual ao Drive.

---

## Caio Cesar — Front-end e integração

### Atividades

- Criar a tela de login conforme o protótipo.
- Integrar o login com `POST /api/v1/auth/login`.
- Enviar o e-mail no campo `username` e a senha no campo `password`.
- Armazenar o token após o login válido.
- Consultar `GET /api/v1/auth/me` para identificar o usuário e seu perfil.
- Criar o botão de sair e encerrar a sessão.
- Proteger as páginas que exigem autenticação.
- Redirecionar usuários sem sessão válida para a tela de login.
- Criar o menu de navegação conforme o perfil autenticado.
- Criar a tela do Dashboard.
- Criar a tela de gestão da equipe para o administrador.
- Integrar o cadastro de usuários com `POST /api/v1/users`.
- Integrar a listagem da equipe com `GET /api/v1/users`, quando a rota estiver disponível.
- Criar a tela de gestão de pacientes.
- Integrar a listagem com `GET /api/v1/patients`.
- Integrar o cadastro com `POST /api/v1/patients`.
- Integrar a edição com `PATCH /api/v1/patients/{id}`.
- Integrar a inativação com `DELETE /api/v1/patients/{id}`.
- Incluir o número do prontuário no formulário de pacientes.
- Validar campos obrigatórios.
- Validar o formato do CPF.
- Validar o formato do e-mail.
- Validar a data de nascimento.
- Exibir mensagens claras de sucesso e erro.
- Exibir mensagem de permissão negada.
- Exibir mensagem quando houver falha de comunicação com a API.
- Atualizar as listas após cadastros, edições e inativações.
- Utilizar dados reais vindos da API.
- Capturar prints das telas integradas.

### Relatório individual

- Descrever as telas desenvolvidas.
- Explicar como o front-end foi integrado à API.
- Informar as validações implementadas.
- Registrar exemplos de mensagens de sucesso e erro.
- Incluir prints das telas funcionando.
- Informar branches, commits ou Pull Requests.
- Enviar o relatório individual ao Drive.

---

## Tarcísio Alves — Regras da API e revisão técnica

### Atividades

- Revisar se a API está alinhada aos formulários do front-end.
- Confirmar os campos obrigatórios do cadastro de usuários.
- Confirmar os campos obrigatórios do cadastro de pacientes.
- Garantir que apenas o administrador possa cadastrar usuários da equipe.
- Permitir que a recepcionista cadastre, consulte, edite e inative pacientes.
- Permitir que o dentista cadastre, consulte e edite pacientes.
- Impedir ações que não estejam autorizadas para cada perfil.
- Implementar `GET /api/v1/users` para a tela de gestão da equipe.
- Revisar a resposta de erro `401` para falhas de autenticação.
- Revisar a resposta de erro `403` para falta de permissão.
- Revisar a resposta de erro `409` para dados duplicados.
- Revisar a resposta de erro `422` para campos inválidos.
- Garantir que as mensagens retornadas possam ser apresentadas no front-end.
- Executar os testes automatizados da API.
- Criar testes para as novas permissões implementadas.
- Revisar Pull Requests relacionados ao back-end.
- Apoiar Caio na resolução de problemas de integração.

### Relatório individual

- Descrever as regras de acesso implementadas.
- Registrar as rotas criadas ou alteradas.
- Informar os testes automatizados executados.
- Incluir evidências dos resultados dos testes.
- Informar branches, commits ou Pull Requests.
- Registrar dificuldades e soluções técnicas.
- Enviar o relatório individual ao Drive.

---

## Luiz Otávio — Ambiente, integração e Docker

### Atividades

- Manter a API e o PostgreSQL disponíveis para os testes de integração.
- Confirmar que o CORS permite o endereço utilizado pelo front-end.
- Apoiar Caio na configuração da URL base da API.
- Testar o fluxo de login pelo front-end.
- Testar o cadastro de usuários pelo front-end.
- Testar o CRUD de pacientes pelo front-end.
- Conferir os logs da API quando houver falhas de requisição.
- Revisar a organização das branches.
- Revisar os commits e Pull Requests.
- Preparar uma branch separada para a configuração do Docker.
- Alterar o `compose.yaml` para utilizar PostgreSQL.
- Remover do Docker a configuração antiga do MySQL.
- Configurar a comunicação entre API e PostgreSQL no Docker.
- Preservar os dados do PostgreSQL por meio de volume.
- Validar o Docker somente após o fluxo local estar funcionando.
- Apoiar a atualização das instruções de execução no README.

### Relatório individual

- Descrever o ambiente utilizado na integração.
- Registrar os testes realizados entre front-end, API e PostgreSQL.
- Informar os ajustes realizados no CORS.
- Documentar as alterações do Docker.
- Incluir prints dos serviços funcionando.
- Informar branches, commits ou Pull Requests.
- Enviar o relatório individual ao Drive.

---

## João Vitor — Testes funcionais e apoio técnico

### Atividades

- Revisar o fluxo esperado do primeiro módulo.
- Conferir se a implementação continua coerente com a arquitetura do sistema.
- Elaborar uma lista de cenários de teste.
- Testar login com credenciais válidas.
- Testar login com credenciais inválidas.
- Testar acesso sem autenticação.
- Testar acesso com perfil sem permissão.
- Testar cadastro de usuário pelo administrador.
- Testar cadastro de usuário duplicado.
- Testar cadastro de paciente.
- Testar edição de paciente.
- Testar inativação de paciente.
- Testar formulários com campos obrigatórios vazios.
- Testar CPF e e-mail inválidos.
- Registrar os resultados encontrados.
- Comunicar os problemas encontrados aos responsáveis.
- Repetir os testes após as correções.
- Apoiar Tarcísio na revisão técnica da API.
- Capturar evidências dos testes funcionais.

### Relatório individual

- Listar os cenários de teste executados.
- Informar os resultados esperados e obtidos.
- Registrar erros encontrados.
- Registrar as correções validadas.
- Incluir prints ou evidências dos testes.
- Informar as dificuldades encontradas.
- Enviar o relatório individual ao Drive.

---

## Cassiano Augusto — Documentação da Sprint

### Atividades

- Definir o padrão dos relatórios individuais.
- Acompanhar o recebimento dos relatórios no Drive.
- Conferir se todos os integrantes enviaram seus relatórios.
- Organizar as evidências recebidas.
- Elaborar a seção da Sprint 4 no documento final.
- Descrever o módulo implementado.
- Apresentar evidências do módulo funcionando.
- Apresentar evidências da persistência de dados.
- Incluir exemplos das validações.
- Incluir evidências das mensagens de erro.
- Demonstrar o fluxo de navegação entre as telas.
- Inserir o link atualizado do GitHub.
- Registrar as dificuldades encontradas.
- Registrar os próximos passos do projeto.
- Identificar corretamente todos os integrantes.
- Revisar a formatação conforme as normas ABNT.
- Conferir a qualidade e a legibilidade das imagens.
- Exportar a versão final em PDF.
- Disponibilizar o PDF para revisão da equipe antes do envio.

### Relatório individual

- Descrever as atividades de organização e documentação.
- Registrar os documentos e evidências recebidos.
- Informar os ajustes realizados na formatação.
- Registrar as dificuldades encontradas durante a consolidação.
- Enviar o relatório individual ao Drive.

---

## Critérios para considerar a Sprint pronta

- O administrador consegue fazer login pelo front-end.
- O administrador consegue cadastrar um usuário da equipe.
- O usuário cadastrado fica salvo no PostgreSQL.
- A recepcionista consegue fazer login.
- A recepcionista consegue cadastrar, consultar, editar e inativar pacientes.
- O dentista consegue fazer login.
- O dentista acessa somente as funcionalidades autorizadas.
- Os pacientes cadastrados ficam salvos no PostgreSQL.
- Os dados continuam disponíveis após reiniciar a API.
- Os formulários bloqueiam informações inválidas ou incompletas.
- O sistema apresenta mensagens claras de sucesso e erro.
- A navegação entre Login, Dashboard, Usuários e Pacientes funciona.
- As operações são realizadas com dados reais da API.
- Os testes principais foram executados.
- Os commits estão organizados e enviados ao GitHub.
- Cada integrante enviou seu relatório individual ao Drive.
- As evidências foram organizadas para o relatório final.
- O relatório final foi revisado pela equipe.

---

## Fora do escopo até o módulo principal estar pronto

- Prontuário médico completo;
- Agenda completa;
- Integração de Inteligência Artificial;
- Funcionalidades avançadas de métricas financeiras;
- Relatórios gerenciais avançados.

---

## Observação sobre o Docker

O Docker não deverá impedir a conclusão da Sprint 4.

Primeiro, a equipe deverá validar localmente o fluxo completo entre front-end, API e PostgreSQL. Após essa validação, a configuração do Docker poderá ser concluída e testada.

O dia **25/09** deverá ser utilizado para Docker, atualização do README, correções finais, organização das evidências e elaboração do relatório.