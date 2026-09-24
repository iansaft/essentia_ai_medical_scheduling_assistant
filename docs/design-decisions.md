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

**Decisão:** a aplicação FastAPI é criada por `create_app(settings)`. Configuração, pool de conexões PostgreSQL e cliente Redis do cache de disponibilidade pertencem à instância da aplicação; ambos são criados e encerrados pelo lifespan e disponibilizados através de `app.state` (`db_pool`, `availability_cache`).

**Motivo:** tornar explícito o ownership da infraestrutura, eliminar dependência de estado global/import-time e permitir que cada instância da aplicação opere com configuração própria.

**Trade-off:** o processo precisa iniciar o Uvicorn em factory mode (`--factory`), mas em troca a aplicação ganha isolamento e testabilidade sem monkey patching de singletons globais.

## DD-17 — Camada web sem regras de domínio

**Decisão:** a SPA em `apps/web` é apenas apresentação e integração: conversa via n8n, leituras determinísticas via FastAPI, sem mutações de agendamento a partir da UI.

**Motivo:** preservar o boundary determinístico (API + PostgreSQL) e evitar duplicar regras de disponibilidade/preço no browser.

**Detalhes e trade-offs do MVP** (request/response síncrono, UUID como `sessionId`, re-fetch como reconciliação): [`web-application.md`](./web-application.md) — WEB-DD-01…10.

## DD-18 — Identidade de paciente via header `X-Patient-Id` (sem autenticação)

**Decisão:** rotas patient-scoped (`GET/POST /v1/appointments*`, `GET /v1/patients/{id}`, `GET /v1/patients/{id}/appointments`) exigem o header `X-Patient-Id`; o servidor compara o header com o dono do recurso (path, `patient_id` do body ou `patient_id` do appointment carregado). Mismatch retorna `403`. `GET /v1/patients`, catálogo, availability e health permanecem sem o header.

**Motivo:** impedir que um paciente leia ou cancele dados de outro sem implementar autenticação completa (fora de escopo no MVP). A comparação no app layer é uma decisão prática de demo; o DB ainda garante integridade referencial, mas não enforce ownership (fase futura opcional: predicado `patient_id` nas queries sqlc).

**Trade-off:** o header é apenas uma asserção de identidade (qualquer cliente pode enviá-lo) — não é prova criptográfica. Com autenticação real no futuro, o mesmo `Depends` passaria a ler o subject do token. Inclui `caller_patient_id` no request hash de cancelamento para evitar replay cross-paciente da mesma `Idempotency-Key`.

## DD-19 — Erros HTTP em RFC 7807 (`application/problem+json`) e logs estruturados com correlation ID

**Decisão:** erros de domínio e falhas não tratadas são respondidos no formato RFC 7807:

```json
{
  "type": "/problems/slot-unavailable",
  "title": "Conflict",
  "status": 409,
  "detail": "Appointment slot is already booked.",
  "instance": "/v1/appointments"
}
```

A hierarchy de exceções vive em `core/errors.py` (`AppError` → `NotFoundError`/`ConflictError`/`ForbiddenError`/`InternalError` + exceções de domínio com `type` próprio). Handlers globais em `register_exception_handlers` serializam `AppError` e qualquer `Exception` não tratada (500 genérico, sem vazar stacktrace).

Logs usam **structlog** em stdout: JSON em produção (`API_LOG_JSON=true`), console legível em dev/test. Middleware `CorrelationIdMiddleware` aceita/gera `X-Correlation-ID`, bind em contextvars (structlog) e ecoa o header na resposta.

**Exceções deliberadamente fora do envelope problem+json:**

- `422` de validação FastAPI/Pydantic — mantém o shape nativo `{"detail": [...]}` (compatibilidade e contratos já congelados);
- `503` do `GET /health/n8n` — mantém `{"detail": {"status": "error"}}` (health check de infraestrutura).

**Motivo:** um envelope único padroniza clientes (n8n, SPA, testes), remove `try/except` de tradução nas rotas, e o correlation ID amarra request → log → fluxo n8n sem depender de stacktrace em resposta.

## DD-20 — Cache-aside de disponibilidade em Redis (fail-open, não autoritativo)

**Decisão:** `GET /v1/availability` é servido por cache-aside em Redis com chave versionada `availability:v1:{service_id|all}:{doctor_id|all}:{date|all}`, TTL base de 30s + jitter aleatório de 0–10s (`AVAILABILITY_CACHE_TTL_SECONDS` / `AVAILABILITY_CACHE_TTL_JITTER_SECONDS`) e kill-switch `AVAILABILITY_CACHE_ENABLED`. Booking e cancelamento invalidam o cross product de 8 chaves **somente após o `POSTGRESQL COMMIT`**. Falhas de `get`/`set`/`delete` no Redis são fail-open: caem para o caminho PostgreSQL e apenas logam (`availability_cache_read_error` / `write_error` / `invalidation_error`).

**Motivo:** disponibilidade é a leitura mais consultada do sistema e é derivada (DD-04), portanto descartável; TTL curto + invalidação pós-commit reduzem carga no PostgreSQL sem introduzir uma segunda fonte de verdade. O Redis **nunca** autoriza booking — double booking continua garantido pelo lock `FOR UPDATE` (DD-09) e pela unique constraint parcial (DD-03).

**Trade-off:** leituras podem ficar até ~30–40s stale quando a invalidação falha (ou entre commit e `DEL` concorrente); sem single-flight, cold start sob carga extrema ainda pode gerar thundering herd ao PostgreSQL (mitigado por TTL+jitter, coalescing é follow-up). Em contrapartida, indisponibilidade do Redis nunca derruba leituras nem desfaz escritas confirmadas.
