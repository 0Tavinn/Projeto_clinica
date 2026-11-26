# Consolidação da Agenda com OpenCL — 25/11/2026

## Versão registrada

Entrega derivada do PR #18, base `f8f10c54a4a702b7d4feccbf5aeb98578db65909`,
na branch `feat/paralelismo-agendamento`.

- `2b6819b`: organização do ambiente PostgreSQL de desenvolvimento.
- `8d0026c`: implementação OpenCL e padrão cotidiano sequencial.
- As evidências selecionadas são registradas no commit que contém este documento.

Os relatórios originais conservam suas referências ao HEAD-base e aos diffs
locais efetivamente testados. Não foram reescritos para simular testes sobre
commits que ainda não existiam naquelas execuções.

## Funcionamento e configuração

Sem configuração explícita, a Agenda usa `APPOINTMENT_CONFLICT_ENGINE=sequential`.
`auto` habilita OpenCL em CPU com fallback sequencial. Os filtros, contratos
HTTP e as proteções transacionais e GiST continuam preservados.
Não existe mudança visual obrigatória nem migração de banco nesta feature.

O OpenCL tem finalidade educativa. Não houve demonstração de ganho consistente
de desempenho. No diagnóstico HTTP anterior, a primeira operação não vazia
com OpenCL levou entre 1,44 e 1,78 segundo; o padrão sequencial evita carregar
e inicializar esse runtime no fluxo cotidiano.

## Evidências e seus limites

- [QA independente](qa/2026-11-25-f8f10c5-opencl-agenda/relatorio.md):
  98 IDs únicos dos testes fornecidos aprovados entre as suítes, além das
  sondagens adicionais documentadas. O parecer é pronto com ressalvas para
  a entrega local anterior ao ajuste do padrão.
- [Diagnóstico HTTP](performance-opencl-http-2026-11-25/relatorio.md):
  360 chamadas reais em ambiente isolado, incluindo primeiras chamadas,
  chamadas aquecidas e concorrência. Tempos da API instrumentada, sem navegador.
- [Ajuste do padrão](sequential-default-2026-11-25/relatorio.md):
  66 testes direcionados aprovados após o ajuste; Compose/default/override
  conferidos e processo padrão sem importar PyOpenCL.

As contagens pertencem a conjuntos diferentes e não devem ser somadas como
casos únicos de uma única execução. Não foi repetido o benchmark HTTP após
a mudança de padrão. A melhoria esperada é retirar o custo de inicialização
OpenCL do caminho padrão; ainda falta medir esse comportamento na versão final.

## Publicação de evidências

Foram incluídos relatórios, matrizes, logs, dados brutos e scripts das rodadas
selecionadas, incluindo registros de tentativas malsucedidas quando pertencem
às respectivas pastas. O diretório gerado `baseline-pr18` do QA não foi duplicado
no Git: a fonte original é recuperável pelo commit-base. Snapshots pequenos
que identificam a versão local testada foram mantidos com seus hashes.

Backups de banco, arquivos `.env`, volumes, imagens e demais configurações
operacionais locais não fazem parte desta publicação. Artefatos não
selecionados permanecem preservados no checkout original da entrega.

## Pendências de execução

Registrar/publicar estes commits e abrir os arquivos na pasta principal não
implanta a imagem nova nem altera o banco existente. Permanecem pendentes:

1. Verificação HTTP curta da versão final, medindo primeira chamada e seguintes
   com o padrão sequencial em ambiente isolado.
2. Implantação autorizada no ambiente de desenvolvimento e conferência pela
   interface; acesso ao Docker não prova que a imagem executada é a nova.
3. Revisão e integração próprias da entrega de prontuários de Tarcísio.

Para executar a demonstração e o runner completo em recursos descartáveis:

```bash
bash backend/tests/run_opencl_qa.sh
```

O runner seleciona `auto` explicitamente nos testes direcionados e preserva
o ambiente diário. Consulte o [guia](../paralelismo-agendamento.md).
