import { LoaderCircle, Mic, Send, Square, Trash2 } from "lucide-react";
import { useRef, useState } from "react";
import { useAudioRecorder } from "../../hooks/useAudioRecorder";
import { formatAudioDuration } from "../../lib/format";

type MessageComposerProps = {
  disabled: boolean;
  isSending: boolean;
  onSendText: (message: string) => Promise<void>;
  onSendAudio: (audio: Blob) => Promise<void>;
};

type ComposerMode = "text" | "record";

type ActionVariant = "record" | "preparing" | "stop" | "discard";

const actionLabels: Record<ActionVariant, string> = {
  record: "Gravar áudio",
  preparing: "Parar gravação",
  stop: "Parar gravação",
  discard: "Descartar áudio",
};

const actionTooltips: Record<ActionVariant, string> = {
  record: "Gravar mensagem de voz",
  preparing: "Finalizar gravação",
  stop: "Finalizar gravação",
  discard: "Descartar mensagem de voz",
};

const actionClassNames: Record<ActionVariant, string> = {
  record:
    "border border-line-strong bg-raised text-ink-muted transition hover:bg-canvas focus-visible:outline-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-40",
  preparing:
    "border border-info bg-info-soft text-info transition focus-visible:outline-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-60",
  stop: "border border-info bg-info-soft text-info transition hover:bg-info hover:text-ink-inverse focus-visible:outline-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-60",
  discard:
    "border border-danger bg-danger-soft text-danger transition hover:bg-danger hover:text-ink-inverse focus-visible:outline-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-40",
};

export function MessageComposer({
  disabled,
  isSending,
  onSendText,
  onSendAudio,
}: MessageComposerProps) {
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState<ComposerMode>("text");
  const [pendingBlob, setPendingBlob] = useState<Blob | null>(null);
  const [recorderError, setRecorderError] = useState<string | null>(null);
  const discardRef = useRef(false);

  const {
    isRecording,
    recordingTime,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useAudioRecorder({
    onComplete: (blob) => {
      if (discardRef.current) {
        return;
      }

      if (blob.size === 0) {
        setRecorderError("Não foi possível capturar o áudio. Tente novamente.");
        setPendingBlob(null);
        setMode("text");
        return;
      }

      setPendingBlob(blob);
    },
    onError: (error) => {
      setRecorderError(
        error.name === "NotAllowedError"
          ? "Permissão de microfone negada."
          : error.name === "NotSupportedError"
            ? "Gravação de áudio não suportada neste navegador."
            : "Não foi possível iniciar a gravação.",
      );
      setPendingBlob(null);
      setMode("text");
    },
  });

  const canSendText =
    mode === "text" && !disabled && !isSending && message.trim().length > 0;

  const canSendAudio =
    mode === "record" &&
    Boolean(pendingBlob) &&
    !disabled &&
    !isSending &&
    !isRecording;

  const actionVariant: ActionVariant =
    mode === "text"
      ? "record"
      : pendingBlob
        ? "discard"
        : isRecording
          ? "stop"
          : "preparing";

  async function handleSubmit() {
    const normalizedMessage = message.trim();

    if (!normalizedMessage || !canSendText) {
      return;
    }

    setMessage("");
    await onSendText(normalizedMessage);
  }

  async function handleSendAudio() {
    if (!pendingBlob || !canSendAudio) {
      return;
    }

    const audio = pendingBlob;
    discardRef.current = true;
    setPendingBlob(null);
    setMode("text");
    setRecorderError(null);
    await onSendAudio(audio);
  }

  function enterRecordMode() {
    if (disabled || isSending) {
      return;
    }

    discardRef.current = false;
    setPendingBlob(null);
    setRecorderError(null);
    setMode("record");
    void startRecording();
  }

  function handleDiscard() {
    discardRef.current = true;
    setPendingBlob(null);
    setRecorderError(null);
    cancelRecording();
    setMode("text");
  }

  function handleActionClick() {
    if (actionVariant === "record") {
      enterRecordMode();
      return;
    }

    if (actionVariant === "stop") {
      stopRecording();
      return;
    }

    if (actionVariant === "discard") {
      handleDiscard();
    }
  }

  const actionDisabled =
    actionVariant === "record"
      ? disabled || isSending
      : actionVariant === "preparing"
        ? true
        : actionVariant === "discard"
          ? isSending
          : false;

  const sendTooltip = mode === "record" ? "Enviar áudio" : "Enviar mensagem";

  return (
    <div className="border-t border-line bg-raised p-4">
      {recorderError && (
        <p className="mb-2 text-xs text-danger" role="alert">
          {recorderError}
        </p>
      )}

      <div className="flex items-end gap-2">
        {mode === "text" ? (
          <textarea
            aria-label="Mensagem para o assistente"
            className="max-h-40 min-h-11 flex-1 resize-none rounded-sm border border-line-strong bg-raised px-3 py-2.5 text-sm leading-5 text-ink outline-none transition placeholder:text-ink-faint focus:border-brand focus:ring-2 focus:ring-brand-light/60 disabled:cursor-not-allowed disabled:bg-canvas"
            disabled={disabled || isSending}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void handleSubmit();
              }
            }}
            placeholder={
              disabled
                ? "Selecione um paciente para iniciar."
                : "Digite sua mensagem..."
            }
            rows={1}
            value={message}
          />
        ) : (
          <div className="flex min-h-11 min-w-0 flex-1 items-center gap-3 rounded-sm border border-line-strong bg-raised px-3">
            {pendingBlob ? (
              <>
                <span
                  aria-hidden="true"
                  className="size-2 shrink-0 rounded-full bg-brand"
                />
                <span className="min-w-0 flex-1 truncate text-sm text-ink-muted">
                  Áudio pronto para envio
                </span>
              </>
            ) : (
              <>
                <span
                  aria-hidden="true"
                  className={`size-2 shrink-0 rounded-full bg-danger ${
                    isRecording ? "essentia-record-pulse" : ""
                  }`}
                />
                <span
                  aria-hidden="true"
                  className="shrink-0 font-mono text-sm tabular-nums text-ink"
                >
                  {formatAudioDuration(recordingTime)}
                </span>
                <span className="min-w-0 flex-1 truncate text-sm text-ink-muted">
                  {isRecording ? "Gravando áudio" : "Preparando gravação…"}
                </span>
              </>
            )}
          </div>
        )}

        <div className="group relative">
          <button
            aria-describedby="composer-action-tooltip"
            aria-label={actionLabels[actionVariant]}
            className={`flex size-11 shrink-0 items-center justify-center rounded-sm ${actionClassNames[actionVariant]}`}
            disabled={actionDisabled}
            onClick={handleActionClick}
            title={actionTooltips[actionVariant]}
            type="button"
          >
            {actionVariant === "record" ? (
              <Mic aria-hidden="true" className="size-5" />
            ) : actionVariant === "discard" ? (
              <Trash2 aria-hidden="true" className="size-5" />
            ) : (
              <Square aria-hidden="true" className="size-3 fill-current" />
            )}
          </button>

          <span
            className="essentia-tooltip"
            id="composer-action-tooltip"
            role="tooltip"
          >
            {actionTooltips[actionVariant]}
          </span>
        </div>

        <div className="group relative">
          <button
            aria-describedby="composer-send-tooltip"
            aria-label={mode === "record" ? "Enviar áudio" : "Enviar mensagem"}
            className="flex size-11 shrink-0 items-center justify-center rounded-sm bg-brand-dark text-ink-inverse transition hover:bg-brand-press focus-visible:outline-2 focus-visible:outline-brand focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-40"
            disabled={mode === "record" ? !canSendAudio : !canSendText}
            onClick={() => {
              if (mode === "record") {
                void handleSendAudio();
                return;
              }
              void handleSubmit();
            }}
            title={sendTooltip}
            type="button"
          >
            {isSending ? (
              <LoaderCircle
                aria-hidden="true"
                className="size-5 animate-spin"
              />
            ) : (
              <Send aria-hidden="true" className="size-5" />
            )}
          </button>

          <span
            className="essentia-tooltip"
            id="composer-send-tooltip"
            role="tooltip"
          >
            {sendTooltip}
          </span>
        </div>
      </div>

      <p className="mt-2 text-[11px] leading-4 text-ink-faint">
        {mode === "record"
          ? isRecording
            ? "Gravando. Pare a gravação para habilitar o envio."
            : pendingBlob
              ? "Envie ou descarte o áudio."
              : "Preparando o microfone…"
          : "Enter envia. Shift + Enter cria uma nova linha."}
      </p>
    </div>
  );
}
