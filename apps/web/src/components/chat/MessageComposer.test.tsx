import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MessageComposer } from "./MessageComposer";

type MockMediaRecorderState = "inactive" | "recording";

class MockMediaRecorder {
  static instances: MockMediaRecorder[] = [];

  state: MockMediaRecorderState = "inactive";
  mimeType = "audio/webm";
  ondataavailable: ((event: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;

  constructor(_stream: MediaStream, options?: { mimeType?: string }) {
    this.mimeType = options?.mimeType ?? "audio/webm";
    MockMediaRecorder.instances.push(this);
  }

  static isTypeSupported(type: string): boolean {
    return type.startsWith("audio/");
  }

  start() {
    this.state = "recording";
  }

  stop() {
    if (this.state === "inactive") {
      return;
    }

    this.state = "inactive";
    this.ondataavailable?.({
      data: new Blob(["audio"], { type: this.mimeType }),
    });
    this.onstop?.();
  }
}

function setup(overrides: Partial<Parameters<typeof MessageComposer>[0]> = {}) {
  const onSendText = vi.fn().mockResolvedValue(undefined);
  const onSendAudio = vi.fn().mockResolvedValue(undefined);

  const props = {
    disabled: false,
    isSending: false,
    onSendText,
    onSendAudio,
    ...overrides,
  };

  const view = render(<MessageComposer {...props} />);
  return { onSendText, onSendAudio, props, view };
}

async function startRecording() {
  fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
  await screen.findByText("Gravando áudio");
}

describe("MessageComposer", () => {
  const getUserMedia = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    MockMediaRecorder.instances = [];

    vi.stubGlobal("MediaRecorder", MockMediaRecorder);

    getUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    });

    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia },
    });
  });

  it("envia texto pelo botão bronze", async () => {
    const { onSendText } = setup();

    fireEvent.change(screen.getByLabelText("Mensagem para o assistente"), {
      target: { value: "Olá" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enviar mensagem" }));

    await waitFor(() => {
      expect(onSendText).toHaveBeenCalledWith("Olá");
    });
  });

  it("alterna para o modo gravação no slot do textarea", async () => {
    setup();

    await startRecording();

    expect(getUserMedia).toHaveBeenCalledTimes(1);
    expect(screen.queryByLabelText("Mensagem para o assistente")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Parar gravação" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Descartar áudio" }),
    ).toBeNull();
    expect(screen.getByText("Gravando áudio")).toBeInTheDocument();
  });

  it("mantém o stop externo no tom de status agendado durante a gravação", async () => {
    setup();

    await startRecording();

    const stopButton = screen.getByRole("button", { name: "Parar gravação" });
    expect(stopButton.className).toContain("bg-info-soft");
    expect(stopButton.className).toContain("text-info");
    expect(stopButton.className).toContain("border-info");
  });

  it("habilita o envio de áudio somente após a gravação parar", async () => {
    const { onSendAudio } = setup();

    await startRecording();

    expect(screen.getByRole("button", { name: "Enviar áudio" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Parar gravação" }));

    await waitFor(() => {
      expect(screen.getByText("Áudio pronto para envio")).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: "Enviar áudio" }),
    ).not.toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Enviar áudio" }));

    await waitFor(() => {
      expect(onSendAudio).toHaveBeenCalledTimes(1);
    });
  });

  it("transforma o stop na lixeira no tom de status cancelado após parar", async () => {
    setup();

    await startRecording();
    fireEvent.click(screen.getByRole("button", { name: "Parar gravação" }));

    await waitFor(() => {
      expect(screen.getByText("Áudio pronto para envio")).toBeInTheDocument();
    });

    expect(screen.queryByRole("button", { name: "Parar gravação" })).toBeNull();

    const discardButton = screen.getByRole("button", {
      name: "Descartar áudio",
    });
    expect(discardButton.className).toContain("bg-danger-soft");
    expect(discardButton.className).toContain("text-danger");
    expect(discardButton.className).toContain("border-danger");
  });

  it("descarta a gravação e volta ao textarea", async () => {
    setup();

    await startRecording();
    fireEvent.click(screen.getByRole("button", { name: "Parar gravação" }));

    await waitFor(() => {
      expect(screen.getByText("Áudio pronto para envio")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Descartar áudio" }));

    expect(
      screen.getByLabelText("Mensagem para o assistente"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Parar gravação" })).toBeNull();
    expect(screen.queryByText("Áudio pronto para envio")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Gravar áudio" }),
    ).toBeInTheDocument();

    const recorder = MockMediaRecorder.instances.at(-1);
    expect(recorder?.state).toBe("inactive");
  });

  it("volta ao botão de gravar após enviar o áudio", async () => {
    setup();

    await startRecording();
    fireEvent.click(screen.getByRole("button", { name: "Parar gravação" }));

    await waitFor(() => {
      expect(screen.getByText("Áudio pronto para envio")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Enviar áudio" }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Gravar áudio" }),
      ).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("button", { name: "Descartar áudio" }),
    ).toBeNull();
  });

  it("expõe tooltips de ação nos botões do composer", async () => {
    setup();

    expect(
      document.getElementById("composer-action-tooltip"),
    ).toHaveTextContent("Gravar mensagem de voz");
    expect(document.getElementById("composer-send-tooltip")).toHaveTextContent(
      "Enviar mensagem",
    );
    expect(
      screen.getByRole("button", { name: "Enviar mensagem" }),
    ).toHaveAccessibleDescription("Enviar mensagem");

    await startRecording();

    expect(
      document.getElementById("composer-action-tooltip"),
    ).toHaveTextContent("Finalizar gravação");

    fireEvent.click(screen.getByRole("button", { name: "Parar gravação" }));

    await waitFor(() => {
      expect(
        document.getElementById("composer-action-tooltip"),
      ).toHaveTextContent("Descartar mensagem de voz");
    });
  });

  it("inicia nova gravação normalmente após descartar a anterior", async () => {
    setup();

    await startRecording();
    fireEvent.click(screen.getByRole("button", { name: "Parar gravação" }));

    await waitFor(() => {
      expect(screen.getByText("Áudio pronto para envio")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Descartar áudio" }));
    expect(
      screen.getByLabelText("Mensagem para o assistente"),
    ).toBeInTheDocument();

    await startRecording();

    expect(screen.getByText("Gravando áudio")).toBeInTheDocument();
    expect(screen.queryByText("Preparando gravação…")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Parar gravação" }),
    ).not.toBeDisabled();
    expect(screen.getByRole("button", { name: "Enviar áudio" })).toBeDisabled();

    const recorder = MockMediaRecorder.instances.at(-1);
    expect(recorder?.state).toBe("recording");
  });

  it("mostra erro quando a permissão de microfone é negada", async () => {
    getUserMedia.mockRejectedValue(
      Object.assign(new Error("denied"), { name: "NotAllowedError" }),
    );

    setup();

    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));

    await waitFor(() => {
      expect(
        screen.getByText("Permissão de microfone negada."),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByLabelText("Mensagem para o assistente"),
    ).toBeInTheDocument();
  });

  it("volta ao modo texto quando a gravação resulta em blob vazio", async () => {
    const originalStop = MockMediaRecorder.prototype.stop;

    MockMediaRecorder.prototype.stop = function stopEmpty() {
      if (this.state === "inactive") {
        return;
      }

      this.state = "inactive";
      this.ondataavailable?.({
        data: new Blob([], { type: this.mimeType }),
      });
      this.onstop?.();
    };

    try {
      setup();

      await startRecording();
      fireEvent.click(screen.getByRole("button", { name: "Parar gravação" }));

      await waitFor(() => {
        expect(
          screen.getByText(
            "Não foi possível capturar o áudio. Tente novamente.",
          ),
        ).toBeInTheDocument();
      });

      expect(
        screen.getByLabelText("Mensagem para o assistente"),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Gravar áudio" }),
      ).toBeInTheDocument();
    } finally {
      MockMediaRecorder.prototype.stop = originalStop;
    }
  });
});
