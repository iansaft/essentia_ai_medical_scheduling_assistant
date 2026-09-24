import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Patient } from "../../types/domain";
import { PatientSelector } from "./PatientSelector";

const patients: Patient[] = [
  {
    id: "3cdf666b-186d-44e6-bce9-5e572e7038f9",
    name: "Maria Silva",
    email: "maria.silva@example.com",
    phone: "+5548999990001",
    isActive: true,
  },
  {
    id: "2338a014-ec7f-4585-a519-c15e9c20b11c",
    name: "Lucas Ferreira",
    email: "lucas.ferreira@example.com",
    phone: null,
    isActive: false,
  },
];

function setup(overrides: Partial<Parameters<typeof PatientSelector>[0]> = {}) {
  const onChange = vi.fn();
  const onCreate = vi.fn();

  const props = {
    patients,
    selectedPatientId: patients[0].id,
    isLoading: false,
    error: null,
    onChange,
    onCreate,
    ...overrides,
  };

  const view = render(<PatientSelector {...props} />);
  return { onChange, onCreate, props, view };
}

describe("PatientSelector", () => {
  it("renderiza o título e o botão de novo paciente", () => {
    setup();

    expect(
      screen.getByRole("heading", { name: "Paciente" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Novo paciente" }),
    ).toBeInTheDocument();
  });

  it("chama onCreate ao clicar em Novo paciente", () => {
    const { onCreate } = setup();

    fireEvent.click(screen.getByRole("button", { name: "Novo paciente" }));

    expect(onCreate).toHaveBeenCalledTimes(1);
  });

  it("permanece habilitado mesmo com a lista vazia", () => {
    setup({ patients: [], selectedPatientId: null });

    expect(screen.getByRole("button", { name: "Novo paciente" })).toBeEnabled();
  });

  it("lista os pacientes no select", () => {
    setup();

    const options = screen.getAllByRole("option");
    expect(options.map((option) => option.textContent)).toEqual([
      "Maria Silva",
      "Lucas Ferreira (inativo)",
    ]);
  });

  it("chama onChange ao selecionar outro paciente", () => {
    const { onChange } = setup();

    fireEvent.change(screen.getByLabelText("Selecionar paciente"), {
      target: { value: patients[1].id },
    });

    expect(onChange).toHaveBeenCalledWith(patients[1].id);
  });

  it("exibe erro com role alert", () => {
    setup({ error: "Não foi possível carregar os pacientes." });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Não foi possível carregar os pacientes.",
    );
  });
});
