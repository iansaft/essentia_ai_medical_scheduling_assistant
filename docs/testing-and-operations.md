# Testes, Observabilidade e Operação

## 1. Estratégia de testes

A arquitetura foi desenhada para que o domínio possa ser validado independentemente do Agent.

A suíte automatizada utiliza `pytest` e executa testes de integração contra uma instância descartável de PostgreSQL 18.4 criada com Testcontainers. Isso permite validar comportamento específico do PostgreSQL, incluindo transações, `FOR UPDATE`, exclusion constraints, unique indexes parciais e concorrência real.

Estado atual da suíte:

```text
53 tests passed
93.04% total coverage
minimum required coverage: 85%
```

### Camada de API

Cobertura inclui:

- paciente existente retorna `200`;
- paciente inexistente retorna `404`;
- serviço existente/inexistente;
- métodos de pagamento por serviço;
- disponibilidade sem filtros;
- disponibilidade filtrada por médico;
- disponibilidade filtrada por serviço;
- disponibilidade filtrada por data;
- slot bloqueado não aparece;
- slot com appointment `scheduled` não aparece;
- slot com appointment cancelado pode voltar a aparecer quando ainda está aberto/futuro.

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

Também são validados o contrato OpenAPI e invariantes diretamente no banco de dados.

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

GET /v1/patients/{patient_id}

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

Endpoint mínimo:

```http
GET /health
```

Resposta esperada:

```json
{
  "status": "ok"
}
```

O health check atual valida a disponibilidade do processo HTTP. Uma evolução possível é separar liveness e readiness caso seja necessário validar dependências externas.

## 6. Observabilidade planejada

Logs devem ser estruturados e conter, quando disponível:

- timestamp;
- level;
- correlation ID;
- operation/request;
- HTTP method/path/status;
- duração;
- tipo de erro;
- identificadores técnicos relevantes sem dados sensíveis desnecessários.

O n8n deve propagar um identificador como `X-Correlation-ID` para permitir rastrear:

```text
mensagem -> workflow -> Agent -> API -> PostgreSQL -> integração externa
```

## 7. Tratamento de erro HTTP

Semântica utilizada:

- `200 OK` — leitura bem-sucedida;
- `201 Created` — appointment criado;
- `404 Not Found` — recurso não encontrado;
- `409 Conflict` — conflito de estado/concorrência, como double booking ou reutilização inválida de chave de idempotência;
- `422 Unprocessable Entity` — validação de parâmetros/body pelo FastAPI/Pydantic;
- `500 Internal Server Error` — falha não tratada, que deve ser observável em logs e não usada para regras esperadas de domínio.

## 8. Configuração e Docker

A API lê configuração de environment variables. Dentro da rede Docker Compose, a API acessa PostgreSQL pelo hostname do serviço (`postgres`), não por `127.0.0.1`.

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
FastAPI create_app()
       ↓
lifespan
       ↓
connection pool
```

Nos testes, a configuração é construída diretamente a partir das credenciais do PostgreSQL criado pelo Testcontainers e injetada em `create_app(settings)`, mantendo a aplicação de teste isolada da configuração local.

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
- executar a suíte completa com `pytest` antes de entrega.
