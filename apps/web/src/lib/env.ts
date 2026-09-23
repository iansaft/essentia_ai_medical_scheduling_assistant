import { z } from "zod";

const envSchema = z.object({
  VITE_API_BASE_URL: z.url(),
  VITE_N8N_CHAT_WEBHOOK_URL: z.url(),
});

const parsedEnv = envSchema.safeParse(import.meta.env);

if (!parsedEnv.success) {
  console.error(
    "Configuração inválida do frontend:",
    parsedEnv.error.flatten(),
  );
  throw new Error(
    "Variáveis de ambiente inválidas. Verifique VITE_API_BASE_URL e VITE_N8N_CHAT_WEBHOOK_URL.",
  );
}

function withoutTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

export const env = {
  apiBaseUrl: withoutTrailingSlash(parsedEnv.data.VITE_API_BASE_URL),
  n8nChatWebhookUrl: parsedEnv.data.VITE_N8N_CHAT_WEBHOOK_URL,
} as const;
