import { ChevronDown, Plus, UserRound } from "lucide-react";
import type { Patient } from "../../types/domain";

type PatientSelectorProps = {
  patients: Patient[];
  selectedPatientId: string | null;
  isLoading: boolean;
  error: string | null;
  onChange: (patientId: string) => void;
  onCreate: () => void;
};

export function PatientSelector({
  patients,
  selectedPatientId,
  isLoading,
  error,
  onChange,
  onCreate,
}: PatientSelectorProps) {
  return (
    <section
      aria-labelledby="patient-selector-title"
      className="rounded-sm border border-line bg-raised p-4 shadow-sm"
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <UserRound
            aria-hidden="true"
            className="size-4 shrink-0 text-brand-dark"
          />
          <h2
            id="patient-selector-title"
            className="text-sm font-semibold text-ink"
          >
            Paciente
          </h2>
        </div>

        <button
          aria-label="Novo paciente"
          className="flex shrink-0 items-center gap-1.5 rounded-sm bg-brand-dark px-2.5 py-1.5 text-xs font-medium text-ink-inverse transition hover:bg-brand-press focus-visible:outline-2 focus-visible:outline-brand focus-visible:outline-offset-2"
          onClick={onCreate}
          type="button"
        >
          <Plus aria-hidden="true" className="size-3.5" />
          Novo paciente
        </button>
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
