# Requisitos do Sistema — Lumina Odonto

## 1. Identificação e referência

- **Versão:** 1.1 — requisitos funcionais e não funcionais.
- **Data:** 27/09/2026.
- **Referência principal:** funcionalidades consolidadas na Sprint 04.
- **Situação do documento:** versão para revisão da equipe.

Este documento descreve os requisitos funcionais e não funcionais do Lumina Odonto e identifica a situação de cada funcionalidade. O relatório da Sprint 04 tem prioridade sobre os documentos anteriores quando houver divergências. Os testes relatados pela equipe na conclusão da Sprint 04 complementam essa referência.

### 1.1 Situações utilizadas

- **Implementado — Sprint 04:** funcionalidade registrada no relatório ou confirmada nos testes relatados pela equipe.
- **Planejado — Sprint 05:** funcionalidade proposta para o módulo de Agenda, com detalhes sujeitos à revisão da equipe.
- **Planejado — etapa futura:** funcionalidade prevista nos documentos, ainda sem entrega funcional confirmada.
- **Escopo congelado:** funcionalidade prevista no backlog inicial, sem prioridade de implementação no momento.
- **Melhoria proposta:** sugestão recente que depende de inclusão no planejamento.

Os identificadores `RF-001`, `RF-002` e seguintes pertencem a este catálogo atualizado. Eles não substituem automaticamente os identificadores históricos da Sprint 01 ou das histórias de usuário do Product Backlog.

## 2. Perfis e contexto atual

O módulo atual possui três perfis autenticados:

| Perfil | Identificador | Acesso atual |
|---|---|---|
| Administrador | `ADMINISTRATOR` | Cadastro e listagem da equipe; cadastro, consulta, edição e inativação de pacientes. |
| Recepcionista | `RECEPTIONIST` | Cadastro, consulta, edição e inativação de pacientes. |
| Dentista | `DENTIST` | Cadastro, consulta e edição de pacientes. |

O paciente possui cadastro próprio no sistema e não dispõe de login no módulo entregue. A presença de um paciente na base não representa a criação de uma conta de usuário.

Os registros de equipe e pacientes são vinculados a uma clínica. Essa vinculação não significa que já exista uma interface completa de administração de várias clínicas.

## 3. Requisitos funcionais implementados

### RF-001 — Autenticar usuários da equipe

O sistema deve permitir que usuários cadastrados e ativos acessem a aplicação por meio de e-mail e senha. Credenciais inválidas ou contas inativas devem impedir o acesso.

**Perfis:** administrador, recepcionista e dentista.  
**Situação:** implementado — Sprint 04.

### RF-002 — Recuperar e renovar a sessão

O sistema deve recuperar a identificação e o perfil do usuário autenticado, manter a sessão durante a navegação e a atualização da mesma aba e renovar o acesso enquanto o token de atualização for válido. Quando a sessão não puder ser recuperada ou renovada, deve solicitar novo login.

**Perfis:** administrador, recepcionista e dentista.  
**Situação:** implementado — Sprint 04.

### RF-003 — Encerrar a sessão

O sistema deve disponibilizar uma ação de saída que remova a sessão local e retorne o usuário à tela de login. As páginas protegidas devem exigir nova autenticação após a saída.

**Perfis:** administrador, recepcionista e dentista.  
**Situação:** implementado — Sprint 04.

### RF-004 — Controlar funcionalidades por perfil

O sistema deve apresentar menus e ações compatíveis com o perfil autenticado e verificar as permissões também na API. A gestão da equipe deve ser restrita ao administrador. A inativação de pacientes deve ser permitida somente ao administrador e à recepcionista.

**Situação:** implementado — Sprint 04.

### RF-005 — Vincular operações à clínica do usuário

O sistema deve associar os usuários e pacientes cadastrados à clínica do usuário autenticado e limitar as consultas e alterações aos registros dessa clínica.

**Situação:** implementado no primeiro módulo, conforme a documentação e os testes relatados. A validação completa com múltiplas clínicas permanece como atividade de teste futura.

### RF-006 — Cadastrar usuários da equipe

O sistema deve permitir ao administrador cadastrar usuários da equipe, informando nome completo, e-mail, CPF, senha, perfil e telefone, quando fornecido. O usuário criado deve ficar disponível no banco e poder autenticar-se quando estiver ativo.

O cadastro de uma conta com perfil dentista não deve ser confundido com a implementação completa de seus dados profissionais, prevista no RF-016.

**Perfil:** administrador.  
**Situação:** implementado — Sprint 04.

### RF-007 — Listar usuários da equipe

O sistema deve permitir ao administrador consultar a equipe vinculada à sua clínica, apresentando a identificação e o perfil dos usuários sem expor senhas ou hashes de senha.

**Perfil:** administrador.  
**Situação:** implementado — Sprint 04.

### RF-008 — Cadastrar pacientes

O sistema deve permitir cadastrar pacientes com nome completo, CPF, número de prontuário e data de nascimento, além de telefone, e-mail e endereço quando fornecidos. O cadastro deve ser associado à clínica do usuário autenticado.

Na versão atual, o número de prontuário é informado manualmente. Sua geração automática permanece como melhoria proposta.

**Perfis:** administrador, recepcionista e dentista.  
**Situação:** implementado — Sprint 04.

### RF-009 — Listar e consultar pacientes

O sistema deve permitir recuperar pacientes da clínica na interface e consultar seus dados cadastrais. As informações exibidas devem corresponder aos registros recuperados pela API.

**Perfis:** administrador, recepcionista e dentista.  
**Situação:** implementado — Sprint 04.

### RF-010 — Atualizar pacientes

O sistema deve permitir atualizar os dados cadastrais de pacientes da clínica, validar os dados enviados e apresentar as informações atualizadas após a gravação.

**Perfis:** administrador, recepcionista e dentista.  
**Situação:** implementado — Sprint 04.

### RF-011 — Inativar pacientes

O sistema deve permitir a inativação lógica de pacientes, alterando sua situação de atividade e preservando o registro no banco. O dentista não deve conseguir executar essa operação.

**Perfis:** administrador e recepcionista.  
**Situação:** implementado — Sprint 04.

### RF-012 — Apresentar painel inicial e navegação

O sistema deve apresentar um painel inicial após a autenticação, com resumos de equipe e pacientes baseados nos dados recuperados pela aplicação, conforme as permissões do usuário. Deve permitir navegar entre as funcionalidades autorizadas e encerrar a sessão.

**Situação:** implementado — Sprint 04, conforme a demonstração relatada pela equipe.

### RF-013 — Validar cadastros e impedir duplicidades

O sistema deve validar os campos obrigatórios e os formatos aceitos nos formulários de usuários e pacientes. Deve impedir duplicidade de e-mail e CPF de usuários e de CPF e número de prontuário de pacientes dentro da mesma clínica.

A validação de CPF descrita neste requisito não declara, por si só, conferência dos dígitos verificadores. O e-mail do paciente não foi definido como exclusivo na modelagem apresentada.

**Situação:** implementado — Sprint 04, conforme as validações e restrições documentadas.

### RF-014 — Informar resultados e falhas das operações

O sistema deve apresentar mensagens compreensíveis para operações concluídas, credenciais inválidas, falta de permissão, registros duplicados, campos inválidos, excesso de tentativas de login e falha de comunicação com a API.

**Situação:** implementado — Sprint 04.

### RF-015 — Recuperar os dados após operações

O sistema deve atualizar as informações apresentadas após cadastros, alterações e inativações, utilizando os resultados persistidos no PostgreSQL. Os registros devem permanecer recuperáveis após nova execução da aplicação.

**Situação:** gravação e recuperação confirmadas nos testes relatados da Sprint 04. A evidência específica de reinicialização deve ser mantida no roteiro de testes.

## 4. Requisitos planejados para a Sprint 05 — Agenda

Os requisitos desta seção são uma proposta de implementação. As permissões, situações, campos e regras de horário devem ser revisados pela equipe e confrontados com a estrutura de `appointments` antes da aprovação final.

### RF-016 — Disponibilizar dentistas para agendamento

O sistema deve permitir identificar os dentistas da clínica elegíveis para receber consultas, vinculando a conta de usuário ao cadastro profissional necessário ao agendamento. A equipe deve definir como cadastrar e consultar CRO, UF e especialidade.

**Situação:** planejado — Sprint 05. A tabela `dentists` foi modelada, mas o fluxo completo de dados profissionais não está confirmado na Sprint 04.

### RF-017 — Consultar a Agenda

O sistema deve apresentar os agendamentos da clínica por data ou período, permitindo filtrar por dentista, paciente e situação. O dentista deve conseguir consultar seus atendimentos agendados.

**Situação:** planejado — Sprint 05.

### RF-018 — Cadastrar agendamentos

O sistema deve permitir ao administrador e à recepcionista registrar consultas vinculadas à clínica, ao paciente e ao dentista, informando data, horário, duração e observações quando necessárias.

O cadastro deve verificar atividade dos envolvidos e disponibilidade de horário. Essas verificações devem ser detalhadas no documento de regras de negócio.

**Situação:** planejado — Sprint 05.

### RF-019 — Consultar detalhes de um agendamento

O sistema deve permitir visualizar paciente, dentista, data, horário, duração, situação e observações de uma consulta, respeitando as permissões do usuário.

**Situação:** planejado — Sprint 05.

### RF-020 — Atualizar e reagendar consultas

O sistema deve permitir ao administrador e à recepcionista atualizar informações ou remarcar consultas, validando novamente a disponibilidade do dentista antes de salvar o novo horário.

**Situação:** planejado — Sprint 05.

### RF-021 — Cancelar consultas

O sistema deve permitir ao administrador e à recepcionista cancelar um agendamento por alteração de sua situação, preservando o registro da consulta no banco.

**Situação:** planejado — Sprint 05.

### RF-022 — Atualizar a situação do atendimento

O sistema deve permitir registrar as situações necessárias ao acompanhamento de consultas, incluindo conclusão e ausência do paciente. O dentista deve poder atualizar os atendimentos sob sua responsabilidade conforme as regras aprovadas.

Os estados e as transições permitidas serão definidos com a equipe; a lista proposta anteriormente não deve ser tratada como enumeração definitiva do banco.

**Situação:** planejado — Sprint 05.

## 5. Requisitos planejados para etapas futuras

### RF-023 — Consultar prontuários clínicos

O sistema deve permitir ao dentista consultar o prontuário e o histórico clínico de pacientes autorizados. A existência de um número de prontuário no cadastro atual não significa que esse módulo clínico esteja implementado.

**Situação:** planejado — etapa futura.

### RF-024 — Registrar evoluções clínicas

O sistema deve permitir ao dentista registrar observações e procedimentos relacionados ao atendimento no prontuário do paciente, identificando o profissional responsável e a data do registro. As regras de rascunho, finalização e alterações posteriores devem ser validadas antes da implementação.

**Situação:** planejado — etapa futura.

### RF-025 — Disponibilizar resumos de apoio ao dentista por IA

O sistema deve disponibilizar ao dentista resumos ou informações de apoio gerados a partir dos dados clínicos autorizados do paciente. A funcionalidade deve ser identificada como apoio ao profissional e depender da disponibilidade do prontuário e de suas evoluções.

O processamento noturno, a preparação em lote e o uso de GPU/OpenCL descritos nos documentos anteriores permanecem propostas técnicas. Não há entrega funcional confirmada desses recursos na Sprint 04.

**Situação:** planejado — etapa futura.

### RF-026 — Consultar registros de auditoria

O sistema deve registrar as operações definidas pela equipe como relevantes para rastreabilidade, relacionando usuário, ação, recurso e momento da operação. Deve disponibilizar sua consulta apenas aos perfis que forem autorizados.

**Situação:** planejado — etapa futura. A tabela `audit_logs` não comprova a execução de auditoria completa pela aplicação.

## 6. Requisitos do backlog com escopo congelado

### RF-027 — Disponibilizar portal do paciente

O sistema poderá permitir que o paciente acesse serviços e solicite agendamentos por um portal próprio, mediante definição de autenticação, permissões e regras de atendimento.

**Situação:** escopo congelado; não disponível no módulo atual.

### RF-028 — Permitir consulta do próprio histórico pelo paciente

O sistema poderá permitir que pacientes autenticados consultem seu histórico de consultas, limitando a visualização às informações autorizadas do próprio paciente.

**Situação:** escopo congelado.

### RF-029 — Gerenciar serviços da clínica

O sistema poderá permitir ao administrador cadastrar e consultar serviços oferecidos pela clínica e suas informações, conforme a modelagem que vier a ser aprovada.

**Situação:** escopo congelado. A modelagem atual apresentada não possui uma tabela de serviços.

### RF-030 — Apresentar relatórios financeiros

O sistema poderá permitir ao administrador consultar informações financeiras relacionadas aos atendimentos, após definição e implementação do registro de valores, cobranças ou pagamentos necessários.

**Situação:** escopo congelado. O dashboard atual não representa um módulo financeiro implementado.

## 7. Melhorias propostas, sujeitas à priorização

| Identificador | Melhoria | Resultado esperado |
|---|---|---|
| RF-031 | Formatar CPF e telefone nos formulários | Permitir digitação numérica com apresentação visual de CPF e telefone, mantendo o formato aceito pela API. |
| RF-032 | Organizar endereço e consultar CEP | Exibir campos separados, preencher dados disponíveis por CEP e reunir o endereço no campo `address` enviado à API. A edição dos endereços existentes deve ser contemplada. |
| RF-033 | Gerar número de prontuário automaticamente | Criar um identificador único no backend durante o cadastro, sem exigir digitação manual. |

**Situação dos itens:** melhoria proposta. Sua inclusão na Sprint 05 depende da prioridade do módulo de Agenda.

Docker e o script de dados fictícios são atividades de infraestrutura e apoio ao desenvolvimento. Permanecem no planejamento da Sprint e não representam funcionalidades clínicas disponíveis ao usuário final.

## 8. Requisitos não funcionais

Os requisitos desta seção estabelecem condições de qualidade, segurança, desempenho, manutenção e operação do Lumina Odonto. A classificação informa se o requisito foi confirmado no módulo atual ou se ainda depende de implementação e validação.

### 8.1 Segurança e controle de acesso

#### RNF-001 — Proteger senhas armazenadas

O sistema deve armazenar somente o hash das senhas dos usuários, utilizando algoritmo apropriado para derivação de senha. Senhas em texto simples não devem ser gravadas no banco de dados, registradas em logs ou retornadas pela API.

**Situação:** implementado no módulo atual com Argon2, conforme a documentação da Sprint 04.

#### RNF-002 — Proteger rotas e operações autorizadas

O sistema deve exigir autenticação nas rotas protegidas e verificar no backend se o perfil autenticado possui permissão para executar cada operação. A ocultação de botões ou telas no frontend não deve ser considerada mecanismo suficiente de autorização.

**Situação:** implementado no primeiro módulo; deve ser mantido e testado no módulo de Agenda.

#### RNF-003 — Limitar a duração e a renovação da sessão

O sistema deve utilizar tokens com prazo de expiração, distinguir tokens de acesso e atualização e exigir nova autenticação quando a sessão não puder ser renovada. O encerramento da sessão deve remover do navegador os dados locais utilizados para autenticação.

**Situação:** implementado no fluxo atual com JWT e armazenamento temporário no `sessionStorage`.

#### RNF-004 — Manter segredos fora do repositório

Credenciais do banco, chaves de assinatura, senhas iniciais e outros segredos devem ser fornecidos por variáveis de ambiente e não devem ser versionados. O repositório deve disponibilizar somente exemplos sem valores reais, como `.env.example`.

**Situação:** obrigatório para todos os ambientes; deve ser verificado em cada Pull Request.

#### RNF-005 — Restringir origens de acesso à API

A API deve aceitar requisições do navegador somente das origens configuradas para o ambiente em uso. A configuração de produção não deve liberar origens indiscriminadamente.

**Situação:** configurável no backend atual; requer revisão na preparação de cada ambiente.

#### RNF-006 — Reduzir tentativas abusivas de autenticação

O sistema deve limitar tentativas repetidas de login e apresentar resposta compreensível quando o limite for excedido, sem revelar se o e-mail informado existe no sistema.

**Situação:** implementado no módulo atual; a estratégia deve ser reavaliada antes do uso em produção distribuída.

### 8.2 Privacidade, dados pessoais e rastreabilidade

#### RNF-007 — Aplicar minimização e finalidade dos dados

O sistema deve solicitar e tratar somente os dados pessoais necessários à gestão da clínica e ao atendimento odontológico. Novos campos e integrações devem possuir finalidade definida antes da implementação.

**Situação:** diretriz obrigatória para evolução do sistema.

#### RNF-008 — Impedir exposição indevida de dados

A API, o frontend, os logs e as mensagens de erro não devem expor hashes de senha, tokens, credenciais do banco ou detalhes internos desnecessários. Dados de pacientes devem ser acessíveis somente aos usuários autorizados da respectiva clínica.

**Situação:** parcialmente atendido no módulo atual; exige revisão contínua e testes específicos de isolamento entre clínicas.

#### RNF-009 — Preservar rastreabilidade de operações sensíveis

O sistema deve permitir o registro de operações sensíveis definidas pela equipe, identificando o usuário, a ação, o recurso afetado e o momento da ocorrência. O acesso aos registros deve ser restrito aos perfis autorizados.

**Situação:** planejado. A existência da tabela `audit_logs` não comprova auditoria funcional completa.

#### RNF-010 — Observar a LGPD e revisar o uso em ambiente real

O tratamento de dados pessoais e clínicos deve observar os princípios aplicáveis da Lei Geral de Proteção de Dados. Antes do uso com pacientes reais, a equipe e a organização responsável devem revisar bases legais, perfis de acesso, retenção, descarte, atendimento aos direitos dos titulares e medidas de segurança.

**Situação:** requisito de conformidade; a aplicação acadêmica atual não deve ser considerada pronta para produção apenas por possuir autenticação.

### 8.3 Integridade, persistência e recuperação

#### RNF-011 — Manter integridade referencial

O banco de dados deve utilizar chaves primárias, chaves estrangeiras, restrições de nulidade e restrições de unicidade para impedir registros inconsistentes. A aplicação deve tratar as violações dessas regras com respostas compreensíveis.

**Situação:** atendido no esquema PostgreSQL atual para as entidades implementadas; deve ser validado na Agenda.

#### RNF-012 — Preservar dados relevantes por inativação lógica

Registros que precisem permanecer disponíveis para histórico ou relacionamentos futuros não devem ser removidos fisicamente por operações comuns da interface. Quando aplicável, o sistema deve alterar sua situação de atividade ou cancelamento.

**Situação:** implementado para pacientes e proposto para cancelamento de agendamentos.

#### RNF-013 — Disponibilizar backup e recuperação

Antes do uso em ambiente real, o banco de dados deve possuir rotina documentada de backup e restauração, com periodicidade, responsável, local protegido de armazenamento e testes periódicos de recuperação.

**Situação:** pendente de definição para o ambiente de implantação.

#### RNF-014 — Versionar alterações do banco

As mudanças de estrutura do banco devem ser reproduzíveis e versionadas. A equipe deve manter uma única estratégia confiável de criação e evolução do esquema, evitando divergência entre scripts SQL, modelos SQLAlchemy e migrações.

**Situação:** pendente de consolidação. O esquema PostgreSQL atual e as migrações devem ser reconciliados antes da automatização do ambiente.

### 8.4 Usabilidade e acessibilidade

#### RNF-015 — Apresentar interface consistente e responsiva

A interface deve manter padrões consistentes de cores, tipografia, botões, formulários, navegação e mensagens. As telas principais devem permanecer utilizáveis em resoluções comuns de computadores e dispositivos móveis definidos pela equipe.

**Situação:** parcialmente atendido; requer validação responsiva sistemática.

#### RNF-016 — Informar claramente o resultado das ações

O sistema deve apresentar estados de carregamento e mensagens de sucesso, validação, indisponibilidade, autenticação e autorização em linguagem compreensível, sem exibir rastros de exceção ou termos técnicos desnecessários.

**Situação:** implementado nos fluxos principais da Sprint 04; deve ser mantido no módulo de Agenda.

#### RNF-017 — Evitar perda acidental de informações

Formulários devem preservar os dados preenchidos quando ocorrer erro corrigível e solicitar confirmação antes de ações que alterem significativamente a situação de um registro, como inativação ou cancelamento.

**Situação:** requisito a validar e complementar nas interfaces atuais e futuras.

#### RNF-018 — Oferecer acessibilidade básica

A interface deve permitir navegação por teclado, apresentar rótulos associados aos campos, manter foco visível, utilizar contraste legível e não depender exclusivamente de cores para comunicar situações.

**Situação:** requisito proposto; deve ser incluído no roteiro de revisão do frontend.

### 8.5 Desempenho, confiabilidade e disponibilidade

#### RNF-019 — Responder adequadamente às operações interativas

Em ambiente local de desenvolvimento, com volume de demonstração, as operações comuns de autenticação, consulta e cadastro devem responder em até 2 segundos em pelo menos 95% das requisições, desconsiderando indisponibilidade externa e o primeiro carregamento de instalação ou compilação.

**Situação:** meta proposta; ainda requer medição automatizada antes de ser classificada como atendida.

#### RNF-020 — Suportar paginação e filtros em listas crescentes

As listagens de pacientes, usuários e agendamentos devem adotar paginação ou outra estratégia equivalente quando o volume de registros tornar inadequado o carregamento completo. Os filtros mais utilizados devem ser processados sem exigir a recuperação integral da base pelo navegador.

**Situação:** planejado; o limite que motivará a paginação deve ser definido com testes de volume.

#### RNF-021 — Manter consistência em falhas

Uma falha durante cadastro ou atualização não deve deixar dados parcialmente gravados. Operações que dependam de mais de uma alteração relacionada devem utilizar transações apropriadas.

**Situação:** requisito obrigatório para todos os módulos; deve ser coberto por testes de serviço e persistência.

#### RNF-022 — Disponibilizar verificação de saúde

O backend deve disponibilizar uma verificação de saúde que permita identificar se a aplicação está em execução. Para uso com Docker e em implantação, deve existir também uma verificação de prontidão que confirme a comunicação com o PostgreSQL.

**Situação:** health check da aplicação implementado; verificação de prontidão do banco pendente.

### 8.6 Compatibilidade e portabilidade

#### RNF-023 — Utilizar navegadores compatíveis

O frontend deve funcionar nas versões atuais dos navegadores Chromium utilizados pela equipe. A equipe deve validar pelo menos um segundo navegador moderno antes da entrega destinada a uso externo.

**Situação:** compatibilidade principal validada informalmente; matriz de navegadores pendente.

#### RNF-024 — Reproduzir o ambiente de execução

O projeto deve permitir a execução integrada do frontend, backend e PostgreSQL por meio de instruções documentadas. A configuração com Docker Compose deve utilizar PostgreSQL, volumes persistentes, variáveis de ambiente e verificações de saúde coerentes com a arquitetura atual.

**Situação:** planejado para a Sprint 05; a configuração antiga baseada em MySQL não representa o ambiente atual.

#### RNF-025 — Manter configurações separadas por ambiente

O sistema deve permitir configurações distintas para desenvolvimento, teste e produção, sem necessidade de alterar o código-fonte para trocar endereços, credenciais, chaves ou origens permitidas.

**Situação:** parcialmente atendido por variáveis de ambiente; precisa ser concluído na containerização.

### 8.7 Manutenibilidade, versionamento e testes

#### RNF-026 — Preservar separação de responsabilidades

O backend deve manter a separação entre rotas, validação de dados, regras de negócio, acesso ao banco e segurança. O frontend deve separar comunicação com a API, controle de sessão e componentes de interface de forma que novos módulos possam ser acrescentados sem duplicar regras centrais.

**Situação:** atendido em parte pela arquitetura atual; deve orientar as novas implementações.

#### RNF-027 — Manter documentação técnica atualizada

Alterações de endpoints, permissões, modelos, variáveis de ambiente, regras de negócio e instruções de execução devem ser refletidas na documentação do repositório na mesma Sprint em que forem incorporadas.

**Situação:** requisito contínuo de desenvolvimento.

#### RNF-028 — Manter histórico de desenvolvimento compreensível

As alterações devem ser desenvolvidas em branches identificáveis, registradas em commits com descrições claras e integradas por revisão ou Pull Request sempre que o fluxo da equipe permitir.

**Situação:** processo utilizado pela equipe e exigido nas Sprints.

#### RNF-029 — Validar alterações antes da integração

Toda alteração deve passar pelas verificações aplicáveis ao componente modificado. No backend, devem ser executados a compilação e os testes automatizados. No frontend, devem ser executadas a verificação de tipos e a compilação de produção. Fluxos que dependam de persistência e permissão devem possuir testes integrados ou roteiro manual registrado.

**Situação:** aplicado na Sprint 04; deve permanecer como critério de aceite.

#### RNF-030 — Utilizar dados fictícios reproduzíveis para teste

O ambiente de desenvolvimento deve permitir gerar dados fictícios consistentes por script idempotente, sem utilizar dados pessoais reais. A execução repetida não deve criar duplicidades indevidas nem apagar dados existentes sem uma opção explícita.

**Situação:** planejado para apoio ao desenvolvimento e aos testes da Sprint 05.

## 9. Conciliação com os documentos anteriores

| Tema | Referência adotada neste catálogo |
|---|---|
| Perfis | Três perfis de equipe: administrador, recepcionista e dentista. O paciente não possui login na versão atual. |
| Permissões do dentista | Cadastro, consulta e edição de pacientes, sem inativação. A antiga herança integral das permissões da recepção não representa o módulo atual. |
| Usuário e paciente | Cadastros distintos, conforme a modelagem relacional e a evolução da Sprint 04. |
| Agenda | Planejada para a Sprint 05; sua tabela ou tela visual não comprova funcionamento integrado. |
| Prontuário, IA e auditoria | Planejados para etapas futuras; não classificados como implementados por existirem diagramas ou tabelas. |
| Serviços, portal e financeiro | Mantidos no escopo congelado do Product Backlog. |
| Tecnologia | A Sprint 04 consolida frontend, FastAPI e PostgreSQL. Alternativas tecnológicas listadas na arquitetura antiga não equivalem a recursos implementados. |

## 10. Documentos consultados

- `Relatorio Sprint 4.pdf`: referência principal, especialmente seções 4.4 a 4.10 e 4.13 a 4.16.
- `Diagrama de Classes do Sistema.pdf`: estrutura e relacionamentos previstos.
- `Documento da Clinica Backend.pdf`: proposta anterior de backend, revisada conforme a Sprint 04.
- `Documento de Arquitetura do Sistema.pdf`: organização e componentes previstos.
- `Modelo de Entidade Relacional.pdf`: entidades e atributos.
- `Modelo_Relacional_Clinica_Odontologica.pdf`: tabelas e campos modelados.
- `Processo do Prontuario Médico.pdf`: proposta de processamento em lote e apoio por IA.
- `Produto Backlog - Sistemas de Gestão de Clinica Odotonlogica.pdf`: prioridades iniciais e itens congelados.

A classificação de implementação baseia-se na documentação e nos testes relatados pela equipe. Esta revisão não inclui uma nova inspeção do código do repositório.