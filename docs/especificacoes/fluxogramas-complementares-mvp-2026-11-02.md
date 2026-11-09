# Lumina Odonto — Fluxogramas complementares em Mermaid

**Data:** 02/11/2026. **Versão documental:** 0.4.\
**Fonte:** [especificação funcional](fluxo-atendimento-mvp-2026-11-02.md).

Cole cada bloco separadamente no Mermaid. O fluxo 5 abaixo substitui o anterior com valor recebido e forma de pagamento. O fluxo 6 é adicional: administrador é o responsável indicado, mas os limites de correção ainda são proposta técnica. Os desenhos não comprovam implementação ou teste.

## 5. Pagamento externo e confirmação pela recepção

```mermaid
flowchart TD
    A["Recepção abre o encaminhamento administrativo"] --> B{"Perfil e clínica permitem acesso?"}
    B -->|Não| C["Negar sem expor dados de outra clínica"]
    B -->|Sim| D["Exibir consulta, paciente, profissional, itens e total"]
    D --> E{"Atendimento sem cobrança?"}
    E -->|Sim| F["Identificar Sem cobrança sem criar recebimento fictício"]
    E -->|Não| G{"Pagamento externo foi recebido e verificado?"}
    G -->|Não| H["Manter pendente sem desfazer atendimento concluído"]
    G -->|Sim| I["Recepção solicita Confirmar pagamento"]
    I --> J["Sistema reconfere clínica, encaminhamento e situação atual"]
    J --> K{"Confirmação válida?"}
    K -->|Não| L["Informar impedimento sem marcar pago"]
    K -->|Já confirmada| M["Recuperar registro existente sem duplicar"]
    K -->|Sim| N["Gravar confirmação, responsável e instante"]
    N --> O{"Gravação confirmada?"}
    O -->|Sim| P["Exibir pagamento confirmado"]
    O -->|Falha confirmada| Q["Informar falha sem afirmar sucesso"]
    O -->|Resposta perdida| R["Consultar resultado persistido antes de repetir"]
    D -.-> S["Não exibir evolução ou anotações clínicas"]
    I -.-> T["Pagamento ocorre fora do sistema: sem integração com maquineta ou novos campos obrigatórios de valor e forma"]
    K -.-> U["PENDENTE: quitação integral e correção de confirmação indevida"]
```

## 6. Correção administrativa de serviços — limites propostos

```mermaid
flowchart TD
    A["Administrador abre encaminhamento da própria clínica"] --> B{"Perfil e clínica válidos?"}
    B -->|Não| C["Negar a operação"]
    B -->|Sim| D["Carregar itens, total e versão do encaminhamento"]
    D --> E{"Pagamento já confirmado?"}
    E -->|Sim| F["PROPOSTA: bloquear correção comum e deixar ajuste financeiro para fluxo futuro"]
    E -->|Não| G["Administrador corrige itens ou Sem cobrança e informa motivo"]
    G --> H["Enviar correção com a versão lida"]
    H --> I["Sistema bloqueia e recarrega o encaminhamento"]
    I --> J["Reconferir autorização, clínica e situação de pagamento"]
    J --> K{"Correção continua permitida?"}
    K -->|Não| C
    K -->|Sim| L{"Versão continua atual?"}
    L -->|Não| M["Informar conflito e pedir revisão sem sobrescrita silenciosa"]
    L -->|Sim| N["Validar itens e motivo e recalcular total no servidor"]
    N --> O{"Dados válidos?"}
    O -->|Não| P["Informar validação sem gravar"]
    O -->|Sim| Q["Gravar correção e histórico anterior e posterior, motivo, administrador, instante e nova versão"]
    Q --> R{"Gravação confirmada?"}
    R -->|Sim| S["Recepção consulta encaminhamento atualizado"]
    R -->|Falha confirmada| T["Reverter a correção inteira e informar falha"]
    R -->|Resposta perdida| U["Recuperar resultado antes de repetir"]
    S -.-> V["Não alterar evolução, autoria clínica ou prontuário"]
    I -.-> W["Confirmação de pagamento e correção devem usar controle concorrente compatível"]
    A -.-> X["PROPOSTA TÉCNICA: limites ainda a fechar; não é operação já implementada"]
```

**Para o backend:** a correção, seu histórico e a atualização da versão devem ter a mesma fronteira transacional. Pagamento confirmado durante a edição deve ser percebido na gravação. A versão é do encaminhamento administrativo, não da evolução. Erros não incluem conteúdo clínico. Detalhar rotas e códigos antes de implementar; não tratá-los como contratos atuais.

**Para a documentação:** substituir o fluxo financeiro anterior, manter os rótulos de proposta e pendência e identificar a versão no PDF. Argon2/paralelismo permanece somente sugestão para avaliar possibilidade de implementação, sem promessa de entrega ou resultado medido.
