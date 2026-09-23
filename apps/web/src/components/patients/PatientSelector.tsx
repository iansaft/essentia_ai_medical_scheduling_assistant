import { ChevronDown, UserRound } from "lucide-react";
import type { Patient } from "../../types/domain";

type PatientSelectorProps = {
  patients: Patient[];
  selectedPatientId: string | null;
  isLoading: boolean;
  error: string | null;
  onChange: (patientId: string) => void;
};

export function PatientSelector({
  patients,
  selectedPatientId,
  isLoading,
  error,
  onChange,
}: PatientSelectorProps) {
  return (
    <section
      aria-labelledby="patient-selector-title"
      className="rounded-sm border border-line bg-raised p-4 shadow-sm"
    >
      <div className="mb-3 flex items-center gap-2">
        <UserRound aria-hidden="true" className="size-4 text-brand-dark" />
        <h2
          id="patient-selector-title"
          className="text-sm font-semibold text-ink"
        >
          Paciente
        </h2>
      </div>

      <div className="relative">
        <label className="sr-only" htmlFor="patient-selector">
          Selecionar paciente
        </label>

        <select
          id="patient-selector"
          className="w-full appearance-none rounded-sm border border-line-strong bg-raised px-3 py-2.5 pr-10 text-sm text-ink outline-none transition focus:border-brand focus:ring-2 focus:ring-brand-light/60 disabled:cursor-not-allowed disabled:bg-canvas"
          disabled={isLoading || patients.length === 0}
          onChange={(event) => onChange(event.target.value)}
          value={selectedPatientId ?? ""}
        >
          {isLoading && <option value="">Carregando pacientes...</option>}

          {!isLoading && patients.length === 0 && (
            <option value="">Nenhum paciente disponível</option>
          )}

          {!isLoading &&
            patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.name}
                {patient.isActive ? "" : " (inativo)"}
              </option>
            ))}
        </select>

        <ChevronDown
          aria-hidden="true"
          className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-ink-muted"
        />
      </div>

      {error && (
        <p className="mt-2 text-xs leading-5 text-danger" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
