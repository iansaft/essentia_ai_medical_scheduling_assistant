export type ConnectionStatus =
  | "online"
  | "browser_offline"
  | "server_unavailable";

export const connectionStatusMeta: Record<
  ConnectionStatus,
  {
    tooltip: string;
    tone: "success" | "warning" | "danger";
  }
> = {
  online: {
    tooltip: "Conexão estável com o servidor",
    tone: "success",
  },
  browser_offline: {
    tooltip: "Falha de conexão com o servidor",
    tone: "warning",
  },
  server_unavailable: {
    tooltip: "Servidor fora do ar",
    tone: "danger",
  },
};
