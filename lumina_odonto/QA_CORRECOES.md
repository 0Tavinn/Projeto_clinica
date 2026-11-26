# Correções propostas — QA 23/11/2026, candidata 4ccdc30

Base: ZIP fornecido, não checkout Git. O ZIP já continha .env.example e sql/; o schema permanece byte a byte igual ao SHA-256 do PR18 informado no PDF: `2ca830bda08ba3711f69408fe5848a5fd3304156373020f90310b04e746eda81`.

| Ficha | Alteração | Reteste necessário |
|---|---|---|
| N01 | Lock e autorização antes de selecionar candidatos; libera durante processamento e revalida com lock antes de devolver | Corrida real PostgreSQL, CPU e OpenCL, inclusive durante kernel |
| N02 | DTO remove scheduled_period interno de listagem, detalhe e mutações; casts de filtros opcionais | GET/PATCH/DELETE e estado persistido |
| N03 | Mantidos arquivos de inicialização presentes no ZIP; .gitignore e .dockerignore adicionados | Checkout limpo, compose config, build, seed |
| N04 | Revogação permite paciente/dentista inativo da mesma clínica; concessão continua exigindo ativos | Evento, auditoria, isolamento e reativação |
| N05 | Handler 422 sem input, ctx ou mensagens que ecoem dados | Sentinelas na resposta e logs |
| N06 | patient_id obrigatório e filtro por paciente | Dois vinculados e um não vinculado |
| N07 | version inteiro estrito positivo | PATCH e finalize, tipos inválidos e versão antiga |
| N08 | Normalização validada antes de selecionar motor; CPU também rejeita vazio | Todos os motores, Unicode |

Decisões propostas: 422 para termo inválido; patient_id obrigatório; scheduled_period não faz parte do DTO público; 413 para orçamento excedido; paginação por candidatos com next_offset (não por resultados). Confirmar com Tech Lead. Também removidos hashes de senha das respostas de atualização de usuários.

Validação local: compileall aprovado; pytest: 4 aprovados, 2 skips (runtime OpenCL e módulo de contrato por falta de psycopg/pwdlib). Docker e PostgreSQL não disponíveis. Não há novo SHA Git nem aceite QA. Os oito defeitos permanecem sujeitos a reteste. A rechecagem de autorização estabelece a ordem transacional antes da serialização; não garante revogação retroativa de dados já enviados. Não foi executada a corrida real nem validada a integração com frontend.

Pendências do relatório: política de exportação, transição API antiga/PR18, inativação durante espera, corrida durante kernel, mais de 1000 candidatos, orçamento de bytes, resets, navegador, conteúdo vencedor e política de rate limit. Migrações históricas não fornecidas no ZIP; não foram recriadas. Execute a suíte original no repositório que contém Alembic. Não use dados reais antes do aceite.
