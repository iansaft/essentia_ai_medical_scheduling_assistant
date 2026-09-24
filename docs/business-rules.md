# Regras de Negócio

## 1. Pacientes

**BR-01.** Apenas pacientes cadastrados podem ser utilizados em um agendamento.

**BR-02.** Paciente inativo não pode criar novo agendamento.

**BR-03.** A consulta de paciente pode retornar dados cadastrais independentemente de existir agenda futura associada a ele.

**BR-37.** O cadastro de paciente (`POST /v1/patients`) é aberto (sem `X-Patient-Id`), exige `full_name` e `email` não vazios, aceita `phone` opcional e normaliza campos com trim antes de persistir.

**BR-38.** E-mail de paciente é único no sistema, sem distinção de caixa; telefone, quando informado, também é único. Violação retorna HTTP `409` com problem type `/problems/patient-email-already-exists` ou `/problems/patient-phone-already-exists`.

## 2. Médicos, especialidades e serviços

**BR-04.** Médicos e serviços possuem estado ativo/inativo.

**BR-05.** Um médico só pode possuir slots para serviços previamente associados a ele em `doctor_services`.

Essa regra é reforçada por FK composta entre `(doctor_id, service_id)` de `appointment_slots` e `doctor_services`.

**BR-06.** Especialidade e serviço são conceitos distintos. A especialidade descreve a área médica; o serviço representa a oferta comercial/agendável, com duração e preço.

**BR-07.** Formas de pagamento são configuradas por serviço em `service_payment_methods`.

## 3. Slots e disponibilidade

**BR-08.** O status do slot representa o estado administrativo da agenda, não a ocupação por paciente.

Estados definidos:

- `open` — potencialmente agendável;
- `blocked` — indisponível por bloqueio administrativo;
- `closed` — encerrado/histórico.

Não existe status `booked` no slot.

**BR-09.** Um slot é efetivamente disponível somente quando todas as condições abaixo são verdadeiras:

1. `appointment_slots.status = 'open'`;
2. `starts_at > CURRENT_TIMESTAMP`;
3. médico ativo;
4. serviço ativo;
5. não existe appointment `scheduled` para o mesmo `slot_id`.

**BR-10.** Um appointment cancelado não torna o slot administrativamente `closed`. Se o slot continua `open` e futuro, ele volta a ser efetivamente disponível.

**BR-11.** Slots do mesmo médico não podem possuir intervalos de tempo sobrepostos. Essa invariante é garantida no PostgreSQL por exclusion constraint com range temporal.

**BR-12.** Filtros de disponibilidade por médico, serviço e data são opcionais.

**BR-13.** O filtro por data interpreta `starts_at` na timezone de negócio `America/Sao_Paulo`.

## 4. Agendamento

**BR-14.** A criação de appointment deve ocorrer dentro de uma transação.

**BR-15.** O slot deve ser bloqueado para escrita (`FOR UPDATE`) durante a tentativa de agendamento.

**BR-16.** Antes de inserir o appointment, a aplicação deve validar:

- paciente existe e está ativo;
- slot existe;
- slot está `open`;
- slot está no futuro;
- médico está ativo;
- serviço está ativo;
- não existe outro appointment `scheduled` para o slot.

**BR-17.** O cliente não informa `doctor_id`, `service_id`, preço, moeda ou status do appointment no comando de booking. Esses valores são derivados a partir do slot e do catálogo persistido.

**BR-18.** O appointment registra snapshot de `price_amount` e `currency`. Mudanças futuras no preço do serviço não alteram o histórico do appointment.

**BR-19.** Apenas um appointment `scheduled` pode existir por slot. O PostgreSQL reforça essa regra por unique index parcial.

**BR-20.** Conflito de concorrência/double booking deve ser traduzido pela API para resposta HTTP `409 Conflict`.

## 5. Cancelamento

**BR-21.** Cancelamento é transição de estado, nunca exclusão física do appointment.

**BR-22.** Apenas appointment em estado `scheduled` pode ser cancelado pelo fluxo normal.

**BR-23.** O cancelamento registra pelo menos:

- `status = 'cancelled'`;
- `cancellation_reason`;
- `cancelled_at`.

**BR-24.** Appointment `completed`, `cancelled` ou `no_show` compõe histórico e não deve ser sobrescrito por um novo booking.

## 6. Estados de appointment

Estados atualmente modelados:

- `scheduled`;
- `cancelled`;
- `completed`;
- `no_show`.

O estado do appointment e o estado do slot são deliberadamente independentes.

## 7. Preço e pagamento

**BR-25.** O preço exibido antes do agendamento vem do serviço atual.

**BR-26.** O preço persistido no appointment é um snapshot do momento da confirmação.

**BR-27.** Métodos de pagamento disponíveis dependem do serviço selecionado.

**BR-28.** O sistema informa meios de pagamento, mas não processa transação financeira real neste escopo.

## 8. Idempotência

**BR-29.** Operações de leitura não exigem chave de idempotência.

**BR-30.** Operações mutáveis iniciadas pelo workflow, especialmente booking e cancellation, devem ser idempotentes.

**BR-31.** Uma mesma chave de idempotência não deve executar novamente a mesma operação quando a requisição for um replay válido.

**BR-32.** A mesma chave reutilizada com payload semanticamente diferente deve ser rejeitada para evitar ambiguidade.

## 9. Conversação e IA

**BR-33.** O LLM pode interpretar intenção, extrair entidades e formular linguagem natural, mas não decide se um slot está realmente disponível.

**BR-34.** Antes de booking ou cancellation, o workflow deve solicitar confirmação explícita do usuário.

**BR-35.** Após confirmação, o Agent chama uma tool determinística correspondente à operação; ele não grava diretamente no banco.

**BR-36.** Informações transacionais não devem ser recuperadas por RAG. Caso pgvector seja utilizado futuramente, seu uso deve ficar restrito a conhecimento não transacional, como FAQ e documentação.
