# Checkpoint — pausa solicitada por Paulo em 25/11/2026

Estado: execução de testes encerrada; relatório final ainda NÃO concluído. Pausa solicitada por Paulo, sem autorização implícita de retomada.

Candidata: pacote /home/paulinho/Work/lumina_odonto_corrigido_QA/lumina_odonto_atualizado, sem Git.
SHA256 do manifesto: 987ee7199972977bc549346246d0ee5bf46d4611b9d15c3c8fc89fdfbd41fe40.
Proveniência informada por Paulo; não comprovada por autoria Git.
Schema SHA256: 2ca830bda08ba3711f69408fe5848a5fd3304156373020f90310b04e746eda81.
Base comparada: 4ccdc30a27143b6c022b7f8cae2e6ccf03860389, subpasta lumina_odonto.

## Execução já concluída

- Dockerfile original construiu sem adaptar aplicação/dependências.
- API Uvicorn HTTP real e PostgreSQL16.16 descartável.
- CPU OpenCL real: PoCL6.0, Intel i5-13420H, PyOpenCL2026.1.5, NumPy2.5.5.
- Sondagens independentes: 74 IDs únicos,73 aprovados,1 reprovado.
- Testes fornecidos:18 aprovados,zero skips,contados separadamente porque se sobrepõem semanticamente às sondagens.
- Pendências na matriz:7 bloqueadas,2 não executadas.
- N01:403 após revogação durante espera comprovada em pg_stat_activity, CPU e OpenCL. Instrumentação EXTERNA preservou o kernel original e comprovou evento RUNNING antes/depois do commit da revogação;403 sem resultados. CPU: revogação após comparação real, antes de retornar à rota; não alegar durante instruções CPU.
- N02/N03/N04/N06/N07/N08: cenários exercitados aprovados, sem transformar contratos propostos em decisão clínica definitiva.
- N05 parcialmente corrigido: corpos422 sem eco e atualização de usuário sem hashes; termo clínico da query ainda aparece no access log padrão da API original. privacy-log-check.json e api-sanitized.log comprovam. Reproduzir GET /api/v1/clinical/search?q=<sentinela fictícia>, com token clínico e sem patient_id:422 e termo presente no log.
- Duas edições mesma versão:200/409,versão2,conteúdo vencedor correto. Edição versus finalização:200/403,FINALIZEDv2,sem sobrescrita.
- Rollbacks de paciente/prontuário e evolução/auditoria passaram com gatilhos temporários apenas no banco QA.
- Paginação1005 candidatos,privacidade,Unicode,limite2MB/413,resets,tokens,reinício com dados/credenciais preservados passaram nos limites dos roteiros.
- Persistência comparou10 tabelas antes/depois de restart dos mesmos contêineres, não recriação/restauração.
- Nenhum teste de frontend/navegador.

## Artefatos disponíveis

matriz.csv, tentativas.csv, totais.json, scripts QA, logs, contratos OpenAPI antes/depois, manifesto de hashes, diff sanitizado, preservation.json, cleanup.json.
Relatorio.md e resumo final para Paulo/Tarcísio/Cassiano AINDA NÃO foram escritos.
Arquivo .qa-ephemeral.env foi removido. A cópia TAR criada pelo QA foi removida para não distribuir hashes fictícios do seed; originais do pacote preservados.
Diff distribuível foi sanitizado de3 hashes fictícios, declaração e hash do diff original em artifact-sanitization.json.

## Preservação e limpeza

Todos os40 arquivos recebidos, inclusive Zone.Identifier, iguais antes/depois.
Checkouts principal e alternativo:HEAD,status e bytes do índice iguais antes/depois.
Principal em feat/paralelismo-agendamento,HEAD e49a3ce22f899ad64d971a50e8d7fd9c99cb5b3a;alternativo destacado no mesmo HEAD conforme inventário desta rodada.
Inventários anteriores/posteriores de containers,volumes,redes iguais.
Recursos próprios lumina-corrected-qa-6ba8c93e83:cinco containers,volume,rede e imagem removidos por rótulo/identidade.
Sem teste ativo nem tarefa longa deixada em andamento.

## Tentativas de roteiro preservadas

- setup-attempt-1.py.txt:syntax error em script de QA, antes de criar recursos; não falha do produto.
- final_probe.py.log:KeyError ao usar id em vez de appointment_id; caso de vínculo duradouro repetido em status_probe.py.log e aprovado.
- concurrency-replay.log:disputa de agenda em horário que já tinha consulta da primeira execução retornou409/409; pré-condição inválida, não defeito. appointment-race-final.log usa horário livre e pacientes novos,201/409,uma consulta/vínculo/evento.
- Último resultado válido por ID na matriz; tentativas não somadas.
- A primeira concorrência foi observada no console sem arquivo; repetição preservada em concurrency-replay.log,mesmos critérios,sem somar como casos distintos.
- Aviso de chave curta no reset_probe.py.log vem de token inválido deliberadamente gerado pelo QA, não da chave real/efêmera da API.

## Próximos passos SOMENTE após Paulo pedir retomada

1. Escrever relatório completo Markdown,comparativo de contratos,reprodução e resumo para Cassiano com base nas evidências salvas.
2. Tabela N01–N08: sete corrigidos nos cenários exercitados,N05 persiste parcialmente; distinguir contrato candidato e implantação.
3. Descrever N05 como falha de privacidade,propor responsável Backend e reteste,sem corrigir aplicação.
4. Documentar comandos de reprodução,especialmente instrumentação e controles de isolamento,sem expor segredos.
5. Revisar matriz e caminhos:coluna de comando dos UNIT usa rótulo de caso após :: em texto; explicar comando pytest completo e seleção individual separadamente.
6. Contar grupos separadamente:74 sondagens,18 testes fornecidos,9 pendências;não anunciar92 cenários distintos.
7. Conferir artefatos e sanitização,gerar manifesto de evidências e entregar links absolutos. Não criar PDF nesta etapa.
8. Parecer restrito à candidata:pendência de privacidade impede declarar pronta para integração com dados clínicos;frontend/publicação/migração seguem sem aceite. Não misturar com Agenda OpenCL nem relatórios históricos.
