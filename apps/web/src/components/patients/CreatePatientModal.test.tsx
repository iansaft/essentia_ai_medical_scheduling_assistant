import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { HttpError } from "../../lib/http";
import type { Patient } from "../../types/domain";
import { CreatePatientModal } from "./CreatePatientModal";

const createPatientMock = vi.fn();

vi.mock("../../services/api.service", () => ({
  createPatient: (...args: unknown[]) => createPatientMock(...args),
}));

const createdPatient: Patient = {
  id: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  name: "Joana Souza",
  email: "joana.souza@example.com",
  phone: "+5548999990009",
  isActive: true,
};

function setup(
  overrides: Partial<Parameters<typeof CreatePatientModal>[0]> = {},
) {
  const onClose = vi.fn();
  const onCreated = vi.fn();

  const props = {
    open: true,
    onClose,
    onCreated,
    ...overrides,
  };

  const view = render(<CreatePatientModal {...props} />);
  return { onClose, onCreated, props, view };
}

function fillValidForm() {
  fireEvent.change(screen.getByLabelText("Nome completo"), {
    target: { value: "Joana Souza" },
  });
  fireEvent.change(screen.getByLabelText("E-mail"), {
    target: { value: "joana.souza@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Telefone (opcional)"), {
    target: { value: "+5548999990009" },
  });
}

describe("CreatePatientModal", () => {
  beforeEach(() => {
    createPatientMock.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("não renderiza quando fechado", () => {
    setup({ open: false });

    expect(screen.queryByRole("dialog", { name: "Novo paciente" })).toBeNull();
  });

  it("renderiza como diálogo modal acessível", () => {
    setup();

    const dialog = screen.getByRole("dialog", { name: "Novo paciente" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(screen.getByLabelText("Nome completo")).toBeInTheDocument();
    expect(screen.getByLabelText("E-mail")).toBeInTheDocument();
    expect(screen.getByLabelText("Telefone (opcional)")).toBeInTheDocument();
  });

  it("foca o nome completo ao abrir", async () => {
    setup();

    await waitFor(() => {
      expect(screen.getByLabelText("Nome completo")).toHaveFocus();
    });
  });

  it("fecha com Escape", () => {
    const { onClose } = setup();

    fireEvent.keyDown(document, { key: "Escape" });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("fecha ao clicar no backdrop", () => {
    const { onClose } = setup();

    const backdrop = document.querySelector('[role="presentation"]');
    expect(backdrop).not.toBeNull();

    fireEvent.mouseDown(backdrop as Element);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("não envia o formulário com campos vazios", () => {
    setup();

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    expect(createPatientMock).not.toHaveBeenCalled();
    expect(screen.getByText("Informe o nome completo.")).toBeInTheDocument();
    expect(screen.getByText("Informe o e-mail.")).toBeInTheDocument();
  });

  it("valida e-mail inválido", () => {
    setup();

    fireEvent.change(screen.getByLabelText("Nome completo"), {
      target: { value: "Joana Souza" },
    });
    fireEvent.change(screen.getByLabelText("E-mail"), {
      target: { value: "nao-e-email" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    expect(createPatientMock).not.toHaveBeenCalled();
    expect(screen.getByText("Informe um e-mail válido.")).toBeInTheDocument();
  });

  it("envia o formulário válido e chama onCreated", async () => {
    createPatientMock.mockResolvedValue(createdPatient);
    const { onCreated } = setup();

    fillValidForm();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(createPatientMock).toHaveBeenCalledWith({
        fullName: "Joana Souza",
        email: "joana.souza@example.com",
        phone: "+5548999990009",
      });
    });

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledWith(createdPatient);
    });
  });

  it("envia phone como null quando omitido", async () => {
    createPatientMock.mockResolvedValue({
      ...createdPatient,
      phone: null,
    });
    const { onCreated } = setup();

    fireEvent.change(screen.getByLabelText("Nome completo"), {
      target: { value: "Joana Souza" },
    });
    fireEvent.change(screen.getByLabelText("E-mail"), {
      target: { value: "joana.souza@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(createPatientMock).toHaveBeenCalledWith({
        fullName: "Joana Souza",
        email: "joana.souza@example.com",
        phone: null,
      });
    });

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalled();
    });
  });

  it("exibe mensagem amigável para 409 de e-mail duplicado", async () => {
    createPatientMock.mockRejectedValue(
      new HttpError(
        "Request falhou com HTTP 409.",
        409,
        JSON.stringify({
          type: "/problems/patient-email-already-exists",
          title: "Conflict",
          status: 409,
          detail: "Patient email already exists.",
          instance: "/v1/patients",
        }),
      ),
    );
    setup();

    fillValidForm();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(
        screen.getByText("Este e-mail já está cadastrado."),
      ).toBeInTheDocument();
    });
  });

  it("exibe mensagem amigável para 409 de telefone duplicado", async () => {
    createPatientMock.mockRejectedValue(
      new HttpError(
        "Request falhou com HTTP 409.",
        409,
        JSON.stringify({
          type: "/problems/patient-phone-already-exists",
          status: 409,
          detail: "Patient phone already exists.",
        }),
      ),
    );
    setup();

    fillValidForm();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(
        screen.getByText("Este telefone já está cadastrado."),
      ).toBeInTheDocument();
    });
  });

  it("exibe erro genérico para falhas não mapeadas", async () => {
    createPatientMock.mockRejectedValue(new Error("Network down"));
    setup();

    fillValidForm();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Network down");
    });
  });

  it("fecha sem enviar ao clicar em Cancelar", () => {
    const { onClose } = setup();

    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(createPatientMock).not.toHaveBeenCalled();
  });

  it("desabilita o envio enquanto está submetendo", async () => {
    createPatientMock.mockImplementation(() => new Promise(() => undefined));
    setup();

    fillValidForm();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Cadastrar/ })).toBeDisabled();
      expect(screen.getByRole("button", { name: "Cancelar" })).toBeDisabled();
    });
  });
});
