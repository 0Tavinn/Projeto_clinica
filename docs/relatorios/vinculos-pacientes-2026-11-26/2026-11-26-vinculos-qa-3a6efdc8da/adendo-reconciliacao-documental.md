# Adendo documental — observação reconciliada em 26/11/2026

A divergência sobre get_patient foi **reconhecida pelo Tech Lead e corrigida no relatório externo do Backend**. A orientação anterior se referia a uma versão intermediária, com somente a chamada posterior de allowed.

Na fonte final testada, get_patient chama allowed **antes dos bloqueios e novamente depois da espera**. O relatório do Backend agora descreve ambas as chamadas e registra a reconciliação, preservando a observação histórica do QA.

Arquivo conferido:app/clinical_patients_service.py.
SHA256:52b2de0a70f08482ec3187dca765f101957caef47232c7e88e5241b169caaf55.
Manifesto dos31 arquivos:95fb2b8e2fd21f7a5a9e125fcbb7aaeb110e74d610eb150f3a4bb7f8d33bfcd7.

Esta observação **não é defeito de produto** e não permanece como correção funcional pendente. Nenhum arquivo da aplicação,guia ou teste foi alterado por esta reconciliação.
Não houve nova execução de testes,build ou operação emDocker/banco.

Os resultados continuam:58 verificações independentes aprovadas,32 testes fornecidos aprovados sem skips,20 asserções transversais de logs e1 comparação decontrato aprovadas,contadas separadamente por sobreposição.

Parecer mantido:pronto com ressalvas para integrar as novas rotas em ambiente de teste. Permanecem as limitações de fonte local semcommit,frontend não executado e implantação/aceite global pendentes.

Os arquivos originais do relatório,matriz,logs e notas do QA não foram reescritos. relatorio-v2.md e resumo-cassiano-v2.md incorporam este esclarecimento.
