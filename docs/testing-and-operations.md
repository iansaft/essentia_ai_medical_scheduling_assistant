# Testes, Observabilidade e Operação

## 1. Estratégia de testes

A arquitetura foi desenhada para que o domínio possa ser validado independentemente do Agent.

A suíte automatizada utiliza `pytest` e executa testes de integração contra instâncias descartáveis de PostgreSQL 18.4 e Redis 8.10 criadas com Testcontainers. Isso permite validar comportamento específico do PostgreSQL (transações, `FOR UPDATE`, exclusion constraints, unique indexes parciais e concorrência real) e do cache de disponibilidade (HIT/MISS, expiração, invalidação e fail-open) contra um Redis real. Há também uma camada de testes unitários (`tests/unit/`) para a lógica de cache com clientes mockados.

A camada web possui suíte própria de testes unitários com `vitest` e React Testing Library, executada de forma independente (ver `make web-test`).

Estado atual da suíte da API:

```text
132 tests passed
94.47% total coverage
minimum required coverage: 85%
```

### Camada de API

Cobertura inclui:

- health check de processo (`GET /health`);
- health check de readiness do n8n (`GET /health/n8n`): `200` quando pronto, `503` quando indisponível, uso da base URL configurada;
- CORS: origem permitida recebe headers, origem negada não recebe, preflight `OPTIONS`;
- paciente existente retorna `200`;
- paciente inexistente retorna `404`;
- listagem de pacientes (ativos e inativos);
- histórico de agendamentos do paciente (todos os status, `starts_at DESC`);
- histórico de paciente inexistente retorna `404`;
- histórico vazio retorna `[]`;
- serviço existente/inexistente;
- métodos de pagamento por serviço;
- disponibilidade sem filtros;
- disponibilidade filtrada por médico;
- disponibilidade filtrada por serviço;
- disponibilidade filtrada por data;
- slot bloqueado não aparece;
- slot com appointment `scheduled` não aparece;
- slot com appointment cancelado pode voltar a aparecer quando ainda está aberto/futuro.

### Cache de disponibilidade

Cobertura unitária (`tests/unit/test_availability_cache.py`) e de integração (`tests/integration/test_availability_cache.py`, com Redis real via Testcontainers):

- formato e determinismo das chaves `availability:v1:{service|all}:{doctor|all}:{date|all}`;
- serialização/deserialização do payload (incluindo lista vazia);
- MISS popula a chave com TTL dentro da janela base + jitter; HIT serve sem consultar o PostgreSQL;
- expiração da chave volta a consultar o PostgreSQL e repopula;
- invalidação pós-commit no booking e no cancelamento (cross product de 8 keys);
- booking rejeitado (ex.: `409`) não invalida a chave;
- fail-open: outage total do Redis e falhas de `set`/`delete` não quebram a leitura/escrita (PostgreSQL continua servindo);
- flag `AVAILABILITY_CACHE_ENABLED=false` ignora o Redis por completo;
- reset autouse da namespace `availability:*` entre testes.

### Booking

Cobertura inclui:

- happy path;
- paciente inativo;
- slot inexistente;
- slot bloqueado/fechado;
- slot passado;
- médico ou serviço inativo;
- double booking;
- concorrência entre duas tentativas para o mesmo slot;
- replay com a mesma `Idempotency-Key`;
- reutilização indevida da chave com payload diferente;
- preservação do snapshot de preço.

### Cancellation

Cobertura inclui:

- cancelamento de `scheduled`;
- tentativa de cancelar appointment já cancelado;
- tentativa de cancelar `completed`/`no_show`;
- preservação do histórico;
- idempotência do comando;
- liberação de slot futuro após cancelamento quando aplicável.

Também são validados o contrato OpenAPI, invariantes diretamente no banco de dados e o cache de disponibilidade (unit + integração com Redis real).

### Camada web

Cobertura dos testes unitários (Vitest) em `apps/web`:

- formatação de datas/valores e schemas Zod;
- serviços HTTP (pacientes, agendamentos, health) com mock de `fetch`;
- componentes de chat (bolha de mensagem, composer, player de áudio, markdown);
- header e status de conexão (online/offline).

Execução: `make web-test` (ou `make web-check` para typecheck + testes).

## 2. Dados de demonstração úteis

### Paciente

```text
Maria Silva
3cdf666b-186d-44e6-bce9-5e572e7038f9
```

### Médico + serviço coerentes

```text
Dr. Helena Costa
0dfc6223-6a11-4d90-a979-bd511bc1d6a9

Cardiology Initial Consultation
e2fb5edd-efbd-4d60-9de3-d6650e31562f
```

Esses IDs formam um cenário consistente de teste de disponibilidade.

## 3. Requests principais

```http
GET /health
GET /health/n8n

GET /v1/patients
GET /v1/patients/{patient_id}
GET /v1/patients/{patient_id}/appointments

GET /v1/services

GET /v1/services/{service_id}

GET /v1/services/{service_id}/payment-methods

GET /v1/availability
GET /v1/availability?doctor_id={doctor_id}
GET /v1/availability?service_id={service_id}
GET /v1/availability?doctor_id={doctor_id}&service_id={service_id}

GET /v1/appointments/{appointment_id}
POST /v1/appointments
POST /v1/appointments/{appointment_id}/cancel
```

Datas dos slots de seed são relativas a `CURRENT_DATE`; por isso, testes permanentes não devem depender de uma data hard-coded antiga.

## 4. OpenAPI e Postman

FastAPI disponibiliza:

```text
/docs
/openapi.json
```

A coleção Postman deve ser gerada/importada a partir de `/openapi.json`.

Parâmetros `Path` e `Query` podem declarar exemplos usando IDs das seeds para fornecer requests imediatamente utilizáveis ao avaliador.

Variável recomendada no Postman:

```text
baseUrl=http://localhost:8000
```

## 5. Health check

### Liveness do processo HTTP

```http
GET /health
```

Resposta esperada:

```json
{
  "status": "ok"
}
```

Valida apenas a disponibilidade do processo HTTP.

### Readiness do n8n

```http
GET /health/n8n
```

Sonda `GET {API_N8N_BASE_URL}/healthz/readiness` com timeout de 2s:

- `200` → `{"status":"ok"}` quando o n8n responde `2xx`;
- `503` → `{"detail":{"status":"error"}}` quando o n8n está inacessível ou não está pronto.

Dentro do Docker Compose a API usa `API_N8N_BASE_URL=http://n8n:5678`; em desenvolvimento local, a variável do `.env` (`http://localhost:5678`) aponta para o host.

## 6. Observabilidade e logs

Logs são emitidos via **structlog** em stdout:

- `API_LOG_JSON=true` (default / produção) → JSON lines (timestamp, level, event, campos de contexto);
- `API_LOG_JSON=false` (dev/test) → console legível;
- `API_LOG_LEVEL` controla o nível mínimo (`INFO` default).

Todo request passa pelo middleware `CorrelationIdMiddleware`:

- lê `X-Correlation-ID` de entrada ou gera um UUID;
- bind em contextvars do structlog (correlaciona todos os logs do request);
- ecoa o header na resposta.

Campos esperados em logs de request/erro:

- timestamp, level, event;
- `correlation_id`, `method`, `path`;
- para erros de domínio: `status`, `error_type`, `detail`;
- para falhas não tratadas: stacktrace via `logger.exception`.

O n8n deve propagar um identificador como `X-Correlation-ID` para permitir rastrear:

```text
mensagem -> workflow -> Agent -> API -> PostgreSQL -> integração externa
```

## 7. Tratamento de erro HTTP

Semântica utilizada:

- `200 OK` — leitura bem-sucedida;
- `201 Created` — appointment criado;
- `403 Forbidden` — `X-Patient-Id` não corresponde ao dono do recurso patient-scoped;
- `404 Not Found` — recurso não encontrado;
- `409 Conflict` — conflito de estado/concorrência, como double booking ou reutilização inválida de chave de idempotência;
- `422 Unprocessable Entity` — validação de parâmetros/body/headers pelo FastAPI/Pydantic (inclui `X-Patient-Id` e `Idempotency-Key` ausentes);
- `503 Service Unavailable` — dependência externa indisponível (readiness do n8n em `GET /health/n8n`);
- `500 Internal Server Error` — falha não tratada, que deve ser observável em logs e não usada para regras esperadas de domínio.

### Formato de resposta de erro (RFC 7807)

**403 / 404 / 409 / 500 de domínio e não tratados** usam `Content-Type: application/problem+json` (DD-19):

```json
{
  "type": "/problems/slot-unavailable",
  "title": "Conflict",
  "status": 409,
  "detail": "Appointment slot is already booked.",
  "instance": "/v1/appointments"
}
```

- `type` — URI relativa estável do problema (ex.: `/problems/patient-access-denied`);
- `title` — resumo HTTP do status (`Conflict`, `Not Found`, …);
- `detail` — mensagem legível para o cliente final (inglês);
- `instance` — path da requisição;
- `500` não tratado usa `/problems/internal-error` e `detail` genérico (`An unexpected error occurred.`) — stacktraces ficam apenas nos logs.

**Exceções com shape preservado:**

- `422` → shape FastAPI/Pydantic nativo `{"detail": [...]}` (não é problem+json);
- `503` de `GET /health/n8n` → `{"detail":{"status":"error"}}`.

### Header `X-Correlation-ID`

Presente em **todas** as respostas (sucesso e erro): ecoa o valor enviado pelo cliente ou o UUID gerado no request.

Respostas com sucesso em origens de browser permitidas incluem headers CORS conforme `API_CORS_ORIGINS` (origens fora da allowlist não recebem `Access-Control-Allow-Origin`).

## 8. Configuração e Docker

A API lê configuração de environment variables. Dentro da rede Docker Compose, a API acessa PostgreSQL e Redis pelos hostnames dos respectivos serviços (`postgres`, `redis`), não por `127.0.0.1`. Variáveis de ambiente da API usam o prefixo `API_*` (ex.: `API_ENV`, `API_HOST`, `API_PORT`, `API_CORS_ORIGINS`, `API_N8N_BASE_URL`, `API_REDIS_HOST`, `API_REDIS_PORT`, `API_REDIS_PASSWORD`). As variáveis do cache (`AVAILABILITY_CACHE_*`) deliberadamente não usam o prefixo `API_*`.

O stack Compose sobe, nesta ordem (via healthchecks/`depends_on`):

```text
PostgreSQL healthy
       ↓
migrations
       ↓
seeds
       ↓
Redis healthy
       ↓
FastAPI create_app()
       ↓
n8n (após API healthy)
       ↓
web (após n8n healthy)
```

Serviços relevantes:

| Serviço | Porta default | Papel |
|---|---|---|
| `postgres` | `5432` | fonte de verdade transacional |
| `redis` | `6379` | cache de disponibilidade (cache-aside, TTL + invalidação pós-commit) |
| `api` | `8000` | FastAPI (REST + CORS + `/health/n8n`) |
| `n8n` | `5678` | orquestração conversacional / AI Agent |
| `web` | `8080` | bundle estático da SPA (nginx) |

Variáveis novas relevantes no `.env`:

- `API_CORS_ORIGINS` — allowlist de origens do browser (separadas por vírgula);
- `API_N8N_BASE_URL` — base do probe de readiness (host: `http://localhost:5678`; Compose: `http://n8n:5678`);
- `API_LOG_LEVEL` — nível mínimo de log (default `INFO`);
- `API_LOG_JSON` — `true` (default) para JSON lines em stdout; `false` para console legível;
- `API_REDIS_HOST`, `API_REDIS_PORT`, `API_REDIS_PASSWORD`, `API_REDIS_DB`, `API_REDIS_SOCKET_TIMEOUT`, `API_REDIS_CONNECT_TIMEOUT` — conexão com o Redis;
- `AVAILABILITY_CACHE_ENABLED` — liga/desliga o cache-aside de disponibilidade (default `true`);
- `AVAILABILITY_CACHE_TTL_SECONDS` — TTL base do cache (default `30`);
- `AVAILABILITY_CACHE_TTL_JITTER_SECONDS` — jitter aleatório somado ao TTL (default `10`); TTL efetivo = base + `0…jitter`;
- `N8N_ENCRYPTION_KEY` — obrigatória para o serviço n8n;
- `VITE_API_BASE_URL`, `VITE_N8N_CHAT_WEBHOOK_URL` — embutidas no bundle web (não contêm segredos).

A aplicação é iniciada pelo Uvicorn em factory mode:

```text
essentia_api.main:create_app --factory
```

O fluxo de inicialização é:

```text
PostgreSQL healthy
       ↓
migrations
       ↓
seeds
       ↓
Redis healthy
       ↓
FastAPI create_app()
       ↓
lifespan
       ↓
connection pool + redis client (app.state.availability_cache)
```

Nos testes, a configuração é construída diretamente a partir das credenciais do PostgreSQL e do Redis criados pelos Testcontainers e injetada em `create_app(settings)`, mantendo a aplicação de teste isolada da configuração local. A namespace `availability:*` é limpa entre testes por um fixture autouse para não haver contaminação entre casos.

## 9. Convenções de desenvolvimento

- não editar arquivos gerados pelo sqlc;
- alterar a query SQL e regenerar o código;
- validar queries com `sqlc compile`, `sqlc vet` e `sqlc diff`;
- manter migrations como owner exclusivo do schema;
- não aceitar preço informado pelo cliente em booking;
- não armazenar disponibilidade como estado redundante;
- não colocar regras transacionais em prompts;
- preferir constraints de banco para invariantes críticas;
- manter exemplos OpenAPI alinhados às seeds;
- executar a suíte completa com `pytest` antes de entrega (ou `make test-availability-cache` ao mexer no cache);
- validar a camada web com `make web-check` (typecheck + Vitest) antes de entrega;
- erros de domínio sempre via exceções de `core/errors.py` (nunca `HTTPException` ad-hoc fora de health 503).
