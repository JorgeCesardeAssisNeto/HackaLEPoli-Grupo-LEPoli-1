import { useEffect, useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  Bell,
  CalendarDays,
  Check,
  ChevronLeft,
  FileText,
  HeartPulse,
  LayoutDashboard,
  LockKeyhole,
  LogOut,
  Menu,
  MessageSquare,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Stethoscope,
  Users,
  Watch,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import { readAccount, requestConnection } from "@/lib/accounts.functions";
import { readCare, sendFeedback, markCareRead } from "@/lib/care.functions";
import { componentName, componentExplanation, examFeedback } from "@/lib/exam-feedback";
import { connectionSchema } from "@/lib/account-schema";

type Account = Awaited<ReturnType<typeof readAccount>>;
type Care = Awaited<ReturnType<typeof readCare>>;
type Report = Care["reports"][number];
export type HubView =
  | "dashboard"
  | "patients"
  | "labs"
  | "history"
  | "wearables"
  | "consents"
  | "agenda"
  | "notifications"
  | "settings";
const modules: { id: HubView; title: string; icon: typeof Users }[] = [
  { id: "dashboard", title: "Visão geral", icon: LayoutDashboard },
  { id: "patients", title: "Pacientes", icon: Users },
  { id: "labs", title: "Exames laboratoriais", icon: FileText },
  { id: "wearables", title: "Wearables", icon: Watch },
  { id: "history", title: "Histórico longitudinal", icon: Activity },
  { id: "consents", title: "Conexões e autorizações", icon: ShieldCheck },
  { id: "agenda", title: "Minha agenda", icon: CalendarDays },
  { id: "notifications", title: "Notificações", icon: Bell },
  { id: "settings", title: "Minha conta", icon: Settings },
];
const formatDate = (date: string) => date.split("-").reverse().join("/");

function Empty({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="dh-empty">
      <FileText size={26} />
      <h3>{title}</h3>
      {children && <p>{children}</p>}
    </div>
  );
}

function ExamTable({ report, search = "" }: { report: Report; search?: string }) {
  const [expanded, setExpanded] = useState<number | null>(null);
  const exams = report.exams
    .map((exam, index) => ({ exam, index }))
    .filter(({ exam }) =>
      componentName(exam.name)
        .toLocaleLowerCase("pt-BR")
        .includes(search.toLocaleLowerCase("pt-BR")),
    );
  return (
    <div className="dh-table-scroll">
      <table className="dh-table">
        <thead>
          <tr>
            <th>Biomarcador</th>
            <th>Resultado</th>
            <th>Referência do laudo</th>
            <th>Comparação</th>
            <th>Detalhes</th>
          </tr>
        </thead>
        <tbody>
          {exams.map(({ exam, index }) => {
            const status = examFeedback(exam);
            return (
              <tr key={index}>
                <td>
                  <strong>{componentName(exam.name)}</strong>
                  {expanded === index && (
                    <div className="dh-explanation">
                      <p>{componentExplanation(exam)}</p>
                      <p>{status.reason}</p>
                      {exam.method && <p>Método: {exam.method}</p>}
                    </div>
                  )}
                </td>
                <td className="tabular-nums">
                  {exam.rawResult} {!exam.rawResult.includes(exam.unit) && exam.unit}
                </td>
                <td>{exam.reference || "Não informada"}</td>
                <td>
                  <span className={`pill ${status.tone}`}>{status.label}</span>
                </td>
                <td>
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-expanded={expanded === index}
                    onClick={() => setExpanded(expanded === index ? null : index)}
                  >
                    <MessageSquare />
                    {expanded === index ? "Fechar" : "Entenda"}
                  </Button>
                </td>
              </tr>
            );
          })}
          {!exams.length && (
            <tr>
              <td colSpan={5}>Nenhum biomarcador corresponde à pesquisa.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function ReportDetail({
  report,
  feedback,
  busy,
  onSend,
}: {
  report: Report;
  feedback: Care["feedback"];
  busy: boolean;
  onSend: (message: string) => Promise<boolean>;
}) {
  const [message, setMessage] = useState(""),
    [search, setSearch] = useState("");
  return (
    <>
      <div className="dh-report-heading">
        <div>
          <span className="eyebrow">LAUDO COMPARTILHADO</span>
          <h2>{report.filename}</h2>
          <p>
            Coleta {formatDate(report.collected_on)} · {report.exams.length} biomarcadores
          </p>
        </div>
        <span className="pill success">
          <ShieldCheck size={13} />
          Autorizado pelo paciente
        </span>
      </div>
      <div className="dh-notice">
        <LockKeyhole size={18} />
        <p>
          Resultados revisados, compartilhados pelo paciente. O PDF original permanece privado; não
          há permissão para editar o laudo.
        </p>
      </div>
      <div className="dh-toolbar">
        <label className="dh-search">
          <Search size={17} />
          <input
            aria-label="Pesquisar biomarcador"
            placeholder="Pesquisar biomarcador"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
      </div>
      <ExamTable report={report} search={search} />
      <section className="dh-section">
        <div className="dh-section-heading">
          <div>
            <h2>Feedback ao paciente</h2>
            <p>Orientações vinculadas a este laudo</p>
          </div>
          <MessageSquare size={20} />
        </div>
        {feedback
          .filter((f) => f.report_id === report.id)
          .map((f) => (
            <article className="dh-feedback" key={f.id}>
              <span>Feedback enviado · {new Date(f.created_at).toLocaleString("pt-BR")}</span>
              <p>{f.message}</p>
            </article>
          ))}
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (await onSend(message)) setMessage("");
          }}
        >
          <label className="dh-field-label" htmlFor="doctor-feedback">
            Sua orientação
          </label>
          <textarea
            id="doctor-feedback"
            className="account-input w-full"
            rows={4}
            maxLength={4000}
            required
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Escreva seu feedback sobre este laudo…"
          />
          <Button className="mt-3" disabled={busy || !message.trim()}>
            <MessageSquare />
            {busy ? "Enviando…" : "Enviar feedback ao paciente"}
          </Button>
        </form>
      </section>
    </>
  );
}

function History({ reports }: { reports: Report[] }) {
  const metrics = [
    ...new Map(
      reports.flatMap((r) =>
        r.exams
          .filter((e) => e.value !== null)
          .map((e) => [JSON.stringify([e.name, e.unit]), e] as const),
      ),
    ).entries(),
  ];
  const [key, setKey] = useState("");
  const chosen = metrics.find(([id]) => id === key) || metrics[0];
  if (!chosen)
    return (
      <Empty title="Sem histórico numérico disponível">
        O paciente precisa compartilhar laudos com resultados numéricos para consultar a evolução.
      </Empty>
    );
  const [id, exam] = chosen;
  const series = [...reports]
    .sort((a, b) => a.collected_on.localeCompare(b.collected_on))
    .flatMap((r) =>
      r.exams
        .filter((e) => JSON.stringify([e.name, e.unit]) === id && e.value !== null)
        .map((e) => ({ date: formatDate(r.collected_on), value: e.value, filename: r.filename })),
    );
  return (
    <section className="dh-section">
      <div className="dh-section-heading">
        <div>
          <h2>Evolução dos exames</h2>
          <p>Somente laudos compartilhados · Sem conversão de unidades</p>
        </div>
        <select
          className="account-input"
          aria-label="Biomarcador do histórico"
          value={id}
          onChange={(e) => setKey(e.target.value)}
        >
          {metrics.map(([metricId, e]) => (
            <option key={metricId} value={metricId}>
              {componentName(e.name)} · {e.unit || "Sem unidade"}
            </option>
          ))}
        </select>
      </div>
      <div className="dh-history">
        <div className="dh-chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={series} margin={{ top: 15, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
              <YAxis tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} width={45} />
              <Tooltip
                content={({ active, payload }) =>
                  active && payload?.[0] ? (
                    <div className="dh-chart-tooltip">
                      <strong>{payload[0].payload.date}</strong>
                      <p>
                        {payload[0].value} {exam.unit}
                      </p>
                      <p>{payload[0].payload.filename}</p>
                    </div>
                  ) : null
                }
              />
              <Line
                dataKey="value"
                name={exam.name}
                stroke={`var(--chart-${Math.max(0, metrics.findIndex(([metricId]) => metricId === id)) % 5 + 1})`}
                strokeWidth={2}
                dot={{ r: 4 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <aside className="dh-metric-detail">
          <h3>{componentName(exam.name)}</h3>
          <p>{componentExplanation(exam)}</p>
          <span>{series.length} resultado(s) compartilhado(s)</span>
          {series.length === 1 && (
            <p>Uma única coleta disponível; ainda não é possível observar uma tendência.</p>
          )}
        </aside>
      </div>
    </section>
  );
}

export function DoctorHub({
  account,
  onSignOut,
  view,
  patientId,
  reportId,
}: {
  account: Account;
  onSignOut: () => Promise<void>;
  view: HubView;
  patientId?: string | undefined;
  reportId?: string | undefined;
}) {
  const read = useServerFn(readCare),
    send = useServerFn(sendFeedback),
    mark = useServerFn(markCareRead),
    request = useServerFn(requestConnection);
  const care = useQuery({ queryKey: ["care"], queryFn: () => read(), refetchInterval: 15000 });
  const client = useQueryClient(),
    navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false),
    [search, setSearch] = useState(""),
    [code, setCode] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(""),
    [failed, setFailed] = useState(false),
    [readFilter, setReadFilter] = useState("all"),
    [dateFilter, setDateFilter] = useState("");
  useEffect(() => {
    if (window.matchMedia("(max-width: 520px)").matches) setCollapsed(true);
  }, []);
  const patients = account.connections
    .filter((c) => c.status === "approved")
    .map((c) => ({
      id: c.patient_id,
      name: account.profiles.find((p) => p.id === c.patient_id)?.display_name || "Paciente",
    }));
  const selected = patients.find((p) => p.id === patientId);
  const reports = care.data?.reports || [],
    notifications = care.data?.notifications || [];
  const selectedReports = reports.filter((r) => r.patient_id === selected?.id);
  const report = selectedReports.find((r) => r.id === reportId);
  const unread = notifications.filter((n) => !n.read_at).length;
  const abnormal = reports.flatMap((r) =>
    r.exams.filter((e) => examFeedback(e).tone === "warning").map((e) => ({ report: r, exam: e })),
  );
  function go(next: HubView, patient?: string, report?: string) {
    if (window.matchMedia("(max-width: 520px)").matches) setCollapsed(true);
    setSearch("");
    setDateFilter("");
    void navigate({ to: "/dashboard", search: { hub: next, patient, report } });
  }
  async function run(action: () => Promise<unknown>, success: string) {
    setBusy(true);
    setNotice("");
    setFailed(false);
    try {
      await action();
      await Promise.all([
        client.invalidateQueries({ queryKey: ["care"] }),
        client.invalidateQueries({ queryKey: ["account"] }),
      ]);
      setNotice(success);
      return true;
    } catch (error) {
      setFailed(true);
      setNotice(error instanceof Error ? error.message : "Não foi possível concluir.");
      return false;
    } finally {
      setBusy(false);
    }
  }
  function reportList(items: Report[]) {
    return !items.length ? (
      <Empty title="Nenhum laudo compartilhado">
        A conexão por si só não libera exames. O paciente escolhe quais laudos compartilhar.
      </Empty>
    ) : (
      <div className="dh-table-scroll">
        <table className="dh-table">
          <thead>
            <tr>
              <th>Paciente</th>
              <th>Laudo / origem</th>
              <th>Coleta</th>
              <th>Acesso</th>
              <th>Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>
                  <strong>{patients.find((p) => p.id === r.patient_id)?.name || "Paciente"}</strong>
                  <small>{r.exams.length} biomarcadores</small>
                </td>
                <td>
                  <strong>{r.filename}</strong>
                  <small>Compartilhado pelo paciente</small>
                </td>
                <td>{formatDate(r.collected_on)}</td>
                <td>
                  <span className="pill success">Autorizado</span>
                </td>
                <td>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => go("labs", r.patient_id, r.id)}
                  >
                    Abrir
                    <ArrowRight />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  const filteredPatients = patients
    .filter((p) =>
      `${p.name} ${p.id}`.toLocaleLowerCase("pt-BR").includes(search.toLocaleLowerCase("pt-BR")),
    )
    .sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
  const filteredReports = reports.filter(
    (r) =>
      (!selected || r.patient_id === selected.id) &&
      (!dateFilter || r.collected_on === dateFilter) &&
      `${r.filename} ${patients.find((p) => p.id === r.patient_id)?.name || ""}`
        .toLocaleLowerCase("pt-BR")
        .includes(search.toLocaleLowerCase("pt-BR")),
  );
  const title = modules.find((m) => m.id === view)?.title || "Visão geral";
  return (
    <div className={`doctor-hub ${collapsed ? "dh-collapsed" : ""}`}>
      <aside className="dh-sidebar">
        <Link to="/" className="dh-brand">
          <span className="dh-brand-mark">
            <HeartPulse />
          </span>
          <span className="dh-nav-label">
            <strong>Open Salus</strong>
            <small>Hub do Médico</small>
          </span>
        </Link>
        <span className="dh-nav-caption dh-nav-label">ÁREA CLÍNICA</span>
        <nav aria-label="Navegação do Hub do Médico">
          {modules.map((m) => (
            <Button
              key={m.id}
              variant="ghost"
              title={m.title}
              className={`dh-nav-item ${view === m.id ? "is-active" : ""}`}
              onClick={() => go(m.id)}
              aria-current={view === m.id ? "page" : undefined}
            >
              <m.icon />
              <span className="dh-nav-label">{m.title}</span>
              {((m.id === "patients" && patients.length > 0) ||
                (m.id === "notifications" && unread > 0)) && (
                <span className="dh-nav-count dh-nav-label">
                  {m.id === "patients" ? patients.length : unread}
                </span>
              )}
            </Button>
          ))}
        </nav>
        {selected && (
          <div className="dh-active-patient dh-nav-label">
            <small>PACIENTE SELECIONADO</small>
            <Button variant="ghost" onClick={() => go("patients", selected.id)}>
              <Users />
              <span>{selected.name}</span>
            </Button>
          </div>
        )}
        <div className="dh-physician">
          <span className="dh-physician-avatar">
            <Stethoscope size={18} />
          </span>
          <div className="dh-nav-label">
            <strong>{account.profile.display_name}</strong>
            <small>Conta médica autenticada</small>
          </div>
        </div>
      </aside>
      <div className="dh-main">
        <header className="dh-topbar">
          <div className="flex items-center gap-3 min-w-0">
            <Button
              variant="ghost"
              size="icon"
              aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
              title={collapsed ? "Expandir menu" : "Recolher menu"}
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? <Menu /> : <ChevronLeft />}
            </Button>
            <strong>{title}</strong>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              title="Notificações"
              aria-label={`Notificações: ${unread} não lidas`}
              onClick={() => go("notifications")}
            >
              <Bell />
            </Button>
            <Button variant="ghost" size="sm" onClick={onSignOut}>
              <LogOut />
              <span>Sair</span>
            </Button>
          </div>
        </header>
        <main className="dh-content">
          <div className="dh-page-heading">
            <div>
              <span className="eyebrow">HUB DO MÉDICO</span>
              <h1>
                {selected ? selected.name : view === "dashboard" ? "Visão geral do cuidado" : title}
              </h1>
              <p>
                {selected
                  ? "Perfil individual · Acesso restrito aos laudos autorizados"
                  : "Acompanhamento dos pacientes e resultados compartilhados"}
              </p>
            </div>
            {view === "dashboard" && (
              <Button onClick={() => go("patients")}>
                <Users />
                Meus pacientes
                <ArrowRight />
              </Button>
            )}
            {selected && (
              <Button variant="outline" onClick={() => go("patients")}>
                <ArrowLeft />
                Todos os pacientes
              </Button>
            )}
          </div>
          {notice && (
            <div
              className={`dh-notice ${failed ? "dh-notice-error" : ""}`}
              role={failed ? "alert" : "status"}
            >
              {failed ? <Bell size={18} /> : <Check size={18} />}
              <p>{notice}</p>
            </div>
          )}
          {care.isPending ? (
            <Empty title="Carregando acompanhamento…" />
          ) : care.isError ? (
            <div className="dh-notice dh-notice-error" role="alert">
              <p>{care.error.message}</p>
              <Button variant="outline" onClick={() => care.refetch()}>
                Tentar novamente
              </Button>
            </div>
          ) : (
            <>
              {view === "dashboard" && (
                <>
                  <div className="dh-notice">
                    <ShieldCheck size={20} />
                    <p>
                      O paciente controla o compartilhamento. Resultados fora da referência não
                      representam um diagnóstico automático.
                    </p>
                  </div>
                  <div className="dh-kpis">
                    {[
                      {
                        label: "Pacientes conectados",
                        value: patients.length,
                        note: "Conexões aprovadas",
                        icon: Users,
                        tone: "primary",
                      },
                      {
                        label: "Laudos compartilhados",
                        value: reports.length,
                        note: "Autorizados pelos pacientes",
                        icon: FileText,
                        tone: "navy",
                      },
                      {
                        label: "Fora da referência",
                        value: abnormal.length,
                        note: "Resultados dos laudos disponíveis",
                        icon: Activity,
                        tone: "danger",
                      },
                      {
                        label: "Avisos não lidos",
                        value: unread,
                        note: "Sinais de alarme informados",
                        icon: Bell,
                        tone: "warning",
                      },
                    ].map((k) => (
                      <article className={`dh-kpi dh-kpi-${k.tone}`} key={k.label}>
                        <div>
                          <span>{k.label}</span>
                          <k.icon size={18} />
                        </div>
                        <strong>{k.value}</strong>
                        <small>{k.note}</small>
                      </article>
                    ))}
                  </div>
                  <section className="dh-section">
                    <div className="dh-section-heading">
                      <div>
                        <h2>Laudos compartilhados recentemente</h2>
                        <p>Resultados disponíveis para consulta e feedback</p>
                      </div>
                      <Button variant="outline" size="sm" onClick={() => go("labs")}>
                        Ver todos
                        <ArrowRight />
                      </Button>
                    </div>
                    {reportList(reports.slice(0, 5))}
                  </section>
                  <section className="dh-section">
                    <div className="dh-section-heading">
                      <div>
                        <h2>Resultados fora da referência</h2>
                        <p>Comparação conservadora com a referência do laudo</p>
                      </div>
                    </div>
                    {!abnormal.length ? (
                      <Empty title="Nenhum resultado fora da referência nos laudos disponíveis">
                        Isso não descarta problemas de saúde.
                      </Empty>
                    ) : (
                      <div className="dh-table-scroll">
                        <table className="dh-table">
                          <thead>
                            <tr>
                              <th>Paciente</th>
                              <th>Biomarcador</th>
                              <th>Resultado</th>
                              <th>Referência</th>
                              <th>Laudo</th>
                            </tr>
                          </thead>
                          <tbody>
                            {abnormal.slice(0, 6).map(({ report: r, exam: e }, i) => (
                              <tr key={`${r.id}-${i}`}>
                                <td>
                                  {patients.find((p) => p.id === r.patient_id)?.name || "Paciente"}
                                </td>
                                <td>{componentName(e.name)}</td>
                                <td>{e.rawResult} {e.unit && !e.rawResult.includes(e.unit) ? e.unit : ''}</td>
                                <td>{e.reference || "Não informada"}</td>
                                <td>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => go("labs", r.patient_id, r.id)}
                                  >
                                    Consultar
                                    <ArrowRight />
                                  </Button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </section>
                </>
              )}
              {view === "patients" && !selected && (
                <>
                  <div className="dh-toolbar">
                    <label className="dh-search">
                      <Search size={18} />
                      <input
                        aria-label="Pesquisar pacientes"
                        placeholder="Pesquisar por nome ou ID do paciente"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                    </label>
                    <span className="text-muted-foreground text-xs">
                      {filteredPatients.length} paciente(s)
                    </span>
                  </div>
                  <section className="dh-section">
                    {!filteredPatients.length ? (
                      <Empty
                        title={search ? "Nenhum paciente encontrado" : "Nenhum paciente conectado"}
                      >
                        Solicite uma conexão pelo ID do paciente em Conexões e autorizações.
                      </Empty>
                    ) : (
                      <div className="dh-table-scroll">
                        <table className="dh-table">
                          <thead>
                            <tr>
                              <th>Paciente</th>
                              <th>Laudos disponíveis</th>
                              <th>Conexão</th>
                              <th>Perfil</th>
                            </tr>
                          </thead>
                          <tbody>
                            {filteredPatients.map((p) => (
                              <tr key={p.id}>
                                <td>
                                  <strong>{p.name}</strong>
                                  <small className="dh-id">{p.id}</small>
                                </td>
                                <td>{reports.filter((r) => r.patient_id === p.id).length}</td>
                                <td>
                                  <span className="pill success">Autorizada</span>
                                </td>
                                <td>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => go("patients", p.id)}
                                  >
                                    Abrir perfil
                                    <ArrowRight />
                                  </Button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </section>
                </>
              )}
              {selected &&
                ["patients", "labs", "history", "wearables", "consents"].includes(view) && (
                  <div className="dh-profile-tabs">
                    {[
                      { id: "patients", label: "Visão geral" },
                      { id: "labs", label: "Exames laboratoriais" },
                      { id: "history", label: "Histórico" },
                      { id: "wearables", label: "Wearables" },
                      { id: "consents", label: "Autorizações" },
                    ].map((t) => (
                      <Button
                        key={t.id}
                        variant="ghost"
                        className={view === t.id ? "is-active" : ""}
                        onClick={() => go(t.id as HubView, selected.id)}
                      >
                        {t.label}
                      </Button>
                    ))}
                  </div>
                )}
              {view === "patients" && selected && (
                <>
                  <section className="dh-section">
                    <div className="dh-section-heading">
                      <div>
                        <h2>Último laudo compartilhado</h2>
                        <p>Coletas disponíveis para acompanhamento</p>
                      </div>
                    </div>
                    {reportList(selectedReports.slice(0, 1))}
                  </section>
                  <History key={selected.id} reports={selectedReports} />
                </>
              )}
              {view === "labs" &&
                (report ? (
                  <ReportDetail
                    key={report.id}
                    report={report}
                    feedback={care.data?.feedback || []}
                    busy={busy}
                    onSend={(message) =>
                      run(
                        () =>
                          send({
                            data: { reportId: report.id, patientId: report.patient_id, message },
                          }),
                        "Feedback enviado ao paciente.",
                      )
                    }
                  />
                ) : (
                  <>
                    <div className="dh-toolbar">
                      <label className="dh-search">
                        <Search size={18} />
                        <input
                          aria-label="Pesquisar laudos"
                          placeholder="Pesquisar por laudo ou paciente"
                          value={search}
                          onChange={(e) => setSearch(e.target.value)}
                        />
                      </label>
                      <input
                        className="account-input"
                        type="date"
                        aria-label="Filtrar por data de coleta"
                        value={dateFilter}
                        onChange={(e) => setDateFilter(e.target.value)}
                      />
                      {!selected && (
                        <select
                          className="account-input"
                          aria-label="Filtrar laudos por paciente"
                          value={patientId || ""}
                          onChange={(e) => go("labs", e.target.value || undefined)}
                        >
                          <option value="">Todos os pacientes</option>
                          {patients.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                    <section className="dh-section">{reportList(filteredReports)}</section>
                  </>
                ))}
              {view === "history" && (
                <>
                  <div className="dh-toolbar">
                    <select
                      className="account-input"
                      aria-label="Paciente do histórico"
                      value={selected?.id || ""}
                      onChange={(e) => go("history", e.target.value || undefined)}
                    >
                      <option value="">Selecione um paciente</option>
                      {patients.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  {selected ? (
                    <History key={selected.id} reports={selectedReports} />
                  ) : (
                    <Empty title="Selecione um paciente">
                      Consulte a evolução dos exames compartilhados, mantendo cada unidade original.
                    </Empty>
                  )}
                </>
              )}
              {view === "notifications" && (
                <>
                  <div className="dh-toolbar">
                    <select
                      className="account-input"
                      aria-label="Filtrar notificações"
                      value={readFilter}
                      onChange={(e) => setReadFilter(e.target.value)}
                    >
                      <option value="all">Todos os avisos</option>
                      <option value="unread">Não lidos</option>
                      <option value="read">Lidos</option>
                    </select>
                  </div>
                  {!notifications.filter(
                    (n) =>
                      readFilter === "all" || (readFilter === "read" ? !!n.read_at : !n.read_at),
                  ).length ? (
                    <Empty title="Nenhum aviso disponível" />
                  ) : (
                    notifications
                      .filter(
                        (n) =>
                          readFilter === "all" ||
                          (readFilter === "read" ? !!n.read_at : !n.read_at),
                      )
                      .map((n) => (
                        <article key={n.id} className="dh-notification">
                          <Bell size={20} />
                          <div>
                            <strong>
                              {patients.find((p) => p.id === n.patient_id)?.name || "Paciente"} ·
                              Solicitou contato urgente
                            </strong>
                            <p>
                              O paciente informou sinais de alarme e foi orientado a procurar
                              atendimento imediatamente.
                            </p>
                            <small>{new Date(n.created_at).toLocaleString("pt-BR")}</small>
                            <div className="mt-3">
                              {n.read_at ? (
                                <span className="pill neutral">
                                  <Check size={12} />
                                  Aviso lido
                                </span>
                              ) : (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  disabled={busy}
                                  onClick={() =>
                                    run(() => mark({ data: n.id }), "Aviso marcado como lido.")
                                  }
                                >
                                  <Check />
                                  Marcar como lido
                                </Button>
                              )}
                            </div>
                          </div>
                        </article>
                      ))
                  )}
                </>
              )}
              {view === "consents" && (
                <>
                  <section className="dh-section">
                    <div className="dh-section-heading">
                      <div>
                        <h2>Conectar um paciente</h2>
                        <p>A conexão depende da aprovação do paciente</p>
                      </div>
                      <ShieldCheck size={20} />
                    </div>
                    <form
                      className="dh-connection-form"
                      onSubmit={(e) => {
                        e.preventDefault();
                        void run(
                          () => request({ data: connectionSchema.parse(code) }),
                          "Solicitação enviada. Aguarde a autorização do paciente.",
                        );
                      }}
                    >
                      <input
                        className="account-input"
                        aria-label="ID do paciente"
                        placeholder="ID completo do paciente"
                        value={code}
                        maxLength={36}
                        required
                        onChange={(e) => setCode(e.target.value)}
                      />
                      <Button disabled={busy}>
                        <Plus />
                        Solicitar conexão
                      </Button>
                    </form>
                  </section>
                  <section className="dh-section">
                    <div className="dh-section-heading">
                      <div>
                        <h2>Conexões e permissões</h2>
                        <p>O compartilhamento de laudos é independente da conexão</p>
                      </div>
                    </div>
                    {!account.connections.length ? (
                      <Empty title="Nenhuma conexão por enquanto" />
                    ) : (
                      <div className="dh-table-scroll">
                        <table className="dh-table">
                          <thead>
                            <tr>
                              <th>Paciente</th>
                              <th>Conexão</th>
                              <th>Laudos compartilhados</th>
                              <th>Perfil</th>
                            </tr>
                          </thead>
                          <tbody>
                            {account.connections.map((c) => (
                              <tr key={c.id}>
                                <td>
                                  {account.profiles.find((p) => p.id === c.patient_id)
                                    ?.display_name || "Nome disponível após autorização"}
                                </td>
                                <td>
                                  <span
                                    className={`pill ${c.status === "approved" ? "success" : "neutral"}`}
                                  >
                                    {(
                                      {
                                        approved: "Autorizada",
                                        pending: "Aguardando paciente",
                                        rejected: "Recusada",
                                        revoked: "Revogada",
                                      } as Record<string, string>
                                    )[c.status] || c.status}
                                  </span>
                                </td>
                                <td>
                                  {reports.filter((r) => r.patient_id === c.patient_id).length}
                                </td>
                                <td>
                                  {c.status === "approved" && (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => go("patients", c.patient_id)}
                                    >
                                      Abrir
                                      <ArrowRight />
                                    </Button>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </section>
                  <div className="dh-notice">
                    <LockKeyhole size={18} />
                    <p>
                      O paciente escolhe os laudos compartilhados. PDFs e wearables continuam
                      privados. A revogação da conexão bloqueia o acesso.
                    </p>
                  </div>
                </>
              )}
              {view === "wearables" && (
                <Empty title="Wearables indisponíveis para o médico">
                  As medições permanecem privadas na conta do paciente. O sistema atual não oferece
                  compartilhamento médico de wearables.
                </Empty>
              )}
              {view === "agenda" && (
                <Empty title="Agenda médica ainda não disponível">
                  A publicação e a edição de horários pelo médico ainda não foram implementadas.
                  Nenhuma disponibilidade fictícia é apresentada.
                </Empty>
              )}
              {view === "settings" && (
                <section className="dh-section">
                  <div className="dh-section-heading">
                    <div>
                      <h2>Conta médica</h2>
                      <p>{account.profile.display_name}</p>
                    </div>
                    <Stethoscope size={20} />
                  </div>
                  <div className="dh-account-info">
                    <p>
                      <ShieldCheck size={16} />
                      Acesso médico autenticado
                    </p>
                    <p>
                      <LockKeyhole size={16} />
                      Dados disponíveis conforme autorização do paciente
                    </p>
                    <p>
                      CPF, CRM, auditoria detalhada, importação médica, edição de laudos e
                      exportação médica do modelo não estão disponíveis no sistema atual.
                    </p>
                  </div>
                </section>
              )}
            </>
          )}
          <footer className="dh-footer">
            <span>
              <ShieldCheck size={14} />
              Acesso restrito · Compartilhamento sob controle do paciente
            </span>
            <Button asChild variant="link" size="sm">
              <Link to="/demo">
                Demonstração separada dos dados reais
                <ArrowRight />
              </Link>
            </Button>
          </footer>
        </main>
      </div>
    </div>
  );
}
