# Requisitos do Sistema

## 1. Objetivo

Construir um assistente de agendamento médico capaz de consultar informações administrativas e executar operações de agenda por meio de uma experiência conversacional. A solução deve integrar IA, workflows e uma API determinística sem delegar regras críticas de negócio ao modelo de linguagem.

## 2. Escopo funcional

### RF-01 — Consultar paciente

O sistema deve permitir recuperar os dados cadastrais necessários de um paciente conhecido pelo sistema.

### RF-02 — Consultar serviços médicos

O sistema deve listar serviços ativos e permitir consultar um serviço específico, incluindo preço, moeda e duração prevista.

### RF-03 — Consultar formas de pagamento

O sistema deve informar os métodos de pagamento aceitos para determinado serviço e, quando aplicável, o número máximo de parcelas e observações comerciais.

### RF-04 — Consultar disponibilidade

O sistema deve retornar apenas horários efetivamente disponíveis, permitindo filtros opcionais por médico, serviço e data.

Disponibilidade efetiva significa:

- slot com status `open`;
- horário futuro;
- médico ativo;
- serviço ativo;
- ausência de appointment com status `scheduled` para o slot.

A leitura pode ser servida por um cache descartável em Redis (cache-aside, DD-20): nesse caso a resposta pode refletir essas condições com atraso limitado ao TTL (30s + jitter até 10s) ou até a invalidação pós-commit do próximo booking/cancelamento. Booking e cancelamento sempre reavaliam contra o PostgreSQL.

### RF-05 — Criar agendamento

O sistema deve permitir agendar um paciente em um slot disponível.

O comando deve receber apenas os identificadores necessários, principalmente `patient_id` e `slot_id`. Preço, moeda, médico e serviço devem ser derivados no servidor.

### RF-06 — Cancelar agendamento

O sistema deve permitir cancelar um appointment atualmente `scheduled`, registrando motivo e horário do cancelamento sem apagar o histórico.

### RF-07 — Conversação em texto

O usuário deve poder solicitar informações e operações por linguagem natural em um canal conversacional processado pelo workflow n8n.

### RF-08 — Conversação por áudio

O workflow deve suportar entrada de áudio, realizar speech-to-text e encaminhar o texto normalizado para o mesmo fluxo de interpretação utilizado para mensagens textuais.

### RF-09 — Confirmação humana antes de operações mutáveis

Antes de criar ou cancelar um agendamento, a conversa deve apresentar os dados relevantes e obter confirmação explícita do usuário.

### RF-10 — Confirmação externa

Após operações relevantes, o workflow deve ser capaz de enviar confirmação por Gmail. Quando o canal suportar retorno em áudio, o workflow poderá gerar resposta por TTS.

### RF-11 — Saudação e encerramento

O fluxo conversacional deve oferecer mensagens adequadas de abertura e encerramento sem alterar regras transacionais da API.

### RF-12 — Experiência web (camada de apresentação)

A solução deve incluir uma aplicação web que permita selecionar o paciente da demonstração, conversar por texto/áudio com o n8n e consultar o histórico de agendamentos pela API, sem implementar regras de agendamento no browser.

Os requisitos detalhados da camada web (WEB-RF-01…08 e WEB-RNF-01…08) estão em [`web-application.md`](./web-application.md).

## 3. Requisitos não funcionais

### RNF-01 — Consistência transacional

Operações de agendamento devem ser transacionais e resistentes a concorrência. O banco deve impedir double booking mesmo que duas requisições concorrentes atravessem a camada de aplicação.

### RNF-02 — Idempotência

Comandos mutáveis disparados por workflows devem aceitar chave de idempotência para impedir efeitos duplicados decorrentes de retry, timeout ou reexecução no n8n.

### RNF-03 — Observabilidade

A solução deve produzir logs estruturados e propagar um correlation ID entre workflow e API. Erros de integração, domínio e persistência devem ser distinguíveis.

### RNF-04 — Determinismo do core

LLMs não devem ser a fonte de verdade para disponibilidade, preço, estado de agendamento ou outras regras transacionais. Essas decisões pertencem à API e ao PostgreSQL. O Redis é apenas um cache descartável e não autoritativo de leituras de disponibilidade (fail-open), nunca fonte de verdade.

### RNF-05 — Contrato HTTP documentado

A API deve expor OpenAPI por meio do FastAPI. A mesma especificação deve ser utilizável para Swagger e geração/importação da coleção Postman.

### RNF-06 — Reprodutibilidade local

O ambiente deve ser inicializável por Docker Compose, com migrations e seeds versionadas e independentes do estado manual da máquina do avaliador.

### RNF-07 — Segurança de dados

Credenciais e segredos não devem ser versionados. Configurações de runtime devem ser fornecidas via environment variables.

### RNF-08 — Manutenibilidade

SQL de schema, seeds, queries geradas, schemas HTTP e regras de aplicação devem permanecer em boundaries distintos. Arquivos gerados não devem ser editados manualmente.

### RNF-09 — Compatibilidade temporal

Datas e horários do domínio são armazenados como `TIMESTAMPTZ`. A data de negócio para consultas de agenda considera `America/Sao_Paulo`.

### RNF-10 — Testabilidade

As regras críticas devem poder ser exercitadas sem IA. A API e o banco precisam ser testáveis diretamente, deixando o n8n como uma camada de integração adicional.

## 4. Fora do escopo atual

Não foram definidos como requisitos centrais neste estágio:

- prontuário eletrônico;
- diagnóstico clínico;
- prescrição médica;
- processamento real de pagamento;
- billing/faturamento completo;
- autorização de convênio;
- autenticação/gestão completa de usuários finais.

## 5. Estado de implementação

O status de implementação é mantido em [docs/README.md — Estado atual](./README.md#estado-atual).
