# Documentação Técnica — Essentia AI Medical Scheduling Assistant

Esta pasta concentra as principais decisões de produto, domínio e engenharia do projeto. O objetivo é permitir uma leitura rápida do desenho do sistema sem exigir a análise completa do código-fonte.

## Índice

| Documento | Conteúdo |
|---|---|
| [system-requirements.md](./system-requirements.md) | Escopo, requisitos funcionais e requisitos não funcionais |
| [business-rules.md](./business-rules.md) | Regras de negócio de pacientes, catálogo, disponibilidade, agendamento e cancelamento |
| [architecture.md](./architecture.md) | Arquitetura, responsabilidades por componente, fluxos e boundaries |
| [n8n-workflow-architecture.md](./n8n-workflow-architecture.md) | Arquitetura, topologia e resiliência do workflow n8n |
| [data-model.md](./data-model.md) | Modelo relacional, invariantes e constraints relevantes |
| [design-decisions.md](./design-decisions.md) | Decisões arquiteturais, trade-offs e alternativas evitadas |
| [web-application.md](./web-application.md) | Especificação da aplicação web (requisitos WEB-RF/RNF, contratos, decisões WEB-DD) |
| [testing-and-operations.md](./testing-and-operations.md) | Estratégia de testes, OpenAPI/Postman, observabilidade e operação local |

## Visão resumida

O sistema é um assistente de agendamento médico com interface conversacional orquestrada por **n8n** e uma API **FastAPI** responsável pelas operações determinísticas do domínio. O **PostgreSQL** mantém a fonte de verdade transacional e também reforça invariantes críticas de consistência; um **Redis** atua apenas como cache descartável (cache-aside) da leitura de disponibilidade, com TTL curto e invalidação pós-commit.

Princípio central:

> O modelo de IA interpreta intenção e linguagem natural; o workflow orquestra integrações; a API governa regras de negócio; o banco garante invariantes finais de consistência.

## Estado atual

### Implementado na API

- health check;
- listagem de pacientes;
- cadastro de pacientes (`POST /v1/patients`, aberto; `409` e-mail/telefone duplicado);
- consulta de paciente por ID;
- histórico de agendamentos do paciente;
- listagem e consulta de serviços;
- consulta de métodos de pagamento por serviço;
- consulta de disponibilidade com filtros opcionais;
- cache de disponibilidade em Redis (cache-aside, TTL 30s + jitter, invalidação pós-commit de booking/cancelamento, fail-open — DD-20);
- consulta de agendamento por ID;
- criação de agendamento (idempotente);
- cancelamento de agendamento (idempotente);
- idempotência completa dos comandos de escrita;
- health check de readiness do n8n (`GET /health/n8n`);
- CORS configurável para origens do browser (`API_CORS_ORIGINS`);
- PostgreSQL com migrations e seeds versionadas;
- persistência SQL tipada gerada via sqlc;
- documentação OpenAPI gerada automaticamente pelo FastAPI;
- coleção Postman derivável do `/openapi.json`.

### Implementado na aplicação web

- SPA React + TypeScript + Vite em `apps/web` (spec: [web-application.md](./web-application.md));
- seleção de paciente com carga via `GET /v1/patients` (WEB-RF-01);
- cadastro de paciente pelo modal **Novo paciente** via `POST /v1/patients`, com `409` amigável e recarga da lista (WEB-RF-01);
- chat textual e de áudio com o webhook do n8n, usando o UUID do paciente como `sessionId` e enviando também `patientId`, `patientName`, `patientEmail` e `patientPhone` (WEB-RF-02…05);
- histórico de agendamentos em painel somente leitura via `GET /v1/patients/{patient_id}/appointments` (WEB-RF-06);
- re-fetch do histórico após cada turno concluído e após troca de paciente (WEB-RF-07);
- isolamento de estado entre pacientes, com abort/ignorância de respostas fora de contexto (WEB-RF-08);
- estados assíncronos explícitos (carregamento, gravação, erro, histórico possivelmente desatualizado);
- testes unitários com Vitest + React Testing Library;
- container Docker (nginx) publicado pelo serviço `web` do Compose.

### Infraestrutura Compose

- serviços `postgres`, `migrate`, `redis`, `api`, `n8n` e `web` com healthchecks e ordem de dependência;
- volume de dados do n8n (`.docker/n8n/n8n_data`) versionado fora do git.

### Planejado / próxima etapa

- confirmação de contratos browser-facing do workflow n8n (webhook de produção, formato de resposta);
- confirmação por Gmail;
- resposta por TTS quando aplicável;
- correlação de logs entre n8n e API.

O status acima deve ser atualizado conforme o projeto evoluir.
