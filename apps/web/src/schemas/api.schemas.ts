import { z } from "zod";

export const patientWireSchema = z.object({
  id: z.uuid(),
  full_name: z.string().min(1),
  email: z.email(),
  is_active: z.boolean(),
});

const patientsListSchema = z.array(patientWireSchema);

export const patientsResponseSchema = z.union([
  patientsListSchema,
  z.object({ items: patientsListSchema }),
]);

const appointmentStatusSchema = z.enum([
  "scheduled",
  "cancelled",
  "completed",
  "no_show",
]);

const nullableString = z.string().nullable().optional();

export const appointmentWireSchema = z.object({
  id: z.uuid(),
  starts_at: z.string().min(1),
  ends_at: nullableString,
  service_name: z.string().min(1),
  doctor_name: z.string().min(1),
  status: appointmentStatusSchema,
  price_amount: z.union([z.number(), z.string()]).nullable().optional(),
  currency: nullableString,
  cancellation_reason: nullableString,
});

const appointmentsListSchema = z.array(appointmentWireSchema);

export const appointmentsResponseSchema = z.union([
  appointmentsListSchema,
  z.object({ items: appointmentsListSchema }),
]);
