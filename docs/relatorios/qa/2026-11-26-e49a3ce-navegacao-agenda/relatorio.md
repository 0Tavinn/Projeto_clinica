# Relatório de navegação da Agenda — Lumina Odonto

**Data:** 26/11/2026. **Executante:** agente Tech Lead desta conversa, por automação real de navegador; não atribuir esta execução a João ou a outro agente de QA.

**Parecer:** fluxos exercitados em desktop aprovados com ressalva. Foram executados **31 cenários: 30 aprovados e 1 reprovado**. A falha bloqueia a navegação pelo menu em janela estreita. Não constitui aceite integral da aplicação nem das demais branches clínicas.

## Versão e ambiente

- Checkout: `/home/paulinho/Work/Projeto_clinica`.
- Branch: `feat/paralelismo-agendamento`.
- Commit: `e49a3ce22f899ad64d971a50e8d7fd9c99cb5b3a`. Exportação por `git archive`, sem usar alterações locais.
- Os **113 arquivos exportados** de código, infraestrutura e configuração de exemplo foram conferidos contra os blobs desse commit após a execução.
- Projeto Docker exclusivo: `lumina_nav_20261126_6ec95835`. API e frontend implantados com o SHA correto nos rótulos de imagem.
- Interface de teste: `http://localhost:18126`; API `http://localhost:18127`; PostgreSQL exclusivo na porta `55466`, banco `lumina_dev`.
- PostgreSQL **16.15**, revisão Alembic `a6e8f0b2c4d6`. Provisionamento de banco novo pela cadeia oficial, conferência do catálogo e seed demonstrativo concluídos.
- Runtime: FastAPI 0.141.1, SQLAlchemy 2.0.52, Pydantic 2.13.5, Uvicorn 0.52.4, NumPy 2.2.6, PyOpenCL 2025.2.7. Dependências detalhadas em `runtime.log` e `init.log`.
- Comparador configurado como **sequential**, padrão aprovado para uso diário. Esta navegação não lançou nem mediu OpenCL; não comprova aceleração.
- Navegador integrado do aplicativo; viewport de desktop 1440 × 1000. Largura estreita inicialmente próxima de 375 px e, na reprodução final, **377 × 774**. O ajuste temporário de viewport foi desfeito ao terminar.

A aplicação diária de `localhost:18088` foi apenas observada na preparação: suas imagens identificam `f8f10c5`, não o commit testado. Ela não foi reconstruída ou atualizada. Confundir as duas versões invalidaria o parecer.

## Dados fictícios e preparação

A carga `backend/database/seed_demo.sql` foi aplicada exclusivamente no banco novo. A fixture complementar `fixture.sql` acrescentou uma recepcionista, um segundo dentista e três consultas para os casos de atendimento passado e isolamento.

Contas exclusivamente fictícias: `recepcao.qa@example.com`, `dentista.demo@example.com`, `admin.demo@example.com`; senha demonstrativa `DemoLumina2026!`. O segundo dentista também está cadastrado para permitir a comparação entre agendas. Nenhuma conta real foi criada ou modificada.

O banco começou o roteiro com 4 usuários, 2 dentistas, 3 pacientes e 5 consultas. As ações da interface criaram outras 4 consultas. O estado final possui 9 consultas, sem duplicata da criação recusada.

## Cenários de navegação

| ID | Cenário | Resultado |
| --- | --- | --- |
| NAV-01 | Abrir a aplicação de teste | Aprovado |
| NAV-02 | Recusar senha inválida | Aprovado |
| NAV-03 | Login válido da recepção | Aprovado |
| NAV-04 | Abrir menu em janela estreita | Reprovado |
| NAV-05 | Acessar Agenda e semana sem consultas | Aprovado |
| NAV-06 | Enviar formulário vazio | Aprovado |
| NAV-07 | Recusar agendamento passado | Aprovado |
| NAV-08 | Criar consulta válida | Aprovado |
| NAV-09 | Consultar os detalhes | Aprovado |
| NAV-10 | Editar duração e observação | Aprovado |
| NAV-11 | Recepção confirma consulta | Aprovado |
| NAV-12 | Persistência após recarregar a página | Aprovado |
| NAV-13 | Recusar sobreposição do mesmo dentista | Aprovado |
| NAV-14 | Aceitar intervalos adjacentes | Aprovado |
| NAV-15 | Filtrar por dentista | Aprovado |
| NAV-16 | Filtrar por situação | Aprovado |
| NAV-17 | Filtrar por período | Aprovado |
| NAV-18 | Recusar período de filtro invertido | Aprovado |
| NAV-19 | Desistir do cancelamento | Aprovado |
| NAV-20 | Cancelar e preservar no histórico | Aprovado |
| NAV-21 | Consultar cancelada sem edição | Aprovado |
| NAV-22 | Liberar horário após cancelar | Aprovado |
| NAV-23 | Permitir o mesmo horário para dentistas distintos | Aprovado |
| NAV-24 | Encerrar a sessão da recepção | Aprovado |
| NAV-25 | Dentista vê somente sua agenda | Aprovado |
| NAV-26 | Ocultar conclusão e ausência antes do horário | Aprovado |
| NAV-27 | Dentista conclui consulta passada | Aprovado |
| NAV-28 | Dentista registra ausência passada | Aprovado |
| NAV-29 | Administrador consulta a agenda da clínica | Aprovado |
| NAV-30 | Recusar edição com sobreposição | Aprovado |
| NAV-31 | Preservar consulta após edição recusada | Aprovado |

Os detalhes de cada caso, horário da observação e expectativa estão em [matriz.csv](matriz.csv). Estados acessíveis de cada caso, capturas e resultados incrementais estão em [navegador](navegador/). Esses 31 casos são cenários de interface, não contagem de testes pytest nem soma com execuções históricas.

## Falha reproduzida: menu estreito sem funcionamento

**NAV-04 — impacto:** abaixo do breakpoint de 760 px, a barra lateral desaparece e o botão “Abrir menu” não abre uma alternativa. A recepção autenticada não consegue chegar à Agenda pelo menu. Ao final, a falha foi novamente reproduzida na Agenda como administrador.

**Causa localizada no código desta versão:** `frontend/src/App.tsx:641` renderiza o botão sem `onClick`. A regra em `frontend/src/styles.css:7` oculta `.sidebar` nesse breakpoint. Ver `menu-source.json` para os trechos exatos. A reprodução pela interface sustenta o defeito; não se trata de erro de senha, banco ou OpenCL.

**Reprodução:** abrir a aplicação com largura menor ou igual a 760 px; autenticar uma conta fictícia; clicar em “Abrir menu”; observar que nenhum menu é aberto. Repetir em desktop mostra a barra lateral e permite continuar o fluxo.

**Correção proposta para decisão:** tarefa de frontend para implementar a abertura e o fechamento de um menu acessível, incluindo navegação e saída de sessão, preservando o layout de desktop. Revalidar o fluxo em largura estreita e desktop. **Nenhuma correção de produto foi aplicada nesta tarefa.**

Evidências: `navegador/NAV-04.jpg`, `navegador/NAV-04.txt`, `navegador/menu-estreito-reproducao-final.jpg` e `.txt`.

## Conferência de persistência e fuso

Além da interface, a consulta SQL final confirmou:

- Consulta A nº 6 preservada como `CANCELED`, com duração 45 e a observação editada.
- Consulta B nº 7 preservada às **09:45 locais**, mesmo após tentativa de editar para 09:15 e receber conflito.
- Consulta C nº 8 aceita no horário liberado pelo cancelamento; D nº 9 aceita no mesmo horário para outro dentista.
- Consulta passada nº 3 em `COMPLETED` e nº 4 em `NO_SHOW` após as ações do dentista.
- Quatro criações novas no total; tentativa conflitante não acrescentou linha.
- Horários de 27/11 às 09:00 e 09:45 no navegador correspondem a **12:00 e 12:45 UTC**, respectivamente. A conversão para `America/Sao_Paulo` foi conferida.

Resultados em `sql-assertions.json` e `appointments-final.json`, ambos contendo apenas dados fictícios. A listagem permaneceu correta após recarregar a página. **Não foi realizado novo teste de reinício da API ou do PostgreSQL nesta tarefa.**

## Contrato e limites

- Na base PR18/e49a3ce, o dentista pode concluir consulta passada a partir de `SCHEDULED`, com confirmação simples na interface. Não foi exigida evolução salva nem `care_occurred_at`. Isso descreve o contrato desta branch; não valida ou substitui decisões e implementações de prontuário em outras branches.
- Foram exercitados recepção, dentista e administrador da mesma clínica. Não foram executados novos casos de outra clínica, chamadas forjadas, paciente inativo, expiração de token ou segunda senha clínica.
- Não houve novo teste de duas requisições simultâneas, espera por bloqueio ou concorrência entre abas. Resultados anteriores de backend continuam históricos, separados desta navegação.
- Não foi realizada nova medição de desempenho HTTP. Tempo percebido e ausência de falha no navegador não demonstram ganho de performance.
- O coletor de console não retornou entradas de erro ou aviso nesta sessão. Isso não equivale a uma auditoria completa de todos os logs.
- Não foram capturados status HTTP individuais suficientes para atribuir códigos às operações. As mensagens de conflito foram verificadas pela UI e a ausência de gravação parcial pelo SQL. `http-from-nginx.json` está vazio e não é evidência de requisições ou status.
- Não foram testados impressão, buscas clínicas ou vínculo administrativo do novo backend de Tarcísio. O recorte foi a Agenda desta branch.

## Intercorrências do roteiro

1. A ferramenta de navegador teve erro de diretório antes da execução. Foi criada a pasta Windows vazia esperada pela sessão para recuperar o controle; o código real continuou no WSL. Não foi criado outro checkout nesse caminho.
2. Duas recusas de autorização automática ocorreram antes de criar o ambiente; após confirmação explícita do usuário, a preparação e o teste foram executados.
3. A primeira tentativa de aguardar o botão Agenda após login não considerava o menu recolhido. O login havia funcionado. A inspeção da UI revelou a falha real do menu.
4. `fill` em controles nativos de data/hora não preencheu os campos nesta ferramenta. Calendário e teclado nativos foram usados, com conferência dos valores antes de salvar. Tentativas incompletas não foram contadas como defeito do produto.
5. Um índice acessível ficou obsoleto após mudar o período; foi atualizado antes de continuar. Confirmações JavaScript interromperam o retorno do clique até serem explicitamente lidas e aceitas ou dispensadas.
6. A primeira asserção SQL comparou horário local com texto UTC. A expectativa do roteiro foi corrigida para conversão de fuso e a conferência final passou. Nenhum código ou dado do produto foi alterado para isso; ver `verification-first-attempt.txt`.

## Preservação, limpeza e entrega

Os contêineres, o volume, a rede e as tags de imagens exclusivos deste teste foram removidos após conferir propriedade. Os três serviços diários continuam saudáveis e com os mesmos IDs, imagens, mounts e horários de início observados antes da preparação. Nenhum comando de escrita foi dirigido ao banco diário; não foi feita nova comparação completa de seus dados.

O código versionado permaneceu intacto. Os únicos arquivos da entrega são relatórios e evidências; **sem commit, push, merge, migração do banco existente ou correção da interface**. `cleanup.json` registra as verificações finais; `.local/qa-navegacao-agenda-20261126/checkpoint.json` conserva o ponto de retomada.

**Próxima ação proposta:** encaminhar NAV-04 ao responsável pelo frontend. Os cenários de desktop exercitados estão aptos a demonstração nesse recorte; o menu estreito precisa de correção antes de considerar esse modo de navegação aprovado.
