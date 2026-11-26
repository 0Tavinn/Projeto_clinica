# Intercorrências de preparação

1. WSL sem elevação retornou Wsl/E_ACCESSDENIED; execução autorizada com elevação funcionou.
2. Duas leituras com aspas Bash/PowerShell falharam (ParserError / uso do sed); comandos de leitura foram corrigidos.
3. Primeiro build passou, mas export PATH sem aspas gerou avisos por caminhos Windows com espaços. Reexecução usa subprocess com env.
4. Exportação inicial git archive HEAD encontrou venv/bin/python3 versionado com link absoluto (tarfile.AbsoluteLinkError). Cópia parcial preservada em .local/nav04-menu-20261126_8d19c4/source-first-attempt. Nova exportação restringe os caminhos necessários.
5. Navegador integrado iab indisponível nesta sessão; tentativa de abrir Brave nativo levou cerca de 238s. Nenhuma dessas tentativas é defeito do produto.

6. UIA no navegador nativo focou campo diferente no login; corrigido por coordenadas observadas.
7. Teclado inicialmente atingiu DevTools; as evidências M02/M03/M04 são tentativas de roteiro, não aprovação. DevTools foi destacado.
8. Após foco real na página, Escape e reabertura por Enter funcionaram. Shift+Tab escapou do limite do diálogo para controles do navegador; acrescentada contenção explícita de Tab. M06 registra a versão intermediária.

9. app.scroll com distância numérica foi recusado; a chamada correta usa {pixels}.
10. A exibição incremental às vezes mostrava só o cursor, mas a inspeção dos bytes confirmou capturas completas. Foram salvas inicialmente com extensão .png; o formato real é JPEG e a extensão foi corrigida para .jpg. Dimensões conferidas em capture-inventory.json.
11. Popup de salvar senha produziu no monitor found for window; janela principal foi recuperada sem salvar senha.
12. Ao clicar Prontuários, CUA encerrou o uso de computador: não conseguiu determinar a URL atual no Windows com confiança para aplicar a política. Nenhuma chamada CUA foi feita depois. Administrador, desktop do dentista e teclado Escape na revisão final ficaram pendentes.
