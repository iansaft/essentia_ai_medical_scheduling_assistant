import { Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { formatAudioDuration } from "../../lib/format";

type AudioPlayerBubbleProps = {
  src: string;
  tone: "user" | "agent";
};

export function AudioPlayerBubble({ src, tone }: AudioPlayerBubbleProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    return () => {
      const audio = audioRef.current;
      if (audio) {
        audio.pause();
      }
    };
  }, []);

  function togglePlayback() {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    if (!isPlaying) {
      void audio.play().then(
        () => {
          setIsPlaying(true);
        },
        () => {
          setIsPlaying(false);
        },
      );
      return;
    }

    audio.pause();
    setIsPlaying(false);
  }

  function handleSeek(event: React.ChangeEvent<HTMLInputElement>) {
    const audio = audioRef.current;
    const next = Number(event.target.value);

    if (audio) {
      audio.currentTime = next;
    }

    setCurrentTime(next);
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
  const playLabel = isPlaying ? "Pausar áudio" : "Reproduzir áudio";
  const timeLabel = `${formatAudioDuration(currentTime)} / ${formatAudioDuration(duration)}`;

  const buttonClass =
    tone === "user"
      ? "flex size-9 shrink-0 items-center justify-center rounded-full bg-ink-inverse text-brand-dark transition hover:bg-brand-light focus-visible:outline-2 focus-visible:outline-ink-inverse"
      : "flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-dark text-ink-inverse transition hover:bg-brand-press focus-visible:outline-2 focus-visible:outline-brand";

  const trackClass = tone === "user" ? "bg-ink-inverse/30" : "bg-line";
  const fillClass = tone === "user" ? "bg-ink-inverse" : "bg-brand-dark";
  const metaClass = tone === "user" ? "text-ink-inverse/85" : "text-ink-muted";

  return (
    <div className="mt-2 flex w-full min-w-56 max-w-72 flex-col">
      {/* biome-ignore lint/a11y/useMediaCaption: Áudio de mensagem (TTS/gravação) sem track de legendas no contrato. */}
      <audio
        ref={audioRef}
        preload="metadata"
        src={src}
        onDurationChange={(event) => {
          setDuration(event.currentTarget.duration || 0);
        }}
        onEnded={() => {
          setIsPlaying(false);
          setCurrentTime(0);
        }}
        onTimeUpdate={(event) => {
          setCurrentTime(event.currentTarget.currentTime);
        }}
      />

      <div className="flex items-center gap-3">
        <button
          aria-label={playLabel}
          className={buttonClass}
          onClick={togglePlayback}
          type="button"
        >
          {isPlaying ? (
            <Pause aria-hidden="true" className="size-4" fill="currentColor" />
          ) : (
            <Play aria-hidden="true" className="size-4" fill="currentColor" />
          )}
        </button>

        <div
          className={`relative h-1.5 min-w-0 flex-1 overflow-hidden rounded-full ${trackClass}`}
        >
          <div
            aria-hidden="true"
            className={`absolute inset-y-0 left-0 rounded-full ${fillClass}`}
            style={{ width: `${progress}%` }}
          />
          <input
            aria-label="Progresso do áudio"
            className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
            max={duration || 0}
            min={0}
            onChange={handleSeek}
            step={0.1}
            type="range"
            value={currentTime}
          />
        </div>
      </div>

      <div className="mt-1 flex gap-3">
        <span aria-hidden="true" className="size-9 shrink-0" />
        <p className={`min-w-0 flex-1 text-[11px] leading-4 ${metaClass}`}>
          {timeLabel}
        </p>
      </div>
    </div>
  );
}
