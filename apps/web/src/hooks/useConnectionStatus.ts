import { useEffect, useState } from "react";
import type { ConnectionStatus } from "../lib/connection";
import { checkApiHealth, checkN8nHealth } from "../services/health.service";
import { useOnlineStatus } from "./useOnlineStatus";

const PROBE_INTERVAL_MS = 15_000;

export function useConnectionStatus(): ConnectionStatus {
  const isBrowserOnline = useOnlineStatus();
  const [servicesOk, setServicesOk] = useState<boolean | null>(null);

  useEffect(() => {
    if (!isBrowserOnline) {
      setServicesOk(null);
      return;
    }

    let cancelled = false;

    async function probe() {
      const [apiOk, n8nOk] = await Promise.all([
        checkApiHealth(),
        checkN8nHealth(),
      ]);

      if (!cancelled) {
        setServicesOk(apiOk && n8nOk);
      }
    }

    void probe();
    const intervalId = setInterval(() => {
      void probe();
    }, PROBE_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [isBrowserOnline]);

  if (!isBrowserOnline) {
    return "browser_offline";
  }

  if (servicesOk === false) {
    return "server_unavailable";
  }

  return "online";
}
