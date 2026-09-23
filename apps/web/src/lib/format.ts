import type { AppointmentStatus } from "../types/domain";

const BUSINESS_TIMEZONE = "America/Sao_Paulo";

const dateTimeFormatter = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: BUSINESS_TIMEZONE,
});

export function formatDateTime(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);

  if (Number.isNaN(date.getTime())) {
    return typeof value === "string" ? value : "";
  }

  return dateTimeFormatter.format(date);
}

export function formatMoney(
  amount: number | null,
  currency: string | null,
): string | null {
  if (amount === null || currency === null) {
    return null;
  }

  try {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency,
    }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency}`;
  }
}

const statusLabels: Record<AppointmentStatus, string> = {
  scheduled: "Agendado",
  cancelled: "Cancelado",
  completed: "Concluído",
  no_show: "Não compareceu",
};

export function appointmentStatusLabel(status: AppointmentStatus): string {
  return statusLabels[status];
}

export function formatAudioDuration(totalSeconds: number): string {
  if (!Number.isFinite(totalSeconds) || totalSeconds < 0) {
    return "0:00";
  }

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);

  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}
