import type { ZodType } from "zod";

export class HttpError extends Error {
  readonly status: number;
  readonly responseBody: string;

  constructor(message: string, status: number, responseBody: string) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.responseBody = responseBody;
  }
}

export async function requestJson<T>(
  url: string,
  schema: ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(url, init);

  if (!response.ok) {
    const responseBody = await response.text().catch(() => "");
    throw new HttpError(
      `Request falhou com HTTP ${response.status}.`,
      response.status,
      responseBody,
    );
  }

  const payload: unknown = await response.json();
  return schema.parse(payload);
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

export function toErrorMessage(error: unknown): string {
  if (error instanceof HttpError) {
    const body = error.responseBody.trim().slice(0, 240);
    return body
      ? `HTTP ${error.status}: ${body}`
      : `Falha HTTP ${error.status}.`;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Ocorreu um erro inesperado.";
}
