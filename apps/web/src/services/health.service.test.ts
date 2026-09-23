import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { env } from "../lib/env";
import { checkApiHealth, checkN8nHealth, n8nHealthUrl } from "./health.service";

describe("health.service", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("n8nHealthUrl aponta para o proxy da API", () => {
    expect(n8nHealthUrl()).toBe(`${env.apiBaseUrl}/health/n8n`);
  });

  it("checkApiHealth faz GET em /health da API", async () => {
    fetchMock.mockImplementationOnce(() => Promise.resolve({ ok: true }));

    await expect(checkApiHealth()).resolves.toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      `${env.apiBaseUrl}/health`,
      expect.objectContaining({
        method: "GET",
        cache: "no-store",
      }),
    );
  });

  it("checkN8nHealth faz GET no proxy /health/n8n da API", async () => {
    fetchMock.mockImplementationOnce(() => Promise.resolve({ ok: true }));

    await expect(checkN8nHealth()).resolves.toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      `${env.apiBaseUrl}/health/n8n`,
      expect.objectContaining({
        method: "GET",
        cache: "no-store",
      }),
    );
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("5678"),
      expect.anything(),
    );
  });

  it("retorna false quando a resposta não é ok", async () => {
    fetchMock.mockImplementationOnce(() => Promise.resolve({ ok: false }));

    await expect(checkN8nHealth()).resolves.toBe(false);
  });

  it("retorna false quando o fetch rejeita", async () => {
    fetchMock.mockImplementationOnce(() =>
      Promise.reject(new TypeError("Failed to fetch")),
    );

    await expect(checkN8nHealth()).resolves.toBe(false);
  });
});
