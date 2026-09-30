# Plano de Testes — Agenda e Agendamentos

## 1. Identificação

- **Projeto:** Lumina Odonto
- **Módulo:** Agenda e Agendamentos
- **Sprint:** Sprint 5 — Segundo Módulo Funcionando
- **Responsável pela validação:** Paulo Sérgio Barros de Souza
- **Situação do documento:** Proposta de testes
- **Data de elaboração:** 30 de setembro de 2026

## 2. Objetivo

Este documento define o roteiro de testes do módulo de Agenda e Agendamentos do Lumina Odonto.

Os testes deverão verificar:

- funcionamento das rotas da API;
- integração entre frontend, API e PostgreSQL;
- persistência dos agendamentos;
- regras de permissão por perfil;
- prevenção de conflitos de horário;
- validação dos estados do agendamento;
- isolamento dos dados por clínica;
- tratamento de dados inválidos;
- mensagens apresentadas ao usuário;
- manutenção dos dados após reinicialização da aplicação.

Este plano deverá ser atualizado caso ocorram mudanças nas regras de negócio ou no contrato final da API.

## 3. Escopo

O plano contempla as seguintes funcionalidades:

- criação de agendamentos;
- consulta da agenda;
- consulta dos detalhes de um agendamento;
- filtros por período, paciente, dentista e situação;
- edição e reagendamento;
- confirmação da consulta;
- conclusão do atendimento;
- cancelamento lógico;
- registro de ausência do paciente;
- prevenção de conflitos de horário;
- permissões de administrador, recepcionista e dentista;
- isolamento entre clínicas;
- persistência dos dados no PostgreSQL;
- mensagens de sucesso e erro no frontend.

Não fazem parte deste plano:

- prontuário odontológico completo;
- evolução clínica;
- prescrições;
- odontograma;
- integração com inteligência artificial;
- envio automático de notificações;
- integração com serviços externos de calendário.

## 4. Regras consideradas neste plano

Este plano utiliza como referência as regras propostas em `docs/business-rules.md` e `docs/agenda-data-proposal.md`.

As regras ainda dependentes de validação técnica deverão ser atualizadas após a revisão da equipe.

### 4.1 Estados previstos

Os estados considerados são:

```text
SCHEDULED
CONFIRMED
COMPLETED
CANCELED
NO_SHOW
```

O estado `NO_SHOW` depende de inclusão na restrição da tabela `appointments`.

### 4.2 Transições propostas

```text
SCHEDULED → CONFIRMED
SCHEDULED → CANCELED
SCHEDULED → NO_SHOW

CONFIRMED → COMPLETED
CONFIRMED → CANCELED
CONFIRMED → NO_SHOW
```

Agendamentos com estado `COMPLETED`, `CANCELED` ou `NO_SHOW` serão considerados encerrados.

### 4.3 Permissões consideradas

| Operação | Administrador | Recepcionista | Dentista |
| :-- | :-- | :-- | :-- |
| Consultar agenda | Agenda da clínica | Agenda da clínica | Próprios atendimentos |
| Criar agendamento | Permitido | Permitido | Negado |
| Editar ou reagendar | Permitido | Permitido | Negado |
| Cancelar | Permitido | Permitido | Negado |
| Confirmar consulta | Permitido | Permitido | Negado |
| Registrar conclusão | Permitido | Negado | Próprios atendimentos |
| Registrar ausência | Permitido | Permitido | Próprios atendimentos |

## 5. Ambiente de testes

Os testes deverão ser executados utilizando:

- frontend do Lumina Odonto;
- API FastAPI;
- PostgreSQL;
- Swagger;
- navegador web;
- terminal do WSL;
- testes automatizados com `pytest`;
- Docker e Docker Compose, quando o ambiente estiver disponível.

Endereços locais esperados:

```text
Frontend: http://localhost:5173
API:      http://127.0.0.1:8000
Swagger:  http://127.0.0.1:8000/docs
Health:   http://127.0.0.1:8000/health
```

Caso o Vite utilize outra porta, deve ser considerado o endereço exibido no terminal.

## 6. Pré-condições

Antes dos testes, deverá ser confirmado que:

- o PostgreSQL está ativo;
- a API consegue acessar o banco;
- o frontend consegue acessar a API;
- as migrações ou ajustes do banco foram aplicados;
- existe pelo menos uma clínica de demonstração;
- existem usuários ativos com os três perfis;
- os usuários dentistas possuem registros correspondentes em `dentists`;
- existem pacientes ativos e inativos;
- as credenciais de teste não foram publicadas no repositório;
- os dados utilizados são fictícios ou anonimizados;
- o horário do sistema está configurado corretamente.

## 7. Dados necessários

Para a execução completa deste plano, recomenda-se possuir:

| Dado | Quantidade mínima |
| :-- | --: |
| Clínicas | 2 |
| Administradores | 2, sendo um por clínica |
| Recepcionistas | 2, sendo um por clínica |
| Dentistas ativos | 4, sendo dois por clínica |
| Dentista inativo | 1 |
| Pacientes ativos | 6 |
| Pacientes inativos | 2 |
| Agendamentos futuros | 6 |
| Agendamentos concluídos | 2 |
| Agendamentos cancelados | 2 |
| Agendamentos com ausência | 2 |

A segunda clínica será utilizada exclusivamente para testar o isolamento dos dados.

## 8. Rotas previstas

As rotas abaixo são uma referência e deverão ser atualizadas de acordo com a implementação final:

```text
POST   /api/v1/appointments
GET    /api/v1/appointments
GET    /api/v1/appointments/{id}
PATCH  /api/v1/appointments/{id}
```

Filtros esperados para a listagem:

```text
start_date
end_date
dentist_id
patient_id
status
```

## 9. Procedimento padrão

Para cada caso de teste:

1. Registrar o usuário e o perfil utilizado.
2. Registrar os dados enviados.
3. Executar a operação pelo frontend ou Swagger.
4. Anotar o código HTTP retornado.
5. Conferir a mensagem apresentada.
6. Consultar o PostgreSQL quando houver alteração de dados.
7. Marcar o teste como aprovado, reprovado ou bloqueado.
8. Registrar o link ou nome da evidência.
9. Abrir um bug quando o resultado for diferente do esperado.

## 10. Casos de teste — autenticação e acesso

| ID | Cenário | Procedimento | Resultado esperado |
| :-- | :-- | :-- | :-- |
| AG-AUT-001 | Acesso sem autenticação | Tentar consultar a Agenda sem token | API retorna `401` e o frontend redireciona para o login |
| AG-AUT-002 | Token inválido | Consultar a Agenda com token inválido | API retorna `401` e apresenta mensagem de sessão inválida |
| AG-AUT-003 | Administrador autenticado | Entrar como administrador e abrir a Agenda | Agenda da clínica é exibida |
| AG-AUT-004 | Recepcionista autenticada | Entrar como recepcionista e abrir a Agenda | Agenda da clínica é exibida |
| AG-AUT-005 | Dentista autenticado | Entrar como dentista e abrir a Agenda | Somente os próprios atendimentos são exibidos |

## 11. Casos de teste — criação de agendamentos

| ID | Cenário | Procedimento | Resultado esperado |
| :-- | :-- | :-- | :-- |
| AG-CRI-001 | Administrador cria agendamento | Informar paciente, dentista, data futura, horário e duração | Agendamento criado com código `201` |
| AG-CRI-002 | Recepcionista cria agendamento | Informar todos os campos válidos | Agendamento criado com código `201` |
| AG-CRI-003 | Dentista tenta criar | Tentar cadastrar uma consulta como dentista | Operação negada com código `403` |
| AG-CRI-004 | Campo obrigatório ausente | Enviar cadastro sem paciente, dentista ou horário | Operação negada com código `422` |
| AG-CRI-005 | Duração inválida | Informar duração igual a zero ou negativa | Operação negada e mensagem clara |
| AG-CRI-006 | Data no passado | Informar data ou horário anterior ao momento atual | Operação negada |
| AG-CRI-007 | Paciente inexistente | Informar ID de paciente inexistente | Operação negada com código `404` |
| AG-CRI-008 | Dentista inexistente | Informar ID de dentista inexistente | Operação negada com código `404` |
| AG-CRI-009 | Paciente inativo | Tentar agendar para paciente inativo | Operação negada |
| AG-CRI-010 | Dentista inativo | Tentar agendar para dentista cujo usuário esteja inativo | Operação negada |
| AG-CRI-011 | Clínica enviada pelo frontend | Tentar informar manualmente outro `clinic_id` | API ignora ou rejeita o valor e utiliza a clínica do usuário autenticado |

## 12. Casos de teste — conflitos de horário

| ID | Cenário | Procedimento | Resultado esperado |
| :-- | :-- | :-- | :-- |
| AG-CON-001 | Mesmo dentista e mesmo horário | Criar dois agendamentos para o mesmo dentista e horário | Segundo agendamento é recusado com código `409` |
| AG-CON-002 | Sobreposição parcial | Criar consulta das 10h às 11h e tentar outra às 10h30 | Segundo agendamento é recusado |
| AG-CON-003 | Consulta imediatamente posterior | Criar consulta das 10h às 10h30 e outra às 10h30 | Segundo agendamento é permitido |
| AG-CON-004 | Dentistas diferentes | Criar consultas no mesmo horário para dentistas diferentes | Ambas são permitidas |
| AG-CON-005 | Horário anteriormente cancelado | Cancelar consulta e criar outra no mesmo horário | Novo agendamento é permitido |
| AG-CON-006 | Horário com ausência registrada | Marcar consulta como `NO_SHOW` e criar outra no horário liberado | Novo agendamento é permitido quando aplicável |
| AG-CON-007 | Duas solicitações simultâneas | Enviar duas criações simultâneas para o mesmo dentista e horário | Apenas uma é criada e a outra é recusada |

O teste `AG-CON-007` deverá ser automatizado, pois não é confiável reproduzir concorrência manualmente pelo Swagger.

## 13. Casos de teste — consulta e filtros

| ID | Cenário | Procedimento | Resultado esperado |
| :-- | :-- | :-- | :-- |
| AG-LIS-001 | Listar agenda da clínica | Consultar sem filtros como administrador | Apenas agendamentos da clínica autenticada são retornados |
| AG-LIS-002 | Filtrar por período | Informar data inicial e final | Apenas consultas dentro do período são retornadas |
| AG-LIS-003 | Filtrar por dentista | Informar `dentist_id` | Apenas consultas do dentista são retornadas |
| AG-LIS-004 | Filtrar por paciente | Informar `patient_id` | Apenas consultas do paciente são retornadas |
| AG-LIS-005 | Filtrar por situação | Informar um status válido | Apenas consultas com a situação informada são retornadas |
| AG-LIS-006 | Combinar filtros | Informar período, dentista e situação | Somente os registros compatíveis são retornados |
| AG-LIS-007 | Período inválido | Informar data final anterior à data inicial | Operação negada com mensagem clara |
| AG-LIS-008 | Consultar detalhes | Consultar um ID válido | Retorna todos os dados autorizados do agendamento |
| AG-LIS-009 | ID inexistente | Consultar um ID inexistente | Retorna código `404` |
| AG-LIS-010 | Dentista consulta outro dentista | Dentista tenta consultar atendimento de outro profissional | Operação negada ou registro não localizado |

## 14. Casos de teste — edição e reagendamento

| ID | Cenário | Procedimento | Resultado esperado |
| :-- | :-- | :-- | :-- |
| AG-EDI-001 | Administrador reagenda | Alterar data ou horário para um período disponível | Dados atualizados |
| AG-EDI-002 | Recepcionista reagenda | Alterar data ou horário para um período disponível | Dados atualizados |
| AG-EDI-003 | Dentista tenta reagendar | Tentar alterar data ou horário | Operação negada com código `403` |
| AG-EDI-004 | Reagendamento com conflito | Alterar para horário ocupado pelo mesmo dentista | Operação negada com código `409` |
| AG-EDI-005 | Reagendamento para o passado | Alterar para data ou horário passado | Operação negada |
| AG-EDI-006 | Alteração de paciente | Alterar o paciente conforme regra final | Operação aceita ou negada conforme contrato documentado |
| AG-EDI-007 | Editar consulta encerrada | Tentar reagendar consulta concluída, cancelada ou com ausência | Operação negada |

## 15. Casos de teste — estados do agendamento

| ID | Cenário | Procedimento | Resultado esperado |
| :-- | :-- | :-- | :-- |
| AG-STA-001 | Confirmar consulta | Alterar `SCHEDULED` para `CONFIRMED` | Situação atualizada |
| AG-STA-002 | Concluir consulta confirmada | Alterar `CONFIRMED` para `COMPLETED` | Situação atualizada |
| AG-STA-003 | Cancelar consulta agendada | Alterar `SCHEDULED` para `CANCELED` | Registro preservado com nova situação |
| AG-STA-004 | Cancelar consulta confirmada | Alterar `CONFIRMED` para `CANCELED` | Registro preservado com nova situação |
| AG-STA-005 | Registrar ausência | Alterar para `NO_SHOW` | Situação atualizada e registro preservado |
| AG-STA-006 | Estado inexistente | Informar situação fora da lista permitida | Operação negada com código `422` |
| AG-STA-007 | Reabrir cancelada | Tentar alterar `CANCELED` para `SCHEDULED` | Operação negada |
| AG-STA-008 | Reabrir concluída | Tentar alterar `COMPLETED` para `CONFIRMED` | Operação negada |
| AG-STA-009 | Concluir cancelada | Tentar alterar `CANCELED` para `COMPLETED` | Operação negada |
| AG-STA-010 | Apagar fisicamente | Verificar o banco após cancelamento | Registro continua armazenado em `appointments` |

## 16. Casos de teste — permissões

| ID | Cenário | Procedimento | Resultado esperado |
| :-- | :-- | :-- | :-- |
| AG-PER-001 | Administrador consulta agenda | Consultar todos os registros da clínica | Operação permitida |
| AG-PER-002 | Administrador cria consulta | Cadastrar agendamento válido | Operação permitida |
| AG-PER-003 | Administrador cancela consulta | Alterar situação para `CANCELED` | Operação permitida |
| AG-PER-004 | Administrador conclui consulta | Alterar situação para `COMPLETED` | Operação permitida |
| AG-PER-005 | Recepcionista cria consulta | Cadastrar agendamento válido | Operação permitida |
| AG-PER-006 | Recepcionista reagenda consulta | Alterar data ou horário | Operação permitida |
| AG-PER-007 | Recepcionista cancela consulta | Alterar situação para `CANCELED` | Operação permitida |
| AG-PER-008 | Recepcionista registra ausência | Alterar situação para `NO_SHOW` | Operação permitida |
| AG-PER-009 | Recepcionista tenta concluir | Tentar alterar para `COMPLETED` | Operação negada |
| AG-PER-010 | Dentista consulta a própria agenda | Abrir os próprios atendimentos | Operação permitida |
| AG-PER-011 | Dentista conclui próprio atendimento | Alterar próprio atendimento para `COMPLETED` | Operação permitida |
| AG-PER-012 | Dentista registra ausência própria | Alterar próprio atendimento para `NO_SHOW` | Operação permitida |
| AG-PER-013 | Dentista tenta criar consulta | Enviar novo agendamento | Operação negada |
| AG-PER-014 | Dentista tenta cancelar | Alterar próprio atendimento para `CANCELED` | Operação negada |
| AG-PER-015 | Dentista altera atendimento de outro | Informar ID pertencente a outro dentista | Operação negada |

## 17. Casos de teste — isolamento entre clínicas

| ID | Cenário | Procedimento | Resultado esperado |
| :-- | :-- | :-- | :-- |
| AG-CLI-001 | Usuário lista agenda | Usuário da clínica A consulta a Agenda | Dados da clínica B não são retornados |
| AG-CLI-002 | Paciente de outra clínica | Usuário da clínica A tenta agendar paciente da clínica B | Operação negada |
| AG-CLI-003 | Dentista de outra clínica | Usuário da clínica A tenta selecionar dentista da clínica B | Operação negada |
| AG-CLI-004 | Consulta de outra clínica | Usuário da clínica A acessa ID da clínica B | Retorna `403` ou `404`, conforme padrão adotado |
| AG-CLI-005 | Alteração em outra clínica | Usuário da clínica A tenta alterar registro da clínica B | Operação negada |
| AG-CLI-006 | Cancelamento em outra clínica | Usuário da clínica A tenta cancelar registro da clínica B | Operação negada |

## 18. Casos de teste — persistência no PostgreSQL

| ID | Cenário | Procedimento | Resultado esperado |
| :-- | :-- | :-- | :-- |
| AG-BAN-001 | Persistência da criação | Criar consulta e verificar diretamente no PostgreSQL | Registro armazenado corretamente |
| AG-BAN-002 | Persistência da edição | Reagendar e consultar novamente o banco | `scheduled_at` e `updated_at` alterados |
| AG-BAN-003 | Persistência do cancelamento | Cancelar e consultar o banco | Registro preservado com `CANCELED` |
| AG-BAN-004 | Persistência da conclusão | Concluir e consultar o banco | Registro preservado com `COMPLETED` |
| AG-BAN-005 | Persistência da ausência | Registrar ausência e consultar o banco | Registro preservado com `NO_SHOW` |
| AG-BAN-006 | Reinício da API | Reiniciar a API e consultar a Agenda | Dados continuam disponíveis |
| AG-BAN-007 | Reinício dos containers | Reiniciar o ambiente Docker | Dados continuam no volume do PostgreSQL |

Consulta sugerida para evidência:

```sql
SELECT
    id,
    clinic_id,
    patient_id,
    dentist_id,
    scheduled_at,
    duration_minutes,
    status,
    notes,
    created_at,
    updated_at
FROM appointments
ORDER BY scheduled_at;
```

## 19. Casos de teste — frontend

| ID | Cenário | Procedimento | Resultado esperado |
| :-- | :-- | :-- | :-- |
| AG-FRO-001 | Navegação para Agenda | Utilizar o menu lateral | Tela carregada corretamente |
| AG-FRO-002 | Dados reais | Comparar listagem do frontend com PostgreSQL | Dados apresentados correspondem ao banco |
| AG-FRO-003 | Formulário incompleto | Tentar salvar sem campos obrigatórios | Interface impede envio e orienta o usuário |
| AG-FRO-004 | Conflito de horário | Tentar reservar horário ocupado | Mensagem clara de conflito |
| AG-FRO-005 | Falta de permissão | Executar ação não autorizada | Interface informa que o usuário não possui permissão |
| AG-FRO-006 | Falha de conexão | Interromper a API e utilizar a Agenda | Interface apresenta mensagem de indisponibilidade |
| AG-FRO-007 | Atualização da lista | Criar ou editar consulta | Agenda é atualizada sem dados fictícios |
| AG-FRO-008 | Botões por perfil | Entrar com cada perfil | Somente as ações permitidas são apresentadas |
| AG-FRO-009 | Carregamento | Abrir Agenda durante requisição | Indicador de carregamento é apresentado |
| AG-FRO-010 | Estado vazio | Consultar período sem agendamentos | Interface informa que não existem consultas no período |

## 20. Testes automatizados mínimos

O backend deverá possuir testes automatizados para:

- criação válida de agendamento;
- autenticação obrigatória;
- permissão de administrador;
- permissão de recepcionista;
- restrições do dentista;
- conflito com o mesmo horário;
- conflito com sobreposição parcial;
- ausência de conflito para dentistas diferentes;
- bloqueio de horário passado;
- paciente inativo;
- dentista inativo;
- paciente de outra clínica;
- dentista de outra clínica;
- transições de estado permitidas;
- transições de estado inválidas;
- cancelamento lógico;
- filtros da listagem;
- concorrência entre duas reservas simultâneas;
- persistência com PostgreSQL real.

## 21. Registro dos resultados

Após a execução, preencher a tabela:

| ID do teste | Data | Responsável | Resultado | Evidência | Bug relacionado |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Exemplo: AG-CRI-001 |  |  | Aprovado/Reprovado/Bloqueado | Nome do print ou arquivo | Número da issue |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

Os resultados possíveis são:

- **Aprovado:** comportamento igual ao esperado;
- **Reprovado:** comportamento diferente do esperado;
- **Bloqueado:** teste não pôde ser executado por dependência ausente;
- **Não executado:** teste ainda não iniciado.

## 22. Registro de bugs

Para cada problema encontrado, registrar:

- identificador do teste;
- perfil utilizado;
- dados enviados;
- comportamento esperado;
- comportamento encontrado;
- código HTTP;
- mensagem apresentada;
- evidência;
- nível de impacto;
- responsável pela correção;
- commit ou Pull Request da correção;
- resultado do reteste.

Modelo:

```markdown
### BUG-AG-001 — Título do problema

- Teste relacionado:
- Perfil utilizado:
- Pré-condição:
- Passos para reproduzir:
- Resultado esperado:
- Resultado encontrado:
- Código HTTP:
- Impacto:
- Evidência:
- Responsável:
- Situação:
- Commit ou Pull Request:
- Resultado do reteste:
```

## 23. Evidências necessárias para a Sprint 5

Deverão ser registradas, no mínimo:

- tela da Agenda com dados reais;
- formulário de novo agendamento;
- consulta criada com sucesso;
- reagendamento realizado;
- mensagem de conflito de horário;
- cancelamento lógico;
- consulta concluída;
- ausência registrada;
- visão da recepcionista;
- visão limitada do dentista;
- resposta de falta de permissão;
- consulta direta à tabela `appointments`;
- resultado dos testes automatizados;
- histórico de commits e Pull Requests;
- persistência após reinício da aplicação.

As imagens deverão seguir a numeração sequencial do relatório geral.

## 24. Critérios de aceitação

O módulo será considerado aprovado quando:

- frontend, API e PostgreSQL estiverem integrados;
- administrador e recepcionista conseguirem gerenciar a Agenda;
- dentista visualizar e atualizar somente os próprios atendimentos autorizados;
- conflitos de horário forem impedidos;
- duas solicitações simultâneas não criarem reservas duplicadas;
- horários passados forem rejeitados;
- pacientes e dentistas inativos não puderem ser agendados;
- dados de clínicas diferentes permanecerem isolados;
- cancelamento não apagar o histórico;
- conclusão e ausência forem persistidas;
- filtros retornarem os dados corretos;
- mensagens de erro forem compreensíveis;
- os dados permanecerem disponíveis após reinicialização;
- testes automatizados e manuais forem executados;
- bugs críticos e altos forem corrigidos;
- evidências forem organizadas para o relatório.

## 25. Pendências antes da execução

- [ ] Validar a proposta técnica da Agenda.
- [ ] Confirmar inclusão do estado `NO_SHOW`.
- [ ] Confirmar transições de estados.
- [ ] Confirmar fluxo de cadastro do perfil profissional do dentista.
- [ ] Confirmar endpoints e filtros finais.
- [ ] Implementar models, schemas, serviços, repositórios e rotas.
- [ ] Criar ou atualizar migrações.
- [ ] Integrar frontend e API.
- [ ] Preparar dados fictícios.
- [ ] Disponibilizar ambiente de testes.