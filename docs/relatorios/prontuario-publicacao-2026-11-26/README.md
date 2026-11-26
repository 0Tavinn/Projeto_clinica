# Prontuário corrigido — preparação da entrega para integração

**Data:** 26/11/2026. **Responsável pela execução:** agente Tech Lead desta conversa, com autorização de Paulo. Esta preparação não incorpora a entrega da Agenda nem implementa as interfaces de Caio/Otávio.

**Parecer:** ambiente da API clínica pronto para iniciar a integração das interfaces em testes locais. Passaram **16 verificações HTTP**, **32 testes fornecidos**, verificação de garantias SQL e parada/retomada do ambiente. Não houve aceite do frontend ou do sistema completo.

## Versão

- Branch: `fix/prontuario-correcoes-qa`.
- Base funcional corrigida: `94e8e22d8a3eb0b704848bccdaf235037ebb5131`.
- Preparação versionada: `4c2682545d2edb7794aa1e9d31774c543c8e848f`.
- Os 31 arquivos de `lumina_odonto/` constantes no manifesto aprovado anteriormente permaneceram byte a byte iguais. Ver `source-check.json` e o manifesto em `docs/relatorios/vinculos-pacientes-2026-11-26/`.
- Acrescentados: Compose alternativo de integração, template público sem segredos, helper de 134 linhas e guia do ambiente. O README da raiz identifica a API correta. A API funcional, SQL, regras, migrações, contratos e requisitos Markdown não foram reescritos.
- A branch da Agenda continua separada em `c3a83b656b8df2396b4ec8944d644abe6aaf77fd`. Não houve merge entre as entregas.

## Onde executar e integrar

O ponto de partida é [o guia de integração](../../../lumina_odonto/INTEGRATION.md).
O contrato para a interface está em [FRONTEND.md](../../../lumina_odonto/FRONTEND.md).

```bash
cd /home/paulinho/Work/Projeto_clinica/lumina_odonto
python3 scripts/integration.py status
```

No computador desta preparação:

| Recurso | Endereço/identificação |
| --- | --- |
| Swagger da API corrigida | http://localhost:18100/docs |
| OpenAPI | http://localhost:18100/openapi.json |
| Base para a interface | http://localhost:18100/api/v1 |
| Banco candidato fictício | 127.0.0.1:55450, lumina_prontuario_integracao |
| Projeto Docker | lumina_prontuario_integracao |
| Volume candidato | lumina_prontuario_integracao_integration_data |

O ambiente fica ativo para a integração. Ele não substitui o banco principal nem o ambiente da Agenda. Os endereços são locais a cada computador; colaboradores precisam clonar a branch e executar o setup descrito no guia. Não se espera que o localhost de Paulo seja acessível de outra máquina.

Não há nova interface nesta entrega. A interface da Agenda em `18088` continua associada à API da Agenda. Apontar esse cliente antigo para `18100` sem adaptar seus contratos não constitui integração válida.

## Configuração e proteção operacional

`setup` cria `.env.integration`, ignorado pelo Git, com permissão 600 e segredos aleatórios. A repetição foi recusada sem modificar o arquivo. O helper aceita somente o prefixo de projeto desta preparação, usa a configuração local com precedência sobre o shell e verifica propriedade de contêineres, rede e volume antes de operar. `stop` preserva dados; não há comando de remoção no helper.

O novo Compose usa portas de loopback, volume e rede próprios, sem reutilizar o volume diário. A API recebe `DATABASE_URL`, `JWT_SECRET` e CORS da configuração privada. O frontend não recebe senha de PostgreSQL ou segredo JWT.

Nenhum segredo real, token de login, arquivo `.env` ou dump foi incluído no relatório. As contas são apenas fictícias:

| Perfil | Conta | Login | Senha clínica |
| --- | --- | --- | --- |
| Administrador | admin.demo@example.com | DemoLumina2026! | Não utiliza |
| Dentista | dentista.demo@example.com | DemoLumina2026! | ClinicaDemo2026! |

A carga oficial traz dois usuários, três pacientes/prontuários, duas consultas, duas evoluções e cenários de vínculo ativo, revogado e ausente. Não há conta de Marina nesse banco candidato; a conta existente no ambiente diário não foi alterada. O seed não cria recepcionista.

## Banco e preservação

PostgreSQL **16.15**. O `sql/schema.sql` é o mesmo do PR18, SHA-256 `2ca830bda08ba3711f69408fe5848a5fd3304156373020f90310b04e746eda81`. Foi aplicado pelo entrypoint PostgreSQL **somente ao volume novo e vazio**. Não houve migração, SQL sobre banco existente nem stamp.

Este caminho SQL não executa a cadeia Alembic nem cria `alembic_version`. Não confundir o candidato com o banco diário, que possui revisão `a6e8f0b2c4d6` e permanece preservado.

O roteiro fornecido `sql/check_clinical_schema.sql` passou no candidato: versões positivas, prontuário único, sobreposição de agenda, evolução, auditoria, histórico e idempotência. As linhas de ensaio foram revertidas pelo ROLLBACK do roteiro; sequências podem avançar, portanto não presumir IDs consecutivos.

O seed repetido foi recusado. As contagens conferidas permaneceram 2 usuários, 3 pacientes, 3 prontuários, 2 consultas e 2 evoluções. A parada e retomada preservaram o volume. Isso não é ensaio de migração ou restauração de um banco com pacientes reais.

O ambiente diário `lumina_pr18_tarcisio` manteve os mesmos IDs, imagens, mounts e horários de início e continuou saudável. Seus arquivos privados foram conferidos por hash, sem serem publicados. Nenhuma escrita foi dirigida ao banco diário.

## Validação reproduzida

| Grupo | Resultado | Evidência |
| --- | --- | --- |
| Build e inicialização Compose | Passou | startup.log |
| HTTP real contra API implantada | 16 verificações passaram | http-smoke.json |
| Testes distribuídos na imagem | 32 passaram, 1 aviso | pytest.log |
| Garantias SQL no candidato | Passou, com rollback | schema-check.log |
| Recusa de setup repetido | Passou | reject-setup-repeat.log |
| Recusa de seed em banco preenchido | Passou | reject-seed-repeat.log |
| Parada/retomada e status | Passaram | stop.log, up-after-stop.log, status.log |

Os grupos se sobrepõem e não devem ser somados como um total de cenários únicos. Não foram repetidos todos os ensaios independentes de concorrência dos relatórios anteriores.

Comando dos testes existentes:

```bash
docker exec lumina_prontuario_integracao-api-1 python -m pytest -q -p no:cacheprovider --disable-warnings --tb=short
```

As verificações HTTP usam a API real, por urllib no host, sem TestClient. Corpos de resposta, conteúdo clínico, senhas e tokens não foram gravados no relatório:

| Verificação | HTTP obtido | Resultado |
| --- | --- | --- |
| health | 200 | Aprovado |
| OpenAPI | 200 | Aprovado |
| login admin JSON | 200 | Aprovado |
| login dentista JSON | 200 | Aprovado |
| identidade | 200 | Aprovado |
| segunda senha | 200 | Aprovado |
| pacientes vinculados | 200 | Aprovado |
| cabecalho autorizado | 200 | Aprovado |
| acesso revogado negado | 403 | Aprovado |
| token de acesso nao e clinico | 401 | Aprovado |
| prontuario | 200 | Aprovado |
| evolucoes | 200 | Aprovado |
| vinculos admin | 200 | Aprovado |
| busca CPU | 200 | Aprovado |
| busca OpenCL real | 200 | Aprovado |
| CORS frontend local | 200 | Aprovado |

A busca `engine_name=opencl` retornou motor OpenCL e os mesmos IDs de resultado que a busca CPU no exemplo fictício. Foi usado PoCL em dispositivo CPU Intel i5-13420H. Isso prova execução, não ganho de performance. Runtime: Python 3.12.16, FastAPI 0.165.0, SQLAlchemy 2.1.9, Pydantic 2.14.4, Uvicorn 0.54.0, NumPy 2.5.5, PyOpenCL 2026.1.5 e pytest 9.2.0; ver `runtime.log`.

## Próxima etapa e limites

Publicar esta branch e informar aos responsáveis pela interface o commit remoto efetivo, a base HTTP e os contratos. A situação remota deve ser confirmada por `git ls-remote`; este relatório não substitui essa confirmação e não presume autenticação GitHub disponível na sessão do agente.

Testar pela interface login, segunda senha, pacientes vinculados, rascunho/versão, finalização, busca, privacidade e revogação/reativação. A recuperação clínica administrativa e a impressão/identificação histórica seguem como lacunas documentadas. A conclusão e filtros da Agenda do outro backend ainda exigem harmonização futura ao reunir as entregas.

Nenhuma pessoa da equipe foi contatada e nenhum merge foi feito. O candidato ativo contém somente dados fictícios para desenvolvimento e validação.
