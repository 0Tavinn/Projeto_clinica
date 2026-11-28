# Agenda - rotas e referências de integração

Este módulo pertence à API legada de `backend/`. A entrega de prontuário
desta branch executa `lumina_odonto/`, com contratos diferentes.

## Rotas da Agenda em backend/

A aplicação monta o prefixo `/api/v1`; o roteador deste módulo usa
`/appointments`.

| Método e rota | Finalidade |
| --- | --- |
| POST `/api/v1/appointments` | Criar agendamento. |
| GET `/api/v1/appointments` | Listar consultas com os filtros definidos no roteador. |
| GET `/api/v1/appointments/{appointment_id}` | Consultar detalhes. |
| PATCH `/api/v1/appointments/{appointment_id}` | Editar consulta conforme permissões do serviço. |
| PATCH `/api/v1/appointments/{appointment_id}/status` | Alterar a situação conforme as regras do serviço. |
| POST `/api/v1/appointments/{appointment_id}/cancel` | Cancelar consulta. |

Fonte estática: [router.py](router.py), [schemas.py](schemas.py) e
[service.py](service.py). Esta tabela identifica operações existentes;
não declara novo teste, aprovação de regra ou aceite da interface.

## Entrega separada da Agenda e OpenCL

Referência publicada conferida em 26/11/2026:
`c3a83b656b8df2396b4ec8944d644abe6aaf77fd`,
branch `feat/paralelismo-agendamento`.

- [Branch da Agenda](https://github.com/0Tavinn/Projeto_clinica/tree/feat/paralelismo-agendamento).
- [Guia do ambiente nessa referência](https://github.com/0Tavinn/Projeto_clinica/blob/c3a83b656b8df2396b4ec8944d644abe6aaf77fd/docs/ambiente-desenvolvimento.md).
- [Paralelismo de agendamento e limites](https://github.com/0Tavinn/Projeto_clinica/blob/c3a83b656b8df2396b4ec8944d644abe6aaf77fd/docs/paralelismo-agendamento.md).
- [Revalidação focada do menu e suas ressalvas](https://github.com/0Tavinn/Projeto_clinica/blob/c3a83b656b8df2396b4ec8944d644abe6aaf77fd/docs/relatorios/qa/2026-11-26-1a2ec6c-nav04-revalidacao/relatorio.md).

Nessa entrega, `sequential` é o padrão e OpenCL em CPU é opcional para
demonstração educativa. Não foi demonstrado ganho consistente de desempenho.
Esses arquivos e resultados pertencem à referência acima; não se presume
que estejam incorporados a esta branch de prontuário.

## Prontuários e vínculos - outra API

- [Índice de rotas para Otávio e Caio](../../../lumina_odonto/docs/frontend/README.md).
- [Contrato administrativo de vínculos](../../../lumina_odonto/docs/frontend/administrative-links.md).
- [Ambiente de integração do prontuário](../../../lumina_odonto/INTEGRATION.md).

A API de `lumina_odonto/` usa login JSON e cancelamento por DELETE, além
de permissões, filtros e retornos distintos. O login da API legada usa
formulário OAuth, e o cancelamento acima usa POST. Não misturar contratos
nem duplicar `/api/v1` ao configurar a base HTTP.

`localhost` identifica o computador que executa cada serviço. A publicação
de uma branch não transfere volumes, configurações privadas ou o ambiente
local de Paulo. A integração das duas APIs e a interface clínica continuam
dependendo de uma candidata identificada e de validação própria.

Nenhuma operação de banco, Docker ou aplicação é executada por este README.
