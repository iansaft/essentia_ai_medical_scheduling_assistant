import { useCallback, useEffect, useRef, useState } from "react";

type UseAudioRecorderOptions = {
  onComplete: (blob: Blob) => void;
  onError: (error: Error) => void;
};

type UseAudioRecorderResult = {
  isRecording: boolean;
  recordingTime: number;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  cancelRecording: () => void;
};

function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") {
    return undefined;
  }

  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
  ];

  for (const type of candidates) {
    if (MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }

  return undefined;
}

export function useAudioRecorder(
  options: UseAudioRecorderOptions,
): UseAudioRecorderResult {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const cancelledRef = useRef(false);
  const optionsRef = useRef(options);

  optionsRef.current = options;

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const releaseStream = useCallback(() => {
    for (const track of streamRef.current?.getTracks() ?? []) {
      track.stop();
    }
    streamRef.current = null;
  }, []);

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;

    if (!recorder || recorder.state === "inactive") {
      return;
    }

    clearTimer();
    recorder.stop();
  }, [clearTimer]);

  const cancelRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      cancelledRef.current = true;
      stopRecording();
      return;
    }

    cancelledRef.current = false;
  }, [stopRecording]);

  const startRecording = useCallback(async () => {
    if (mediaRecorderRef.current?.state === "recording") {
      return;
    }

    if (
      typeof navigator === "undefined" ||
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      optionsRef.current.onError(
        new Error("Gravação de áudio não suportada neste navegador."),
      );
      return;
    }

    cancelledRef.current = false;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          noiseSuppression: true,
          echoCancellation: true,
        },
      });

      if (cancelledRef.current) {
        for (const track of stream.getTracks()) {
          track.stop();
        }
        return;
      }

      streamRef.current = stream;
      chunksRef.current = [];

      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(
        stream,
        mimeType ? { mimeType } : undefined,
      );
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const wasCancelled = cancelledRef.current;
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });

        chunksRef.current = [];
        mediaRecorderRef.current = null;
        cancelledRef.current = false;
        releaseStream();
        clearTimer();
        setIsRecording(false);
        setRecordingTime(0);

        if (!wasCancelled) {
          optionsRef.current.onComplete(blob);
        }
      };

      recorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      const startedAt = Date.now();
      timerRef.current = setInterval(() => {
        setRecordingTime(Math.floor((Date.now() - startedAt) / 1000));
      }, 250);
    } catch (error) {
      releaseStream();
      mediaRecorderRef.current = null;
      setIsRecording(false);
      setRecordingTime(0);

      optionsRef.current.onError(
        error instanceof Error ? error : new Error(String(error)),
      );
    }
  }, [clearTimer, releaseStream]);

  useEffect(() => {
    return () => {
      cancelledRef.current = true;
      clearTimer();

      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        try {
          recorder.stop();
        } catch {
          // MediaRecorder already inactive
        }
      }

      mediaRecorderRef.current = null;
      releaseStream();
    };
  }, [clearTimer, releaseStream]);

  return {
    isRecording,
    recordingTime,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
