import { describe, expect, it } from "vitest";
import {
  appointmentStatusLabel,
  formatAudioDuration,
  formatMoney,
} from "./format";

describe("formatMoney", () => {
  it("formata valores monetários", () => {
    expect(formatMoney(150, "BRL")).toContain("150");
  });

  it("retorna null quando o valor está ausente", () => {
    expect(formatMoney(null, "BRL")).toBeNull();
  });
});

describe("appointmentStatusLabel", () => {
  it("traduz o status agendado", () => {
    expect(appointmentStatusLabel("scheduled")).toBe("Agendado");
  });
});

describe("formatAudioDuration", () => {
  it("formata segundos em m:ss", () => {
    expect(formatAudioDuration(0)).toBe("0:00");
    expect(formatAudioDuration(65)).toBe("1:05");
  });
});
