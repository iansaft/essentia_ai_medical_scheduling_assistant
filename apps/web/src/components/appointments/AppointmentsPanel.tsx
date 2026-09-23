import {
  CalendarDays,
  CircleAlert,
  LoaderCircle,
  RefreshCw,
} from "lucide-react";
import {
  appointmentStatusLabel,
  formatDateTime,
  formatMoney,
} from "../../lib/format";
import type { Appointment, Patient } from "../../types/domain";

type AppointmentsPanelProps = {
  patient: Patient | null;
  appointments: Appointment[];
  isLoading: boolean;
  isStale: boolean;
  error: string | null;
  onRefresh: () => void;
};

const statusClassNames: Record<Appointment["status"], string> = {
  scheduled: "bg-info-soft text-info",
  cancelled: "bg-danger-soft text-danger",
  completed: "bg-success-soft text-success",
  no_show: "bg-warning-soft text-warning",
};

export function AppointmentsPanel({
  patient,
  appointments,
  isLoading,
  isStale,
  error,
  onRefresh,
}: AppointmentsPanelProps) {
  return (
    <section
      aria-labelledby="appointments-title"
      className="overflow-hidden rounded-sm border border-line bg-raised shadow-sm"
    >
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <CalendarDays
            aria-hidden="true"
            className="size-4 shrink-0 text-brand-dark"
          />
          <div className="min-w-0">
            <h2
              id="appointments-title"
              className="truncate text-sm font-semibold text-ink"
            >
              Agendamentos
            </h2>
            <p className="truncate text-xs text-ink-muted">
              {patient ? patient.name : "Selecione um paciente"}
            </p>
          </div>
        </div>

        <button
          aria-label="Atualizar agendamentos"
          className="flex size-9 shrink-0 items-center justify-center rounded-sm border border-line text-ink-muted transition hover:bg-canvas focus-visible:outline-2 focus-visible:outline-brand disabled:opacity-40"
          disabled={!patient || isLoading}
          onClick={onRefresh}
          type="button"
        >
          {isLoading ? (
            <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />
          ) : (
            <RefreshCw aria-hidden="true" className="size-4" />
          )}
        </button>
      </div>

      {(error || isStale) && (
        <div
          className="flex gap-2 border-b border-warning-line bg-warning-soft px-4 py-3 text-xs leading-5 text-warning"
          role={error ? "alert" : undefined}
        >
          <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          <span>
            {error ??
              "Os dados exibidos podem estar desatualizados. Tente sincronizar novamente."}
          </span>
        </div>
      )}

      {!patient ? (
        <EmptyAppointments message="Selecione um paciente para consultar o histórico." />
      ) : isLoading && appointments.length === 0 ? (
        <div className="flex min-h-48 items-center justify-center text-sm text-ink-muted">
          <LoaderCircle
            aria-hidden="true"
            className="mr-2 size-4 animate-spin"
          />
          Carregando agendamentos...
        </div>
      ) : appointments.length === 0 ? (
        <EmptyAppointments message="Nenhum agendamento encontrado." />
      ) : (
        <div className="divide-y divide-line">
          {appointments.map((appointment) => {
            const price = formatMoney(
              appointment.priceAmount,
              appointment.currency,
            );

            return (
              <article className="p-4" key={appointment.id}>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-ink">
                      {appointment.serviceName}
                    </h3>
                    <p className="mt-0.5 text-xs text-ink-muted">
                      {appointment.doctorName}
                    </p>
                  </div>

                  <span
                    className={`rounded-sm px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] ${statusClassNames[appointment.status]}`}
                  >
                    {appointmentStatusLabel(appointment.status)}
                  </span>
                </div>

                <dl className="mt-3 grid gap-2 text-xs">
                  <div className="flex justify-between gap-4">
                    <dt className="text-ink-muted">Início</dt>
                    <dd className="text-right font-medium text-ink">
                      {formatDateTime(appointment.startsAt)}
                    </dd>
                  </div>

                  {appointment.endsAt && (
                    <div className="flex justify-between gap-4">
                      <dt className="text-ink-muted">Fim</dt>
                      <dd className="text-right font-medium text-ink">
                        {formatDateTime(appointment.endsAt)}
                      </dd>
                    </div>
                  )}

                  {price && (
                    <div className="flex justify-between gap-4">
                      <dt className="text-ink-muted">Valor</dt>
                      <dd className="text-right font-medium text-ink">
                        {price}
                      </dd>
                    </div>
                  )}
                </dl>

                {appointment.cancellationReason && (
                  <p className="mt-3 rounded-sm bg-canvas px-3 py-2 text-xs leading-5 text-ink-muted">
                    Motivo do cancelamento: {appointment.cancellationReason}
                  </p>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function EmptyAppointments({ message }: { message: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center px-6 text-center text-sm leading-6 text-ink-muted">
      {message}
    </div>
  );
}
