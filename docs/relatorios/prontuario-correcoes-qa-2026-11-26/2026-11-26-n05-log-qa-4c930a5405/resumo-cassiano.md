# Resumo para Paulo e Cassiano — reteste N05-LOG

**N05-LOG encerrado para a candidata e a configuração testadas. Correção pronta com ressalvas de alcance.**

Em **26/11/2026**, o **agente de QA** executou um reteste independente da cópia corrigida, sem Git, identificada pelo manifesto SHA256 **e3b28488163b174758f7e3782dbe916b0cc1cf8120cadf5a3cd5da79200e2825**. A imagem original foi iniciada pelo CMD distribuído, com API HTTP real, PostgreSQL **16.16** descartável e OpenCL real em CPU PoCL.

O pacote anterior foi recebido de Tarcísio segundo Paulo. A cópia N05 foi preparada pelo **agente de Backend**, sob coordenação do Tech Lead e autorização de Paulo. Nenhuma das duas origens tem autoria Git comprovada.

Passaram **25 objetivos HTTP finais**, **23 verificações transversais sobre os mesmos logs** e **1 comparação de OpenAPI**. Os testes recebidos concluíram com **26 aprovações, sem skips: 18 anteriores e 8 focados**. Esses grupos não devem ser somados como cenários distintos. As 74 verificações antigas não foram repetidas.

As buscas válidas preservaram o conteúdo autorizado nas respostas, enquanto as entradas fictícias não apareceram no stdout/stderr da API nos caminhos testados. Erros 401/403/404/422 e um erro SQL real com resposta 500 mantiveram a proteção. Método, rota estática, status, HTTP/1.0/1.1 e eventos operacionais continuaram disponíveis.

Uma expectativa do roteiro foi corrigida de forma explícita: o parser rejeitou um método inventado com 400 antes do roteamento; isso não era defeito do produto. Um complemento restrito com TRACE recebeu 405 e confirmou o registro OTHER sem eco. Ambas as evidências foram preservadas.

Não houve teste de navegador, migração, publicação, implantação ou aceite integrado da Sprint. Proxy, coletor e configurações externas de logging continuam fora da prova. A redução do detalhe de exceções exige diagnóstico seguro por reprodução controlada.

O pacote original, a candidata, os relatórios anteriores e os checkouts foram preservados. Todos os recursos próprios foram removidos. O próximo passo é publicar uma referência verificável, conferir os hashes do conteúdo publicado e preparar a integração com o frontend, mantendo separadas as pendências de contratos, migração e decisões clínicas.
