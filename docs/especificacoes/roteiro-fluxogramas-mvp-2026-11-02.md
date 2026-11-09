# Lumina Odonto — Roteiro para produzir os fluxogramas

**Data:** 02/11/2026.\
**Fonte:** [especificação funcional, versão 0.4](fluxo-atendimento-mvp-2026-11-02.md).\
**Uso:** descrição para quem desenhará as imagens. Este arquivo não gera imagens e não declara implementação.

## 1. Orientação visual

Produzir imagens separadas, legíveis no PDF, sem concentrar todo o sistema em um único desenho. Usar raias quando útil para identificar paciente, recepção, dentista e sistema. Administrador participa do fluxo próprio de recuperação. O sistema é executor, não um perfil humano.

Paciente participa fora da plataforma; não desenhar login, aplicativo ou portal de paciente. Usar caixas para ações e losangos para decisões, com saídas nomeadas. Não representar senha, dados clínicos ou valores reais nos exemplos.

Legenda obrigatória, escrita além das cores:
- **Atual/local:** operação encontrada, podendo depender de alterações não publicadas.
- **Novo aprovado:** comportamento definido por Paulo e ainda a implementar.
- **Recomendação técnica:** desenho técnico sujeito ao detalhamento dos contratos.
- **Pendente:** regra não definida; o desenho não escolhe uma solução em seu lugar.

Usar fundo claro, texto em português e setas sem cruzamentos desnecessários. Preferir SVG ou PDF vetorial; PNG deve ter resolução suficiente para leitura. Identificar número do fluxo, versão 0.4 e data. Não adicionar telas, rotas, estados ou permissões que não estejam na especificação.

## 2. Imagem 1 — Atendimento e encaminhamento

**Objetivo:** explicar o percurso normal sem misturar as três finalizações.

Raias: paciente, recepção, dentista e sistema.

1. Paciente solicita consulta à recepção.
2. Recepção agenda e registra confirmação autorizada; sistema guarda situação e evidência.
3. Dentista seleciona consulta própria.
4. Sistema verifica conta, perfil, clínica, cadastro profissional e fundamento assistencial.
5. Decisão: acesso elegível? Não → informar impedimento sem conteúdo clínico; terminar ou voltar à consulta. Sim → verificar liberação da segunda senha.
6. Sem liberação válida → entrar no fluxo de desbloqueio da imagem 2. Com liberação válida → abrir histórico autorizado.
7. Dentista realiza atendimento e salva evolução com descrição. A evolução pode permanecer rascunho; salvamento é confirmado pelo sistema.
8. Dentista informa itens com nome, quantidade e preço, OU declara Sem cobrança. Sistema calcula totais.
9. Dentista revisa, informa horário da realização com fuso e solicita Concluir atendimento.
10. Sistema verifica: consulta CONFIRMED com evidência, responsável, horário válido, evolução correspondente salva com descrição e itens ou Sem cobrança explícito.
11. Se inválido → informar o ponto de correção, sem concluir.
12. Se válido → gravar conclusão, evidência de realização e encaminhamento numa operação consistente, conforme proposta técnica.
13. Decisão: gravação confirmada? Não → apresentar falha e recuperar estado conforme imagem 2. Sim → mostrar consulta concluída e disponibilizar encaminhamento administrativo.
14. Recepção recebe somente identificação e itens administrativos. Caminho com cobrança → imagem 5; Sem cobrança → encaminhamento identificado como tal, sem inventar recebimento.
15. Dentista pode consultar Consultas realizadas; acesso posterior ao prontuário continua exigindo autorização e liberação clínica.

Notas ao lado do desenho:
- Salvar/finalizar evolução não conclui consulta. Concluir não finaliza evolução nem registra pagamento.
- Evolução salva antes continua salva se a conclusão posterior falhar; não desenhar um rollback apagando todo o atendimento.
- Contrato atual de conclusão ainda não cria encaminhamento; essa etapa é nova.
- Não transformar Sem cobrança em pagamento recebido zero ou terceiro estado financeiro sem definição.

## 3. Imagem 2 — Desbloqueio, acesso e falhas

Raias: dentista e sistema, com referência à recepção para eventos da Agenda.

### Desbloqueio e perda de acesso

1. Conta principal autenticada → verificar liberação clínica válida.
2. Se válida, verificar também o vínculo; se não, solicitar segunda senha.
3. Senha correta → emitir liberação conforme contrato futuro → reconferir vínculo → permitir conteúdo autorizado.
4. Senha incorreta → negar, sem conteúdo; nova tentativa segundo política pendente. Não desenhar tentativas ilimitadas.
5. Esqueci a senha → imagem 4. Falha de conexão → informar indisponibilidade sem afirmar senha errada.
6. Liberação expira durante edição → bloquear nova gravação, orientar autenticação e retomada segura do trabalho; não indicar sucesso nem descarte silencioso. Duração e mecanismo de preservação são pendentes.
7. Logout ou recuperação → invalidar liberação conforme política que será definida.

### Cancelamento ou ausência

1. Recepção registra cancelamento/ausência nas permissões vigentes.
2. Sistema preserva evidência histórica e reavalia todas as origens da dupla paciente–dentista na clínica.
3. Existe outra confirmação confiável ativa ou atendimento anterior comprovado? Sim → manter leitura autorizada, exigindo liberação clínica válida. Não → retirar preparação, negar conteúdo e interromper gravação não autorizada.
4. Não criar concessão por segunda senha nem permitir que administrador contorne a regra.

### Falha ao concluir e resposta perdida

1. Erro antes do commit → reverter conclusão, evidência e encaminhamento daquela operação; mostrar consulta não concluída e oferecer correção/reenvio seguro.
2. Resposta perdida, sem certeza do resultado → consultar o estado persistido ou repetir com mecanismo de idempotência definido pelo backend.
3. Já concluído/encaminhado pela mesma operação → recuperar resultado, sem segunda cobrança.
4. Pedido diferente ou estado concorrente → informar conflito e recarregar. Não indicar rollback confirmado apenas por falha de rede.

## 4. Imagem 3 — Salvar, editar e finalizar evolução

Raias: dentista e sistema.

1. Abrir rascunho próprio autorizado e obter sua versão.
2. Editar e enviar descrição/campos com a versão lida.
3. Sistema verifica autorização vigente, autoria, estado DRAFT e versão atual sob controle concorrente.
4. Sem autorização → negar, sem gravar nem expor conteúdo. Registro já finalizado → bloquear edição comum.
5. Versão atual → salvar, incrementar versão e retornar confirmação; só então mostrar salvo.
6. Versão antiga → HTTP 409; preservar o texto digitado com segurança e orientar revisão/recarga. Não reenviar automaticamente substituindo a versão.
7. Falha técnica → não mostrar sucesso; permitir recuperar estado antes de repetir.
8. Finalizar evolução é outra ação, com confirmação do dentista; se aceita, passa a FINALIZED e fica sem edição comum.
9. Retificação segue pendente; não desenhar reabertura ou edição da finalizada.

Nota: obrigatoriedade de evolução salva antes de concluir não significa finalizar automaticamente. O número da versão é detalhe do contrato; não exigir que o usuário o digite.

## 5. Imagem 4 — Recuperação da senha clínica

Raias: dentista, administrador e sistema.

1. Dentista solicita recuperação.
2. Administrador autentica-se e verifica solicitante e clínica.
3. Solicitação autorizada? Não → recusar, sem mudar credenciais. Outra clínica → negar.
4. Sim → sistema emite credencial temporária para a finalidade específica, com validade e uso único; registrar emissão sem segredo em logs.
5. Entrega ao dentista por canal a definir. Falha de entrega → registrar falha e seguir política de reemissão pendente; não desenhar envio automático por canal não aprovado.
6. Dentista entra na conta principal e apresenta credencial temporária para definir nova senha clínica.
7. Sistema verifica alvo, clínica, finalidade, prazo e consumo. Inválida/expirada/consumida → negar e orientar nova solicitação.
8. Válida → salvar hash da nova senha, consumir credencial e invalidar liberações anteriores numa operação consistente.
9. Falha ao salvar → informar sem declarar recuperação concluída. Dois resgates simultâneos não podem ser aceitos com a mesma credencial.
10. Dentista desbloqueia a área com a nova senha; vínculo e demais permissões continuam exigidos.

Notas: administrador não recebe a senha definitiva; credencial temporária não abre prontuário; recuperação do login principal não está incluída neste fluxo.

## 6. Imagem 5 — Recepção e pagamento simples

Raias: paciente, recepção e sistema.

1. Recepção abre encaminhamento administrativo da própria clínica.
2. Sistema mostra consulta, paciente, profissional, itens e totais, sem evolução ou notas clínicas.
3. Atendimento declarado Sem cobrança? Sim → mostrar identificação administrativa; não criar recebimento fictício. Representação financeira definitiva ainda a detalhar.
4. Com cobrança → pagamento ocorreu? Não → manter pendente, sem impedir o registro de atendimento concluído.
5. Sim → paciente paga fora da plataforma, por maquineta ou outro meio da clínica; recepção verifica e solicita confirmação no sistema. Não exigir digitação de valor recebido ou forma de pagamento neste recorte.
6. Sistema valida identidade, clínica, encaminhamento e situação da confirmação.
7. Inválido → informar motivo, sem gravar. Confirmação indevida e correção → sinalizar decisão pendente, sem inventar estorno.
8. Válido → registrar a confirmação de pagamento externo, responsável e instante. Mostrar sucesso somente após confirmação da gravação.
9. Resposta perdida ou reenvio → recuperar registro e impedir duplicidade. Falha de gravação → informar sem marcar pago.

Não adicionar integração com maquineta, processamento de cartão/Pix, parcelamento, emissão fiscal ou caixa. A confirmação registra a declaração da recepção; não comprova eletronicamente a transação externa. O significado exato de quitação integral ainda deve ser explicitado.

## 7. Imagem 6 — Correção de serviços pelo administrador

Raias: administrador, sistema e recepção. Fonte em [Mermaid complementar](fluxogramas-complementares-mvp-2026-11-02.md).

**Situação:** responsabilidade administrativa definida; condições abaixo são limites técnicos propostos, ainda sujeitos a fechamento. Não representam API existente.

1. Administrador abre encaminhamento da própria clínica, sem acesso ao texto da evolução.
2. Sistema verifica perfil e clínica. Se pagamento já estiver confirmado, bloquear correção comum; não criar estorno neste recorte.
3. Antes da confirmação, administrador revisa itens e informa motivo; a requisição leva a versão lida do encaminhamento.
4. Sistema bloqueia/recarrega e reconfere autorização, pagamento e versão no momento da gravação.
5. Pagamento confirmado nesse intervalo → recusar. Versão desatualizada → apresentar conflito para revisão.
6. Validar itens ou Sem cobrança e recalcular totais.
7. Gravar correção e histórico anterior/posterior, motivo, ator, instante e nova versão em operação consistente.
8. Falha → reverter a correção; resposta perdida → recuperar o resultado sem duplicar.
9. Recepção consulta dados atualizados. Evolução, autoria clínica e situação de atendimento permanecem sob suas regras próprias.

Não indicar que uma correção apaga o registro anterior ou que o administrador pode editar prontuários. Não usar o número de versão da evolução como versão do encaminhamento.

## 8. Entrega das imagens e composição documental

Paulo encaminhará as imagens à documentação. A documentação deverá:
1. Conferir cada imagem contra este roteiro e a especificação da mesma versão.
2. Registrar divergências antes de incorporar, sobretudo regras ou estados adicionados pelo desenhista.
3. Identificar versão, legenda e autoria/fonte, sem atribuir teste ou implementação ao desenho.
4. Inserir figuras legíveis no PDF, dividindo páginas conforme necessário.
5. Preservar fonte editável e indicar pendências. Uma imagem bem apresentada não transforma proposta em requisito aprovado.

Os nomes Imagem 1 a Imagem 6 organizam o material; não são IDs de novos requisitos funcionais. O fluxo 6 foi acrescentado na versão 0.4. Paralelismo do Argon2 permanece apenas sugestão textual e não precisa de diagrama próprio neste material.
