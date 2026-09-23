import { env } from "../lib/env";

async function probe(url: string, signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(url, {
      method: "GET",
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
      signal,
    });

    return response.ok;
  } catch {
    return false;
  }
}

export async function checkApiHealth(signal?: AbortSignal): Promise<boolean> {
  return probe(`${env.apiBaseUrl}/health`, signal);
}

export function n8nHealthUrl(): string {
  return `${env.apiBaseUrl}/health/n8n`;
}

export async function checkN8nHealth(signal?: AbortSignal): Promise<boolean> {
  return probe(n8nHealthUrl(), signal);
}
