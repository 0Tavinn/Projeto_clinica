# Revalidação NAV-04 — Menu móvel e navegação em desktop

**Data:** 26/11/2026. **Execução:** agente Tech Lead desta conversa, por navegador real integrado ao aplicativo, contra API e PostgreSQL descartáveis. Esta execução complementa a entrega do frontend; não foi realizada por João.

**Parecer:** correção NAV-04 aprovada nos cenários de menu executados. Foram **28 cenários aprovados, zero reprovados**. Os testes pendentes de administrador, dentista em desktop e Escape na revisão final foram concluídos. O caminho que reproduzia a falha original agora permite à recepção abrir a Agenda em largura estreita.

Isso não constitui aceite do fluxo clínico completo: a entrada em Prontuários por senha adicional permaneceu sem validação neste navegador, conforme a limitação descrita abaixo.

## Versão efetivamente testada

- Checkout: `/home/paulinho/Work/Projeto_clinica`, Ubuntu WSL.
- Branch: `feat/paralelismo-agendamento`.
- Base Git: `1a2ec6c519272840e31acf89996f882a9aaa71d7`.
- **A correção permanece sem commit.** A versão executada foi exportada de HEAD e recebeu sobreposição explícita dos três arquivos locais abaixo. Identificar somente o HEAD não identifica o código corrigido.
- Os 113 arquivos-base exportados foram conferidos, respeitando a substituição de App.tsx; os dois arquivos novos e os três hashes sobrepostos foram igualmente conferidos contra o checkout final. Nenhuma mudança inesperada na exportação.

SHA-256 da correção final, iguais aos registrados pelo frontend:

- `frontend/src/App.tsx`: `552515058ed4cea3f2041479a17fe5e5354a07122df6b0bdd7cf27d9d8e04c70`.
- `frontend/src/AppNavigation.tsx`: `29f80a0bc307f39ef28a6bf620dc00f602d4753987f7becbfbbe8819fa8b6606`.
- `frontend/src/AppNavigation.css`: `0143800ef3e42f1f00c52345e016abde684599734061db45796e983bcc60dd8d`.

Arquivos de referência: `tested-source.json`, `source-integrity.json` e `tracked-diff.patch`. Os arquivos de produto não foram alterados por estes testes.

## Ambiente

- Projeto Docker exclusivo: `lumina_nav04_review_20261126_0c2bed5f`.
- Interface `http://localhost:18146`, API `http://localhost:18147`, PostgreSQL na porta local `55486`, banco `lumina_dev`.
- Provisionamento pela cadeia Alembic oficial, revisão `a6e8f0b2c4d6`, catálogo conferido e health checks HTTP 200 na preparação.
- PostgreSQL **16.15**. Runtime exato em `runtime.log`.
- Build Docker de frontend e API concluído na exportação com os arquivos locais sobrepostos; log em `init.log`. Não foi repetido o build local npm já registrado pelo frontend, nem foi adicionada infraestrutura de testes unitários.
- Comparador da Agenda `sequential`; nenhum teste ou medição OpenCL nesta revisão.
- Viewports configurados: **377 × 780** para móvel e **1440 × 1000** para desktop. A largura efetiva do conteúdo, incluindo variação por barra de rolagem, está em cada campo `ui` de `navegador/resultados.json`; não são testes em aparelho físico.
- Contas totalmente fictícias: `admin.demo@example.com`, `dentista.demo@example.com` e `recepcao.revisao@example.com`, com senha demonstrativa `DemoLumina2026!`. Usadas somente no ambiente descartável.

Preparação: exportar os arquivos do commit, sobrepor os três arquivos conferidos, executar `scripts/setup_dev.py` com projeto e portas exclusivos, `scripts/dev.py init`, `scripts/dev.py seed-demo` e a fixture complementar `fixture.sql`. O banco iniciou com 3 usuários, 3 pacientes, 2 consultas, 3 prontuários e 2 evoluções. A conferência final manteve essas contagens; o roteiro não criou novos registros clínicos ou agendamentos.

## Matriz executada

| ID | Perfil | Cenário | Resultado |
| --- | --- | --- | --- |
| M01 | Administrador | Abrir menu com destinos administrativos | Aprovado |
| M02 | Administrador | Escape fecha e restaura foco na revisão final | Aprovado |
| M03 | Administrador | Selecionar Equipe no menu móvel | Aprovado |
| M04 | Administrador | Selecionar Pacientes no menu móvel | Aprovado |
| M05 | Administrador | Selecionar Agenda no menu móvel | Aprovado |
| M06 | Administrador | Conter Tab e Shift+Tab no painel | Aprovado |
| M07 | Administrador | Fechar ao clicar fora do painel | Aprovado |
| M08 | Administrador | Fechar pelo botão dedicado | Aprovado |
| M09 | Administrador | Mudar para desktop com menu aberto | Aprovado |
| M10 | Administrador | Equipe em desktop | Aprovado |
| M11 | Administrador | Pacientes em desktop | Aprovado |
| M12 | Administrador | Dashboard em desktop | Aprovado |
| M13 | Administrador | Retornar ao móvel sem painel residual | Aprovado |
| M14 | Administrador | Logout administrativo pelo menu móvel | Aprovado |
| M15 | Dentista | Destinos corretos em desktop | Aprovado |
| M16 | Dentista | Selecionar Consultas em desktop | Aprovado |
| M17 | Dentista | Selecionar Pacientes em desktop | Aprovado |
| M18 | Dentista | Retornar ao Dashboard em desktop | Aprovado |
| M19 | Dentista | Menu móvel do dentista preserva os destinos | Aprovado |
| M20 | Dentista | Escape na versão final para dentista | Aprovado |
| M21 | Dentista | Selecionar Consultas no menu móvel | Aprovado |
| M22 | Dentista | Logout do dentista no menu móvel | Aprovado |
| M23 | Recepção | Menu da recepção sem destinos de outros perfis | Aprovado |
| M24 | Recepção | Escape na versão final para recepção | Aprovado |
| M25 | Recepção | Revalidar o caminho original NAV-04 | Aprovado |
| M26 | Recepção | Voltar ao Dashboard pelo menu | Aprovado |
| M27 | Recepção | Preservar Agenda em desktop para recepção | Aprovado |
| M28 | Recepção | Logout em desktop | Aprovado |

Detalhes, instantes e condições observadas em [matriz.csv](matriz.csv). As observações DOM incluem diálogo aberto/modal, `aria-expanded`, `aria-controls`, controle com foco, rolagem e botões do menu. Não se usou JavaScript para simular cliques ou alterar o estado da aplicação; as interações ocorreram pelos controles e teclado do navegador.

O roteiro conferiu abertura, fechamento, Escape, clique fora, Tab e Shift+Tab, restauração de foco, seleção de destino, logout e mudança de breakpoint. Os destinos visíveis permaneceram coerentes para cada perfil. A ocultação na interface não substitui autorização da API; esta revisão não repete ensaios de chamadas forjadas.

## Fechamento de NAV-04

A evidência M25 reexecuta o caminho original da recepção: Dashboard em largura estreita → Abrir menu → Agenda. O painel aparece, oferece Agenda, a tela de Agenda abre e o painel fecha. A antiga navegação inacessível não foi reproduzida.

M02, M20 e M24 confirmam **Escape na mesma versão final** para administrador, dentista e recepção. M06 confere os dois limites do teclado: Shift+Tab do primeiro controle vai a Sair, e Tab de Sair volta a Fechar menu. M09 confere menu aberto → desktop, com remoção do diálogo, retorno da sidebar, foco em Agenda e rolagem liberada.

Capturas principais: `navegador/M01.jpg` (administrador móvel), `M09.jpg` (desktop), `M19.jpg` (dentista móvel), `M23.jpg` (recepção móvel) e `M25.jpg` (Agenda acessada). Estados acessíveis correspondentes e resultados foram salvos progressivamente.

## Ressalva fora do aceite do menu: entrada clínica

Ao clicar Prontuários no desktop do dentista, a tela permaneceu em Pacientes. A API documentada de diálogo do navegador integrado não apresentou um diálogo JavaScript disponível. A leitura de `frontend/src/App.tsx:613` confirma que a entrada existente chama `window.prompt` para pedir a senha clínica e só navega após sua validação.

**Não foi possível confirmar a causa pelo navegador e não se atribui aprovação nem defeito de produto a esse fluxo.** Não houve preenchimento da senha clínica, abertura de prontuário ou aceite de suas operações. O controle de menu e os outros destinos permaneceram utilizáveis. A tentativa está registrada em `navegador/tentativa-prontuarios-desktop.txt` e `tentativas.json`.

Essa ressalva já pertencia ao fluxo clínico não concluído pelo frontend. Para eliminá-la é necessário um teste específico da segunda senha e da navegação clínica em um navegador que exponha essa confirmação com segurança. Não foram substituídos prompt, autenticação, contratos ou tokens para contornar a limitação.

## Intercorrências do roteiro

- O controle do navegador foi reinicializado após inatividade; a documentação e as referências da sessão foram recuperadas antes das ações.
- A tentativa de ler o arquivo de fonte pelo caminho UNC no processo do navegador falhou. A fonte foi lida depois pelo terminal WSL, sem alteração. Isso não é defeito da interface.
- Fora a etapa clínica acima, não houve interrupção que impedisse os 28 cenários do menu.
- Nenhuma entrada de erro/aviso foi retornada pelo coletor de console nesta sessão (`navegador/console.json`). Não representa auditoria de todos os logs do navegador ou servidor.

## Preservação e limpeza

Após conferir propriedade, foram removidos somente contêineres, volume, rede e tags de imagem do projeto exclusivo. Os serviços diários `lumina_pr18_tarcisio` continuaram saudáveis e com os mesmos IDs, imagens, mounts e horários de início; ver `daily-before.json`, `daily-after.json` e `cleanup.json`.

Nenhum comando de escrita foi dirigido ao banco diário. Não foi feita nova comparação integral de seu conteúdo. A porta diária **18088 não foi atualizada**. O ajuste de viewport foi desfeito e a guia temporária foi fechada.

Os arquivos do frontend mantiveram os mesmos hashes antes e depois dos testes. Os relatórios anteriores, inclusive o resultado histórico de 30/31 da Agenda e o parecer parcial do frontend, foram preservados. Esta execução tem versão e escopo próprios; não somar seus casos como se fossem uma única suíte repetida.

Sem commit, push ou merge nesta etapa. A correção e os relatórios estão disponíveis para registro após decisão de Paulo. O código do menu está apto a esse registro no recorte validado; permanece pendente o aceite do fluxo clínico completo e de outros navegadores/dispositivos, bem como auditoria com leitor de tela.
