import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { connectionStatusMeta } from "../lib/connection";
import { AppHeader } from "./AppHeader";

describe("AppHeader", () => {
  it("mostra apenas o ícone com tooltip de conexão estável", () => {
    render(<AppHeader status="online" />);

    const button = screen.getByRole("button", {
      name: "Conexão estável com o servidor",
    });
    expect(button).toBeInTheDocument();
    expect(screen.queryByText("Online")).toBeNull();
    expect(screen.getByRole("tooltip")).toHaveTextContent(
      connectionStatusMeta.online.tooltip,
    );
  });

  it("mostra ícone offline com tooltip de falha de conexão", () => {
    render(<AppHeader status="browser_offline" />);

    expect(
      screen.getByRole("button", { name: "Falha de conexão com o servidor" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Sem internet")).toBeNull();
    expect(screen.getByRole("tooltip")).toHaveTextContent(
      connectionStatusMeta.browser_offline.tooltip,
    );
  });

  it("mostra ícone com tooltip de servidor fora do ar sem citar componentes", () => {
    render(<AppHeader status="server_unavailable" />);

    expect(
      screen.getByRole("button", { name: "Servidor fora do ar" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Servidor offline")).toBeNull();
    expect(screen.getByRole("tooltip")).toHaveTextContent(
      connectionStatusMeta.server_unavailable.tooltip,
    );
    expect(connectionStatusMeta.server_unavailable.tooltip).not.toMatch(
      /n8n|API/i,
    );
  });

  it("mantém os três textos de tooltip distintos", () => {
    const tooltips = [
      connectionStatusMeta.online.tooltip,
      connectionStatusMeta.browser_offline.tooltip,
      connectionStatusMeta.server_unavailable.tooltip,
    ];

    expect(new Set(tooltips).size).toBe(3);
  });
});
