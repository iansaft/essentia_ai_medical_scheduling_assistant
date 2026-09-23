import { Bot, CircleAlert, UserRound } from "lucide-react";
import { formatDateTime } from "../../lib/format";
import type { ChatMessage } from "../../types/domain";
import { AudioPlayerBubble } from "./AudioPlayerBubble";
import { MarkdownText } from "./MarkdownText";

type MessageBubbleProps = {
  message: ChatMessage;
};

function messageAudioSrc(message: ChatMessage): string | null {
  if (message.audio) {
    return `data:${message.audio.mimeType};base64,${message.audio.base64}`;
  }

  return message.localAudio;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const audioSrc = messageAudioSrc(message);
  const hideTextForLocalAudio = isUser && Boolean(message.localAudio);

  return (
    <article
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      <div
        className={`mt-1 flex size-8 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? "bg-brand-dark text-ink-inverse"
            : "border border-line bg-raised text-ink-muted"
        }`}
      >
        {isUser ? (
          <UserRound aria-hidden="true" className="size-4" />
        ) : (
          <Bot aria-hidden="true" className="size-4" />
        )}
      </div>

      <div className={`max-w-[82%] ${isUser ? "text-right" : "text-left"}`}>
        <div
          className={`inline-block rounded-sm px-4 py-3 text-left text-sm ${
            isUser
              ? "bg-brand-dark text-ink-inverse"
              : "border border-line bg-raised text-ink shadow-sm"
          }`}
        >
          {!hideTextForLocalAudio && (
            <MarkdownText
              content={message.content}
              className={
                isUser
                  ? "prose prose-invert prose-sm prose-stone max-w-none break-words"
                  : "prose prose-sm prose-stone max-w-none break-words"
              }
            />
          )}

          {audioSrc && (
            <AudioPlayerBubble
              src={audioSrc}
              tone={isUser ? "user" : "agent"}
            />
          )}

          <time
            className={`mt-1 block text-right text-[11px] leading-4 ${
              isUser ? "text-ink-inverse/70" : "text-ink-faint"
            }`}
            dateTime={message.createdAt.toISOString()}
          >
            {formatDateTime(message.createdAt)}
          </time>
        </div>

        {isUser &&
          (message.status === "failed" || message.status === "unknown") && (
            <p className="mt-1 flex items-center justify-end gap-1 text-xs text-warning">
              <CircleAlert aria-hidden="true" className="size-3" />
              {message.status === "unknown"
                ? "Resultado da operação desconhecido"
                : "Falha no envio"}
            </p>
          )}
      </div>
    </article>
  );
}
