import { LoaderCircle, X } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { z } from "zod";
import { HttpError, toErrorMessage } from "../../lib/http";
import { createPatient } from "../../services/api.service";
import type { Patient } from "../../types/domain";

type CreatePatientModalProps = {
  open: boolean;
  onClose: () => void;
  onCreated: (patient: Patient) => void;
};

type FieldErrors = {
  fullName?: string;
  email?: string;
  phone?: string;
};

const inputClassName =
  "w-full rounded-sm border border-line-strong bg-raised px-3 py-2.5 text-sm text-ink outline-none transition focus:border-brand focus:ring-2 focus:ring-brand-light/60 placeholder:text-ink-faint";

function friendlySubmitError(error: unknown): string {
  if (error instanceof HttpError && error.status === 409) {
    if (error.responseBody.includes("patient-email-already-exists")) {
      return "Este e-mail já está cadastrado.";
    }

    if (error.responseBody.includes("patient-phone-already-exists")) {
      return "Este telefone já está cadastrado.";
    }
  }

  return toErrorMessage(error);
}

function validate(fullName: string, email: string, phone: string): FieldErrors {
  const errors: FieldErrors = {};

  if (!fullName.trim()) {
    errors.fullName = "Informe o nome completo.";
  } else if (fullName.trim().length > 200) {
    errors.fullName = "O nome completo deve ter no máximo 200 caracteres.";
  }

  if (!email.trim()) {
    errors.email = "Informe o e-mail.";
  } else if (email.trim().length > 320) {
    errors.email = "O e-mail deve ter no máximo 320 caracteres.";
  } else if (!z.email().safeParse(email.trim()).success) {
    errors.email = "Informe um e-mail válido.";
  }

  if (phone.trim() && phone.trim().length > 32) {
    errors.phone = "O telefone deve ter no máximo 32 caracteres.";
  }

  return errors;
}

export function CreatePatientModal({
  open,
  onClose,
  onCreated,
}: CreatePatientModalProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const dialogRef = useRef<HTMLDivElement | null>(null);
  const fullNameRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    fullNameRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSubmitting) {
        event.stopPropagation();
        onClose();
        return;
      }

      if (event.key !== "Tab" || !dialogRef.current) {
        return;
      }

      const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), [href], select, textarea, [tabindex]:not([tabindex="-1"])',
      );

      if (focusable.length === 0) {
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;

      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown, true);
    return () => document.removeEventListener("keydown", handleKeyDown, true);
  }, [isSubmitting, onClose, open]);

  if (!open) {
    return null;
  }

  function resetForm() {
    setFullName("");
    setEmail("");
    setPhone("");
    setFieldErrors({});
    setSubmitError(null);
  }

  function handleRequestClose() {
    if (isSubmitting) {
      return;
    }

    resetForm();
    onClose();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    const errors = validate(fullName, email, phone);
    setFieldErrors(errors);
    setSubmitError(null);

    if (errors.fullName || errors.email || errors.phone) {
      return;
    }

    setIsSubmitting(true);

    try {
      const patient = await createPatient({
        fullName: fullName.trim(),
        email: email.trim(),
        phone: phone.trim() || null,
      });

      resetForm();
      onCreated(patient);
    } catch (error) {
      setSubmitError(friendlySubmitError(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return createPortal(
    // biome-ignore lint/a11y/noStaticElementInteractions: clique no scrim fecha o modal
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4 backdrop-blur-sm"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          handleRequestClose();
        }
      }}
      role="presentation"
    >
      <div
        aria-labelledby="create-patient-title"
        aria-modal="true"
        className="relative w-full max-w-md rounded-sm border border-line bg-raised p-4 shadow-sm"
        onMouseDown={(event) => event.stopPropagation()}
        ref={dialogRef}
        role="dialog"
      >
        <div className="mb-4 flex items-center justify-between gap-2">
          <h2
            className="text-sm font-semibold text-ink"
            id="create-patient-title"
          >
            Novo paciente
          </h2>

          <button
            aria-label="Fechar"
            className="flex size-8 shrink-0 items-center justify-center rounded-sm border border-line text-ink-muted transition hover:bg-canvas focus-visible:outline-2 focus-visible:outline-brand"
            disabled={isSubmitting}
            onClick={handleRequestClose}
            type="button"
          >
            <X aria-hidden="true" className="size-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          {submitError && (
            <p
              className="mb-3 rounded-sm border border-danger-line bg-danger-soft px-3 py-2 text-xs leading-5 text-danger"
              role="alert"
            >
              {submitError}
            </p>
          )}

          <div className="space-y-3">
            <div>
              <label
                className="mb-1 block text-xs font-medium text-ink"
                htmlFor="create-patient-full-name"
              >
                Nome completo
              </label>
              <input
                className={inputClassName}
                id="create-patient-full-name"
                maxLength={200}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Joana Souza"
                ref={fullNameRef}
                required
                type="text"
                value={fullName}
              />
              {fieldErrors.fullName && (
                <p className="mt-1 text-xs text-danger" role="alert">
                  {fieldErrors.fullName}
                </p>
              )}
            </div>

            <div>
              <label
                className="mb-1 block text-xs font-medium text-ink"
                htmlFor="create-patient-email"
              >
                E-mail
              </label>
              <input
                className={inputClassName}
                id="create-patient-email"
                maxLength={320}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="joana.souza@example.com"
                required
                type="email"
                value={email}
              />
              {fieldErrors.email && (
                <p className="mt-1 text-xs text-danger" role="alert">
                  {fieldErrors.email}
                </p>
              )}
            </div>

            <div>
              <label
                className="mb-1 block text-xs font-medium text-ink"
                htmlFor="create-patient-phone"
              >
                Telefone (opcional)
              </label>
              <input
                className={inputClassName}
                id="create-patient-phone"
                maxLength={32}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="+5548999990009"
                type="tel"
                value={phone}
              />
              {fieldErrors.phone && (
                <p className="mt-1 text-xs text-danger" role="alert">
                  {fieldErrors.phone}
                </p>
              )}
            </div>
          </div>

          <div className="mt-5 flex justify-end gap-2">
            <button
              className="rounded-sm border border-line px-3 py-2 text-sm font-medium text-ink transition hover:bg-canvas focus-visible:outline-2 focus-visible:outline-brand disabled:opacity-40"
              disabled={isSubmitting}
              onClick={handleRequestClose}
              type="button"
            >
              Cancelar
            </button>
            <button
              className="flex items-center gap-1.5 rounded-sm bg-brand-dark px-3 py-2 text-sm font-medium text-ink-inverse transition hover:bg-brand-press focus-visible:outline-2 focus-visible:outline-brand focus-visible:outline-offset-2 disabled:opacity-40"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting && (
                <LoaderCircle
                  aria-hidden="true"
                  className="size-4 animate-spin"
                />
              )}
              Cadastrar
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body,
  );
}
