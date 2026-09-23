import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ChatMessage } from "../../types/domain";
import { MessageBubble } from "./MessageBubble";

function createMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id: "msg-1",
    role: "assistant",
    content: "Olá",
    createdAt: new Date("2026-01-01T12:00:00Z"),
    status: "sent",
    audio: null,
    localAudio: null,
    ...overrides,
  };
}

describe("MessageBubble", () => {
  it("renderiza markdown na mensagem do agente", () => {
    render(
      <MessageBubble
        message={createMessage({
          content: "Agende uma consulta de **cardiologia**",
        })}
      />,
    );

    const strong = screen.getByText("cardiologia");
    expect(strong.tagName).toBe("STRONG");
  });

  it("renderiza listas e tabelas GFM", () => {
    render(
      <MessageBubble
        message={createMessage({
          content:
            "- Segunda\n- Terça\n\n| Dia | Hora |\n| --- | --- |\n| Seg | 10:00 |",
        })}
      />,
    );

    expect(screen.getByRole("list")).toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("10:00")).toBeInTheDocument();
  });

  it("renderiza markdown na mensagem do usuário com tema invertido", () => {
    render(
      <MessageBubble
        message={createMessage({
          role: "user",
          content: "Oi, **tudo bem**?",
        })}
      />,
    );

    const strong = screen.getByText("tudo bem");
    expect(strong.tagName).toBe("STRONG");
    expect(strong.closest(".prose-invert")).not.toBeNull();
  });

  it("não interpreta HTML cru como elemento executável", () => {
    const { container } = render(
      <MessageBubble
        message={createMessage({
          content: '<img src="x" onerror="alert(1)">',
        })}
      />,
    );

    expect(container.querySelector("img")).toBeNull();
    expect(container.textContent).toContain("<img");
  });

  it("aplica rel de segurança e target em links", () => {
    render(
      <MessageBubble
        message={createMessage({
          content: "[site](https://example.com)",
        })}
      />,
    );

    const link = screen.getByRole("link", { name: "site" });
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("href", "https://example.com");
  });

  it("converte quebra de linha simples em <br>", () => {
    const { container } = render(
      <MessageBubble
        message={createMessage({
          content: "linha um\nlinha dois",
        })}
      />,
    );

    expect(container.querySelector("br")).not.toBeNull();
    expect(container.textContent).toContain("linha um");
    expect(container.textContent).toContain("linha dois");
  });

  it("bloqueia protocolo de URL inseguro em links", () => {
    const { container } = render(
      <MessageBubble
        message={createMessage({
          content: "[clique](javascript:alert(1))",
        })}
      />,
    );

    const link = container.querySelector("a");
    expect(link).not.toBeNull();
    expect(link?.getAttribute("href") ?? "").not.toContain("javascript:");
  });

  it("renderiza player de áudio para mensagem do assistente com TTS", () => {
    render(
      <MessageBubble
        message={createMessage({
          content: "Oi",
          audio: {
            mimeType: "audio/webm",
            base64: "AAAA",
          },
        })}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Reproduzir áudio" }),
    ).toBeInTheDocument();
  });

  it("oculta o rótulo textual e mostra o player no áudio local do usuário", () => {
    render(
      <MessageBubble
        message={createMessage({
          role: "user",
          content: "Mensagem de áudio",
          localAudio: "blob:local-audio",
        })}
      />,
    );

    expect(screen.queryByText("Mensagem de áudio")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Reproduzir áudio" }),
    ).toBeInTheDocument();
  });

  it("exibe data e hora em formato brasileiro na mensagem de texto", () => {
    render(<MessageBubble message={createMessage({ content: "Olá" })} />);

    const time = screen.getByText("01/01/2026, 09:00");
    expect(time.tagName).toBe("TIME");
    expect(time).toHaveAttribute("datetime", "2026-01-01T12:00:00.000Z");
  });

  it("exibe data e hora em formato brasileiro na mensagem de áudio", () => {
    render(
      <MessageBubble
        message={createMessage({
          role: "user",
          content: "Mensagem de áudio",
          localAudio: "blob:local-audio",
          createdAt: new Date("2026-03-15T18:30:00Z"),
        })}
      />,
    );

    expect(screen.getByText("15/03/2026, 15:30")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Reproduzir áudio" }),
    ).toBeInTheDocument();
  });
});
