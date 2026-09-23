# Decisões de Design e Trade-offs

Este documento registra as principais decisões para evitar que o racional arquitetural fique apenas implícito no código.

## DD-01 — FastAPI como boundary determinístico

**Decisão:** regras de agenda ficam em uma API Python/FastAPI, separadas do n8n e do LLM.

**Motivo:** booking, cancellation, preço e disponibilidade exigem comportamento determinístico, testável e transacional.

**Trade-off:** adiciona um serviço próprio além do workflow, mas reduz fortemente o acoplamento entre regras críticas e automação visual.

## DD-02 — n8n como orquestrador, não como domínio

**Decisão:** n8n coordena canal, Agent, STT/TTS, Gmail e retries.

**Motivo:** workflows são adequados para integrações e etapas externas, mas não são a melhor fonte de verdade para invariantes transacionais complexas.

## DD-03 — PostgreSQL como última linha de defesa

**Decisão:** invariantes críticas são repetidas no banco através de FK, exclusion constraint e unique index parcial.

**Motivo:** validações de aplicação isoladas não eliminam condições de corrida.

## DD-04 — Disponibilidade derivada

**Decisão:** não existe `slot.status = booked`.

**Motivo:** manter ocupação simultaneamente em slot e appointment criaria duas fontes de verdade que poderiam divergir.

**Modelo:** `open slot` + ausência de `scheduled appointment` = disponível.

## DD-05 — Slot referencia médico e serviço

**Decisão:** o slot contém `doctor_id` e `service_id`, com FK composta para `doctor_services`.

**Motivo:** a agenda precisa saber exatamente qual oferta pode ocupar aquele intervalo, e o banco deve rejeitar combinações não permitidas.

## DD-06 — Appointment referencia slot, não duplica catálogo

**Decisão:** médico e serviço são obtidos através do slot; não são duplicados como FKs no appointment.

**Motivo:** evita inconsistência como appointment apontar para um médico diferente do slot reservado.

A exceção deliberada é o snapshot financeiro (`price_amount` e `currency`).

## DD-07 — Snapshot de preço

**Decisão:** appointment persiste o preço efetivamente utilizado na reserva.

**Motivo:** preço de catálogo é mutável; histórico financeiro não deve ser retroativamente alterado.

## DD-08 — Cancelamento como mudança de estado

**Decisão:** appointments não são apagados ao cancelar.

**Motivo:** preservação histórica, auditabilidade e possibilidade de analisar comportamento operacional.

## DD-09 — Lock pessimista durante booking

**Decisão:** carregar o slot com `FOR UPDATE` dentro da transação de booking.

**Motivo:** serializar tentativas concorrentes sobre o mesmo slot e reduzir disputa antes do INSERT.

A unique constraint parcial continua necessária como garantia final.

## DD-10 — Idempotência na API

**Decisão:** comandos mutáveis devem aceitar `Idempotency-Key`.

**Motivo:** n8n e integrações externas trabalham naturalmente com retry e entrega potencialmente repetida.

A API deve suportar semantics de at-least-once sem duplicar efeitos.

## DD-11 — SQL explícito + sqlc em vez de ORM

**Decisão:** queries são escritas explicitamente e o acesso Python é gerado pelo sqlc.

**Motivo:** maior controle sobre locking, constraints, SQL de disponibilidade e comportamento do PostgreSQL, mantendo tipos no código de aplicação.

**Trade-off:** o desenvolvedor precisa entender a API gerada e lidar com detalhes como aliases Python (`id_`) e parâmetros keyword-only.

## DD-12 — golang-migrate como owner de schema

**Decisão:** migrations e seeds são gerenciadas por `golang-migrate`; sqlc não altera schema.

**Motivo:** ownership único evita drift e deixa a evolução do banco explícita e reversível.

## DD-13 — OpenAPI como fonte da documentação HTTP

**Decisão:** FastAPI gera OpenAPI, e Postman importa essa especificação.

**Motivo:** elimina manutenção duplicada de endpoints, parâmetros e schemas em coleção manual.

Examples de IDs conhecidos podem ser declarados com `Path`/`Query` para melhorar Swagger e Postman.

## DD-14 — Timezone de negócio explícita

**Decisão:** `America/Sao_Paulo` é utilizada quando um instante precisa ser interpretado como data civil da operação.

**Motivo:** evita comportamento implícito dependente da timezone do container, host ou conexão.

## DD-15 — RAG fora do core transacional

**Decisão:** informações como agenda, preço e appointment não são servidas por vector search/RAG.

**Motivo:** respostas transacionais exigem leitura atual e determinística.

pgvector pode ser adicionado posteriormente para FAQ ou conhecimento textual sem substituir consultas relacionais.

## DD-16 — Application Factory e infraestrutura por instância

**Decisão:** a aplicação FastAPI é criada por `create_app(settings)`. Configuração e pool de conexões pertencem à instância da aplicação; o pool é criado e encerrado pelo lifespan e disponibilizado através de `app.state`.

**Motivo:** tornar explícito o ownership da infraestrutura, eliminar dependência de estado global/import-time e permitir que cada instância da aplicação opere com configuração própria.

**Trade-off:** o processo precisa iniciar o Uvicorn em factory mode (`--factory`), mas em troca a aplicação ganha isolamento e testabilidade sem monkey patching de singletons globais.

## DD-17 — Camada web sem regras de domínio

**Decisão:** a SPA em `apps/web` é apenas apresentação e integração: conversa via n8n, leituras determinísticas via FastAPI, sem mutações de agendamento a partir da UI.

**Motivo:** preservar o boundary determinístico (API + PostgreSQL) e evitar duplicar regras de disponibilidade/preço no browser.

**Detalhes e trade-offs do MVP** (request/response síncrono, UUID como `sessionId`, re-fetch como reconciliação): [`web-application.md`](./web-application.md) — WEB-DD-01…10.
