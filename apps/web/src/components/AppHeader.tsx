import { Activity, CloudOff, Wifi, WifiOff } from "lucide-react";
import { type ConnectionStatus, connectionStatusMeta } from "../lib/connection";

type AppHeaderProps = {
  status: ConnectionStatus;
};

const toneClassNames = {
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
} as const;

function StatusIcon({ status }: { status: ConnectionStatus }) {
  if (status === "online") {
    return <Wifi aria-hidden="true" className="size-4" />;
  }

  if (status === "browser_offline") {
    return <WifiOff aria-hidden="true" className="size-4" />;
  }

  return <CloudOff aria-hidden="true" className="size-4" />;
}

export function AppHeader({ status }: AppHeaderProps) {
  const meta = connectionStatusMeta[status];

  return (
    <header className="shrink-0 border-b border-brand/40 bg-surface/90 backdrop-blur">
      <div className="mx-auto flex min-h-16 max-w-[1600px] items-center justify-between gap-4 px-4 py-3 lg:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-sm bg-brand-dark text-ink-inverse">
            <Activity aria-hidden="true" className="size-5" />
          </div>

          <div className="min-w-0">
            <h1 className="truncate font-display text-sm font-semibold uppercase tracking-[0.2em] text-ink">
              Essentia AI
            </h1>
            <p className="mt-0.5 truncate text-xs text-ink-muted">
              Assistente de agendamento médico
            </p>
          </div>
        </div>

        <div className="group relative">
          <button
            aria-describedby="connection-status-tooltip"
            aria-label={meta.tooltip}
            className={`flex size-8 shrink-0 cursor-help items-center justify-center rounded-sm transition hover:bg-canvas focus-visible:outline-2 focus-visible:outline-brand ${toneClassNames[meta.tone]}`}
            title={meta.tooltip}
            type="button"
          >
            <StatusIcon status={status} />
          </button>

          <span
            className="essentia-tooltip"
            id="connection-status-tooltip"
            role="tooltip"
          >
            {meta.tooltip}
          </span>
        </div>
      </div>
    </header>
  );
}
