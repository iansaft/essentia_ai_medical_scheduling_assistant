import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { checkApiHealth, checkN8nHealth } from "../services/health.service";
import { useConnectionStatus } from "./useConnectionStatus";

vi.mock("../services/health.service", () => ({
  checkApiHealth: vi.fn(),
  checkN8nHealth: vi.fn(),
}));

function setNavigatorOnline(value: boolean) {
  Object.defineProperty(window.navigator, "onLine", {
    configurable: true,
    get: () => value,
  });
}

describe("useConnectionStatus", () => {
  const checkApiHealthMock = vi.mocked(checkApiHealth);
  const checkN8nHealthMock = vi.mocked(checkN8nHealth);

  beforeEach(() => {
    vi.clearAllMocks();
    setNavigatorOnline(true);
    checkApiHealthMock.mockResolvedValue(true);
    checkN8nHealthMock.mockResolvedValue(true);
  });

  it("retorna online quando rede, API e n8n respondem", async () => {
    const { result } = renderHook(() => useConnectionStatus());

    await waitFor(() => {
      expect(result.current).toBe("online");
    });

    expect(checkApiHealthMock).toHaveBeenCalled();
    expect(checkN8nHealthMock).toHaveBeenCalled();
  });

  it("retorna browser_offline quando o navegador está sem rede", () => {
    setNavigatorOnline(false);

    const { result } = renderHook(() => useConnectionStatus());

    expect(result.current).toBe("browser_offline");
    expect(checkApiHealthMock).not.toHaveBeenCalled();
  });

  it("retorna server_unavailable quando API ou n8n falham", async () => {
    checkApiHealthMock.mockResolvedValue(false);
    checkN8nHealthMock.mockResolvedValue(true);

    const { result } = renderHook(() => useConnectionStatus());

    await waitFor(() => {
      expect(result.current).toBe("server_unavailable");
    });
  });

  it("retorna server_unavailable quando só o n8n falha", async () => {
    checkApiHealthMock.mockResolvedValue(true);
    checkN8nHealthMock.mockResolvedValue(false);

    const { result } = renderHook(() => useConnectionStatus());

    await waitFor(() => {
      expect(result.current).toBe("server_unavailable");
    });
  });
});
