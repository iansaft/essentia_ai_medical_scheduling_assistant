import { useCallback, useEffect, useRef, useState } from "react";
import { AppHeader } from "../components/AppHeader";
import { AppointmentsPanel } from "../components/appointments/AppointmentsPanel";
import { ChatPanel } from "../components/chat/ChatPanel";
import { CreatePatientModal } from "../components/patients/CreatePatientModal";
import { PatientSelector } from "../components/patients/PatientSelector";
import { useConnectionStatus } from "../hooks/useConnectionStatus";
import { isAbortError, toErrorMessage } from "../lib/http";
import { listPatientAppointments, listPatients } from "../services/api.service";
import { sendAudioMessage, sendTextMessage } from "../services/chat.service";
import type {
  Appointment,
  ChatMessage,
  ConversationStatus,
  Patient,
} from "../types/domain";

type AsyncListState<T> = {
  data: T[];
  isLoading: boolean;
  error: string | null;
};

const initialAppointmentsState: AsyncListState<Appointment> = {
  data: [],
  isLoading: false,
  error: null,
};

function revokeLocalAudioUrls(items: ChatMessage[]) {
  for (const item of items) {
    if (item.localAudio) {
      URL.revokeObjectURL(item.localAudio);
    }
  }
}

export function App() {
  const connectionStatus = useConnectionStatus();

  const [patientsState, setPatientsState] = useState<AsyncListState<Patient>>({
    data: [],
    isLoading: true,
    error: null,
  });
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(
    null,
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationStatus, setConversationStatus] =
    useState<ConversationStatus>("idle");
  const [conversationError, setConversationError] = useState<string | null>(
    null,
  );
  const [appointmentsState, setAppointmentsState] = useState<
    AsyncListState<Appointment>
  >(initialAppointmentsState);
  const [appointmentsAreStale, setAppointmentsAreStale] = useState(false);
  const [isCreatePatientOpen, setIsCreatePatientOpen] = useState(false);

  const selectedPatientIdRef = useRef<string | null>(null);
  const messagesRef = useRef<ChatMessage[]>([]);
  const chatAbortRef = useRef<AbortController | null>(null);
  const appointmentsAbortRef = useRef<AbortController | null>(null);
  const patientsAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const selectedPatient =
    patientsState.data.find((patient) => patient.id === selectedPatientId) ??
    null;

  useEffect(() => {
    selectedPatientIdRef.current = selectedPatientId;
  }, [selectedPatientId]);

  const refreshPatients = useCallback(
    async (options?: { selectInitial?: boolean }) => {
      patientsAbortRef.current?.abort();

      const controller = new AbortController();
      patientsAbortRef.current = controller;

      setPatientsState((current) => ({
        data: current.data,
        isLoading: true,
        error: null,
      }));

      try {
        const patients = await listPatients(controller.signal);

        setPatientsState({
          data: patients,
          isLoading: false,
          error: null,
        });

        if (options?.selectInitial) {
          const initialPatient =
            patients.find((patient) => patient.isActive) ?? null;

          setSelectedPatientId(initialPatient?.id ?? null);
        }
      } catch (error) {
        if (isAbortError(error)) {
          return;
        }

        setPatientsState((current) => ({
          data: current.data,
          isLoading: false,
          error: `Não foi possível carregar os pacientes. ${toErrorMessage(error)}`,
        }));
      }
    },
    [],
  );

  useEffect(() => {
    void refreshPatients({ selectInitial: true });

    return () => patientsAbortRef.current?.abort();
  }, [refreshPatients]);

  const refreshAppointments = useCallback(
    async (patientId: string, preserveExisting = true) => {
      appointmentsAbortRef.current?.abort();

      const controller = new AbortController();
      appointmentsAbortRef.current = controller;

      setAppointmentsState((current) => ({
        data: preserveExisting ? current.data : [],
        isLoading: true,
        error: null,
      }));

      try {
        const appointments = await listPatientAppointments(
          patientId,
          controller.signal,
        );

        if (selectedPatientIdRef.current !== patientId) {
          return;
        }

        setAppointmentsState({
          data: appointments,
          isLoading: false,
          error: null,
        });
        setAppointmentsAreStale(false);
      } catch (error) {
        if (isAbortError(error)) {
          return;
        }

        if (selectedPatientIdRef.current !== patientId) {
          return;
        }

        setAppointmentsState((current) => ({
          data: current.data,
          isLoading: false,
          error: `Não foi possível sincronizar os agendamentos. ${toErrorMessage(error)}`,
        }));
        setAppointmentsAreStale(true);
      }
    },
    [],
  );

  useEffect(() => {
    if (!selectedPatientId) {
      appointmentsAbortRef.current?.abort();
      setAppointmentsState(initialAppointmentsState);
      setAppointmentsAreStale(false);
      return;
    }

    void refreshAppointments(selectedPatientId, false);
  }, [selectedPatientId, refreshAppointments]);

  useEffect(() => {
    if (connectionStatus !== "online" || !selectedPatientId) {
      return;
    }

    if (appointmentsAreStale) {
      void refreshAppointments(selectedPatientId);
    }
  }, [
    appointmentsAreStale,
    connectionStatus,
    refreshAppointments,
    selectedPatientId,
  ]);

  useEffect(() => {
    return () => {
      chatAbortRef.current?.abort();
      appointmentsAbortRef.current?.abort();
      revokeLocalAudioUrls(messagesRef.current);
    };
  }, []);

  function handlePatientChange(patientId: string) {
    if (patientId === selectedPatientId) {
      return;
    }

    chatAbortRef.current?.abort();
    appointmentsAbortRef.current?.abort();

    revokeLocalAudioUrls(messagesRef.current);
    setSelectedPatientId(patientId);
    setMessages([]);
    setConversationStatus("idle");
    setConversationError(null);
    setAppointmentsAreStale(false);
  }

  async function handlePatientCreated(patient: Patient) {
    setIsCreatePatientOpen(false);

    await refreshPatients();

    handlePatientChange(patient.id);
  }

  function handleCreatePatientOpen() {
    setIsCreatePatientOpen(true);
  }

  function handleCreatePatientClose() {
    setIsCreatePatientOpen(false);

    document
      .querySelector<HTMLElement>('[aria-label="Novo paciente"]')
      ?.focus();
  }

  function appendUserMessage(
    content: string,
    localAudio: string | null = null,
  ): string {
    const id = crypto.randomUUID();

    setMessages((current) => [
      ...current,
      {
        id,
        role: "user",
        content,
        createdAt: new Date(),
        status: "sending",
        audio: null,
        localAudio,
      },
    ]);

    return id;
  }

  function updateMessageStatus(
    messageId: string,
    status: ChatMessage["status"],
  ) {
    setMessages((current) =>
      current.map((message) =>
        message.id === messageId ? { ...message, status } : message,
      ),
    );
  }

  function appendAssistantMessage(
    content: string,
    audio: ChatMessage["audio"],
  ) {
    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content,
        createdAt: new Date(),
        status: "sent",
        audio,
        localAudio: null,
      },
    ]);
  }

  async function executeConversationTurn(
    patient: Patient,
    userMessageId: string,
    request: (signal: AbortSignal) => ReturnType<typeof sendTextMessage>,
  ) {
    chatAbortRef.current?.abort();

    const controller = new AbortController();
    chatAbortRef.current = controller;

    setConversationStatus("sending");
    setConversationError(null);

    try {
      const reply = await request(controller.signal);

      if (selectedPatientIdRef.current !== patient.id) {
        return;
      }

      updateMessageStatus(userMessageId, "sent");
      appendAssistantMessage(reply.message, reply.audio);
      setConversationStatus("idle");

      await refreshAppointments(patient.id);
    } catch (error) {
      if (isAbortError(error)) {
        return;
      }

      if (selectedPatientIdRef.current !== patient.id) {
        return;
      }

      // Em falhas de rede/timeout não é possível afirmar que uma mutação
      // não ocorreu no n8n/FastAPI. Por isso o estado é "unknown" e não há
      // retry automático do turno.
      updateMessageStatus(userMessageId, "unknown");
      setConversationStatus("idle");
      setConversationError(
        `A resposta do assistente não foi recebida. O processamento pode ter continuado no servidor. Os agendamentos serão reconciliados sem reenviar a mensagem. Detalhe: ${toErrorMessage(error)}`,
      );

      console.error("Falha no turno conversacional:", error);

      await refreshAppointments(patient.id);
    }
  }

  async function handleSendText(message: string) {
    const patient = selectedPatient;

    if (!patient || conversationStatus === "sending") {
      return;
    }

    const messageId = appendUserMessage(message);

    await executeConversationTurn(patient, messageId, (signal) =>
      sendTextMessage(patient, message, signal),
    );
  }

  async function handleSendAudio(audio: Blob) {
    const patient = selectedPatient;

    if (!patient || conversationStatus === "sending") {
      return;
    }

    const localAudio = URL.createObjectURL(audio);
    const messageId = appendUserMessage("Mensagem de áudio", localAudio);

    await executeConversationTurn(patient, messageId, (signal) =>
      sendAudioMessage(patient, audio, signal),
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden bg-canvas text-ink">
      <AppHeader status={connectionStatus} />

      <main className="mx-auto grid min-h-0 w-full max-w-[1600px] flex-1 gap-4 overflow-hidden px-4 py-4 lg:grid-cols-[minmax(0,1fr)_380px] lg:px-6 lg:py-6">
        <div className="flex min-h-0 min-w-0 flex-col">
          <ChatPanel
            conversationStatus={conversationStatus}
            error={conversationError}
            messages={messages}
            onSendAudio={handleSendAudio}
            onSendText={handleSendText}
            patient={selectedPatient}
          />
        </div>

        <aside className="min-h-0 space-y-4 overflow-y-auto pr-0.5">
          <PatientSelector
            error={patientsState.error}
            isLoading={patientsState.isLoading}
            onChange={handlePatientChange}
            onCreate={handleCreatePatientOpen}
            patients={patientsState.data}
            selectedPatientId={selectedPatientId}
          />

          <AppointmentsPanel
            appointments={appointmentsState.data}
            error={appointmentsState.error}
            isLoading={appointmentsState.isLoading}
            isStale={appointmentsAreStale}
            onRefresh={() => {
              if (selectedPatientId) {
                void refreshAppointments(selectedPatientId);
              }
            }}
            patient={selectedPatient}
          />
        </aside>
      </main>

      <CreatePatientModal
        onClose={handleCreatePatientClose}
        onCreated={(patient) => {
          void handlePatientCreated(patient);
        }}
        open={isCreatePatientOpen}
      />
    </div>
  );
}
