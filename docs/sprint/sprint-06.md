Sprint 6 — Aprimoramento do Lumina Odonto

**Período de trabalho:** 12 a 17 de outubro de 2026  
**Prazo da disciplina:** 17/10/2026, às 23h59  
**Meta interna:** deixar o fluxo principal demonstrável até 16/10  
**Situação deste documento:** proposta para alinhamento da equipe

## 1. Objetivo

Entregar um terceiro módulo funcional de **Prontuário e Evolução Clínica**, integrado a pacientes, dentistas, Agenda, API FastAPI e PostgreSQL. A Sprint também contempla correções identificadas na Pré-Banca e nos testes da Sprint 5, melhorias pontuais de interface e navegação, e a atualização do ambiente Docker.

O módulo deve permitir demonstrar, com dados fictícios, o caminho: dentista entra → abre uma consulta sob sua responsabilidade → consulta o prontuário autorizado → registra uma evolução → salva um rascunho → finaliza o registro → encontra o histórico após reiniciar a aplicação.

## 2. Decisões e limites do escopo

### 2.1 Acesso às informações clínicas

- A recepção pode administrar pacientes e agendamentos, mas não pode ler ou alterar descrição clínica, procedimentos e evoluções.
- O perfil de administrador não recebe acesso clínico automático. Se um administrador também exercer atendimento odontológico, deverá ter uma identidade profissional vinculada e uma regra de acesso específica, aprovada pela equipe.
- O dentista autenticado acessa somente pacientes para os quais exista vínculo assistencial autorizado. Na primeira versão, a consulta atribuída a ele pode servir como prova desse vínculo; a equipe deve definir a abrangência temporal e o acesso ao histórico.
- O dentista pode criar e editar somente os próprios rascunhos. A finalização registra autoria e horário e bloqueia edição ou exclusão pelas rotas normais. Correções posteriores exigirão um mecanismo próprio, a ser definido com orientação profissional.
- O paciente possui direito de acesso e cópia do prontuário, mas um portal de login do paciente não será implementado nesta Sprint. Documentar um procedimento supervisionado de solicitação e entrega de cópia.
- A API deve verificar essas regras em cada rota e cada registro. Esconder botões no frontend não constitui controle de acesso.

Essas regras são uma **proposta de implementação** para o protótipo acadêmico. A equipe deve validá-las com o professor e registrar ajustes antes de tratar o módulo como pronto para uso clínico.

### 2.2 Segurança e proposta de TPM

João ficará como responsável inicial pela investigação da proposta de proteção com TPM, em colaboração com Tarcísio e Otávio. O resultado desta Sprint será um documento técnico e, se houver tempo, uma prova de conceito isolada. A pesquisa deve descrever: quais dados proteger; onde estão as chaves; como autorizar outro dentista responsável; o que ocorre na perda do computador; como recuperar backup; e quais riscos permanecem para quem administra o sistema ou o banco.

O TPM pode proteger chaves e apoiar a criptografia do disco, mas não substitui autorização por usuário nem implementa sozinho criptografia de ponta a ponta. Nenhuma função de segurança futura deve ser apresentada como já implementada no prontuário. A interface local continua envolvendo navegador, API e PostgreSQL, mesmo que executados no mesmo computador.

O projeto usará apenas dados fictícios para demonstração. Finalizar uma evolução no sistema não será descrito como assinatura digital certificada.

### 2.3 Funcionalidades adiadas

Portal do paciente, odontograma, anexos de exames, prescrições, assinatura digital certificada, integração funcional de IA e criptografia de ponta a ponta completa permanecem fora do escopo da Sprint 6.

## 3. Entregas obrigatórias da disciplina

1. Registrar as observações recebidas na Pré-Banca, as ações correspondentes e as pendências. A recomendação sobre sigilo do prontuário já está identificada; outras observações precisam ser acrescentadas pela equipe.
2. Demonstrar o terceiro módulo com operações reais e dados persistidos.
3. Demonstrar integração entre autenticação, pacientes, Agenda, prontuário e evoluções.
4. Mostrar melhorias de interface e mensagens compreensíveis para o usuário.
5. Corrigir os problemas de navegação observados na etapa anterior.
6. Manter repositório e documentação atualizados e reunir evidências para o PDF cumulativo de todas as Sprints.

## 4. Divisão de atividades

### 4.1 Paulo Sérgio — Regras, processo, banco e validação

- Desenhar um BPMN **enxuto** do atendimento: recepção agenda, dentista atende, registra evolução e finaliza, paciente solicita acesso quando necessário. Identificar quem executa cada ação e onde existem dados clínicos sigilosos.
- Atualizar requisitos e regras de negócio com a matriz de acesso do item 2.1, vínculo entre dentista e paciente, estados da evolução e critérios de finalização.
- Conferir as tabelas `medical_records` e `clinical_evolutions` no PostgreSQL e apoiar alterações de banco apenas quando o contrato do módulo exigir. Registrar como aplicar a alteração em banco já existente; não presumir que editar `schema.sql` atualiza o banco local.
- Preparar roteiro de testes por perfil e registrar as observações reais da Pré-Banca, bugs, correções e evidências.
- Validar o fluxo completo no PostgreSQL local e conferir persistência após reinício da API.

**Aceite:** BPMN, matriz de acesso e roteiro revisados pela equipe; evidências dos fluxos e da persistência; pendências registradas com responsável.

### 4.2 Tarcísio — Backend do prontuário e das evoluções

- Revisar ORM, esquema SQL e migrações das tabelas clínicas, definindo uma estratégia única para atualizar bancos existentes.
- Criar schemas, repositórios, serviço e rotas para abrir/consultar prontuário, listar evoluções, criar rascunho, editar rascunho próprio e finalizar evolução.
- Integrar o registro ao paciente e, quando aplicável, ao agendamento e ao dentista responsável.
- Aplicar autorização por clínica e vínculo assistencial em todas as consultas e mutações. Administrador e recepcionista não devem obter o conteúdo clínico por rotas alternativas.
- Registrar autor, data/hora e CRO do profissional de forma coerente com o registro exibido. Impedir edição ou exclusão comum de evolução finalizada.
- Padronizar respostas de erro que o frontend consiga apresentar, incluindo acesso negado, registro inexistente e transição inválida.
- Revisar com João os testes que cobrem acesso indevido e finalização.

**Aceite:** rotas documentadas no Swagger, persistência em PostgreSQL, controles aplicados no backend e fluxo demonstrável com dados fictícios.

### 4.3 João Vitor — Testes técnicos e investigação de segurança

- Construir testes para dentista responsável, outro dentista, recepção, administrador e usuário de outra clínica. Cobrir leitura, criação, edição de rascunho, finalização e tentativa de alterar registro finalizado.
- Testar integração das rotas com paciente e consulta. Validar uma execução real em PostgreSQL além dos testes em SQLite, com dados fictícios.
- Investigar o uso de TPM e criptografia para o futuro do módulo. Produzir um documento curto com desenho proposto, ameaças cobertas, limitações, gestão e recuperação das chaves e passos necessários para implementação posterior.
- Apoiar Tarcísio na correção de problemas encontrados; comunicar cedo qualquer bloqueio no banco ou na autorização.

**Aceite:** testes executados e resultados registrados; demonstração de que acessos proibidos são bloqueados; proposta de segurança revisável sem afirmar proteção ainda inexistente.

### 4.4 Caio Cesar — Frontend clínico

- Criar as telas de prontuário e histórico de evoluções a partir das rotas reais, vinculadas ao paciente e ao agendamento selecionado.
- Criar formulário para descrição clínica, procedimento e observações, com ações claras para salvar rascunho, editar o próprio rascunho e finalizar.
- Exibir autor, CRO, data/hora e situação do registro. Após finalizar, atualizar a tela e impedir visualmente ações de edição.
- Apresentar estados de carregamento e mensagens de sucesso, erro, sessão expirada e acesso negado. Não colocar informações clínicas nos logs do navegador.
- Restringir a navegação clínica aos dentistas autorizados, lembrando que a API permanece responsável pela autorização final.

**Aceite:** fluxo clínico completo demonstrável pela interface, com dados reais da API e respostas compreensíveis.

### 4.5 Luiz Otávio — Integração, interface, navegação e ambiente

- Definir com Caio e Tarcísio o contrato das rotas e apoiar a integração entre formulário, API e PostgreSQL.
- Corrigir os controles de situação da Agenda observados na Sprint 5: apresentar as ações permitidas para cada perfil e estado, especialmente conclusão e ausência pelo dentista responsável quando a regra temporal permitir.
- Revisar navegação entre Agenda, paciente e prontuário, sem expor conteúdo clínico em telas administrativas.
- Atualizar a configuração Docker para PostgreSQL, API e frontend; documentar inicialização e validar o fluxo integrado no ambiente. Solicitar apoio técnico de João se a integração do Docker ameaçar o prazo do terceiro módulo.
- Acompanhar a proposta de TPM para avaliar impacto na arquitetura atual, sem acoplar uma solução experimental ao fluxo obrigatório desta Sprint.

**Aceite:** interface e API integradas, navegação demonstrável, correções da Agenda verificadas e ambiente Docker documentado ou bloqueio concreto registrado com plano de resolução.

### 4.6 Cassiano Augusto — Evidências e relatório

- Consolidar relatos individuais, observações da Pré-Banca, decisões de escopo, testes e dificuldades.
- Organizar capturas legíveis da Agenda, prontuário, Swagger, PostgreSQL, controles de acesso e Docker.
- Preparar o **PDF único cumulativo** com as Sprints anteriores e a Sprint 6, identificação do grupo e do projeto, link atualizado do GitHub, melhorias e próximos passos.
- Conferir a numeração contínua das figuras e a distinção entre funcionalidades comprovadas e propostas futuras.

**Aceite:** PDF revisável pela equipe antes do envio pelo Scrum Master.

## 5. Plano de execução

| Data | Marco verificável |
| --- | --- |
| **12/10, segunda** | Validar observações da Pré-Banca, regras clínicas, contrato das rotas e divisão de trabalho. |
| **13/10, terça** | Banco/ORM e endpoints iniciais; telas e testes iniciados sobre contrato acordado. |
| **14/10, quarta** | Cadastro e consulta de rascunho funcionando de ponta a ponta. |
| **15/10, quinta** | Finalização, permissões, correções de interface e ensaio com PostgreSQL. |
| **16/10, sexta** | Correções finais, Docker, coleta de evidências e revisão do PDF. |
| **17/10, sábado** | Margem para problemas restantes e envio oficial até 23h59. |

Se o prazo apertar, a prioridade é: **terceiro módulo funcional e seguro por perfil → integração e testes → correções de interface e navegação → Docker → pesquisa de TPM**. A pesquisa não deve impedir a conclusão do fluxo clínico.

## 6. Roteiro mínimo de demonstração

1. Entrar como recepcionista, localizar paciente e agendar uma consulta; tentar abrir conteúdo clínico e confirmar acesso negado.
2. Entrar como dentista responsável, abrir a consulta e consultar o prontuário autorizado.
3. Criar uma evolução em rascunho, sair e entrar novamente; conferir que o texto permanece salvo.
4. Editar o próprio rascunho e finalizá-lo; conferir autor, CRO, data/hora e bloqueio de nova edição.
5. Entrar como outro dentista e como administrador; confirmar que nenhum deles obtém conteúdo clínico sem vínculo assistencial autorizado.
6. Reiniciar a aplicação e conferir no PostgreSQL e na interface que prontuário e evolução permanecem disponíveis ao profissional autorizado.
7. Mostrar as correções da Agenda, a navegação entre módulos e, se concluído, o fluxo em Docker.

## 7. Evidências e pendências a registrar

- Capturas da interface nas etapas principais, sem dados reais de pacientes.
- Resultado dos testes automatizados e das verificações manuais no PostgreSQL.
- Respostas da API para acesso permitido e proibido.
- Registro das ações tomadas para cada observação da Pré-Banca.
- Situação do Docker, dos links do repositório, das migrações e da proposta de TPM, indicando claramente o que foi concluído e o que continua pendente.

## 8. Referências para validar as regras clínicas

- [Código de Ética Odontológica do CFO](https://website.cfo.org.br/wp-content/uploads/2018/03/codigo_etica.pdf), especialmente artigos 17 e 18 sobre prontuário físico ou digital e acesso do paciente.
- [Manual do Prontuário do CFO](https://website.cfo.org.br/wp-content/uploads/2026/03/CFO_Manual_do_Prontuario_Ebook.pdf), sobre sigilo, acesso e continuidade da assistência.
- [Lei nº 13.787/2018](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13787.htm), sobre guarda e proteção de documentos digitais de prontuário.
- [Microsoft Learn: uso do TPM no Windows](https://learn.microsoft.com/en-us/windows/security/hardware-security/tpm/how-windows-uses-the-tpm), para delimitar a proteção oferecida pelo hardware.
