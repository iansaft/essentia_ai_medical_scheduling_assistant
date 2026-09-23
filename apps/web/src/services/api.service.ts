import { env } from "../lib/env";
import { requestJson } from "../lib/http";
import {
  appointmentsResponseSchema,
  patientsResponseSchema,
} from "../schemas/api.schemas";
import type { Appointment, Patient } from "../types/domain";

function unwrapItems<T>(value: T[] | { items: T[] }): T[] {
  return Array.isArray(value) ? value : value.items;
}

export async function listPatients(signal?: AbortSignal): Promise<Patient[]> {
  const payload = await requestJson(
    `${env.apiBaseUrl}/v1/patients`,
    patientsResponseSchema,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal,
    },
  );

  return unwrapItems(payload).map((patient) => ({
    id: patient.id,
    name: patient.full_name,
    email: patient.email,
    isActive: patient.is_active,
  }));
}

export async function listPatientAppointments(
  patientId: string,
  signal?: AbortSignal,
): Promise<Appointment[]> {
  const payload = await requestJson(
    `${env.apiBaseUrl}/v1/patients/${encodeURIComponent(patientId)}/appointments`,
    appointmentsResponseSchema,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal,
    },
  );

  return unwrapItems(payload).map((appointment) => ({
    id: appointment.id,
    startsAt: appointment.starts_at,
    endsAt: appointment.ends_at ?? null,
    serviceName: appointment.service_name,
    doctorName: appointment.doctor_name,
    status: appointment.status,
    priceAmount:
      appointment.price_amount === undefined ||
      appointment.price_amount === null
        ? null
        : Number(appointment.price_amount),
    currency: appointment.currency ?? null,
    cancellationReason: appointment.cancellation_reason ?? null,
  }));
}
