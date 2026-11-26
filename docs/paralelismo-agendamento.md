# Paralelismo educativo na Agenda com OpenCL

O motor compara os intervalos já filtrados pelo repositório com o intervalo
solicitado. Cada work-item OpenCL compara um agendamento existente. O host
reduz as flags individuais com any. O intervalo é semiaberto: 09:00–09:30
não conflita com 09:30–10:00.

## Organização

- `backend/app/appointments/conflict_detection.py` normaliza datas, fornece
  referência sequencial, divide lotes e seleciona o motor com fallback.
- `backend/app/appointments/opencl_conflicts.py` inicializa PyOpenCL em CPU
  sob demanda e reutiliza contexto/programa. Cada chamada possui fila,
  kernel e buffers próprios, protegendo chamadas concorrentes.
- `backend/app/appointments/kernels/check_overlap.cl` compara um intervalo
  por work-item sem uma flag global compartilhada.
- `backend/app/appointments/repository.py` mantém filtros de clínica,
  dentista, situação e exclusão do próprio ID. Fecha o cursor mesmo quando
  um conflito encerra a leitura antecipadamente.

Datas sem fuso conservam a interpretação UTC usada pela Agenda.
A conversão usa inteiros de microssegundos, sem timestamp em ponto
flutuante. O fim é calculado por timedelta antes da conversão.

## Configuração e execução

APPOINTMENT_CONFLICT_ENGINE=sequential é o padrão cotidiano, inclusive
quando a opção está ausente. Auto habilita explicitamente OpenCL CPU e usa
a referência sequencial se biblioteca, plataforma, dispositivo, compilação
ou execução falhar. Uma configuração explícita existente é respeitada.
`APPOINTMENT_CONFLICT_BATCH_SIZE` aceita de 1 a 65536, com padrão 4096.
O lote que falha é comparado novamente sequencialmente. Lotes posteriores
também são processados, sem descartar candidatos.

O Dockerfile inclui PoCL e o carregador ICD para execução em CPU, sem
depender de GPU. NumPy 2.2.6 e PyOpenCL 2025.2.7 suportam Python 3.11/3.12.
O kernel acompanha o pacote instalado. O Compose e o template da raiz
expõem as duas configurações. Reconstruir uma imagem só terá efeito no
serviço quando a implantação for autorizada e realizada.

Não há mudança de rotas, schemas HTTP, autorização ou respostas.
O service continua normalizando para UTC, validando futuro/duração e
adquirindo o advisory lock transacional da dupla clínica/dentista.
A exclusão GiST PostgreSQL continua impedindo reservas sobrepostas na
persistência, inclusive se a prevenção em memória for contornada.

## Verificação reproduzível

No checkout correto, com Docker disponível, executar:

```bash
cd /home/paulinho/Work/Projeto_clinica_clinical_2fa
bash backend/tests/run_opencl_qa.sh
```

O runner constrói imagens de QA, rede, contêiner PostgreSQL 16 e volume
exclusivos, com nomes aleatórios e rótulos de propriedade. Aplica o schema
PR18 somente ao banco novo. Não publica portas nem usa o Compose diário.
A limpeza remove apenas recursos com o rótulo exclusivo da execução.
Os logs ficam em `docs/relatorios/opencl-<identificador>/`.

O runner fornece APPOINTMENT_CONFLICT_ENGINE=auto explicitamente ao
contêiner dirigido. Assim, o comando acima é também a demonstração isolada
com OpenCL, sem editar o .env diário. A suíte completa usa o novo padrão
sequencial e seus testes de kernel selecionam auto explicitamente.

A execução dirigida exige OpenCL real: `LUMINA_REQUIRE_OPENCL=1` transforma
a ausência do runtime em falha, em vez de aceitar fallback como prova.
A suíte completa separa testes PostgreSQL sem destino configurado por skip.
O ensaio de corrida usa TestClient e sessões SQL independentes e observa
espera real em pg_stat_activity. Também contorna a prevenção apenas na
sondagem para conferir a exclusão GiST e rollback.

`backend/scripts/benchmark_conflicts.py` mede inicialização separada,
tempo completo de comparação (incluindo preparo, cópias e redução) e
tempo dos kernels por profiling. Usa dados fictícios, exclui SQL/HTTP/rede
e não demonstra aceleração da aplicação. Metadados internos indicam
`sequential`, `opencl` ou `mixed`, sem expor conteúdo de pacientes.
Lista vazia não lança kernel. O cache do driver pode reduzir recompilações
entre processos.

Os testes e medidas efetivamente executados constam no relatório da tarefa.
Decisões clínicas, migrações e funcionalidades de outros módulos seguem
seus próprios contratos.

## Motivo do padrão cotidiano

As medições HTTP e do comparador não demonstraram ganho consistente com
OpenCL CPU. No diagnóstico HTTP, a primeira utilização não vazia em processo
novo levou aproximadamente 1,44–1,78 s em auto. Sequential evita essa
inicialização no agendamento cotidiano. O relatório de performance registra
amostras, dispersão e limites; os resultados históricos continuam referentes
ao snapshot anterior ao ajuste de default.

O Compose usa o padrão sequential quando a opção está ausente ou vazia.
O setup_dev gera APPOINTMENT_CONFLICT_ENGINE=sequential apenas para um .env
novo. O helper preserva .env existente e carrega seus valores com precedência
sobre variáveis do shell. Para demonstrar OpenCL sem alterar esse ambiente,
use o runner isolado acima. Em um ambiente separado já preparado por Compose,
a variável explícita auto é encaminhada à API, conforme o Compose renderizado.
A mudança do código local não implanta nem reinicia serviços existentes.
