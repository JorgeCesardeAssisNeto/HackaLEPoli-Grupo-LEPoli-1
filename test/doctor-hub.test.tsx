import { fireEvent, render, screen, waitFor, cleanup } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  read: vi.fn(),
  send: vi.fn(),
  mark: vi.fn(),
  request: vi.fn(),
}));
vi.mock("@tanstack/react-router", () => ({
  Link: ({ children }: { children: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => mocks.navigate,
}));
vi.mock("@tanstack/react-start", () => ({ useServerFn: (fn: unknown) => fn }));
vi.mock("@/lib/accounts.functions", () => ({
  readAccount: vi.fn(),
  requestConnection: mocks.request,
}));
vi.mock("@/lib/care.functions", () => ({
  readCare: mocks.read,
  sendFeedback: mocks.send,
  markCareRead: mocks.mark,
}));
import { DoctorHub, type HubView } from "@/components/doctor-hub";
const patientId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const reportId = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
const doctorId = "cccccccc-cccc-4ccc-8ccc-cccccccccccc";
const account = {
  profile: {
    id: doctorId,
    display_name: "Médica de teste",
    consent_at: "2026-11-14",
    created_at: "2026-11-14",
    patient_code: doctorId,
  },
  role: "doctor" as const,
  connections: [
    {
      id: "connection",
      doctor_id: doctorId,
      patient_id: patientId,
      created_at: "2026-11-14",
      status: "approved",
    },
  ],
  profiles: [{ id: patientId, display_name: "Paciente de teste", patient_code: patientId }],
};
const data = {
  reports: [
    {
      id: reportId,
      patient_id: patientId,
      filename: "laudo-teste.pdf",
      collected_on: "2026-11-14",
      exams: [
        {
          name: "Ferritina",
          rawResult: "12",
          value: 12,
          unit: "ng/mL",
          reference: "15 a 150",
          method: "",
        },
      ],
    },
  ],
  feedback: [],
  notifications: [
    { id: "notice", patient_id: patientId, created_at: "2026-11-14T12:00:00Z", read_at: null },
  ],
  shares: [],
  followups: [],
};
function mount(view: HubView, patient?: string, report?: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <DoctorHub
        account={account}
        onSignOut={vi.fn()}
        view={view}
        patientId={patient}
        reportId={report}
      />
    </QueryClientProvider>,
  );
}
beforeEach(() => {
  vi.clearAllMocks();
  mocks.read.mockResolvedValue(data);
  mocks.send.mockResolvedValue({ ok: true });
  mocks.mark.mockResolvedValue({ ok: true });
});
afterEach(cleanup);
describe("doctor hub existing actions", () => {
  it("opens the selected connected patient through dashboard navigation", async () => {
    mount("patients");
    fireEvent.click(await screen.findByRole("button", { name: /Abrir perfil/ }));
    expect(mocks.navigate).toHaveBeenCalledWith({
      to: "/dashboard",
      search: { hub: "patients", patient: patientId, report: undefined },
    });
  });
  it("sends feedback for the selected report and patient through the existing action", async () => {
    mount("labs", patientId, reportId);
    fireEvent.change(await screen.findByLabelText("Sua orientação"), {
      target: { value: "Vamos revisar este resultado na consulta." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Enviar feedback ao paciente/ }));
    await waitFor(() =>
      expect(mocks.send).toHaveBeenCalledWith({
        data: { reportId, patientId, message: "Vamos revisar este resultado na consulta." },
      }),
    );
    await waitFor(() => expect(screen.getByLabelText("Sua orientação")).toHaveValue(""));
  });
  it("marks a notification read through the existing action", async () => {
    mount("notifications");
    fireEvent.click(await screen.findByRole("button", { name: /Marcar como lido/ }));
    await waitFor(() => expect(mocks.mark).toHaveBeenCalledWith({ data: "notice" }));
  });
  it("keeps failed feedback in the editor for retry", async () => {
    mocks.send.mockRejectedValue(new Error("Acesso revogado."));
    mount("labs", patientId, reportId);
    fireEvent.change(await screen.findByLabelText("Sua orientação"), {
      target: { value: "Revisar resultado." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Enviar feedback ao paciente/ }));
    await screen.findByRole("alert");
    expect(screen.getByLabelText("Sua orientação")).toHaveValue("Revisar resultado.");
  });
});
