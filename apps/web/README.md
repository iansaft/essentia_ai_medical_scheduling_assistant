# Essentia AI Web

Cliente web conversacional para o assistente de agendamento médico Essentia AI.

A aplicação é uma *Single Page Application* leve construída com React, TypeScript e Vite. Sua responsabilidade é limitada à interface conversacional do usuário e à comunicação com o fluxo de trabalho de chat do n8n.

## Responsabilidades

A aplicação web é responsável por:

* Selecionar o paciente da demonstração (`GET /v1/patients`), com seleção automática do primeiro ativo;
* Exibir a conversa entre o usuário e o assistente de IA;
* Enviar mensagens de texto para o *n8n Chat Trigger*, usando o UUID do paciente como `sessionId`;
* Gravar áudio através do microfone do navegador;
* Enviar o áudio gravado para o n8n para processamento de *speech-to-text* (fala para texto);
* Exibir o histórico de agendamentos do paciente (`GET /v1/patients/{patient_id}/appointments`) em painel somente leitura;
* Re-consultar o histórico após cada turno concluído e após trocar de paciente;
* Isolar conversa e estado entre pacientes (requests do paciente anterior são abortados/ignorados);
* Manter o identificador da sessão conversacional no navegador;
* Apresentar estados de carregamento, gravação, erro e histórico possivelmente desatualizado.

Regras de negócio, consistência de agendamento médico e persistência não pertencem ao *frontend*.

A orquestração conversacional é tratada pelo n8n, enquanto as operações determinísticas de negócio são tratadas pela aplicação FastAPI e pelo PostgreSQL. A spec completa está em [`docs/web-application.md`](../../docs/web-application.md).

## Stack

* React
* TypeScript
* Vite
* Tailwind CSS
* Zod
* Lucide React
* Vitest
* React Testing Library
* Biome

O *bundle* de produção é servido pelo Nginx.

## Requisitos

* Node.js 24 LTS e npm são recomendados para desenvolvimento local.
* O Docker pode ser usado para compilar e executar a versão de produção sem instalar o *runtime* do *frontend* diretamente no hospedeiro (*host*).

## Ambiente

O *frontend* utiliza o arquivo `.env` localizado na raiz do repositório.

Variáveis obrigatórias:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_N8N_CHAT_WEBHOOK_URL=http://localhost:5678/webhook-test/essentia-ia-assistent

```

Variáveis prefixadas com `VITE_` são embutidas no *bundle* do cliente e nunca devem conter segredos/credenciais.

A credencial da API da Mistral e outras credenciais privadas devem permanecer dentro do n8n e não podem ser expostas ao navegador.

## Desenvolvimento local

Instale as dependências:

```bash
npm install

```

Inicie o servidor de desenvolvimento do Vite:

```bash
npm run dev

```

A aplicação estará disponível em:

`http://localhost:5173`

O *n8n Chat Trigger* deve permitir esta origem durante o desenvolvimento local.

### Via Makefile (raiz do repositório)

```bash
make web-deps-sync   # npm ci
make web-dev          # servidor de desenvolvimento (:5173)
make web-test         # suíte Vitest
make web-typecheck    # tsc --noEmit
make web-lint         # biome check
make web-build        # build de produção
make web-preview      # preview do build (:4173)
make web-check        # typecheck + testes
```

## Build de produção

Gere os ativos estáticos com:

```bash
npm run build

```

Os arquivos gerados são gravados em:

`dist/`

Visualize o *build* de produção localmente com:

```bash
npm run preview

```

## Docker

A partir da raiz do repositório, construa e inicie a aplicação web com:

```bash
docker compose up -d --build web

```

A aplicação estará disponível em:

`http://localhost:8080`

O contêiner expõe um *endpoint* de verificação de saúde (*health*):

`GET /health`

Exemplo:

```bash
curl http://localhost:8080/health

```

Resposta esperada:

```text
ok

```

## Arquitetura

O *frontend* intencionalmente não contém nenhuma regra de negócio de agendamento.

O modelo de IA é responsável pela interpretação conversacional e seleção de ferramentas. O n8n gerencia a orquestração, enquanto o FastAPI e o PostgreSQL permanecem como a fonte determinística da verdade para as operações de agendamento.

## Segurança

* Nenhuma chave de API de provedor de LLM é exposta ao *frontend*.
* O navegador se comunica com o *endpoint* conversacional do n8n (conversa) e com a FastAPI (leituras: pacientes, agendamentos, health) — nunca com o PostgreSQL nem com providers de IA.
* Todas as credenciais de provedores devem ser configuradas usando os *n8n Credentials* ou variáveis de ambiente no lado do servidor.
* Não coloque segredos em variáveis prefixadas com `VITE_`.