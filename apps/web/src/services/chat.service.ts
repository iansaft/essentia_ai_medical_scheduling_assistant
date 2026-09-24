import { env } from "../lib/env";
import { HttpError } from "../lib/http";
import { n8nReplySchema } from "../schemas/chat.schemas";
import type { AssistantReply, Patient } from "../types/domain";

type N8nReply = ReturnType<typeof n8nReplySchema.parse>;

function normalizeReply(payload: N8nReply): AssistantReply {
  const item = Array.isArray(payload) ? payload[0] : payload;

  if ("message" in item) {
    return {
      message: item.message,
      audio: item.audio ?? null,
    };
  }

  if ("output" in item) {
    return {
      message: item.output,
      audio: item.audio ?? null,
    };
  }

  return {
    message: item.text,
    audio: item.audio ?? null,
  };
}

async function parseN8nResponse(response: Response): Promise<AssistantReply> {
  if (!response.ok) {
    const responseBody = await response.text().catch(() => "");
    throw new HttpError(
      `n8n respondeu com HTTP ${response.status}.`,
      response.status,
      responseBody,
    );
  }

  const rawBody = await response.text().catch(() => "");
  let payload: unknown;

  try {
    payload = JSON.parse(rawBody);
  } catch {
    throw new HttpError(
      "n8n retornou corpo que não é JSON válido.",
      response.status,
      rawBody,
    );
  }

  try {
    return normalizeReply(n8nReplySchema.parse(payload));
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new HttpError(
      `Resposta do n8n fora do contrato esperado: ${detail}`,
      response.status,
      rawBody,
    );
  }
}

/**
 * Contrato isolado do Chat Trigger.
 *
 * Nesta versão:
 * - patient.id é reutilizado como sessionId;
 * - o request permanece aberto até o workflow terminar;
 * - o adapter aceita respostas { message }, { output } ou { text } para
 *   facilitar o alinhamento final com o workflow n8n.
 */
export async function sendTextMessage(
  patient: Patient,
  chatInput: string,
  signal?: AbortSignal,
): Promise<AssistantReply> {
  const response = await fetch(env.n8nChatWebhookUrl, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      action: "sendMessage",
      sessionId: patient.id,
      patientId: patient.id,
      patientName: patient.name,
      patientEmail: patient.email,
      patientPhone: patient.phone ?? "",
      chatInput,
    }),
    signal,
  });

  return parseN8nResponse(response);
}

export async function sendAudioMessage(
  patient: Patient,
  audio: Blob,
  signal?: AbortSignal,
): Promise<AssistantReply> {
  const body = new FormData();

  body.append("action", "sendMessage");
  body.append("sessionId", patient.id);
  body.append("patientId", patient.id);
  body.append("patientName", patient.name);
  body.append("patientEmail", patient.email);
  body.append("patientPhone", patient.phone ?? "");
  body.append("messageType", "audio");
  body.append("audio", audio, audioFilename(audio.type));

  const response = await fetch(env.n8nChatWebhookUrl, {
    method: "POST",
    headers: {
      Accept: "application/json",
    },
    body,
    signal,
  });

  return parseN8nResponse(response);
}

function audioFilename(mimeType: string): string {
  if (mimeType.includes("ogg")) {
    return "recording.ogg";
  }

  if (mimeType.includes("mp4")) {
    return "recording.m4a";
  }

  return "recording.webm";
}
