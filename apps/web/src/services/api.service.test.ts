import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { env } from "../lib/env";
import { createPatient, listPatients } from "./api.service";

describe("api.service", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("listPatients faz GET e mapeia o domínio", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve([
          {
            id: "3cdf666b-186d-44e6-bce9-5e572e7038f9",
            full_name: "Maria Silva",
            email: "maria.silva@example.com",
            phone: "+5548999990001",
            is_active: true,
          },
        ]),
    });

    const patients = await listPatients();

    expect(fetchMock).toHaveBeenCalledWith(
      `${env.apiBaseUrl}/v1/patients`,
      expect.objectContaining({ method: "GET" }),
    );
    expect(patients).toEqual([
      {
        id: "3cdf666b-186d-44e6-bce9-5e572e7038f9",
        name: "Maria Silva",
        email: "maria.silva@example.com",
        phone: "+5548999990001",
        isActive: true,
      },
    ]);
  });

  it("createPatient faz POST com o corpo snake_case e mapeia o domínio", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          id: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
          full_name: "Joana Souza",
          email: "joana.souza@example.com",
          phone: "+5548999990009",
          is_active: true,
          created_at: "2027-04-12T10:00:00Z",
          updated_at: "2027-04-12T10:00:00Z",
        }),
    });

    const patient = await createPatient({
      fullName: "Joana Souza",
      email: "joana.souza@example.com",
      phone: "+5548999990009",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `${env.apiBaseUrl}/v1/patients`,
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
        body: JSON.stringify({
          full_name: "Joana Souza",
          email: "joana.souza@example.com",
          phone: "+5548999990009",
        }),
      }),
    );
    expect(patient).toEqual({
      id: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
      name: "Joana Souza",
      email: "joana.souza@example.com",
      phone: "+5548999990009",
      isActive: true,
    });
  });

  it("createPatient envia phone null quando omitido", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          id: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
          full_name: "Joana Souza",
          email: "joana.souza@example.com",
          phone: null,
          is_active: true,
        }),
    });

    await createPatient({
      fullName: "Joana Souza",
      email: "joana.souza@example.com",
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse(init.body)).toEqual({
      full_name: "Joana Souza",
      email: "joana.souza@example.com",
      phone: null,
    });
  });
});
