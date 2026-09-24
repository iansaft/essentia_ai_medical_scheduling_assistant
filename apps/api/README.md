# Essentia AI Medical Scheduling Assistant — API REST

API **FastAPI** responsável pelas operações determinísticas do domínio de agendamento médico: consulta de pacientes, catálogo de serviços e pagamentos, disponibilidade de agenda, criação e cancelamento de agendamentos.

A API é a fonte da verdade para regras de negócio transacionais (o LLM/Agente e o n8n consomem este contrato; a aplicação web em `apps/web` consome as rotas de leitura e o cadastro aberto de pacientes). A especificação HTTP é gerada automaticamente pelo FastAPI em `/openapi.json` — é a única fonte de documentação de endpoints.

- Documentação técnica do projeto: [`../../docs/`](../../docs/README.md)
- Timezone de negócio: `America/Sao_Paulo`

## Stack

| Camada | Tecnologia |
|---|---|
| Web framework | FastAPI + Uvicorn (factory mode: `essentia_api.main:create_app --factory`) |
| Linguagem | Python ≥ 3.14 |
| Banco | PostgreSQL 18 (sem ORM — Psycopg 3 + `psycopg_pool`) |
| Cache | Redis 8 (cache-aside de disponibilidade — ver [Cache de disponibilidade](#cache-de-disponibilidade-redis)) |
| Acesso a dados | SQL tipado gerado pelo **sqlc** (`src/essentia_api/db/generated/` — não editar manualmente) |
| Schema/seed | `golang-migrate` (migrations em `db/migrations`, seeds em `db/seeds`, tabelas de controle independentes) |
| Testes | pytest + Testcontainers (PostgreSQL 18.4 e Redis 8.10 descartáveis por execução) |
| Contrato HTTP | OpenAPI gerado pelo FastAPI (`/docs`, `/openapi.json`) |

## Como rodar a API

### Opção A — Docker Compose (recomendado para avaliar)

Sobe PostgreSQL → migrations → seeds → Redis → API nesta ordem (healthcheck/`depends_on` garantem a ordem):

```bash
# na raiz do repositório
cp .env.example .env
# edite PG_SUPERUSER_PW e mantenha API_DB_PW igual a ele
# defina N8N_ENCRYPTION_KEY (obrigatória para o serviço n8n)

docker compose up -d --build
curl http://localhost:8000/health         # {"status":"ok"}
curl http://localhost:8000/health/n8n     # {"status":"ok"} quando o n8n está pronto
```

O Compose sobe `postgres` → migrations/seeds → `redis` → `api` → `n8n` → `web` (healthchecks/`depends_on` garantem a ordem):

- API: `http://localhost:8000` (porta `API_PORT`, default 8000)
- n8n: `http://localhost:5678` (porta `N8N_PORT`)
- Web: `http://localhost:8080` (porta `WEB_PORT`)
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Opção B — local (sem subir a API no Docker)

```bash
cp .env.example .env           # se ainda não existir
docker compose up -d postgres  # apenas o banco

make migrate-up                # aplica schema
make seed-up                   # aplica dados de demonstração
make api-dev                   # Uvicorn com reload em :8000
```

### Reiniciar o estado de demonstração

Os comandos de escrita alteram o estado das seeds. Para voltar ao estado inicial:

```bash
make seed-down && make seed-up
# ou, com Docker Compose: docker compose down -v && docker compose up -d --build
```

## Recursos da API REST

Todas as rotas de domínio estão sob o prefixo `/v1`. **Não há autenticação nesta etapa**, mas rotas patient-scoped exigem o header `X-Patient-Id` (UUID do paciente), que deve coincidir com o dono do recurso acessado — mismatch retorna `403`. `GET /v1/patients`, `POST /v1/patients`, services, availability e health permanecem sem o header.

Habilitação de CORS: o middleware `CORSMiddleware` libera apenas as origens em `API_CORS_ORIGINS` (separadas por vírgula; default `http://localhost:5173,http://localhost:4173,http://localhost:8080` — Vite dev, Vite preview e container web).

| Método | Recurso | Descrição |
|---|---|---|
| `GET` | `/health` | Health check do processo HTTP (liveness) |
| `GET` | `/health/n8n` | Readiness do n8n via probe em `API_N8N_BASE_URL` |
| `GET` | `/v1/patients` | Lista todos os pacientes (ativos e inativos) |
| `POST` | `/v1/patients` | Cadastra um novo paciente (aberto) |
| `GET` | `/v1/patients/{patient_id}` | Dados cadastrais de um paciente |
| `GET` | `/v1/patients/{patient_id}/appointments` | Histórico de agendamentos do paciente |
| `GET` | `/v1/services` | Lista serviços ativos |
| `GET` | `/v1/services/{service_id}` | Detalhe de um serviço (preço, moeda, duração) |
| `GET` | `/v1/services/{service_id}/payment-methods` | Métodos de pagamento aceitos pelo serviço |
| `GET` | `/v1/availability` | Slots efetivamente disponíveis (filtros opcionais) |
| `GET` | `/v1/appointments/{appointment_id}` | Detalhe de um agendamento |
| `POST` | `/v1/appointments` | Cria um agendamento (**idempotente**) |
| `POST` | `/v1/appointments/{appointment_id}/cancel` | Cancela um agendamento (**idempotente**) |

### `GET /health`

Sem parâmetros. Resposta `200`:

```json
{ "status": "ok" }
```

### `GET /health/n8n`

Sem parâmetros. Sonda `GET {API_N8N_BASE_URL}/healthz/readiness` (timeout 2s):

| Situação | HTTP | Corpo |
|---|---|---|
| n8n responde `2xx` | `200` | `{"status":"ok"}` |
| n8n inacessível ou não pronto | `503` | `{"detail":{"status":"error"}}` |

Dentro do Compose a API usa `API_N8N_BASE_URL=http://n8n:5678`; em desenvolvimento local, o `.env` usa `http://localhost:5678`.

### `GET /v1/patients`

Sem parâmetros e **sem** `X-Patient-Id` (público — necessário para o seletor de pacientes da UI). `200` com a lista de **todos** os pacientes, ativos e inativos (`PatientResponse`: `id`, `full_name`, `email`, `phone`, `is_active`, timestamps), em ordem determinística (`created_at`, `id`). Pacientes inativos são incluídos com `is_active = false` (WEB-RF-01).

### `POST /v1/patients` — cadastrar paciente

| | |
|---|---|
| Header | **sem** `X-Patient-Id` e **sem** `Idempotency-Key` (endpoint aberto) |
| Body | `{"full_name": "<1–200>", "email": "<3–320>", "phone": "<1–32, opcional>"}` |
| Sucesso | `201` com `PatientResponse` (`is_active = true`) |
| Erro | `409` se o email (case-insensitive) ou o phone já existir; `422` se o body for inválido ou com campos em branco |

Cadastro de novo paciente sem autenticação — basta informar `full_name` e `email`; `phone` é opcional (`null` no response quando omitido). Campos são normalizados com trim antes da persistência.

| Condição | HTTP | `problem_type` |
|---|---|---|
| Email já cadastrado (qualquer caixa) | `409` | `/problems/patient-email-already-exists` |
| Phone já cadastrado | `409` | `/problems/patient-phone-already-exists` |
| Body ausente/inválido ou campo em branco | `422` | FastAPI `detail[]` |

Example no OpenAPI: `joana.souza@example.com` (não colide com as seeds).

### `GET /v1/patients/{patient_id}`

| | |
|---|---|
| Path | `patient_id` (UUID, obrigatório) |
| Header | **`X-Patient-Id`** (UUID, obrigatório) — deve ser igual ao `patient_id` da path |
| Sucesso | `200` com `PatientResponse` (`id`, `full_name`, `email`, `phone`, `is_active`, timestamps) |
| Erro | `403` se o header não corresponder ao path; `404` se o paciente não existir; `422` se o header/path for inválido ou ausente |

Consulta dados cadastrais mesmo sem agenda futura associada (BR-03).

### `GET /v1/patients/{patient_id}/appointments`

| | |
|---|---|
| Path | `patient_id` (UUID, obrigatório) |
| Header | **`X-Patient-Id`** (UUID, obrigatório) — deve ser igual ao `patient_id` da path |
| Sucesso | `200` com lista de `AppointmentResponse` ordenada por `starts_at DESC` |
| Erro | `403` se o header não corresponder ao path; `404` se o paciente não existir; `422` se o UUID for inválido ou o header ausente |

Retorna **todos** os agendamentos do paciente, em qualquer status (`scheduled`, `cancelled`, `completed`, `no_show`), preservando o snapshot de preço e os dados de cancelamento (WEB-RF-06). Paciente existente sem agendamentos retorna `200` com `[]`.

Example no OpenAPI: `3cdf666b-186d-44e6-bce9-5e572e7038f9` (Maria Silva).

### `GET /v1/services`

Sem parâmetros. `200` com a lista de serviços **ativos** (`ServiceResponse`: `id`, `code`, `name`, `description`, `price`, `currency`, `duration_minutes`).

### `GET /v1/services/{service_id}`

| | |
|---|---|
| Path | `service_id` (UUID, obrigatório) |
| Sucesso | `200` com `ServiceResponse` |
| Erro | `404` |

### `GET /v1/services/{service_id}/payment-methods`

| | |
|---|---|
| Path | `service_id` (UUID, obrigatório) |
| Sucesso | `200` com lista de `PaymentMethodResponse` (`code`, `name`, `max_installments`, `notes`) |
| Erro | `404` |

Os métodos e o número máximo de parcelas dependem do serviço (BR-07/BR-27). A API informa meios de pagamento, mas não processa pagamento real (BR-28).

### `GET /v1/availability`

Retorna apenas slots **efetivamente disponíveis** (RF-04 / BR-09). Um slot aparece somente quando:

1. `status = 'open'` (não `blocked` nem `closed`);
2. `starts_at` no futuro;
3. médico ativo;
4. serviço ativo;
5. **não** existe appointment `scheduled` ocupando o slot.

Filtros query (**todos opcionais**):

| Parâmetro | Tipo | Example no OpenAPI | Observação |
|---|---|---|---|
| `doctor_id` | UUID | `0dfc6223-6a11-4d90-a979-bd511bc1d6a9` (Dr. Helena Costa) | Filtra por médico |
| `service_id` | UUID | `e2fb5edd-efbd-4d60-9de3-d6650e31562f` (Cardiology Initial Consultation) | Filtra por serviço |
| `date` | `YYYY-MM-DD` | `2027-04-12` | Data civil em `America/Sao_Paulo` (BR-13) |

Resposta `200` com lista de `AvailableSlotResponse` (`id`, `doctor_id`/`doctor_name`, `service_id`/`service_code`/`service_name`, `price`, `currency`, `starts_at`, `ends_at`).

Observações:

- A disponibilidade é **derivada** (slot `open` + ausência de `scheduled`), não é um campo persistido;
- cancelar um agendamento **libera** o slot para os filtros, sem mudar o status administrativo do slot (BR-10);
- `date` inválida (ex.: `21-09-2026`) retorna `422`.

### `GET /v1/appointments/{appointment_id}`

| | |
|---|---|
| Path | `appointment_id` (UUID, obrigatório) |
| Header | **`X-Patient-Id`** (UUID, obrigatório) — deve ser o `patient_id` dono do agendamento |
| Sucesso | `200` com `AppointmentResponse` (inclui `patient_*`, `doctor_*`, `service_*`, `starts_at`/`ends_at`, `status`, snapshot `price_amount`/`currency`, campos de cancelamento) |
| Erro | `403` se o header não for o dono; `404` se não existir; `422` se o header ausente/inválido |

Example no OpenAPI: `8029d8d3-8fff-4dcc-a2ef-2ae0808bf95e` (agendamento `scheduled` das seeds, dono Maria `3cdf666b-…`).

### `POST /v1/appointments` — criar agendamento

| | |
|---|---|
| Header | **`Idempotency-Key`** (string 1–255, obrigatório) |
| Header | **`X-Patient-Id`** (UUID, obrigatório) — deve ser igual ao `patient_id` do body |
| Body | `{"patient_id": "<uuid>", "slot_id": "<uuid>"}` |
| Sucesso | `201` com `AppointmentResponse` |
| Erro | `403` se `X-Patient-Id` ≠ `body.patient_id` |

O cliente envia **apenas** os ids (BR-17): preço, moeda, médico e serviço são derivados no servidor a partir do slot/catálogo, e `price_amount`/`currency` gravam um **snapshot** imutável no appointment (BR-18/BR-26).

Validações (BR-16) → respostas:

| Condição | HTTP |
|---|---|
| Paciente ou slot inexistente | `404` |
| `X-Patient-Id` ≠ `body.patient_id` | `403` |
| Paciente inativo; slot não `open`; slot no passado; médico/serviço inativo; slot já ocupado por `scheduled` (double booking); reuso de `Idempotency-Key` com payload diferente | `409` |
| Body inválido ou header (`Idempotency-Key`/`X-Patient-Id`) ausente | `422` |

Regras de idempotência (BR-29–BR-32):

- mesma key + mesmo payload (replay) → devolve o mesmo `201` sem duplicar o registro;
- mesma key + payload diferente → `409`;
- uma única execução por slot `scheduled` é garantida também por unique index parcial no PostgreSQL (BR-19).

Examples no OpenAPI (válidos para as seeds): `patient_id = 3cdf666b-186d-44e6-bce9-5e572e7038f9`, `slot_id = 8e06b231-a27f-4bf3-bc69-7565f20c3f7d`.

### `POST /v1/appointments/{appointment_id}/cancel` — cancelar agendamento

| | |
|---|---|
| Path | `appointment_id` (UUID, obrigatório) |
| Header | **`Idempotency-Key`** (string 1–255, obrigatório) |
| Header | **`X-Patient-Id`** (UUID, obrigatório) — deve ser o dono do agendamento |
| Body | `{"cancellation_reason": "<3–500 chars>"}` |
| Sucesso | `200` com `AppointmentResponse` (`status = "cancelled"`, `cancellation_reason`, `cancelled_at`) |

Cancelamento é **transição de estado**, nunca exclusão física (BR-21). Regras:

| Condição | HTTP |
|---|---|
| Appointment inexistente | `404` |
| `X-Patient-Id` ≠ dono do appointment | `403` |
| Status diferente de `scheduled` (já cancelado, `completed`, `no_show`) | `409` |
| Motivo com menos de 3 caracteres / body ou headers ausentes | `422` |
| Mesma key reutilizada com motivo ou caller diferente | `409` |

Example no OpenAPI: `8029d8d3-8fff-4dcc-a2ef-2ae0808bf95e` (único `scheduled` nas seeds).

## Estados de appointment

`scheduled` → `cancelled` (cancelamento) ou `completed` / `no_show` (histórico). Estado do appointment e estado do slot são independentes: o slot não possui status `booked`.

## Códigos de erro HTTP

| Código | Semântica |
|---|---|
| `200 OK` | Leitura (ou cancelamento) bem-sucedida |
| `201 Created` | Appointment ou paciente criado (`POST /v1/appointments`, `POST /v1/patients`) |
| `403 Forbidden` | `X-Patient-Id` não corresponde ao dono do recurso (path, body ou `patient_id` do appointment) |
| `404 Not Found` | Recurso não encontrado |
| `409 Conflict` | Conflito de estado/concorrência: double booking, slot não cancelável, reuso inválido de `Idempotency-Key`, paciente/serviço/médico inativo, slot não `open`/passado, e-mail ou telefone de paciente já existentes (`POST /v1/patients`) |
| `422 Unprocessable Entity` | Validação de path/query/body/header (Pydantic/FastAPI), incluindo `X-Patient-Id`/`Idempotency-Key` ausentes |
| `503 Service Unavailable` | Dependência externa indisponível (`GET /health/n8n` quando o n8n não está pronto) |
| `500 Internal Server Error` | Falha não tratada |

### Formato das respostas de erro

**403 / 404 / 409 / 500 de domínio** (e falhas não tratadas) usam `Content-Type: application/problem+json` (RFC 7807 — DD-19):

```json
{
  "type": "/problems/slot-unavailable",
  "title": "Conflict",
  "status": 409,
  "detail": "Appointment slot is already booked.",
  "instance": "/v1/appointments"
}
```

- `type` — URI estável do problema (ex.: `/problems/patient-access-denied`);
- `detail` — mensagem em inglês para o cliente;
- `instance` — path da requisição;
- `500` não tratado → `/problems/internal-error` com `detail` genérico (stacktrace apenas nos logs).

**Shapes preservados** (não usam problem+json):

| Cenário | Shape |
|---|---|
| `422` de validação FastAPI/Pydantic | `{"detail": [ { "loc", "msg", "type", ... } ]}` |
| `503` em `GET /health/n8n` | `{"detail":{"status":"error"}}` |

### Header `X-Correlation-ID`

Todas as respostas (sucesso e erro) ecoam `X-Correlation-ID`. Se o cliente (n8n, SPA) envia o header, o valor é preservado; caso contrário a API gera um UUID. O mesmo id é anexado a todos os logs do request via structlog (ver DD-19 e `docs/testing-and-operations.md`).

### Logging

- `API_LOG_LEVEL` (default `INFO`) — nível mínimo;
- `API_LOG_JSON` (default `true`) — JSON lines em stdout (prod); `false` → console legível (dev/test).

### Observações de `GET /v1/availability`

A resposta é servida via cache-aside em Redis (ver [Cache de disponibilidade](#cache-de-disponibilidade-redis)); o contrato HTTP (filtros, shape, códigos) não muda.

## Cache de disponibilidade (Redis)

`GET /v1/availability` usa **cache-aside** em Redis; o PostgreSQL continua sendo a única fonte da verdade. Implementação: `services/availability.py` (orquestração) + `cache/availability.py` (operações) — a rota é um delegate fino.

### Estratégia

| Aspecto | Decisão |
|---|---|
| Padrão | Cache-aside: `GET` → hit serve o JSON; miss consulta o PostgreSQL e popula o cache |
| Autoridade | Redis **nunca** autoriza booking — double-booking continua garantido pelo índice único no PostgreSQL |
| TTL | `AVAILABILITY_CACHE_TTL_SECONDS` (default `30`) + jitter aleatório `0…AVAILABILITY_CACHE_TTL_JITTER_SECONDS` (default `10`) → TTL efetivo 30–40s |
| Jitter | Espalha expirações simultâneas de chaves populadas no mesmo instante (mitiga thundering herd na expiração) |
| Chave | `availability:v1:{service_id\|all}:{doctor_id\|all}:{date\|all}` — versão (`v1`) para evolução de formato, partes ausentes viram `all` |
| Data na chave | Data civil em `BUSINESS_TIMEZONE` (`America/Sao_Paulo`) extraída de `starts_at` (TIMESTAMPTZ) |
| Payload | JSON serializado dos `AvailableSlotResponse` (inclusive lista vazia `[]` — é um hit válido) |
| Desabilitar | `AVAILABILITY_CACHE_ENABLED=false` → bypass total (sem cliente Redis nas rotas de leitura) |

### Consistência e invalidação

- **Invalidação pós-commit**: `POST /v1/appointments` e `POST .../cancel` limpam as chaves **somente após** o `COMMIT` do PostgreSQL — uma falha de `DEL` nunca desfaz uma escrita confirmada (o pior caso é stale até o TTL expirar);
- **Escopo do `DEL`**: cross product de 8 chaves `{service|all} × {doctor|all} × {date|all}` derivado do appointment (`service_id`, `doctor_id`, data de `starts_at`) — remove qualquer variante de filtro já populada;
- **Falha de escrita idempotente (replay)**: não invalida (nenhuma mudança de estado);
- **Booking rejeitado** (`409`, ex.: double booking): não invalida (nenhuma mudança);
- **Fail-open**: falha de conexão/timeout do Redis em `get`/`set`/`delete` cai para o caminho PostgreSQL e loga `availability_cache_read_error` / `write_error` / `invalidation_error` — **nunca** gera `500` nem rollback;
- **Post-commit transactional** via `with connection.transaction()` em `services/appointments.py`: response é montado dentro da transação; o `DEL` roda fora, após confirmar.

### Trade-offs

- **Janela de staleness**: entre o commit de um booking/cancelamento concorrente e o `DEL`, uma leitura pode ver estado antigo; em falha de invalidação, até 30–40s (TTL). Aceitável para disponibilidade de agenda;
- **Stampede**: mitigado por TTL curto + jitter; **não** há single-flight/lock entre instâncias — sob carga extrema de cold start é possível thundering herd ao PostgreSQL (documentado como follow-up: `SET NX` de request coalescing);
- **Hit ratio**: `hits / (hits + misses)` — medir com `availability_cache_hit` vs `availability_cache_miss` nos logs structlog; com TTL 30s e tráfego de leitura >> escrita, espera-se razão alta, e cada booking zera as variantes afetadas;
- **Invalidação broad**: o `DEL` de 8 keys apaga também variantes não consultadas (ex.: chave inexistente) — `DEL` multi-key é idempotente e barato; mais simples que tracking de quais variantes existem.

### Evidências manuais (stack via Docker Compose)

Executadas contra `docker compose up -d --build` com seeds frescas:

| # | Comando | Resultado observado |
|---|---|---|
| 1 | `redis-cli -a $REDIS_PASSWORD ping` | `PONG`; `--scan --pattern availability:*` → `0` keys |
| 2 | `GET /v1/availability?date=2027-04-12` (1ª vez) | `200`; log `availability_cache_miss` + `availability_cache_set` (ttl 31s); key `availability:v1:all:all:2027-04-12` criada |
| 3 | Mesmo `GET` (2ª vez) | `200`; log `availability_cache_hit`; payload idêntico ao da 1ª chamada (5 slots) |
| 4 | `PTTL availability:v1:all:all:2027-04-12` | `21542` ms — dentro da janela `0 < ttl ≤ 40000` |
| 5 | `GET availability:v1:all:all:2027-04-12` | JSON array de `AvailableSlotResponse` (ex.: `Dr. Bruno Martins`, `"price":"180.00"`) |
| 6 | `POST /v1/appointments` (slot `8e06b231-…`) | `201`; log `availability_cache_invalidation` com as **8** keys; scan → vazio |
| 7 | `POST /v1/appointments/{id}/cancel` | `200` (`status: cancelled`); novo log de invalidação com 8 keys; scan → vazio |
| 8 | `docker compose stop redis` → `GET /v1/availability` | `200` com 5 slots (fail-open) + log `availability_cache_read_error`; Redis reiniciado → `PONG` |

### Logs estruturados (structlog)

`availability_cache_hit` · `availability_cache_miss` · `availability_cache_set` · `availability_cache_invalidation` · `availability_cache_read_error` · `availability_cache_write_error` · `availability_cache_invalidation_error` — todos com `cache_key`, filtros (`service_id`/`doctor_id`/`date`), `correlation_id` do request.

## Dados de demonstração (seeds)

IDs usados nos examples do OpenAPI — todos existem em `db/seeds/`:

**Pacientes**

| Nome | ID | Ativo |
|---|---|---|
| Maria Silva | `3cdf666b-186d-44e6-bce9-5e572e7038f9` | ✅ (example do `create`) |
| Carlos Souza | `9195382a-3a1c-44e7-94b6-6d55c8b9338f` | ✅ |
| Ana Oliveira | `e8fd74e7-b450-47fe-84e8-e34813bb4031` | ✅ |
| Lucas Ferreira | `2338a014-ec7f-4585-a519-c15e9c20b11c` | ❌ inativo (testa `409`) |

**Médicos e serviços**

| Médico | ID | Serviço | ID | Preço |
|---|---|---|---|---|
| Dr. Helena Costa | `0dfc6223-6a11-4d90-a979-bd511bc1d6a9` | Cardiology Initial Consultation | `e2fb5edd-efbd-4d60-9de3-d6650e31562f` | 320,00 BRL |
| Dr. Rafael Lima | `64a33ade-1719-4093-a6e1-2ea442e47e0b` | Dermatology Consultation | `b9d24a3f-45eb-48bf-9d48-1f075e4c40a3` | 250,00 BRL |
| Dr. Bruno Martins | `0466ab03-bb89-4b4e-9326-78edb1fe6aa2` | General Medical Consultation | `6640a42f-830c-4187-aacf-ed576b464b74` | 180,00 BRL |
| — | — | Follow-up Consultation | `93391495-8729-48f7-86e7-b8052b53b868` | 150,00 BRL |

**Slots (datas fixas nas seeds)**

| Data | Conteúdo |
|---|---|
| `2027-04-12` | Slots futuros de cardiologia, dermatologia e clínica geral (1º dia útil do example de `date`) |
| `2027-04-13` | 2º dia de slots futuros |
| `2026-09-19` | Slot histórico `closed` (consulta concluída) |
| `2026-09-18` | Slot histórico `closed` (no-show) |

Slots relevantes:

| ID | Situação |
|---|---|
| `8e06b231-a27f-4bf3-bc69-7565f20c3f7d` | `open`, futuro, livre — **example do `create`** |
| `26036bfd-3ba4-405d-9e7a-4df6a540ee1f` | Ocupado pelo appointment `scheduled` seed (não aparece em availability; usar para testar `409`) |
| `51d9ec84-aa0a-46ca-a37b-4952a5e35cc7` | `open` (liberado após cancelamento seed) |
| `7b983580-560d-42d5-a40a-8189b8035dbc` | `blocked` (testa `409` no create) |

**Appointments**

| ID | Status | Uso |
|---|---|---|
| `8029d8d3-8fff-4dcc-a2ef-2ae0808bf95e` | `scheduled` | **Examples de `get` e `cancel`** |
| `d6e99970-3b01-43c4-84a9-4042188262be` | `cancelled` | Cancelar de novo → `409` |
| `75adebb0-cff9-4a8c-9dfc-43bc321fabed` | `completed` | Snapshot de preço histórico (300,00 BRL) |
| `607179d5-2c1e-45ca-96bd-4a3593462caa` | `no_show` | Histórico |

> **Validade dos examples de data:** os slots futuros ficam em `2027-04-12`/`2027-04-13`. O example de `date` e o slot do `create` permanecem válidos até **2027-04-12**; após essa data as seeds precisam ser revisadas.

## Passo a passo: testar a API no Postman

### 1. Subir a API

```bash
cp .env.example .env   # ajuste as senhas, se ainda não o fez
docker compose up -d --build
curl http://localhost:8000/health
```

### 2. Importar a coleção OpenAPI

1. Postman → **Import** → **Link** → coleie `http://localhost:8000/openapi.json` (importar via URL faz o Postman herdar o host da API);
2. Confirme a variável da coleção: `baseUrl = http://localhost:8000`;
3. Todos os endpoints, bodies, headers e examples vêm pré-preenchidos do OpenAPI — nada precisa ser digitado à mão na primeira passada.

### 3. Sequência de leitura e cadastro (efetos limitados)

O passo `5b` cria um paciente de demonstração no banco (efeito colateral limitado e removível com `make seed-down && seed-up`); os demais passos desta sequência são leitura.

| # | Request | Expectativa |
|---|---|---|
| 1 | `GET /health` | `200` → `{"status":"ok"}` |
| 1b | `GET /health/n8n` | `200` → `{"status":"ok"}` (n8n pronto) ou `503` se o n8n estiver fora |
| 2 | `GET /v1/services` | `200` → 4 serviços |
| 3 | `GET /v1/services/{service_id}` (example `e2fb5edd-…`) | `200` → Cardiologia, 320,00 BRL |
| 4 | `GET /v1/services/{service_id}/payment-methods` (mesmo id) | `200` → PIX, cartão de crédito (até 6x), débito |
| 5 | `GET /v1/patients/{patient_id}` (example `3cdf666b-…`) | `200` → Maria Silva |
| 5b | `POST /v1/patients` — body example (Joana Souza, sem headers especiais) | `201` → novo paciente com `is_active: true` |
| 5c | Reenvie o mesmo body | `409` problem+json (`/problems/patient-email-already-exists`) |
| 5d | `GET /v1/patients` | `200` → lista inclui Joana (além das seeds) |
| 6 | `GET /v1/availability` sem filtros | `200` → lista slots futuros (não inclui `26036bfd-…` nem `7b983580-…`) |
| 7 | `GET /v1/availability?doctor_id=0dfc6223-…` | `200` → só slots da Dr. Helena |
| 8 | `GET /v1/availability?service_id=e2fb5edd-…` | `200` → só slots de cardiologia |
| 9 | `GET /v1/availability?date=2027-04-12` | `200` → slots do 1º dia futuro seedado |
| 10 | `GET /v1/availability` com os 3 filtros | `200` → interseção (Helena + Cardiologia + `2027-04-12`) |
| 11 | `GET /v1/appointments/{appointment_id}` (example `8029d8d3-…`) | `200` → `status: "scheduled"` |

### 4. Sequência de escrita (com `Idempotency-Key`)

> Execute nesta ordem. O cancelamento é o único passo destrutivo do estado seed — deixe-o por último.

| # | Request | Expectativa |
|---|---|---|
| 12 | `POST /v1/appointments` — body example (`patient_id` + `slot_id` pré-preenchidos) + header `Idempotency-Key` (example `7ff768c5-…` ou qualquer string única) | `201` → appointment criado para Maria no slot `8e06b231-…`, preço 320,00 BRL derivado do serviço |
| 13 | Reenvie o **mesmo** request (mesma key, mesmo body) | `201` idêntico — replay idempotente, nenhum registro duplicado |
| 14 | Mesmo body com uma **nova** key | `409` → slot já ocupado (double booking) |
| 15 | `POST /v1/appointments` **sem** `Idempotency-Key` | `422` |
| 16 | `POST /v1/appointments/{appointment_id}/cancel` — id `8029d8d3-…`, body example de motivo + `Idempotency-Key` | `200` → `status: "cancelled"` |
| 17 | `GET /v1/appointments/8029d8d3-…` | `200` → agora `cancelled`, com `cancellation_reason` e `cancelled_at` |
| 18 | Cancel de novo (id `8029d8d3-…`, key nova) | `409` → "Only scheduled appointments can be cancelled." |
| 19 | `GET /v1/availability?doctor_id=0dfc6223-…&service_id=e2fb5edd-…` | `200` → o slot `26036bfd-…` (10:00) reapareceu liberado |

### 5. Caminhos de erro (opcionais)

Respostas `403/404/409/500` de domínio usam `application/problem+json` (corpo com `type`/`title`/`status`/`detail`/`instance`).

| Request | Expectativa |
|---|---|
| `GET /v1/appointments/00000000-0000-4000-8000-000000000001` | `404` problem+json (`Appointment not found.`) |
| `GET /v1/patients/{id}` com UUID inexistente | `404` problem+json |
| `POST /v1/patients` com email `maria.silva@example.com` (seed, qualquer caixa) | `409` problem+json (`/problems/patient-email-already-exists`) |
| `POST /v1/patients` com phone `+5548999990001` (Maria, seed) | `409` problem+json (`/problems/patient-phone-already-exists`) |
| `POST /v1/patients` com body vazio | `422` FastAPI `detail[]` |
| `POST /v1/appointments` com `patient_id = 2338a014-…` (Lucas, inativo) | `409` problem+json |
| `POST /v1/appointments` com `slot_id = 7b983580-…` (blocked) | `409` problem+json |
| `GET /v1/availability?date=21-09-2026` | `422` FastAPI `detail[]` |
| Cancel de `d6e99970-…` (já cancelado) | `409` problem+json |

Exemplo problem+json de `POST /v1/patients`:

```json
{
  "type": "/problems/patient-email-already-exists",
  "title": "Conflict",
  "status": 409,
  "detail": "Patient email already exists.",
  "instance": "/v1/patients"
}
```

### 6. Resetar o estado para repetir

```bash
make seed-down && make seed-up
# ou Docker Compose:
docker compose down -v && docker compose up -d --build
```

## OpenAPI / Swagger

| URL | Uso |
|---|---|
| `http://localhost:8000/docs` | Swagger UI interativa |
| `http://localhost:8000/openapi.json` | Especificação OpenAPI (import no Postman) |

O FastAPI é a única fonte da documentação HTTP: endpoints, parâmetros, schemas e examples são gerados a partir do código das rotas/schemas. Os examples de ids foram alinhados às seeds para que a coleção importada no Postman funcione na primeira tentativa.

## Testes automatizados

A suíte roda com Testcontainers (PostgreSQL e Redis descartáveis) e não depende da API local:

```bash
make test                  # suíte completa com coverage (mínimo 85%)
make test-fast             # sem coverage
make test-openapi          # contrato OpenAPI (operações e header Idempotency-Key)
make test-appointments     # booking, cancelamento e idempotência
make test-availability     # disponibilidade e filtros
make test-availability-cache # cache de disponibilidade (unit + integração com Redis real)
make test-db               # invariantes de banco (constraints)
make check                 # sqlc + suíte da API + typecheck e testes do web
make web-check             # apenas validações do web (typecheck + Vitest)
```

O cache tem testes unitários (`tests/unit/test_availability_cache.py` — telemetria, chaves, TTL/jitter, fail-open com mocks) e de integração (`tests/integration/test_availability_cache.py` — HIT/MISS contra Redis real, expiração, invalidação pós-commit, outage total, flag desabilitada).

Convenções relevantes (detalhes em [`../../docs/testing-and-operations.md`](../../docs/testing-and-operations.md)):

- não editar arquivos em `db/generated` (gerados pelo sqlc);
- migrations são o único owner do schema;
- manter examples do OpenAPI alinhados às seeds;
- `ruff check src tests` para lint.

## Estrutura do projeto

```text
apps/api/src/essentia_api/
├── api/
│   ├── routes/          # adaptação HTTP (health, patients, services, availability, appointments)
│   ├── dependencies.py  # pool de conexão + cache via app.state
│   └── router.py        # prefixo /v1
├── cache/
│   ├── availability.py  # AvailabilityCache: get/set/invalidation, chaves, serialização
│   └── redis.py         # create_redis_client (lifespan da aplicação)
├── core/
│   ├── config.py        # Settings (env vars, logging, Redis/cache)
│   ├── errors.py        # hierarchy AppError + handlers RFC 7807
│   ├── logging.py       # setup structlog (JSON stdout / console)
│   ├── middleware.py    # CorrelationIdMiddleware (X-Correlation-ID)
│   └── pool.py          # (ver db/)
├── db/
│   ├── pool.py
│   ├── queries/         # SQL fonte do sqlc
│   └── generated/       # persistência gerada (não editar)
├── schemas/             # contratos Pydantic (request/response + examples OpenAPI)
├── services/            # regras de uso e transações de escrita
│   └── availability.py  # cache-aside de leitura (services de escrita invalidam)
└── main.py              # Application Factory (create_app)
```

## Documentação relacionada

| Documento | Conteúdo |
|---|---|
| [`../../docs/system-requirements.md`](../../docs/system-requirements.md) | Requisitos funcionais e não funcionais |
| [`../../docs/business-rules.md`](../../docs/business-rules.md) | Regras de domínio (BR-01…BR-38) |
| [`../../docs/architecture.md`](../../docs/architecture.md) | Arquitetura e fluxos (booking, cancelamento, disponibilidade) |
| [`../../docs/data-model.md`](../../docs/data-model.md) | Modelo relacional e invariantes |
| [`../../docs/design-decisions.md`](../../docs/design-decisions.md) | Trade-offs (idempotência, snapshot de preço, sqlc) |
| [`../../docs/web-application.md`](../../docs/web-application.md) | Especificação da aplicação web (WEB-RF/WEB-DD) |
| [`../../docs/testing-and-operations.md`](../../docs/testing-and-operations.md) | Estratégia de testes e operação local |
