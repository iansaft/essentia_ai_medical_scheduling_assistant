export type Patient = {
  id: string;
  name: string;
  email: string;
  isActive: boolean;
};

export type AppointmentStatus =
  | "scheduled"
  | "cancelled"
  | "completed"
  | "no_show";

export type Appointment = {
  id: string;
  startsAt: string;
  endsAt: string | null;
  serviceName: string;
  doctorName: string;
  status: AppointmentStatus;
  priceAmount: number | null;
  currency: string | null;
  cancellationReason: string | null;
};

export type ChatMessageRole = "user" | "assistant";

export type ChatMessageStatus = "sending" | "sent" | "failed" | "unknown";

export type ChatAudio = {
  mimeType: string;
  base64: string;
};

export type ChatMessage = {
  id: string;
  role: ChatMessageRole;
  content: string;
  createdAt: Date;
  status: ChatMessageStatus;
  audio: ChatAudio | null;
  /** URL local (blob:) do áudio gravado no cliente; não vai ao servidor. */
  localAudio: string | null;
};

export type AssistantReply = {
  message: string;
  audio: ChatAudio | null;
};

export type ConversationStatus = "idle" | "sending";
