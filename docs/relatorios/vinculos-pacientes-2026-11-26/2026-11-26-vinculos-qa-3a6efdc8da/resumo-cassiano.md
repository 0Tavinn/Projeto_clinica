# Resumo para Paulo e Cassiano — pacientes clínicos e vínculos

**Pronto com ressalvas para integrar as novas rotas em ambiente de teste.**

Em **26/11/2026**, o **agente de QA** testou independentemente a implementação local do Backend em **fix/prontuario-correcoes-qa**, sobre o HEAD **67068ac969cb7b34396b5d94e4ee09a7001ef8b4**, com alterações ainda sem commit e índice vazio. A fonte efetivamente testada é identificada pelos **31 arquivos** do manifesto **95fb2b8e2fd21f7a5a9e125fcbb7aaeb110e74d610eb150f3a4bb7f8d33bfcd7**.

Passaram **58 verificações independentes HTTP/SQL** e os **32 testes distribuídos**, sem skips. Os grupos se sobrepõem e não devem ser somados como cenários distintos. Também passaram 20 asserções sobre os mesmos logs e a comparação do OpenAPI. Os resultados do Backend e as 74 sondagens antigas não foram incorporados.

A API real, iniciada pelo CMD original, usou **PostgreSQL 16.16 descartável**. Foram verificados isolamento por dentista/clínica, identificação mínima, vínculos manuais sem consulta, prontuário vazio ou ausente, pesquisa literal, cursor, permissões e administração de inativos com preservação de dados e auditoria.

Com bloqueios reais comprovados pelo PostgreSQL, revogar retirou o paciente da página e fez o detalhe retornar403. A página vazia manteve cursor útil. Invalidar a sessão durante a espera retornou 401 nas duas rotas. Os logs registraram os templates corretos sem query, ID, token ou sentinelas clínicas; a busca antiga também executou OpenCL real em CPU.

Não foi reproduzido defeito de produto no recorte. Uma tentativa do auxiliar foi interrompida antes do HTTP, preservada e corrigida somente no cliente QA. Há uma observação documental sobre a ordem das chamadas de autorização; a fonte congelada foi registrada como referência.

Aplicação, frontend, Git, pacotes e serviços existentes foram preservados; todos os recursos próprios foram removidos. O parecer não concede aceite de navegador, implantação ou Sprint. O próximo passo é publicar uma referência verificável e executar a integração com o frontend.
