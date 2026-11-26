# NAV-04 — Correção do menu em largura estreita

**Data:** 26/11/2026. **Responsável pela execução:** agente de Frontend deste chat.
**Parecer:** correção implementada, build final aprovado e navegação real parcialmente revalidada. A ferramenta interrompeu o teste antes de concluir administrador e outros cenários; não há aceite integral de navegação.

## Versão e causa

- Checkout real: /home/paulinho/Work/Projeto_clinica, acessado pelo Ubuntu WSL.
- Branch preservada: feat/paralelismo-agendamento.
- HEAD preservado: 1a2ec6c519272840e31acf89996f882a9aaa71d7.
- Estado inicial: limpo. Sem troca de branch, stash, commit, push, merge ou publicação.
- Antes: App.tsx:641 renderizava Abrir menu sem onClick; styles.css:7 ocultava a sidebar em max-width:760px. Assim o menu desaparecia e o botão não oferecia alternativa.
- Depois: painel móvel com os mesmos destinos da Sidebar existente. Desktop mantém a navegação anterior.

## Arquivos de produto

| Arquivo | Alteração |
| --- | --- |
| frontend/src/App.tsx | Integra AppNavigation; fecha menu antes de navegar ou sair. A lista por perfil e as verificações existentes permanecem na Sidebar/navigate. |
| frontend/src/AppNavigation.tsx | Componente de 121 linhas: diálogo nativo, acionador, fechamento, foco, contenção de Tab/Shift+Tab, Escape via cancel, clique fora, limpeza da rolagem e mudança de breakpoint. |
| frontend/src/AppNavigation.css | 61 linhas de estilos restritos ao painel móvel; identidade visual reaproveitada. |

O acionador possui aria-expanded, aria-controls no móvel e aria-haspopup=dialog. O diálogo tem nome acessível e botão Fechar menu. O menu fecha ao selecionar um destino e no logout. A rolagem anterior é restaurada ao fechar, sair, desmontar ou mudar para desktop.

Não houve mudança no cliente HTTP, contratos, autenticação, perfis, backend, schema PostgreSQL, Docker versionado ou OpenCL.

## Build e integridade da versão testada

- npm run build no checkout final: aprovado, Node v22.23.3 / npm 10.9.9. Log: build.log.
- Build Docker do frontend final: aprovado usando o Dockerfile existente, base node:24-alpine. Log: frontend-rebuild.log.
- Sem infraestrutura de testes frontend além do build no package.json: nenhum framework foi instalado e nenhum teste unitário foi declarado como executado.
- git diff --check -- frontend/src/App.tsx: aprovado.
- Arquivos novos conferidos com git diff --no-index --check contra /dev/null, sem avisos. O retorno 1 dessas chamadas indica existência do diff, não erro de whitespace; ver diff-check.json.
- Exportação por git archive dos caminhos backend/frontend/scripts/compose.yml/.env.example e sobreposição EXPLÍCITA dos três arquivos sem commit.
- 112 arquivos-base exportados foram conferidos contra HEAD; nenhuma diferença inesperada. Hashes dos três arquivos sobrepostos iguais ao checkout final.
- implementation.patch contém a alteração de App.tsx e os dois arquivos novos; tested-source.json e source-integrity.json registram os hashes.

SHA-256:
- App.tsx: 552515058ed4cea3f2041479a17fe5e5354a07122df6b0bdd7cf27d9d8e04c70
- AppNavigation.tsx: 29f80a0bc307f39ef28a6bf620dc00f602d4753987f7becbfbbe8819fa8b6606
- AppNavigation.css: 0143800ef3e42f1f00c52345e016abde684599734061db45796e983bcc60dd8d

## Ambiente descartável

- Projeto: lumina_nav04_20261126_8d19c4.
- UI: http://localhost:18136; API: http://localhost:18137; PostgreSQL: 55476.
- Volume: lumina_nav04_20261126_8d19c4_postgres_data.
- Rede: lumina_nav04_20261126_8d19c4_default.
- Banco novo provisionado pela cadeia oficial até a6e8f0b2c4d6; PostgreSQL 16.15.
- Seed demonstrativo oficial e fixture mínima de recepção, exclusivamente nesse banco novo.
- Contas fictícias: recepcao.nav04@example.com, dentista.demo@example.com e admin.demo@example.com. Somente as duas primeiras foram usadas na execução desta UI.
- Comparador sequential; nenhum ensaio ou alteração OpenCL.
- O build local sem VITE_API_URL e o build Docker com VITE_API_URL=/api/v1 produzem nomes de JS diferentes. A navegação usou a imagem Docker temporária com a correção, não a porta diária 18088.

Comandos principais efetivamente executados na cópia exclusiva:
- python3 scripts/setup_dev.py --project lumina_nav04_20261126_8d19c4 --frontend-port 18136 --api-port 18137 --db-port 55476
- python3 scripts/dev.py init
- python3 scripts/dev.py seed-demo
- docker compose --env-file .env -p lumina_nav04_20261126_8d19c4 -f compose.yml build frontend
- docker compose --env-file .env -p lumina_nav04_20261126_8d19c4 -f compose.yml up -d --no-deps --wait frontend

## Navegação REAL observada

Execução por CUA no Brave nativo, em guia exclusiva. O navegador integrado iab estava indisponível. As dimensões são as configuradas no modo Responsive do navegador; houve zoom de apresentação/fit e não teste em aparelho físico.

Os IDs F01 a F14 são 14 observações da revisão final, não testes unitários, nem repetição dos 31 casos históricos da Agenda.

| Evidência | Perfil / resolução | Ação observada | Resultado |
| --- | --- | --- | --- |
| F01 | Recepção, 375x810 | Shift+Tab no limite inicial | Foco em Sair, dentro do painel |
| F02 | Recepção, 375x810 | Tab no último item | Foco volta a Fechar menu |
| F03 | Recepção, 375x810 | Enter em Fechar menu | Fecha; foco retorna a Abrir menu |
| F04 | Recepção, 375x810 | Selecionar Agenda | Agenda real aberta; painel fechado |
| F05 | Recepção, 375x810 | Clique no fundo escurecido | Fecha; mantém Agenda |
| F06 | Recepção, 375x810 | Botão Fechar menu | Fecha sem mudar destino |
| F07 | Recepção, 1440x1000 | Ampliar largura com painel aberto | Modal removido; sidebar desktop e Agenda preservadas |
| F08 | Recepção, 1440x1000 | Pacientes | Lista real com dados fictícios |
| F09 | Recepção, 1440x1000 | Dashboard | Navegação desktop preservada |
| F10 | Recepção, 377x780 | Retornar do desktop ao móvel | Acionador visível; menu fechado, sem painel residual |
| F11 | Recepção, 377x780 | Rolar a página após fechar/mudar largura | Página rola normalmente |
| F12 | Recepção, 377x780 | Sair no painel móvel | Login reaparece; menu removido |
| F13 | Dentista, 377x780 | Abrir menu | Dashboard/Pacientes/Prontuários/Consultas/Sair, sem Equipe |
| F14 | Dentista, 377x780 | Consultas | Tela Consultas aberta; painel fechado; sem Nova consulta |

Arquivos .txt e capturas .jpg em navegador/. capture-inventory.json confere o formato e as dimensões reais das capturas. observations.json registra os marcos progressivamente.

## Intercorrências e limite da cobertura

- As tentativas M01 a M06 pertencem à revisão intermediária e/ou à recuperação do roteiro; não são somadas às observações finais.
- Escape fechou o diálogo e restaurou foco na revisão intermediária (M05). O mesmo tratamento cancel permaneceu no código, mas Escape não foi repetido após acrescentar a contenção explícita de Tab.
- O teste revelou saída de Shift+Tab para a interface do navegador. Foi acrescentada contenção explícita; a revisão final passou pelos limites anterior e posterior.
- Houve erro de foco no DevTools, chamada de scroll com assinatura inadequada, dificuldade inicial com UIA e recuperação após popup de salvar senha. Foram erros de roteiro, preservados em attempts.md e nas evidências intermediárias.
- Ao clicar Prontuários do dentista, CUA encerrou o uso do computador por não conseguir determinar a URL atual do navegador no Windows com confiança para aplicar sua política. A partir dessa interrupção não houve mais chamadas de interação com navegador. Não atribuir aprovação ao clique ou ao fluxo clínico subsequente.
- Permanecem pendentes: administrador em móvel e desktop (incluindo Equipe); dentista em desktop; conclusão da navegação de Prontuários; repetição de Escape na revisão final; verificação específica de atributos ARIA/foco por leitor de tela e de aparelhos/navegadores adicionais.
- O botão/menu de administrador permanece baseado na mesma Sidebar por perfil, mas leitura de código não equivale a teste de navegador.
- A guia de teste pode permanecer aberta com a confirmação clínica ou com a aplicação antiga em memória. O ambiente HTTP temporário foi removido após salvar as evidências.

## Limpeza e preservação

cleanup.json e cleanup.log comprovam remoção dos contêineres, volume, rede e tags exclusivas desta execução, após conferir labels de propriedade. Também foi removida a imagem intermediária exclusiva sem tags. Cache compartilhado de build não foi limpo.

Os três serviços diários lumina_pr18_tarcisio mantiveram os mesmos IDs, imagens, mounts, horários de início e saúde da observação inicial; ver daily-before.json e daily-after.json. Nenhuma escrita foi dirigida ao banco diário. Não foi feita comparação completa de seu conteúdo.

Checkpoints e configuração privada do ambiente descartável permanecem sob .local/nav04-menu-20261126_8d19c4, ignorado pelo Git, para rastreabilidade e retomada. A cópia parcial da exportação que falhou foi preservada. A pasta Windows C:/home/paulinho/Work/Projeto_clinica foi usada apenas para transportar evidências; não contém o checkout.

## Estado da entrega

Correção de produto implementada e sem commit; código e evidências disponíveis para revisão do Tech Lead. A validação real cobriu os cenários listados e ficou parcial por interrupção da ferramenta. Não há nova aprovação de API, backend, concorrência, prontuário ou de todos os perfis/resoluções.

Próximo passo: concluir os cenários pendentes da matriz no navegador e revisar o diff antes de Paulo decidir pelo commit/push.
