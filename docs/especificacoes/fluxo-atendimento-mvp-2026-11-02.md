# Lumina Odonto — Especificação do fluxo de atendimento do MVP

**Data:** 02/11/2026.\
**Versão:** 0.4 — correção administrativa detalhada e paralelismo mantido como sugestão; não é aceite de implementação.\
**Decisor de produto:** Paulo Sérgio.\
**Finalidade:** orientar o protótipo, os contratos da API e os futuros testes; fornecer a fonte para o PDF da equipe.\
**Referência técnica:** branch `chore/sprint-07-docker-integration`, HEAD `2f7dbfe6d0d7a747f57dbeeede3a716938adc5fa`, com alterações locais. Isso não identifica uma versão integralmente publicada ou executada.

## 1. Como usar este documento

Esta especificação consolida a reunião de 29/10, os pareceres de backend, frontend e QA e as decisões de Paulo em 02/11. Os pareceres foram análises, sem execução de novos testes. Não constituem aprovação das correções QA-01/QA-02 nem das funcionalidades propostas.

Os fluxogramas serão produzidos separadamente, conforme o [roteiro de desenho](roteiro-fluxogramas-mvp-2026-11-02.md). Paulo encaminhará as imagens à documentação para composição do PDF. Esta revisão não gera imagens nem PDF e não exige uma ferramenta específica de desenho.

Os [fluxogramas complementares em Mermaid](fluxogramas-complementares-mvp-2026-11-02.md) contêm o pagamento externo atualizado e a correção de serviços pelo administrador. A versão anterior do fluxo 5 que solicitava valor recebido e forma deve ser substituída pelo pagamento externo simplificado. O fluxo 6 é adicional e explicita limites técnicos propostos.

| Classificação | Significado |
|---|---|
| Aprovado por Paulo | Direção funcional definida; não comprova implementação. |
| Contrato atual/local | Comportamento encontrado na API; alterações locais precisam de identificação e publicação próprias. |
| Recomendação técnica | Solução orientada pelo Tech Lead; detalhes de contrato devem ser conferidos pelo backend. |
| Pendente | Escolha ainda não tomada; o protótipo deve mostrar a pendência sem inventar comportamento. |

## 2. Decisões aprovadas

| Tema | Decisão e alcance |
|---|---|
| Atores | Paciente, recepção, dentista e administrador. Paciente é participante externo; não será criado portal ou login de paciente neste recorte. |
| Segunda senha | O dentista terá senha de entrada e uma segunda senha pessoal para a área clínica. Não é senha por paciente e não substitui vínculo, autoria ou isolamento por clínica. |
| Recuperação clínica | Paulo aprovou credencial temporária com validade e uso único, para o dentista definir sua senha clínica definitiva sem revelá-la ao administrador. Prazo, entrega e verificação de identidade ainda precisam ser definidos. |
| Evolução antes da conclusão | Paulo aprovou exigir evolução salva com descrição. Ela pode permanecer em DRAFT; finalizar evolução é ação separada. Descrição vazia ou só espaços não satisfaz essa condição. Não criar nem finalizar uma evolução automaticamente para permitir a conclusão. |
| Serviços | Paulo aprovou itens informados pelo dentista, com nome, quantidade e preço, ou indicação explícita de atendimento sem cobrança ao concluir. Catálogo completo e tabela automática de preços não são exigidos nesta versão. |
| Pagamento externo — refinamento de Paulo | O pagamento ocorre fora da plataforma, pela maquineta ou outro meio da clínica. A recepção apenas confirma no sistema que o pagamento foi efetuado. Não exigir valor recebido ou forma como novos campos neste recorte. A confirmação deve identificar responsável e instante; não integra, processa ou comprova automaticamente uma transação financeira externa. |
| Responsável por corrigir serviços | Paulo indicou o administrador e autorizou detalhar o fluxo nesta especificação. Os limites técnicos propostos constam na seção 5.4; não confundir autorização para especificar com implementação ou aprovação automática de cada restrição. Não concede edição de evolução clínica. |
| Política clínica anterior | Confirmação confiável ativa sustenta preparação; atendimento comprovado sustenta continuidade. Finalizadas são compartilhadas entre dentistas autorizados, e rascunhos são privados ao autor. |

As decisões novas refinam RF-022, RF-023, RF-024 e as RN relacionadas. Não foram atribuídos novos IDs nem reescritos os catálogos nesta tarefa. Segunda credencial, encaminhamento administrativo e pagamento precisarão de formalização própria após conferência dos identificadores existentes.

## 3. Atores e limites

| Ator | Responsabilidade | Limite |
|---|---|---|
| Paciente | Solicitar/confirmar por atendimento da clínica, comparecer e pagar fora da plataforma quando houver cobrança. | Não possui tela ou credencial nesta proposta. Pode sair com pagamento pendente; consulta concluída não implica recebimento. |
| Recepção | Agendar e confirmar nas permissões vigentes; consultar encaminhamentos; registrar pagamento simples. | Não recebe texto clínico, diagnóstico, general_notes, descrição de evolução ou senha clínica. |
| Dentista | Atender consultas próprias, desbloquear área clínica, consultar histórico autorizado, salvar evolução, informar itens e concluir atendimento. | Não altera rascunhos de terceiros nem registros finalizados por edição comum. Senha correta não amplia pacientes autorizados. |
| Administrador | Recuperar a credencial clínica e corrigir serviços administrativos da própria clínica, conforme limites a fechar. | Não conhece a senha definitiva nem ganha acesso clínico por operar recuperação ou correção. Não edita evolução. Recuperação da senha principal é outro fluxo. |

O sistema executa validações e persistência; não é um quinto perfil de usuário.

## 4. Fluxo principal e sequência do protótipo

| Etapa | Ator e ação | Resultado pretendido e falhas a representar |
|---|---|---|
| 1 | Paciente solicita atendimento; recepção agenda e confirma. | Usar a operação autorizada: confirmação grava situação e evidência. Apenas mudar o status diretamente no banco não basta. |
| 2 | Dentista abre Consultas e seleciona consulta própria. | Listar por período/situação. Agendamento SCHEDULED isolado não libera prontuário. Exibir estado vazio, carregamento e consulta indisponível. |
| 3 | Sistema verifica conta ativa, perfil, clínica, cadastro profissional e fundamento assistencial. | Negar sem expor conteúdo se qualquer condição falhar. Não oferecer atalho administrativo para contornar o vínculo. |
| 4 | Dentista informa a segunda senha quando não houver liberação clínica válida. | Sucesso permite prosseguir somente dentro do conjunto já autorizado. Senha inválida, expiração e indisponibilidade devem ter caminhos próprios. Esta operação ainda não existe na API. |
| 5 | Dentista consulta histórico e registra/salva a evolução da consulta. | Exigir descrição. Guardar rascunho e sua versão; mostrar sucesso somente após confirmação do servidor. Conflito 409 não sobrescreve o registro nem descarta o texto digitado. |
| 6 | Dentista informa serviços e valores ou seleciona Sem cobrança. | O servidor calcula os totais. Confirmar a escolha explícita; lista vazia, sozinha, não significa atendimento gratuito. |
| 7 | Dentista informa o horário real com fuso, revisa e solicita Concluir atendimento. | Reusar a restrição vigente: dentista responsável, consulta CONFIRMED, confirmação confiável e condições de horário. Verificar também evolução salva com descrição e itens ou Sem cobrança, conforme decisões novas. |
| 8 | Sistema confirma conclusão, evidência da realização e encaminhamento administrativo. | Recomenda-se uma transação consistente para essas três partes. Falha não pode confirmar apenas parte delas. Evolução salva anteriormente não é finalizada por essa operação. |
| 9 | Recepção consulta os itens administrativos encaminhados. | Resposta própria, limitada à clínica. Nada de reutilizar a resposta do prontuário. Sem pagamento imediato, manter pendência de cobrança. |
| 10 | Pagamento ocorre fora da plataforma; recepção confere e confirma o recebimento no sistema. | Registrar a confirmação, o responsável e o instante, sem integração com maquineta, cobrança automática ou exigência de digitar valor e forma. Somente exibir sucesso após gravação; prevenir duplicidade de confirmação. |
| 11 | Dentista consulta Consultas realizadas e retorna ao histórico quando autorizado. | Reaproveitar filtro COMPLETED. Abertura do prontuário exige vínculo e liberação clínica válidos; não presumir autorização a partir de uma linha da listagem. |

Confirmar consulta, salvar rascunho, finalizar evolução, concluir atendimento e registrar pagamento são operações diferentes. O protótipo deve nomear cada ação e não sugerir finalizações ou pagamentos automáticos.

**Impacto de ordem:** exigir evolução salva antes de concluir obriga a permitir esse salvamento na consulta confirmada, respeitando autorização e autoria. Não se pode oferecer criação apenas depois de COMPLETED. Isso não aprova escrita em qualquer estado, atendimento avulso ou edição de finalizadas.

## 5. Procedimentos, consistência e pagamento

### 5.1 Itens e privacidade

- Itens informados pelo dentista: nome, quantidade e valor unitário; subtotal e total calculados no servidor com representação decimal apropriada.
- Lista curta de sugestões pode facilitar o protótipo; não criar dependência de catálogo mantido por usuários nesta versão.
- Preservar nome e preço praticados. Mudança posterior de sugestão não reescreve atendimento anterior.
- Vincular a consulta, paciente, clínica e dentista corretos. A evolução exigida deve corresponder ao atendimento, não ser um registro qualquer do paciente.
- Recepção recebe consulta, paciente, profissional, itens, totais e situação administrativa. Não recebe conteúdo clínico nem mesmo em mensagens de erro.
- `procedure_performed` permanece texto clínico. Não é tabela de preços nem fonte a expor à recepção.
- Sem cobrança é uma declaração administrativa explícita. Não fabricar recebimento zero nem confundir gratuidade com pagamento realizado. O backend deve propor a representação financeira desse caso.

### 5.2 Fronteira transacional recomendada

| Operação | Gravações e garantias |
|---|---|
| Salvar evolução | Transação própria, autoria e autorização; edição usa versão. Continua salva se uma conclusão posterior falhar. |
| Finalizar evolução | Ação própria, explícita e sujeita às regras clínicas; não conclui consulta. |
| Concluir e encaminhar — proposta nova | Validar consulta, evolução correspondente e serviços/Sem cobrança; gravar COMPLETED, evidência de realização e encaminhamento em um commit, ou reverter essas partes juntas. Não finalizar evolução nem registrar pagamento aqui. |
| Confirmar pagamento externo | Transação administrativa própria, com clínica, recepcionista e instante; não executa pagamento nem altera situação clínica. |

Propor unicidade do encaminhamento por consulta e idempotência de reenvio, sem limitar uma consulta a apenas um item de serviço. Após resposta perdida, recuperar o resultado persistido antes de tentar nova gravação. O contrato deve distinguir repetição idêntica de pedido diferente e impedir duas cobranças pelo mesmo encaminhamento.

A validação e os bloqueios precisam impedir que uma evolução validada seja removida ou invalidada durante a conclusão, ou que dados de serviços mudem enquanto seu total é usado no pagamento. A estratégia precisa ser detalhada pelo backend, sem ampliar os acessos clínicos.

### 5.3 Confirmação do pagamento externo

O refinamento de Paulo substitui o preenchimento de valor recebido e forma pela confirmação administrativa de pagamento efetuado fora da plataforma. Serviços e preços do encaminhamento continuam existindo; eles não são um registro de transação de cartão ou Pix.

Fluxo mínimo: encaminhamento com cobrança pendente → paciente paga pelo meio da clínica → recepção verifica o recebimento → confirma no sistema → sistema registra responsável e instante e apresenta a confirmação. Sem recebimento, manter pendente. Reenvio não gera segunda confirmação independente para o mesmo evento.

Não integrar adquirente, não armazenar dados de cartão, não calcular troco ou parcelamento e não emitir documento fiscal. A confirmação é declaração da recepção; não valida eletronicamente o pagamento externo. O significado exato de quitação integral, confirmação indevida e sua correção ainda precisa ser fechado; não inventar conciliação financeira.

### 5.4 Correção de serviços — responsável indicado, alcance pendente

Administrador foi indicado por Paulo como responsável. Recomendação técnica para limitar o MVP: permitir correção administrativa somente enquanto o pagamento estiver pendente, exigir motivo e preservar autor, instante e dados anteriores. Após confirmação de pagamento, bloquear alteração comum de itens/preços e deixar ajuste financeiro para fluxo futuro. Essa restrição é proposta, não decisão aprovada.

Corrigir um serviço administrativo não modifica descrição de evolução, autoria clínica, prontuário ou evidência de atendimento. Ações de correção devem respeitar a clínica e evitar concorrência com a confirmação de pagamento. Caso essa proteção e rastreabilidade não caibam na entrega, propor adiamento explícito da correção; não liberar sobrescrita sem histórico para reduzir esforço.

**Fluxo técnico recomendado ao backend:**
1. Administrador abre o encaminhamento da própria clínica; a resposta não inclui texto clínico.
2. Se o pagamento já estiver confirmado, recusar a correção comum e orientar tratamento posterior. Isso não é autorização para desfazer recebimento ou executar estorno.
3. Antes da confirmação de pagamento, apresentar itens atuais e solicitar correção e motivo, preservando a versão lida do encaminhamento.
4. Na gravação, bloquear/recarregar o encaminhamento, reconferir perfil, clínica, situação de pagamento e versão, sem confiar apenas no estado exibido ao abrir a tela.
5. Se o pagamento foi confirmado durante a edição, recusar. Se a versão mudou, informar conflito e pedir revisão sem descartar silenciosamente o texto digitado.
6. Validar itens ou Sem cobrança e recalcular totais no servidor. Não aceitar total arbitrário do cliente.
7. Gravar novos dados, histórico anterior/posterior, motivo, administrador, instante e nova versão em uma transação; falha reverte a correção inteira.
8. Recepção passa a consultar a versão atualizada. Reenvio após resposta perdida recupera o resultado em vez de duplicar a correção.

Confirmação de pagamento e correção devem usar estratégia de bloqueio/versão compatível, para não aceitar pagamento sobre itens que acabaram de mudar. A versão proposta é do encaminhamento administrativo; não reutilizar a versão da evolução clínica para controlar outro registro. A implementação e o contrato HTTP são novos e precisam de detalhamento do backend. Ver fluxo 6 no arquivo complementar.

## 6. Segunda senha e recuperação

### 6.1 Liberação clínica

Manter login JWT existente e acrescentar verificação da segunda senha na API. Rotas que leem ou alteram conteúdo clínico precisam exigir uma liberação curta e verificável, ligada à conta, clínica e sessão definida pelo contrato. Não criar vínculo permanente com pacientes a partir dessa liberação.

Senhas devem ser guardadas por hash, aproveitando a stack existente, sem segredo legível em banco ou logs. Duas senhas não são autenticação de dois fatores nem criptografia do prontuário por paciente.

Definir criação inicial, troca normal, duração, tentativas e eventos de invalidação. Expiração durante edição deve impedir gravação sem autenticação válida, mas permitir que o profissional retome seu trabalho com segurança. Não manter conteúdo visível após perda de autorização; não persistir rascunhos ou segredos em armazenamento de navegador sem desenho explícito de proteção.

### 6.2 Recuperação aprovada em direção funcional

1. Dentista solicita ajuda; administrador autentica-se e verifica solicitante e clínica.
2. Sistema emite credencial temporária exclusiva para recuperação da senha clínica, com validade e uso único.
3. Entrega ocorre por canal a definir; registrar emissão sem gravar segredo em log.
4. Dentista autenticado na conta principal apresenta a credencial e define sua nova senha clínica.
5. Sistema valida finalidade, alvo, prazo e consumo; grava hash, consome a credencial e invalida liberações clínicas anteriores de forma consistente.
6. Dentista desbloqueia a área com a nova senha; acesso continua condicionado ao vínculo.

A credencial temporária não abre prontuários e não serve para login principal. Duas tentativas simultâneas de resgate não podem ter sucesso com a mesma credencial. Senha definitiva não é exibida ao administrador.

Representar no protótipo: recusa da solicitação, outra clínica, falha de entrega, credencial inválida/expirada/consumida, reemissão e falha ao salvar nova senha. Definir se uma reemissão invalida credenciais anteriores; não criar exceção automática para contornar erro.

### 6.3 Paralelismo e proteção de senhas — somente sugestão para estudo

Por orientação expressa de Paulo, esta seção registra apenas uma possibilidade técnica para avaliar posteriormente. Não aprova mudança de parâmetros, implementação nova, benchmark ou compromisso de entrega. Não incluir esse experimento como funcionalidade pronta nem como condição já definida do fluxo de recuperação.

Paulo solicitou avaliar paralelismo para a exigência acadêmica do projeto. A implementação existente usa Passlib com Argon2. Na leitura da biblioteca instalada localmente em 02/11, o handler padrão informou Argon2id, custo de memória 65536 KiB, três passagens e paralelismo 4. Isso não é benchmark nem comprovação da configuração ou do uso de CPU no contêiner.

Argon2 é uma função de hash de senhas; não é criptografia reversível nem criptografia do conteúdo do prontuário. Seu parâmetro de paralelismo define lanes que podem executar concorrentemente. Recomenda-se reutilizar a biblioteca para ambas as senhas, com parâmetros explicitados e medidos, em vez de criar algoritmo criptográfico próprio.

Para demonstrar paralelismo, propor experimento controlado com p=1, p=2 e p=4, mantendo memória e passagens comparáveis e registrando tempo, CPU, memória e limites do contêiner. Não pressupor aceleração, aumento automático de segurança ou atendimento do critério acadêmico apenas pela configuração p=4. Conferir o enunciado para saber se paralelismo interno de biblioteca atende ou se é exigida implementação autoral. Nenhum experimento foi executado nesta revisão.

Referências técnicas: [RFC 9106, parâmetros e lanes](https://www.rfc-editor.org/rfc/rfc9106.html#section-3.1), [escolha de parâmetros do argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/parameters.html) e [interface Argon2 do Passlib](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.argon2.html).

## 7. Estado técnico consultado e lacunas

| Tema | Atual/local | Necessário para o fluxo pretendido |
|---|---|---|
| Login | JWT e Argon2 existentes. | Segunda senha, liberação e recuperação ainda sem contratos implementados. |
| Agenda | Confirmação e conclusão com evidência; care_occurred_at com fuso. | Nova validação de evolução e serviços; encaminhamento transacional. |
| Prontuário | GET pode criar após autorizar; D02 continua aberta. | Não desenhar GET como leitura pura; decidir abertura definitiva. |
| Concorrência | QA-01 reconfere vínculo sob bloqueios; QA-02 local exige version, com 409 para edição desatualizada. | Revisão independente pendente e implantação ainda não demonstrada. Não usar texto desatualizado do README da Agenda para negar a existência do controle local. |
| Frontend atual | Não envia version na edição nem care_occurred_at na conclusão. | Adaptar cliente conforme novos contratos; nesta rodada foi feita revisão, não implementação. |
| Serviços e pagamento | Campo clínico livre; não há itens e pagamento estruturados nos módulos examinados. | Persistência e respostas administrativas próprias. |
| Consultas realizadas | Listagem atual pode filtrar COMPLETED e próprias consultas. | Definir detalhes, indicadores e filtros sem inventar dados ausentes da API. |

Os catálogos locais ainda contêm classificações anteriores à implementação. Esta especificação não os corrige silenciosamente nem declara migrações aplicadas no banco existente.

## 8. Critérios para revisão e futuro aceite

| Tema | Critério ou dependência |
|---|---|
| Conclusão | Sem evolução salva com descrição, ou sem itens/Sem cobrança explícito, a nova operação deve recusar sem concluir parcialmente. |
| Evolução | Pode permanecer DRAFT após concluir; finalizar exige ação separada. Conteúdo e autoria não são preenchidos automaticamente. |
| Liberação | Login ou segunda senha isolados não bastam; vínculo e clínica continuam obrigatórios em chamadas diretas. Prazo e tentativas dependem de definição. |
| Cancelamento/ausência | Retiram preparação quando não existir outra origem válida; preservam histórico e continuidade comprovada. |
| Conflito | Duas edições da mesma versão não sobrescrevem silenciosamente; retorno 409 permite revisão sem descartar texto. |
| Reenvio | Repetição após perda da resposta não duplica encaminhamento, realização ou pagamento. Contrato técnico deve ser fechado antes de teste. |
| Privacidade | Recepção e administrador não recebem texto clínico, senha definitiva ou acesso por recuperação. |
| Pagamento | Atendimento pode continuar com pagamento pendente. Confirmação pela recepção registra quem e quando, sem processar a transação externa; não exigir valor e forma como novos campos do MVP. Regra de confirmação indevida/correção ainda pendente. |
| Recuperação | Uso único inclusive sob concorrência, prazo e finalidade verificados; falha não salva nova senha deixando credencial indevidamente reutilizável. |

Critério definido não significa cenário executado ou aprovado. O parecer de QA separa cenários verificáveis e condicionados a decisão; sua matriz é a fonte de detalhamento para os testes futuros.

## 9. Revisões recebidas, pendências e próximos passos

| Parecer | Contribuição incorporada |
|---|---|
| Backend | Distinguir conclusão atual da nova operação composta; liberação clínica no servidor; persistência administrativa separada; idempotência e estado real de versionamento. |
| Frontend | Separar ações; prever carregamento, vazio, validação, sessão expirada, perda de acesso, conflitos e falhas; paciente externo sem portal. |
| QA | Não exigir pagamento imediato; cobrir erros de desbloqueio, cancelamento, recuperação, concorrência, reenvio e validações ainda pendentes. |

**Decisões ainda com Paulo:** duração e criação inicial da senha/liberação; canal e verificação da recuperação; alcance da confirmação de pagamento e correção indevida; limites da correção administrativa de itens; política de paciente inativo, retificação e legado. Conferir também a exigência acadêmica de paralelismo. As decisões aprovadas constam na seção 2; não reabri-las como pendentes.

**Backend:** detalhar contratos e fronteiras transacionais a partir desta revisão, incluindo implementação futura dos novos pré-requisitos de conclusão. Não inventar rotas como existentes.

**Protótipo:** usar a sequência da seção 4 e o roteiro separado. Identificar atual, novo aprovado e pendente em cada tela.

**QA:** atualizar a matriz com as decisões novas; executar somente em etapa posteriormente autorizada, numa versão identificada. A revisão independente de QA-01/QA-02 foi prevista por Paulo para a próxima sprint.

**Documentação:** quando Paulo fornecer as imagens, conferir aderência ao roteiro, incluir legendas e referências e montar PDF e fonte editável. Se uma imagem apresentar erro ou decisão não aprovada, devolver a divergência antes de tratá-la como fluxo oficial. Pode circular como especificação em refinamento; não como aceite da aplicação.

## 10. Fontes e histórico desta revisão

- [Reunião de 29/10](../relatorios/reunioes/relatorio-parcial-reuniao-2026-10-29.md).
- [Parecer de backend](pareceres-2026-11-02/backend.md), [frontend](pareceres-2026-11-02/frontend.md) e [QA](pareceres-2026-11-02/qa.md), preservados como fontes recebidas.
- [RF-023](../requisitos/RF-023-prontuario-do-paciente.md), [RF-024](../requisitos/RF-024-evolucoes-clinicas.md) e [RN-031](../regras-de-negocio/RN-031-RF-023-acesso-ao-prontuario.md).
- Decisões explícitas de Paulo em 02/11: evolução salva, itens ou Sem cobrança e recuperação temporária de uso único; aprovação anterior de pagamento simples.

Versão 0.1: direção inicial e dois diagramas preliminares. Versão 0.2: incorpora pareceres e decisões; substitui diagramas internos por roteiro separado, para produção posterior das imagens e composição pela documentação. Nenhum parecer foi convertido em resultado de teste.

Versão 0.3: Paulo simplifica o pagamento para confirmação de operação externa e indica administrador para correção de serviços; inclui proposta técnica de estudo do paralelismo interno do Argon2, sem implementação ou benchmark novos. Os limites da correção continuam pendentes.

Versão 0.4: explicita que paralelismo é somente sugestão; detalha correção administrativa com limites ainda propostos e acrescenta o fluxo 6. O pagamento externo atualizado é a referência para substituir versões anteriores do fluxo 5.

## 11. Prontidão documental

**Pronto para a documentação compor o PDF de alinhamento da equipe**, com identificação de propostas e pendências. A fonte funcional, o roteiro, os pareceres e o complemento Mermaid estão disponíveis. Não é especificação integralmente fechada para implementação nem aceite de funcionalidades: duração/liberação da segunda senha, canal de recuperação, significado exato da confirmação e tratamento de erros financeiros, além dos limites propostos de correção, ainda exigem fechamento.

Esta revisão altera somente documentação. Não executa testes, não modifica código, banco ou contêineres e não cria commit ou publicação.
