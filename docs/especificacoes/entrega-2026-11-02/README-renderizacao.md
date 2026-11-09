# Fontes e reprodução da entrega v0.4

Esta pasta contém a especificação editável, dez painéis de **seis fluxos lógicos**, arquivos Mermaid `.mmd`, SVGs, PNGs de alta resolução e o PDF final. Os arquivos `05-pagamento-externo.mmd` e `06-correcao-administrativa-servicos.mmd` foram copiados sem alteração dos blocos Mermaid da [fonte complementar v0.4](../fluxogramas-complementares-mvp-2026-11-02.md). Os fluxos 1, 2, 3 e 4 seguem o [roteiro](../roteiro-fluxogramas-mvp-2026-11-02.md). O manifesto em `diagramas-renderizados/manifesto.json` registra dimensões e posições de nós usadas para dividir páginas sem cortar os textos.

## Gerar novamente em uma máquina com Node e navegador Chromium/Edge

Na **pasta desta entrega**, executar `npm install` e depois `npm run diagramas`. O arquivo `package.json` fixa Mermaid 12.2.0 e Playwright 1.62.1. Instalar o navegador Playwright, ou definir `LUMINA_BROWSER_PATH` para um executável Chromium/Edge já instalado. O renderizador usa o navegador **localmente**, lê os `.mmd` e recria os SVGs, PNGs e o manifesto nesta pasta; não envia o conteúdo a um serviço externo. As dependências da aplicação Lumina Odonto não são afetadas.

Para gerar o PDF, instalar as bibliotecas de `requirements-renderizacao.txt` em ambiente Python separado e executar `python gerar-pdf.py` nesta pasta. O script usa o Markdown e as imagens geradas; procura DejaVu Sans no Linux ou Arial no Windows, pagina diagramas longos entre os nós e escreve `Lumina-Odonto-Fluxo-atendimento-MVP-v0.4.pdf`. O PDF usa páginas A3 em orientação retrato para manter os textos dos fluxogramas legíveis. As fontes Mermaid e SVG permanecem separadas para edição.

Na elaboração de 02/11/2026, o Mermaid foi instalado apenas em `/tmp` e o Edge/Playwright local gerou as imagens. O PDF foi montado com as bibliotecas locais do aplicativo, sem instalar dependências no projeto. Reproduzir os desenhos não executa a API, não altera banco ou Docker e não demonstra funcionalidades implementadas.

| Fluxo lógico | Painéis renderizados |
| --- | --- |
| 1. Atendimento e encaminhamento | `01a`, `01b` |
| 2. Desbloqueio, autorização e falhas | `02a`, `02b`, `02c` |
| 3. Evolução | `03` |
| 4. Recuperação da senha clínica | `04a`, `04b` |
| 5. Pagamento externo | `05` |
| 6. Correção administrativa de serviços | `06` |

**Estado documental:** versão 0.4 para alinhamento. Decisões pendentes e recomendações técnicas estão identificadas no documento. Diagramas e PDF não constituem aceite da implementação.
