# Resumo para Paulo, Tarcísio e Cassiano

**Não pronto para integração desta candidata.**

Em **25/11/2026**, o **AGENTE DE QA** revalidou o pacote de prontuários e busca OpenCL informado por Paulo como entrega corrigida de Tarcísio. O pacote não possui Git: sua identidade é o manifesto SHA256 **987ee7199972977bc549346246d0ee5bf46d4611b9d15c3c8fc89fdfbd41fe40**. O relatório foi finalizado em **26/11**, sem novos testes funcionais nessa data.

O Dockerfile original construiu, e a API foi exercitada por HTTP real com **PostgreSQL 16.16 descartável** e OpenCL real em CPU PoCL. Das **74 verificações independentes, 73 passaram e 1 reprovou**. Os **18 testes fornecidos passaram, sem skips**, e ficam em contagem separada por sobreposição de cobertura. A matriz também registra **7 pendências bloqueadas e 2 não executadas**. Os resultados históricos de 23/11 não foram somados.

Sete defeitos anteriores passaram no recorte revalidado. Foram comprovados: resposta 403 após revogação durante espera por bloqueio e durante execução real do kernel; edições concorrentes com 200/409 e conteúdo vencedor correto; operações de Agenda sem a falha de serialização exercitada; revogação de alvos inativos; busca limitada ao paciente; e validação estrita da versão. O reinício dos mesmos contêineres manteve os dados das dez tabelas comparadas.

**N05 está parcialmente corrigido:** a resposta 422 deixou de ecoar a entrada clínica, mas o termo de busca enviado na URL permanece no log padrão do Uvicorn. A reprodução usou uma sentinela fictícia. Não foi demonstrado acesso de terceiros nem exposição de dados reais. O Backend deve omitir ou redigir valores clínicos dos logs e repetir as verificações de privacidade antes de encerrar o defeito.

Este parecer não aprova interface, implantação, upgrade de banco ou futuro commit com conteúdo diferente. Faltam alinhamento dos contratos candidatos, referência publicada verificável, estratégia de migração/transição e percurso com frontend identificado. D05/D06, exportação e critérios de rate limiting dependem de decisão. Os recursos exclusivos foram removidos, e o pacote, os checkouts e os ambientes existentes foram preservados.

O relatório completo, a matriz, as tentativas, os totais e os roteiros estão nesta pasta. Não foi criado PDF nem publicado conteúdo. As execuções são do **agente de QA**, não de João Vitor.
