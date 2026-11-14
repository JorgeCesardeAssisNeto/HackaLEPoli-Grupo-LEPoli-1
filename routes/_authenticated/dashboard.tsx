import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { useState } from "react";
import { Toaster } from "sonner";
import {
  HeartPulse,
  LogOut,
  Copy,
  ShieldCheck,
  Check,
  X,
  UserRound,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { supabase } from "@/integrations/supabase/client";
import { readAccount, respondConnection, createInvitation } from "@/lib/accounts.functions";
import { PatientHealth } from "@/components/patient-health";
import { DoctorHub, type HubView } from "@/components/doctor-hub";
import { WearableStrip, ResultsDonut } from "@/components/patient-overview";
import doctorPhoto from '@/assets/health-welcome.jpg';
export const Route = createFileRoute("/_authenticated/dashboard")({
  validateSearch: (
    search: Record<string, unknown>,
  ): { hub?: HubView | undefined; patient?: string | undefined; report?: string | undefined } => ({
    hub:
      typeof search["hub"] === "string" &&
      [
        "dashboard",
        "patients",
        "labs",
        "history",
        "wearables",
        "consents",
        "agenda",
        "notifications",
        "settings",
      ].includes(search["hub"])
        ? (search["hub"] as HubView)
        : undefined,
    patient: typeof search["patient"] === "string" ? search["patient"] : undefined,
    report: typeof search["report"] === "string" ? search["report"] : undefined,
  }),
  head: () => ({
    meta: [
      { title: "Minha conta e Hub do Médico | Open Salus" },
      {
        name: "description",
        content:
          "Acompanhe laudos compartilhados, feedbacks e conexões autorizadas no Open Salus.",
      },
      { property: "og:title", content: "Minha conta e Hub do Médico | Open Salus" },
      {
        property: "og:description",
        content: "Conexões e resultados de cuidado sob controle do paciente.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Dashboard,
});
function Dashboard() {
  const search = Route.useSearch();
  const read = useServerFn(readAccount),
    respond = useServerFn(respondConnection),
    invite = useServerFn(createInvitation);
  const queryClient = useQueryClient(),
    navigate = useNavigate();
  const account = useQuery({
    queryKey: ["account"],
    queryFn: () => read(),
    refetchInterval: 15000,
  });
  const [email, setEmail] = useState(""),
    [notice, setNotice] = useState(""),
    [inviteLink, setInviteLink] = useState(""),
    [busy, setBusy] = useState(false);
  async function run(action: () => Promise<unknown>, message: string) {
    setBusy(true);
    setNotice("");
    try {
      await action();
      await queryClient.invalidateQueries({ queryKey: ["account"] });
      setNotice(message);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível concluir.");
    } finally {
      setBusy(false);
    }
  }
  async function signOut() {
    await queryClient.cancelQueries();
    queryClient.clear();
    await supabase.auth.signOut();
    await navigate({ to: "/auth", replace: true });
  }
  const data = account.data;
  if (data?.role === "doctor")
    return (
      <>
        <Toaster richColors position="bottom-right" />
        <DoctorHub
          account={data}
          onSignOut={signOut}
          view={search["hub"] || "dashboard"}
          patientId={search["patient"]}
          reportId={search["report"]}
        />
      </>
    );
  return (
    <>
      <Toaster richColors position="bottom-right" />
      {data?.role === 'patient' && <img className="patient-background-photo" src={doctorPhoto} alt="" aria-hidden="true" />}
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-symbol">
            <HeartPulse />
          </span>
          <span className="brand-title">
            Open Salus
          </span>
        </Link>
        <Button variant="outline" onClick={signOut}>
          <LogOut />
          Sair
        </Button>
      </header>
      <main className="workspace">
        {account.isPending ? (
          <p role="status">Carregando sua conta…</p>
        ) : account.isError ? (
          <div>
            <p role="alert">{account.error.message}</p>
            <Button onClick={() => account.refetch()}>Tentar novamente</Button>
          </div>
        ) : (
          data && (
            <>
              {data.role === "patient" && <WearableStrip patientId={data.profile.id} />}
              <div className="page-heading">
                <div>
                  <span className="eyebrow">
                    {data.role === "patient" ? "PACIENTE" : "ADMINISTRADOR"}
                  </span>
                  <h1 className="mt-3">Olá, {data.profile.display_name}.</h1>
                  <p>Seu cuidado começa com conexões de confiança.</p>
                </div>
                <ShieldCheck className="text-primary" />
              </div>
              {data.role === "patient" && <ResultsDonut patientId={data.profile.id} />}
              {data.role === "patient" && (
                <PatientHealth
                  patientId={data.profile.id}
                  doctors={data.connections
                    .filter((c) => c.status === "approved")
                    .map((c) => ({
                      id: c.doctor_id,
                      name:
                        data.profiles.find((p) => p.id === c.doctor_id)?.display_name ||
                        "Médico autorizado",
                    }))}
                />
              )}
              {data.role === "patient" && (
                <section className="account-section">
                  <h2>Seu ID de paciente</h2>
                  <div className="flex flex-wrap items-center gap-3">
                    <code className="break-all text-sm">{data.profile.patient_code}</code>
                    <Button
                      variant="outline"
                      size="icon"
                      title="Copiar ID"
                      aria-label="Copiar ID"
                      onClick={() =>
                        run(
                          () => navigator.clipboard.writeText(data.profile.patient_code),
                          "ID copiado.",
                        )
                      }
                    >
                      <Copy />
                    </Button>
                  </div>
                  <p>Compartilhe com seu médico. Você decide se autoriza o acesso.</p>
                </section>
              )}
              {data.role !== "admin" && (
                <section className="account-section">
                  <h2>{"Médicos e autorizações"}</h2>
                  {data.connections.length === 0 ? (
                    <p>Nenhuma conexão por enquanto.</p>
                  ) : (
                    <div className="divide-y divide-border">
                      {data.connections.map((connection) => {
                        const other = data.profiles.find(
                          (profile) => profile.id === connection.doctor_id,
                        );
                        return (
                          <div
                            key={connection.id}
                            className="py-5 flex flex-wrap gap-3 items-center"
                          >
                            <UserRound className="text-primary" />
                            <div className="flex-1">
                              <strong>{other?.display_name || "Médico"}</strong>
                              <p>
                                {
                                  (
                                    {
                                      pending: "Aguardando autorização",
                                      approved: "Acesso autorizado",
                                      rejected: "Solicitação recusada",
                                      revoked: "Acesso revogado",
                                    } as Record<string, string>
                                  )[connection.status]
                                }
                              </p>
                            </div>
                            {data.role === "patient" && connection.status === "pending" && (
                              <>
                                <Button
                                  disabled={busy}
                                  onClick={() =>
                                    run(
                                      () =>
                                        respond({
                                          data: { id: connection.id, status: "approved" },
                                        }),
                                      "Acesso autorizado.",
                                    )
                                  }
                                >
                                  <Check />
                                  Autorizar
                                </Button>
                                <Button
                                  variant="outline"
                                  disabled={busy}
                                  onClick={() =>
                                    run(
                                      () =>
                                        respond({
                                          data: { id: connection.id, status: "rejected" },
                                        }),
                                      "Solicitação recusada.",
                                    )
                                  }
                                >
                                  <X />
                                  Recusar
                                </Button>
                              </>
                            )}
                            {data.role === "patient" && connection.status === "approved" && (
                              <Button
                                variant="outline"
                                disabled={busy}
                                onClick={() =>
                                  run(
                                    () =>
                                      respond({ data: { id: connection.id, status: "revoked" } }),
                                    "Acesso revogado.",
                                  )
                                }
                              >
                                <X />
                                Revogar acesso
                              </Button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </section>
              )}
              {data.role === "admin" && (
                <section className="account-section">
                  <h2>Convites de administrador</h2>
                  <form
                    className="flex flex-wrap gap-3"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void run(async () => {
                        const result = await invite({ data: email });
                        setInviteLink(
                          `${window.location.origin}/auth?invite=${encodeURIComponent(result.token)}`,
                        );
                      }, "Convite criado para este email. Válido por 7 dias e para um único cadastro.");
                    }}
                  >
                    <input
                      className="account-input flex-1"
                      aria-label="Email do administrador"
                      type="email"
                      value={email}
                      maxLength={255}
                      onChange={(event) => setEmail(event.target.value)}
                      required
                    />
                    <Button disabled={busy}>Gerar convite privado</Button>
                  </form>
                  {inviteLink && (
                    <div className="mt-4 flex gap-3">
                      <input
                        className="account-input flex-1 min-w-0"
                        aria-label="Link privado de convite"
                        readOnly
                        value={inviteLink}
                      />
                      <Button
                        variant="outline"
                        size="icon"
                        title="Copiar convite"
                        aria-label="Copiar convite"
                        onClick={() =>
                          run(
                            () => navigator.clipboard.writeText(inviteLink),
                            "Convite copiado. Envie apenas à pessoa convidada.",
                          )
                        }
                      >
                        <Copy />
                      </Button>
                    </div>
                  )}
                </section>
              )}

            </>
          )
        )}
        {notice && (
          <p className="mt-4 text-primary" role="status">
            {notice}
          </p>
        )}
      </main>
    </>
  );
}
