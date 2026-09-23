import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AudioPlayerBubble } from "./AudioPlayerBubble";

function mockAudioElement() {
  const play = vi.fn().mockResolvedValue(undefined);
  const pause = vi.fn();

  Object.defineProperty(HTMLMediaElement.prototype, "play", {
    configurable: true,
    value: play,
  });
  Object.defineProperty(HTMLMediaElement.prototype, "pause", {
    configurable: true,
    value: pause,
  });

  return { play, pause };
}

describe("AudioPlayerBubble", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("alterna play e pause", async () => {
    const { play, pause } = mockAudioElement();
    render(<AudioPlayerBubble src="blob:audio" tone="agent" />);

    const button = screen.getByRole("button", { name: "Reproduzir áudio" });
    fireEvent.click(button);

    await screen.findByRole("button", { name: "Pausar áudio" });
    expect(play).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Pausar áudio" }));
    expect(pause).toHaveBeenCalledTimes(1);
    expect(
      screen.getByRole("button", { name: "Reproduzir áudio" }),
    ).toBeInTheDocument();
  });

  it("renderiza o slider de progresso e o tempo", () => {
    mockAudioElement();
    render(<AudioPlayerBubble src="blob:audio" tone="user" />);

    expect(
      screen.getByRole("slider", { name: "Progresso do áudio" }),
    ).toBeInTheDocument();
    expect(screen.getByText("0:00 / 0:00")).toBeInTheDocument();
  });
});
