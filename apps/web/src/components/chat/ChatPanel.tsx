import { Bot, LoaderCircle, MessagesSquare } from "lucide-react";
import { useEffect, useRef } from "react";
import type {
  ChatMessage,
  ConversationStatus,
  Patient,
} from "../../types/domain";
import { MessageBubble } from "./MessageBubble";
import { MessageComposer } from "./MessageComposer";

type ChatPanelProps = {
  patient: Patient | null;
  messages: ChatMessage[];
  conversationStatus: ConversationStatus;
  error: string | null;
  onSendText: (message: string) => Promise<void>;
  onSendAudio: (audio: Blob) => Promise<void>;
};

export function ChatPanel({
  patient,
  messages,
  conversationStatus,
  error,
  onSendText,
  onSendAudio,
}: ChatPanelProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: Deps intencionais para reexecutar o auto-scroll a cada mensagem/status.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, conversationStatus]);

  return (
    <section
      aria-labelledby="chat-title"
      className="flex h-full min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-line bg-canvas shadow-sm"
    >
      <div className="flex shrink-0 items-center justify-between gap-3 border-b border-line bg-raised px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <MessagesSquare
            aria-hidden="true"
            className="size-4 shrink-0 text-brand-dark"
          />
          <div className="min-w-0">
            <h2
              id="chat-title"
              className="truncate text-sm font-semibold text-ink"
            >
              Conversa
            </h2>
            <p className="truncate text-xs text-ink-muted">
              {patient
                ? `${patient.name} · sessão ${patient.id.slice(0, 8)}…`
                : "Nenhum paciente selecionado"}
            </p>
          </div>
        </div>

        {conversationStatus === "sending" && (
          <span className="flex shrink-0 items-center gap-1.5 text-xs text-ink-muted">
            <LoaderCircle
              aria-hidden="true"
              className="size-3.5 animate-spin"
            />
            Processando
          </span>
        )}
      </div>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div
          aria-live="polite"
          className="essentia-chat-scroll flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto p-4 sm:p-5"
        >
          {messages.length === 0 ? (
            <div className="flex min-h-0 flex-1 items-center justify-center py-8">
              <div className="max-w-sm text-center">
                <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-sm border border-brand/40 bg-raised text-brand-dark">
                  <Bot aria-hidden="true" className="size-5" />
                </div>

                <h3 className="font-display text-sm font-semibold tracking-wide text-ink">
                  {patient
                    ? `Conversa com ${patient.name}`
                    : "Selecione um paciente"}
                </h3>

                <div
                  aria-hidden="true"
                  className="mx-auto my-3 w-16 border-t border-brand/50"
                />

                <p className="text-sm leading-6 text-ink-muted">
                  {patient
                    ? "Pergunte sobre disponibilidade, valores ou solicite um agendamento."
                    : "O paciente selecionado define também a chave da sessão conversacional."}
                </p>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))
          )}

          {conversationStatus === "sending" && (
            <div className="flex gap-3">
              <div className="mt-1 flex size-8 shrink-0 items-center justify-center rounded-full border border-line bg-raised text-ink-muted">
                <Bot aria-hidden="true" className="size-4" />
              </div>
              <div className="rounded-sm border border-line bg-raised px-4 py-3 shadow-sm">
                <div className="flex gap-1">
                  <span className="size-1.5 animate-bounce rounded-full bg-ink-faint [animation-delay:-0.2s]" />
                  <span className="size-1.5 animate-bounce rounded-full bg-ink-faint [animation-delay:-0.1s]" />
                  <span className="size-1.5 animate-bounce rounded-full bg-ink-faint" />
                </div>
              </div>
            </div>
          )}

          <div aria-hidden="true" className="h-0 shrink-0" ref={endRef} />
        </div>
      </div>

      {error && (
        <div
          className="shrink-0 border-t border-warning-line bg-warning-soft px-4 py-2.5 text-xs leading-5 text-warning"
          role="alert"
        >
          {error}
        </div>
      )}

      <div className="shrink-0">
        <MessageComposer
          disabled={!patient?.isActive}
          isSending={conversationStatus === "sending"}
          onSendAudio={onSendAudio}
          onSendText={onSendText}
        />
      </div>
    </section>
  );
}
