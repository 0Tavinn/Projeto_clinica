# Preparação da integração Docker — Sprint 7

**Data:** 23/10/2026
**Área de revisão:** branch local `chore/sprint-07-docker-integration`
**Referência funcional:** `ab129d7` (`clinic/sprint-07-maintenance-dashboard`)
**Origem da infraestrutura:** `e293d3c` (`feat/containerizacao-docker`, Otávio)
**Base comum dos commits:** `b224faa`

## O que foi reunido

A área de revisão parte da Sprint 7. As alterações do commit de Otávio foram aplicadas sem criar commit: Compose na raiz, PostgreSQL, imagens da API e do frontend, Nginx, variáveis de exemplo e instruções de execução. As correções de inicialização da API, o frontend clínico e `docs/sprint/sprint-07.md` permanecem na base.

As mudanças locais de Paulo em `docs/requirements.md`, `docs/business-rules.md` e `docs/requisitos/` também foram copiadas para esta área. A pasta original e o arquivo `project-backups/20261023-pre-otavio-docker/` são o ponto de retorno. Esta cópia documental ainda não é um commit aprovado.

## Revisão técnica inicial

- A versão de Otávio isolada não importa a API: a anotação de `Dentist` falha em `backend/app/users/models.py`; `backend/app/main.py` também registra o router clínico antes de criar `app`. A base Sprint 7 já corrige esses dois pontos.
- Nesta área integrada, `import app.main` e `configure_mappers()` passaram com o ambiente Python local e SQLite apenas para importação; o OpenAPI expõe 17 caminhos. Isso não valida PostgreSQL nem os contêineres.
- `docker compose --env-file .env.example config --quiet` passou. A consulta de volumes Docker não encontrou `lumina_odonto_postgres_data` neste host em 23/10/2026. Esse foi o resultado da revisão inicial; o ensaio posterior está registrado abaixo.
- `docker-compose.yml` inicializa `backend/database/schema.sql` quando o volume PostgreSQL é criado. Não executa Alembic. O DBA deve aprovar a estratégia para bancos existentes antes de qualquer migração.
- O volume tem nome fixo `lumina_odonto_postgres_data`. Antes do ensaio, conferir se já existe um volume com esse nome e escolher um volume descartável próprio para a integração. Evitar `docker compose down -v` em dados que não sejam do ensaio.
- O frontend usa imagem de build e Nginx; alterações de código exigem reconstrução da imagem. Uma configuração de desenvolvimento com atualização automática pode ser planejada depois do primeiro aceite.

## Ensaio do backend relatado em 23/10/2026

O responsável pelo backend informou que `docker compose config --quiet` e o build da API passaram. No contêiner, `import app.main`, `configure_mappers()` e a presença das cinco rotas clínicas sob `/api/v1` passaram. Em Compose isolado, PostgreSQL e API ficaram saudáveis; `/health` respondeu 200. Um `SELECT` pela API conectou ao PostgreSQL e encontrou as oito tabelas iniciais. Paulo confirmou ao backend o uso de banco descartável com `schema.sql`.

O ensaio usou o projeto `lumina_s07_review_20261023`, override `/tmp/lumina-s07-compose-CDWOeD.yml` e volume exclusivo `lumina_s07_docker_review_20261023`. Os contêineres foram parados e o volume foi preservado. Estes são resultados **relatados pelo backend**; este registro não contém logs completos nem uma repetição independente do ensaio.

A comunicação API–PostgreSQL foi demonstrada. Os testes posteriores dos três serviços estão registrados abaixo. Permissões e persistência clínica permaneceram fora desse ensaio.

## Ensaio dos três serviços e persistência em 23/10/2026

Paulo executou `docker compose ... up -d --build db api frontend` no projeto isolado. O Compose informou PostgreSQL e API saudáveis e frontend iniciado; o `ps` mostrou os três saudáveis. As respostas de `/health` da API (porta 18008) e do frontend (porta 18080) foram HTTP 200. O seed criou usuários, dentistas, 50 pacientes e dois agendamentos fictícios. Paulo relatou que a interface e o login administrativo funcionaram.

Após `docker compose ... restart db api frontend`, Paulo atualizou a interface e informou que ela permaneceu disponível. Uma verificação direta posterior confirmou os três contêineres saudáveis e `SELECT count(*) FROM patients` retornou **50** no PostgreSQL. Isso demonstra inicialização e recuperação dos dados de demonstração após reinício neste ambiente isolado.

## Próximos passos

1. João registra o aceite formal da integração com a versão testada e confere permissões por perfil e clínica.
2. Caio identifica defeitos reproduzíveis na interface; backend e DBA corrigem os problemas correspondentes na API e no banco.
3. Otávio revisa Compose, Dockerfiles, Nginx, variáveis e instruções desta versão integrada.
4. O fluxo clínico recebe aceite separado após aprovação das regras de acesso e testes com dados fictícios.

**Limite deste registro:** os ensaios demonstram o ambiente Docker básico e a persistência dos dados seed. Não demonstram fluxo clínico completo, isolamento entre clínicas nem dashboard e relatórios da Sprint 7.
