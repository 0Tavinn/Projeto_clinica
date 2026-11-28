# Caio e Otávio — sessão compartilhada da API de prontuário

## Decisão para esta integração

A Agenda continua com sua API e sessão atuais. Vínculos e Prontuários usam
uma segunda sessão da API `lumina_odonto/`, compartilhada pelos dois módulos.
É uma etapa transitória: não migra Dashboard, cadastros ou Agenda para a nova API.
O usuário pode precisar de um segundo login ao entrar nestes módulos.
Uma sessão só pode ser compartilhada dentro da mesma aplicação/origem;
outra porta/origem de frontend não compartilha sessionStorage automaticamente.

Caio e Otávio devem usar um único cliente de sessão para a API nova.
Não copiar tokens do legado, compartilhar segredos JWT entre APIs ou tentar
usar um token administrativo como clínico. Cada API mantém seu próprio logout.

## Ambiente e contas de demonstração

Na raiz `lumina_odonto/`, preparar a API conforme [INTEGRATION.md](../../INTEGRATION.md).
Para um ambiente já preparado, `python3 scripts/integration.py up` reconstrói a API
sem recriar a configuração ou reaplicar o seed. Não executar setup/seed novamente.
A base padrão local é `http://localhost:18100/api/v1` e o Swagger fica em `/docs`.
O localhost do colega é o computador dele; volumes e contas locais não são transferidos pelo Git.

No seed fictício:

| Perfil | E-mail | Senha de entrada | Senha clínica |
| --- | --- | --- | --- |
| Administrador | admin.demo@example.com | DemoLumina2026! | Não se aplica |
| Dentista | dentista.demo@example.com | DemoLumina2026! | ClinicaDemo2026! |

## Rotas e validade

| Operação | Método e caminho, após a base | Token | Retorno |
| --- | --- | --- | --- |
| Entrar na API nova | POST `/auth/login` | Sem Bearer | 200: access_token, token_type, expires_in |
| Restaurar/conferir sessão | GET `/auth/me` | access_token | 200: id, clinic_id, full_name, email, role, is_active |
| Liberar prontuários | POST `/auth/clinical-unlock` | access_token | 200: clinical_token, token_type, expires_in |
| Bloquear prontuários | POST `/auth/clinical-lock` | access_token do dentista | 204, sem corpo |
| Encerrar sessão da API nova | POST `/auth/logout` | access_token | 204, sem corpo |

Login envia JSON `{"email":"...","password":"..."}`; desbloqueio envia
`{"password":"..."}`. Logout e bloqueio não exigem corpo JSON.
As duas operações novas usam `Authorization: Bearer <access_token>`.

`expires_in` é um inteiro em segundos, contado a partir da emissão:
**1800 para acesso e 900 para liberação clínica**. É um campo adicional;
as chaves de token anteriores permanecem. O JWT/servidor determina a validade,
não o relógio ou o temporizador do navegador. Não existe refresh nesta API.
O prazo do token clínico é independente; o logout invalida ambos antes desses prazos.

## Fluxo que Caio deve integrar

1. Ao abrir Vínculos, conferir a sessão da API nova com GET `/auth/me`.
2. Sem sessão válida, pedir o login específico desta API. Não reutilizar a
   senha/token da Agenda automaticamente nem armazenar senha para reenviar.
3. Conferir ADMINISTRATOR antes de oferecer o painel. As permissões efetivas
   continuam no servidor. Recepção e dentista não gerenciam vínculos.
4. Compartilhar este cliente/estado com o módulo de Otávio; Vínculos não pede
   desbloqueio clínico. Otávio solicita a senha clínica ao acessar prontuários.
5. Usar as operações do [contrato administrativo](administrative-links.md).
6. Ao sair desta API, executar POST `/auth/logout`, limpar seus tokens e dados
   locais e encerrar as telas dos dois módulos. A sessão da Agenda é independente.

Guardar os tokens em chaves próprias, por exemplo `lumina.clinical_api.access_token`
e `lumina.clinical_api.clinical_token`, sem sobrescrever as chaves do legado.
Não gravar senhas, tokens ou respostas clínicas em logs/telemetria. Preferir
sessionStorage/estado de sessão ao armazenamento persistente em localStorage.
Na troca de conta/clínica ou logout, invalidar listas/cache e requisições pendentes;
ignorar respostas iniciadas na sessão anterior que cheguem depois da troca.

## Sair, bloquear e falhar são situações diferentes

POST `/auth/logout` incrementa a versão de sessão **da conta nesta API**.
Invalida todos os tokens de acesso e clínicos já emitidos para ela, inclusive
em outras abas/dispositivos; não representa logout apenas de um token.
Não altera outra conta, vínculo, prontuário ou sessão da API legada.
Novo login válido emite tokens na versão atual.

POST `/auth/clinical-lock` é exclusivo do dentista e invalida todas as suas
liberações clínicas anteriores nesta API, preservando o login de acesso.
Remover imediatamente conteúdo clínico/cache da interface. Para voltar,
usar `/auth/clinical-unlock` com uma sessão de acesso ainda válida.
Nenhuma dessas operações altera senha ou revoga vínculo de paciente.

| Situação | Ação do cliente |
| --- | --- |
| 401 em rota de acesso | Limpar sessão nova e conteúdo dos módulos; solicitar novo login. |
| 401 em rota clínica | Remover conteúdo; conferir `/auth/me` com access_token. Se válido, pedir desbloqueio; se inválido, novo login. |
| 403 no painel/prontuário | Tratar perfil/vínculo negado e retirar dados negados; não repetir escrita. |
| 409 em operação de vínculo | Recarregar contexto e pedir decisão; não substituir a ação automaticamente. |
| Logout repetido com token revogado | 401; manter estado local encerrado. |
| Rede/500 durante logout | Limpar estado local; informar que a revogação no servidor não foi confirmada. Não anunciar confirmação inexistente. |
| 204 | Não chamar response.json(); o corpo é vazio. |

A revogação e a auditoria são atômicas. Se uma requisição antiga aguardar lock
e um reset/logout alterar as versões, ela pode receber 401 ao sair da espera.
Nesse caso, limpar o estado correspondente e conferir a sessão atual;
não reenviar automaticamente a operação com outro token.

## Limites desta entrega e teste

Esta entrega prepara o backend/contrato. Caio ainda implementa o cliente e
a interface; Otávio utiliza a mesma sessão. Não há SSO entre as duas APIs.
Pesquisa administrativa, contagens, projeção mínima do seletor e a divergência
da senha clínica obrigatória no cadastro continuam itens de manutenção separados.
Não foram alteradas regras de concessão/revogação ou o esquema PostgreSQL.

Executar o teste reproduzível, da raiz `lumina_odonto/`:

```bash
python3 scripts/verify_sessions.py --output ../.local/session-qa
```

O runner cria recursos Docker exclusivos, esquema novo e seed fictício;
exercita a suíte, HTTP real, reinício e remove somente seus próprios recursos.
Nunca executa migração, seed ou teste de escrita no banco da equipe.
O resultado técnico não substitui o aceite da interface no navegador.
