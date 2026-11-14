import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useServerFn } from '@tanstack/react-start';
import { AlertTriangle, Bell, MessageSquare, Send, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { readCare, shareReport, sendFeedback, submitFollowup, markCareRead } from '@/lib/care.functions';
import { answersSchema, questions, type Answers } from '@/lib/care-data';
import { referenceStatus } from '@/lib/pdf-extraction';
type Doctor = { id: string; name: string };

function SafetyQuestions({ reportId, saved, onSaved }: { reportId: string; saved: { answers: unknown; urgent: boolean } | undefined; onSaved: () => Promise<unknown> }) {
  const parsed = answersSchema.safeParse(saved?.answers);
  const [answers, setAnswers] = useState<Partial<Answers>>(parsed.success ? parsed.data : {});
  const [consent, setConsent] = useState(false), [busy, setBusy] = useState(false), [notice, setNotice] = useState(''), [error, setError] = useState('');
  const submit = useServerFn(submitFollowup);
  const urgent = saved?.urgent || answers.chest_pain || answers.breathlessness || answers.fainting;
  async function save() {
    setBusy(true); setError(''); setNotice('');
    try { const result = await submit({ data: { reportId, answers: answersSchema.parse(answers), consent } }); await onSaved(); setNotice(result.notified ? `Respostas salvas. ${result.notified} médico(s) autorizado(s) receberam um aviso no painel.` : consent ? 'Respostas salvas. Nenhum aviso foi enviado: não há sinal de alarme informado ou médico autorizado.' : 'Respostas salvas. Você não autorizou o envio de aviso ao médico.'); }
    catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível salvar.'); } finally { setBusy(false); }
  }
  return <div className={urgent ? 'care-safety urgent' : 'care-safety'} role={urgent ? 'alert' : undefined}>
    <h3 className="flex gap-2 items-center"><AlertTriangle size={20}/>{urgent ? 'Sinal de alarme informado' : 'Resultado fora da referência do laudo'}</h3>
    <p>{urgent ? 'Procure atendimento médico imediatamente. Em emergência, ligue 192. Não aguarde resposta do médico ou do aplicativo.' : 'Consulte um médico para interpretar este resultado. Estar fora da referência não confirma uma doença.'}</p>
    <p className="text-xs">Perguntas de segurança, não um modelo preditivo validado. Respostas negativas não descartam risco.</p>
    <form onSubmit={event => { event.preventDefault(); void save(); }} className="mt-5 space-y-4">
      {questions.map(q => <fieldset key={q.key} className="care-question"><legend>{q.label}</legend><div className="flex gap-5 mt-2">{[true, false].map(value => <label key={String(value)} className="flex items-center gap-2"><input type="radio" name={`${reportId}-${q.key}`} checked={answers[q.key] === value} required onChange={() => setAnswers(a => ({ ...a, [q.key]: value }))}/>{value ? 'Sim' : 'Não'}</label>)}</div></fieldset>)}
      <label className="flex items-start gap-3 text-sm"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} className="mt-1"/>Autorizo avisar meus médicos com conexão ativa se eu informar sinais de alarme. O aviso não inclui minhas respostas ou resultados.</label>
      <Button disabled={busy || questions.some(q => answers[q.key] === undefined)}><Send/>{busy ? 'Salvando…' : 'Salvar respostas'}</Button>
    </form>
    {notice && <p role="status">{notice}</p>}{error && <p role="alert">{error}</p>}
  </div>;
}

export function PatientCare({ doctors }: { doctors: Doctor[] }) {
  const read = useServerFn(readCare), share = useServerFn(shareReport);
  const client = useQueryClient();
  const care = useQuery({ queryKey: ['care'], queryFn: () => read(), refetchInterval: 15000 });
  const [error, setError] = useState(''), [busy, setBusy] = useState(false);
  async function refresh() { await client.invalidateQueries({ queryKey: ['care'] }); }
  async function toggle(reportId: string, doctorId: string, enabled: boolean) { setBusy(true); setError(''); try { await share({ data: { reportId, doctorId, enabled } }); await refresh(); } catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível compartilhar.'); } finally { setBusy(false); } }
  return <>
    <section className="account-section"><h2 className="flex gap-2 items-center"><MessageSquare className="text-primary"/>Feedbacks dos seus médicos</h2>
      {care.isPending ? <p role="status">Carregando acompanhamento…</p> : care.isError ? <p role="alert">{care.error.message} <Button variant="outline" onClick={() => care.refetch()}>Tentar novamente</Button></p> : <>
        {!care.data?.feedback.length && <p>Nenhum feedback recebido até o momento.</p>}
        {care.data?.feedback.map(f => <article className="care-feedback" key={f.id}><strong>{doctors.find(d => d.id === f.doctor_id)?.name || 'Médico responsável'} · {care.data.reports.find(r => r.id === f.report_id)?.filename || 'Laudo'}</strong><time className="block text-xs text-muted-foreground mt-1">{new Date(f.created_at).toLocaleString('pt-BR')}</time><p className="whitespace-pre-wrap break-words">{f.message}</p></article>)}
        <details className="mt-5"><summary className="cursor-pointer text-primary">Autorizar laudos para feedback médico</summary><p>Selecione cada laudo e médico. Somente os resultados revisados serão compartilhados, não o PDF ou medições de wearables. Revogar a conexão também bloqueia o acesso.</p>
          {!doctors.length && <p>Autorize uma conexão médica abaixo para compartilhar laudos.</p>}
          {care.data?.reports.map(r => <div key={r.id} className="py-3 border-b border-border"><strong className="break-words">{r.filename}</strong>{doctors.map(d => <label key={d.id} className="flex gap-3 items-center mt-3"><input type="checkbox" disabled={busy} checked={care.data.shares.some(s => s.report_id === r.id && s.doctor_id === d.id)} onChange={e => void toggle(r.id, d.id, e.target.checked)}/><ShieldCheck size={16} className="text-primary"/>{d.name}</label>)}</div>)}
        </details>
      </>}{error && <p role="alert">{error}</p>}
    </section>
    <section className="account-section"><h2 className="flex gap-2 items-center"><Bell className="text-primary"/>Avisos importantes sobre seus exames</h2><p>Avaliação preditiva ainda não integrada. Os avisos abaixo comparam os resultados com as referências do laboratório.</p>
      {care.data?.reports.filter(r => r.exams.some(e => referenceStatus(e) === 'Alterado') || care.data.followups.some(f => f.report_id === r.id && f.urgent)).map(r => <div key={r.id} className="mt-5"><h3 className="font-medium break-words mb-3">{r.filename} · {r.collected_on.split('-').reverse().join('/')}</h3><p>{r.exams.filter(e => referenceStatus(e) === 'Alterado').map(e => e.name).join(' · ')}</p><SafetyQuestions key={r.id} reportId={r.id} saved={care.data.followups.find(f => f.report_id === r.id)} onSaved={refresh}/></div>)}
      {care.data && !care.data.reports.some(r => r.exams.some(e => referenceStatus(e) === 'Alterado') || care.data.followups.some(f => f.report_id === r.id && f.urgent)) && <p>Nenhum resultado fora das referências reconhecidas nos laudos salvos. Isso não descarta problemas de saúde.</p>}
    </section>
  </>;
}

export function DoctorCare({ patients }: { patients: Doctor[] }) {
  const read = useServerFn(readCare), send = useServerFn(sendFeedback), mark = useServerFn(markCareRead);
  const care = useQuery({ queryKey: ['care'], queryFn: () => read(), refetchInterval: 15000 });
  const client = useQueryClient();
  const [messages, setMessages] = useState<Record<string,string>>({}), [busy, setBusy] = useState(false), [notice, setNotice] = useState('');
  async function run(action: () => Promise<unknown>) { setBusy(true); setNotice(''); try { await action(); await client.invalidateQueries({ queryKey: ['care'] }); setNotice('Atualizado.'); } catch (err) { setNotice(err instanceof Error ? err.message : 'Não foi possível concluir.'); } finally { setBusy(false); } }
  return <section className="account-section"><h2 className="flex gap-2 items-center"><Bell className="text-primary"/>Acompanhamento dos pacientes</h2>{care.isPending ? <p>Carregando…</p> : care.isError ? <p role="alert">{care.error.message}</p> : <>
    {!care.data?.notifications.length && <p>Nenhum aviso de paciente recebido.</p>}
    {care.data?.notifications.map(n => <article key={n.id} className="care-safety urgent mb-4"><strong>{patients.find(p => p.id === n.patient_id)?.name || 'Paciente'} · Solicitou contato urgente</strong><p>O paciente informou sinais de alarme e foi orientado a procurar atendimento imediatamente.</p><p>{new Date(n.created_at).toLocaleString('pt-BR')}</p>{n.read_at ? <span className="text-xs">Aviso lido</span> : <Button variant="outline" disabled={busy} onClick={() => void run(() => mark({ data: n.id }))}>Marcar como lido</Button>}</article>)}
    <h3 className="font-medium mt-6">Laudos autorizados para feedback</h3>{!care.data?.reports.length && <p>Nenhum laudo compartilhado. A conexão sozinha não permite ler exames.</p>}
    {care.data?.reports.map(r => <div key={r.id} className="py-5 border-b border-border"><h3 className="font-medium break-words">{patients.find(p => p.id === r.patient_id)?.name || 'Paciente'} · {r.filename}</h3><p>{r.collected_on.split('-').reverse().join('/')}</p><div className="table-scroll"><table className="lab-table"><thead><tr><th>Exame</th><th>Resultado</th><th>Referência</th></tr></thead><tbody>{r.exams.map((e,i) => <tr key={i}><td>{e.name}</td><td>{e.rawResult} {e.unit && !e.rawResult.includes(e.unit) ? e.unit : ''}</td><td>{e.reference || 'Não informada'}</td></tr>)}</tbody></table></div>{care.data.feedback.filter(f => f.report_id === r.id).map(f => <p className="whitespace-pre-wrap break-words" key={f.id}>{f.message}</p>)}<form onSubmit={e => { e.preventDefault(); void run(async () => { await send({ data: { reportId: r.id, patientId: r.patient_id, message: messages[r.id] || '' } }); setMessages(m => ({ ...m, [r.id]: '' })); }); }}><textarea className="account-input w-full mt-4" aria-label={`Feedback para ${r.filename}`} maxLength={4000} rows={3} required value={messages[r.id] || ''} onChange={e => setMessages(m => ({ ...m, [r.id]: e.target.value }))}/><Button className="mt-3" disabled={busy}><Send/>Enviar feedback ao paciente</Button></form></div>)}
  </>}{notice && <p role="status">{notice}</p>}</section>;
}