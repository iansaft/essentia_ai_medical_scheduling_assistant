# Documentação Técnica — Essentia AI Medical Scheduling Assistant

Esta pasta concentra as principais decisões de produto, domínio e engenharia do projeto. O objetivo é permitir uma leitura rápida do desenho do sistema sem exigir a análise completa do código-fonte.

## Índice

| Documento | Conteúdo |
|---|---|
| [system-requirements.md](./system-requirements.md) | Escopo, requisitos funcionais, requisitos não funcionais e estado atual |
| [business-rules.md](./business-rules.md) | Regras de negócio de pacientes, catálogo, disponibilidade, agendamento e cancelamento |
| [architecture.md](./architecture.md) | Arquitetura, responsabilidades por componente, fluxos e boundaries |
| [data-model.md](./data-model.md) | Modelo relacional, invariantes e constraints relevantes |
| [design-decisions.md](./design-decisions.md) | Decisões arquiteturais, trade-offs e alternativas evitadas |
| [testing-and-operations.md](./testing-and-operations.md) | Estratégia de testes, OpenAPI/Postman, observabilidade e operação local |

## Visão resumida

O sistema é um assistente de agendamento médico com interface conversacional orquestrada por **n8n** e uma API **FastAPI** responsável pelas operações determinísticas do domínio. O **PostgreSQL** mantém a fonte de verdade transacional e também reforça invariantes críticas de consistência.

Princípio central:

> O modelo de IA interpreta intenção e linguagem natural; o workflow orquestra integrações; a API governa regras de negócio; o banco garante invariantes finais de consistência.

## Estado atual

### Implementado na API

- health check;
- consulta de paciente por ID;
- listagem e consulta de serviços;
- consulta de métodos de pagamento por serviço;
- consulta de disponibilidade com filtros opcionais;
- PostgreSQL com migrations e seeds versionadas;
- persistência SQL tipada gerada via sqlc;
- documentação OpenAPI gerada automaticamente pelo FastAPI;
- coleção Postman derivável do OpenAPI.

### Planejado / próxima etapa

- criação de agendamento;
- cancelamento de agendamento;
- idempotência completa dos comandos de escrita;
- integração n8n;
- AI Agent com tool/function calling;
- entrada de texto e áudio com STT;
- confirmação por Gmail;
- resposta por TTS quando aplicável;
- correlação de logs entre n8n e API.

O status acima deve ser atualizado conforme o projeto evoluir.
