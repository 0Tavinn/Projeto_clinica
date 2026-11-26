# Prontuário — consolidação das correções de QA

Registro em 26/11/2026. Responsável pela consolidação: Paulo Sérgio,
com execução assistida pelos agentes de Backend, QA e Tech Lead.

## Histórico e origem

A branch `fix/prontuario-correcoes-qa` parte de
`4ccdc30a27143b6c022b7f8cae2e6ccf03860389`, entrega publicada de Tarcísio em
`tata2005-patch-1`, descendente do banco preparado no PR #18.

O pacote corrigido recebido de Tarcísio foi identificado pelo manifesto
`987ee7199972977bc549346246d0ee5bf46d4611b9d15c3c8fc89fdfbd41fe40`.
O agente de Backend corrigiu depois o N05-LOG em uma cópia separada,
sob coordenação do Tech Lead e autorização de Paulo. A origem do pacote
recebido é informada por Paulo; não foi inventada autoria Git para ele.

O código consolidado está em `lumina_odonto/`, no commit
`21cefa608327fa157938308a4c9e16fbfa3a6eb4`.
Os **22 arquivos daquele commit correspondem byte a byte à candidata final validada**,
com manifesto canônico
`e3b28488163b174758f7e3782dbe916b0cc1cf8120cadf5a3cd5da79200e2825`.
O mapa está em [manifesto-pacote-aprovado.json](manifesto-pacote-aprovado.json).
Os 17 caminhos alterados no commit são a diferença desses 22 arquivos
contra a referência publicada; cinco arquivos já eram iguais.

As referências dos relatórios a pacotes sem Git e caminhos locais descrevem
as execuções históricas reais. Não foram reescritas para simular testes
executados depois da criação deste commit.

## O que foi registrado

- Correções de autorização/rechecagem de busca, DTO da Agenda, revogação
  administrativa, validação privada, escopo por paciente, versão estrita
  e normalização do termo de busca recebidas no pacote corrigido.
- Arquivos de provisionamento e dados demonstrativos fornecidos no pacote.
- Política de logs do N05: módulo próprio com comentários em português;
  preserva método, rota estática, status e eventos operacionais, sem query,
  valores de parâmetros ou traceback potencialmente clínico nos caminhos testados.
- Testes fornecidos, testes de logging e documentação da API.

O schema SQL copiado mantém SHA256
`2ca830bda08ba3711f69408fe5848a5fd3304156373020f90310b04e746eda81`,
igual ao PR #18. Copiar SQL ao Git não executa DDL nem migra banco existente.

## Evidências e limites de cada rodada

| Rodada | Resultado e alcance | Fonte |
|---|---|---|
| Pacote recebido, 25/11 | 73 de 74 verificações independentes aprovadas; 18 testes fornecidos separados. Sete defeitos passaram; N05 parcial por query clínica no log. | [Relatório original](2026-11-25-pacote-corrigido-987ee71999-bd315/relatorio.md) |
| Correção N05 pelo Backend, 26/11 | 18 testes anteriores e 8 focados aprovados; 16 verificações HTTP e erro real de servidor, com logs sanitizados. | [Relatório do Backend](2026-11-26-n05-log-backend-cfaac6e1/relatorio.md) |
| Reteste independente N05, 26/11 | 26 testes aprovados; 25 objetivos HTTP aprovados; 23 asserções transversais sobre os mesmos logs e 1 comparação OpenAPI. N05 encerrado na candidata/configuração testadas. | [Relatório do QA](2026-11-26-n05-log-qa-4c930a5405/relatorio.md) |

Os grupos sobrepõem cobertura e **não devem ser somados como cenários únicos**.
As 74 verificações antigas não foram repetidas integralmente na candidata N05.
A tentativa com método HTTP inventado retornou 400 no parser; ficou preservada.
O complemento TRACE chegou ao roteamento, retornou 405 e confirmou o log OTHER.
Não houve alteração da aplicação para transformar essa tentativa em aprovação.

A busca OpenCL executou realmente em CPU PoCL. O reteste N05 usou API Uvicorn
servida por HTTP real e PostgreSQL 16.16 descartável. Não foi alegado ganho
de velocidade, benchmark novo ou validação por navegador.

## Organização das evidências

As três subpastas preservam os arquivos selecionados das rodadas originais,
incluindo matrizes, tentativas, mapas de hashes, logs sanitizados e scripts.
Os originais continuam nas pastas de evidências fora do repositório.
O [resumo para Cassiano](2026-11-26-n05-log-qa-4c930a5405/resumo-cassiano.md)
e a [matriz final](2026-11-26-n05-log-qa-4c930a5405/matriz.csv) apoiam o repasse.

Os roteiros históricos contêm caminhos absolutos do ambiente ensaiado.
Uma repetição em outra máquina exige adaptar somente a orquestração externa,
identificar fonte e dependências efetivas e usar recursos próprios. Não usar
portas, volumes ou credenciais do ambiente diário. Não executar diretamente
os scripts dentro destas evidências se eles sobrescreverem seus resultados.
As versões de dependências declaradas têm faixas abertas; um build futuro
pode resolver versões diferentes das registradas nos relatórios.

## Conferência do conteúdo versionado

O manifesto abaixo identifica o snapshot histórico consolidado em
21cefa6. As rotas clínicas acrescentadas posteriormente são uma revisão
funcional nova e têm evidências próprias. Para verificar o pacote histórico,
leia os blobs desse commit, independentemente das alterações atuais:

```bash
python3 - <<'PY'
import hashlib, json, subprocess
from pathlib import Path
manifest = json.loads(Path('docs/relatorios/prontuario-correcoes-qa-2026-11-26/manifesto-pacote-aprovado.json').read_text())
for name, expected in manifest.items():
    blob = subprocess.check_output(['git', 'show', '21cefa6:lumina_odonto/' + name])
    assert hashlib.sha256(blob).hexdigest() == expected, name
print(f'{len(manifest)} arquivos do snapshot histórico correspondem ao pacote aprovado.')
PY
```

Essa comparação não atribui o parecer antigo ao código funcional posterior.
As evidências originais das subpastas permanecem históricas.

## O que permanece pendente

- Publicação e revisão desta branch: os commits desta consolidação são locais.
- Alinhar API e frontend: patient_id obrigatório, paginação por candidatos,
  total da página, códigos 422/413, envelope de erro, version e token clínico.
- Definir e executar a transição entre a API avulsa `lumina_odonto/` e o
  backend/Compose usados pela equipe; esta branch não substitui a API diária.
- Planejar migração/upgrade e validar frontend integrado em versão identificada.
- Decisões clínicas e de operação ainda abertas nos relatórios (D05/D06,
  exportação e critérios de rate limiting) não foram decididas por este commit.

A política de logs foi validada nos loggers Uvicorn e configuração distribuída.
Proxy, coletor, SQL echo e loggers externos exigem revisão própria. A redução
de detalhes de exceção protege a entrada clínica, mas limita o diagnóstico.

A branch de OpenCL da Agenda `feat/paralelismo-agendamento` foi preservada
no commit `e49a3ce22f899ad64d971a50e8d7fd9c99cb5b3a` e não integra esta branch.
Não houve push, merge, implantação, reinício dos serviços ou alteração do banco
diário nesta consolidação. O código não representa aceite global da Sprint.
