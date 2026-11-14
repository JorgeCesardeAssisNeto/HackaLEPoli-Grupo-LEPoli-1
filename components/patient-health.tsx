import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useServerFn } from '@tanstack/react-start';
import { Activity, ArrowLeft, ArrowRight, FileText, Pause, Play, Plus, RefreshCw, Watch, Download, Upload, LoaderCircle, Copy, ExternalLink } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { PdfImport } from './pdf-import';
import { supabase } from '@/integrations/supabase/client';
import { readPatientHealth, savePatientReport, saveWearableRecords } from '@/lib/patient.functions';
import { examKey, metricMeaning, reportSeries, saveReportSchema, wearableImportSchema, latestWearableMetrics } from '@/lib/patient-data';
import { type ExtractedReport } from '@/lib/pdf-extraction';
import { wearableSources, type RemoteWearable, type wearableSourceSchema } from '@/lib/wearable-integration';
import type { z } from 'zod';
import { toast } from 'sonner';
import { parseWearableCsv } from '@/lib/care-data';
import { PatientCare } from './patient-care';
import { PatientAppointments } from './patient-appointments';
import { authorizeWearable, synchronizeWearable } from '@/lib/clinical.functions';
import { alertTone } from '@/lib/health-api';
import type { ClinicalAlert } from '@/lib/clinical-contract';
import { componentName, componentExplanation, examFeedback } from '@/lib/exam-feedback';
import { mapApiExam } from '@/lib/exam-api';
import {
  causalAnswersToFactors,
  defaultCausalAnswers,
  type CausalQuestionAnswers,
} from '@/lib/causal-questions';
import { CausalQuestionsPanel } from './causal-questions';

export function PatientHealth({ patientId, doctors }: { patientId: string; doctors: { id: string; name: string }[] }) {
  const read = useServerFn(readPatientHealth), save = useServerFn(savePatientReport), saveWearable = useServerFn(saveWearableRecords);
  const authorizeRemote = useServerFn(authorizeWearable), synchronize = useServerFn(synchronizeWearable);
  const [reportsConsented, setReportsConsented] = useState(false);
  const [evaluationBusy, setEvaluationBusy] = useState(false), [evaluationError, setEvaluationError] = useState('');
  const [evaluationResult, setEvaluationResult] = useState<{ alerts: ClinicalAlert[]; sentCount: number; syncedAt: string } | null>(null);
  const client = useQueryClient();
  const health = useQuery({ queryKey: ['patient-health', patientId], queryFn: () => read() });
  const [importOpen, setImportOpen] = useState(false), [slide, setSlide] = useState(0), [paused, setPaused] = useState(false), [hovered, setHovered] = useState(false), [selected, setSelected] = useState('');
  const [source, setSource] = useState('Fitbit'), [wearableBusy, setWearableBusy] = useState(false), [wearableError, setWearableError] = useState(''), [wearableNotice, setWearableNotice] = useState('');
  const [deviceSource, setDeviceSource] = useState<z.infer<typeof wearableSourceSchema>>('fitbit');
  const [deviceStatus, setDeviceStatus] = useState('');
  const [portalBusy, setPortalBusy] = useState(false);
  const [connectionPage, setConnectionPage] = useState('');
  const [remoteMetrics, setRemoteMetrics] = useState<RemoteWearable[]>([]);
  const syncInFlight = useRef(false);
  const consentRef = useRef(false);
  const [causalAnswers, setCausalAnswers] = useState<CausalQuestionAnswers>(defaultCausalAnswers);
  const answersRef = useRef<CausalQuestionAnswers>(defaultCausalAnswers);
  const syncCache = useQuery<{ metrics: RemoteWearable[]; alerts: ClinicalAlert[]; sentCount: number; syncedAt: string; demonstration?: boolean }>({ queryKey: ['rook-sync', patientId], enabled: false, queryFn: async () => { throw new Error('Sincronize o wearable para atualizar.'); } });
  useEffect(() => {
    const consent = sessionStorage.getItem(`rook-report-consent:${patientId}`) === 'true';
    setReportsConsented(consent); consentRef.current = consent;
    const success = sessionStorage.getItem('rook-return-message'), failure = sessionStorage.getItem('rook-return-error');
    if (success) { toast.success(success); sessionStorage.removeItem('rook-return-message'); }
    if (failure) { toast.error(failure); setWearableError(failure); sessionStorage.removeItem('rook-return-error'); }
  }, [patientId]);
  useEffect(() => { if (syncCache.data?.demonstration === false) { setRemoteMetrics(syncCache.data.metrics); setEvaluationResult(syncCache.data); } else { setRemoteMetrics([]); setEvaluationResult(null); } }, [syncCache.data]);
  const [detail, setDetail] = useState<{ value: number | null; reference: string; exam: ExtractedReport['exams'][number] } | null>(null);
  const csvRef = useRef<HTMLInputElement>(null);
  const reports = useMemo(() => (health.data?.reports ?? []).map(report => ({ ...report, exams: report.exams.map(exam => mapApiExam(exam as unknown as Record<string, unknown>)) })), [health.data]);
  const latest = useMemo(() => {
    const found = new Map<string, { exam: ExtractedReport['exams'][number]; date: string }>();
    for (const report of reports) for (const exam of report.exams) if (!found.has(examKey(exam))) found.set(examKey(exam), { exam, date: report.collected_on });
    return [...found.values()];
  }, [health.data]);
  const activeKey = selected || (latest[0] ? examKey(latest[0].exam) : '');
  const active = latest.find(item => examKey(item.exam) === activeKey);
  const chartLabel = componentName(active?.exam.name);
  const points = reportSeries(reports, activeKey);
  const chartColor = `var(--chart-${Math.max(0, latest.findIndex(item => examKey(item.exam) === activeKey)) % 5 + 1})`;
  const overview = useMemo(() => [
    ...latest.map(item => ({ kind: 'exam' as const, ...item })),
    ...latestWearableMetrics(health.data?.wearables ?? []).map(item => ({ kind: 'wearable' as const, origin: 'arquivo', ...item })),
    ...latestWearableMetrics(remoteMetrics.map(row => ({ measured_on: row.date, source: 'ROOK', metrics: row }))).map(item => ({ kind: 'wearable' as const, origin: 'ROOK', ...item })),
  ], [latest, health.data?.wearables, remoteMetrics]);
  const slideCount = Math.max(1, Math.ceil(overview.length / 3));
  useEffect(() => {
    if (paused || hovered || slideCount < 2 || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const timer = window.setInterval(() => setSlide(value => (value + 1) % slideCount), 14000);
    return () => window.clearInterval(timer);
  }, [paused, hovered, slideCount]);
  async function saveReport(report: ExtractedReport, file: File) {
    const collected = /^\d{2}\/\d{2}\/\d{4}$/.test(report.collected) ? report.collected.split('/').reverse().join('-') : report.collected;
    const data = saveReportSchema.parse({ ...report, collected, identityConfirmed: true });
    const path = `${patientId}/${report.id}.pdf`;
    const { error } = await supabase.storage.from('patient-reports').upload(path, file, { contentType: 'application/pdf', upsert: false });
    if (error) throw new Error('Não foi possível armazenar o PDF. Tente novamente.');
    try { await save({ data }); } catch (err) { await supabase.storage.from('patient-reports').remove([path]); throw err; }
    await Promise.all([client.invalidateQueries({ queryKey: ['patient-health', patientId] }), client.invalidateQueries({ queryKey: ['care'] })]); setImportOpen(false);
  }
  const syncWearable = useCallback(async () => {
    if (syncInFlight.current) return;
    syncInFlight.current = true; setEvaluationBusy(true); setEvaluationError(''); setWearableError('');
    try {
      const response = await synchronize({ data: { transmitReports: consentRef.current, factors: causalAnswersToFactors(answersRef.current) } });
      if (response.error || !response.result) throw new Error(response.error || 'Sincronização não concluída.');
      setRemoteMetrics(response.result.metrics); setEvaluationResult(response.result);
      client.setQueryData(['rook-sync', patientId], response.result);
      await Promise.all([client.invalidateQueries({ queryKey: ['patient-health', patientId] }), client.invalidateQueries({ queryKey: ['api-metrics'] }), client.invalidateQueries({ queryKey: ['api-alerts', patientId] })]);
      setDeviceStatus(response.result.metrics.length ? 'Medições reais sincronizadas' : 'Aguardando medições reais do dispositivo');
      toast.success(`${response.result.sync.records_processed} registros processados · ${response.result.sync.alerts_generated} alertas gerados.`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Não foi possível sincronizar.';
      setRemoteMetrics([]); setEvaluationResult(null); client.removeQueries({ queryKey: ['rook-sync', patientId], exact: true });
      setEvaluationError(message); setWearableError(message); toast.error(message);
    } finally { setEvaluationBusy(false); syncInFlight.current = false; }
  }, [synchronize, client, patientId]);
  const loadPortal = useCallback(async () => {
    setPortalBusy(true); setWearableError(''); setConnectionPage('');
    try {
      const response = await authorizeRemote({ data: { source: deviceSource } });
      if (response.error || !response.authorization) throw new Error(response.error || 'Portal ROOK indisponível.');
      const url = response.authorization.connection_page_url || response.authorization.authorization_url;
      if (!url) throw new Error('O serviço não retornou o endereço do portal ROOK. Tente novamente ou importe suas medições por CSV.');
      setConnectionPage(url);
    } catch (error) { setWearableError(error instanceof Error ? error.message : 'Não foi possível carregar o portal ROOK.'); }
    finally { setPortalBusy(false); }
  }, [authorizeRemote, deviceSource]);
  useEffect(() => { void loadPortal(); }, [loadPortal]);
  async function importWearable(file?: File) {
    if (!file) return;
    setWearableBusy(true); setWearableError(''); setWearableNotice('');
    try {
      if (file.size > 5 * 1024 * 1024) throw new Error('O arquivo deve ter até 5 MB.');
      const data = file.name.toLowerCase().endsWith('.csv') ? parseWearableCsv(await file.text(), source) : wearableImportSchema.parse(JSON.parse(await file.text()));
      const result = await saveWearable({ data });
      await client.invalidateQueries({ queryKey: ['patient-health', patientId] });
      setWearableNotice(`${result.count} dias de medições do arquivo salvos na sua conta. Não é sincronização automática.`);
    } catch (err) { setWearableError(err instanceof Error && 'issues' in err ? 'Arquivo incompatível. Confira datas, valores e formato. Sono deve estar entre 0 e 24 horas; passos não podem ser negativos.' : err instanceof Error ? err.message : 'Não foi possível importar.'); }
    finally { setWearableBusy(false); if (csvRef.current) csvRef.current.value = ''; }
  }
  async function download(path: string) {
    const { data, error } = await supabase.storage.from('patient-reports').download(path);
    if (error) { setWearableError('Não foi possível baixar o laudo.'); return; }
    const url = URL.createObjectURL(data), a = document.createElement('a'); a.href = url; a.download = reports.find(report => report.storage_path === path)?.filename ?? 'laudo.pdf'; a.click(); URL.revokeObjectURL(url);
  }
  return <div className="patient-health">
    <section className="patient-overview" aria-label="Resumo dos exames"><div className="section-heading"><h2><Activity/>Seus exames, em perspectiva</h2><Button onClick={() => setImportOpen(true)}><Plus/>Anexar exame</Button></div>
      {health.isPending ? <p role="status">Carregando seus exames…</p> : health.isError ? <div role="alert">Não foi possível carregar seus dados. <Button variant="outline" onClick={() => health.refetch()}>Tentar novamente</Button></div> : overview.length === 0 ? <div className="patient-empty"><FileText size={32}/><h3>Seu histórico começa com o primeiro registro.</h3><p>Nenhum exame ou medição de wearable salvo na sua conta.</p><Button variant="outline" onClick={() => setImportOpen(true)}><Plus/>Anexar meu primeiro exame</Button></div> : <>
        <div className="patient-carousel" onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)} onFocusCapture={() => setHovered(true)} onBlurCapture={() => setHovered(false)}><div className="patient-summary-grid">{overview.slice((slide % slideCount) * 3, (slide % slideCount) * 3 + 3).map(item => {
          if (item.kind === 'wearable') return <article className="patient-result" key={`wearable:${item.id}`}><div className="flex flex-wrap justify-between gap-3"><span className="text-muted-foreground text-xs">{item.date.split('-').reverse().join('/')}</span><span className="pill neutral"><Watch size={12}/>Wearable · {item.origin}</span></div><h3>{item.name}</h3><div className="patient-result-value">{item.value.toLocaleString('pt-BR')} <small>{item.unit}</small></div><p>Origem: {item.source}</p><p>{item.meaning}</p></article>;
          const { exam, date } = item;
          return <article className="patient-result" key={examKey(exam)}><div className="flex justify-between gap-3"><span className="text-muted-foreground text-xs">{date.split('-').reverse().join('/')}</span><span className={`pill ${examFeedback(exam).tone}`}>{examFeedback(exam).label}</span></div><h3>{componentName(exam.name)}</h3><div className="patient-result-value">{exam.value === null ? exam.rawResult : exam.value.toLocaleString('pt-BR')} <small>{exam.value === null ? '' : exam.unit}</small></div><p>Referência: {exam.reference || 'Não informada'}</p><p>{componentExplanation(exam)}</p><p>{examFeedback(exam).reason}</p></article>; })}</div></div>
        <div className="flex items-center justify-end gap-2 mt-3"><span className="text-xs text-muted-foreground mr-2">{(slide % slideCount) + 1} / {slideCount}</span><Button variant="outline" size="icon" aria-label="Registros anteriores" disabled={slideCount < 2} onClick={() => setSlide(value => (value - 1 + slideCount) % slideCount)}><ArrowLeft/></Button><Button variant="ghost" size="icon" aria-label={paused ? 'Retomar carrossel' : 'Pausar carrossel'} onClick={() => setPaused(!paused)}>{paused ? <Play/> : <Pause/>}</Button><Button variant="outline" size="icon" aria-label="Próximos registros" disabled={slideCount < 2} onClick={() => setSlide(value => (value + 1) % slideCount)}><ArrowRight/></Button></div>
      </>}
      <p className="text-xs text-muted-foreground mt-4">Comparação com a referência do laudo, não um diagnóstico. As explicações são educativas.</p>
    </section>
    <section className="account-section"><div className="section-heading mt-0"><h2>Histórico dos exames</h2>{latest.length > 0 && <select aria-label="Biomarcador do histórico" className="account-input patient-metric-select" value={activeKey} onChange={event => { setSelected(event.target.value); setDetail(null); }}>{latest.map(({ exam }) => <option key={examKey(exam)} value={examKey(exam)}>{exam.name} · {exam.unit || 'sem unidade'}</option>)}</select>}</div><div className="patient-history"><div className="patient-line-chart">{points.length > 0 ? <ResponsiveContainer width="100%" height="100%"><LineChart data={points} margin={{ top: 20, right: 20, left: 0, bottom: 20 }} onMouseMove={state => { const point = points[state.activeTooltipIndex ?? -1]; if (point) setDetail(point); }}><CartesianGrid stroke="var(--border)" vertical={false}/><XAxis dataKey="date" tickFormatter={value => String(value).split('-').reverse().join('/')} tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}/><YAxis domain={['auto', 'auto']} tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}/><Tooltip contentStyle={{ background: 'var(--card)', borderColor: 'var(--border)', color: 'var(--foreground)' }}/><Line dataKey="value" name={chartLabel} stroke={chartColor} strokeWidth={2.5} dot={{ r: 5 }} activeDot={{ r: 7 }} isAnimationActive={false}/></LineChart></ResponsiveContainer> : <div className="patient-empty"><Activity size={30}/><p>{latest.length ? 'Sem valores numéricos comparáveis para este exame.' : 'Ainda não há resultados para o histórico.'}</p></div>}</div><aside className="patient-metric-detail"><span className="eyebrow">SOBRE O BIOMARCADOR</span><h3>{active?.exam.name || 'Seu acompanhamento'}</h3><p>{active ? componentExplanation(active.exam) : 'Os resultados dos seus laudos aparecerão aqui, com a data de coleta e a referência original.'}</p>{active && <><dl><dt>Resultado {detail ? 'selecionado' : 'mais recente'}</dt><dd>{detail?.value ?? active.exam.value ?? active.exam.rawResult} {active.exam.unit}</dd><dt>Referência do laudo</dt><dd>{(detail?.reference ?? active.exam.reference) || 'Não informada'}</dd></dl><p>{examFeedback(detail?.exam ?? active.exam).label}</p><p>{examFeedback(detail?.exam ?? active.exam).reason}</p>{points.length === 1 && <p className="text-xs">Uma coleta disponível. A evolução aparece quando houver novas coletas comparáveis.</p>}</>}</aside></div></section>
    <PatientCare doctors={doctors}/>
    <section className="account-section" aria-label="Avaliação autenticada dos exames">
      <div className="section-heading mt-0"><h2><Activity/>Integração dos exames</h2><span role="status" className={`pill ${evaluationError ? 'danger' : evaluationResult ? 'success' : 'neutral'}`}>{evaluationBusy ? 'Sincronizando…' : evaluationError ? 'Falha na integração' : evaluationResult ? 'Sincronização autenticada' : 'Aguardando envio'}</span></div>
      <p className="text-sm text-muted-foreground mb-4">Avaliação dos últimos 14 dias com dados retornados pelo Render. O modelo é experimental e não fornece diagnóstico.</p>
      <CausalQuestionsPanel
        compact
        answers={causalAnswers}
        onChange={next => { setCausalAnswers(next); answersRef.current = next; }}
        disabled={evaluationBusy}
      />
      <label className="flex items-start gap-3 my-4 text-sm"><input type="checkbox" checked={reportsConsented} disabled={evaluationBusy} onChange={event => { setReportsConsented(event.target.checked); consentRef.current = event.target.checked; sessionStorage.setItem(`rook-report-consent:${patientId}`, String(event.target.checked)); setEvaluationResult(null); }}/><span>Autorizo o envio dos meus exames salvos ao Render para a avaliação junto às medições do wearable. Suas respostas da inferência causal acima acompanham o envio para ajustar os fatores de confusão.</span></label>
      <Button disabled={!reportsConsented || !reports.length || evaluationBusy || health.isError} onClick={() => void syncWearable()}>{evaluationBusy ? <LoaderCircle className="animate-spin motion-reduce:animate-none"/> : <RefreshCw/>}{evaluationBusy ? 'Enviando exames…' : 'Enviar exames e atualizar alertas'}</Button>
      {evaluationError && <p role="alert" className="mt-3 text-danger">{evaluationError}</p>}
      {evaluationResult && <><p className="mt-3 text-sm text-muted-foreground">{evaluationResult.sentCount} biomarcadores enviados · {new Date(evaluationResult.syncedAt).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' })} · Saída experimental do modelo, não um diagnóstico.</p>{evaluationResult.alerts.length === 0 ? <p className="mt-3 text-sm">Nenhum alerta retornado pelo serviço. Isso não comprova ausência de risco.</p> : evaluationResult.alerts.map(alert => <article className="panel p-4 mt-3" key={alert.id}><div className="flex flex-wrap gap-2 items-center"><h3 className="text-sm font-semibold">{alert.target_id}</h3><span className={`pill ${alertTone(alert.alert_level)}`}>{alert.alert_level}</span><span className="pill neutral">{alert.status}</span></div><p className="text-sm mt-3 whitespace-pre-wrap break-words">{alert.clinical_rationale}</p>{alert.recommended_action && <p className="text-sm mt-2 text-muted-foreground">{alert.recommended_action}</p>}</article>)}</>}
    </section>
    <PatientAppointments patientId={patientId} doctors={doctors}/>
    <section className="account-section"><div className="section-heading mt-0"><h2><Watch/>Wearables</h2><span className="pill neutral">{evaluationBusy ? 'Sincronizando…' : remoteMetrics.length ? 'Medições reais ROOK' : 'Sem medições reais ROOK'}</span></div><div className="patient-wearable"><div><h3>Conectar pelo portal ROOK</h3><p>Abra o portal ROOK, escolha a marca do seu dispositivo, entre na conta do fabricante e autorize o compartilhamento. Mantenha o relógio sincronizado com o aplicativo da marca. Depois, volte aqui e clique em “Sincronizar Wearable” para buscar suas medições.</p><div className="flex flex-wrap gap-3 mt-4"><select aria-label="Marca do wearable" className="account-input" value={deviceSource} onChange={event => { const next = wearableSources.find(item => item.id === event.target.value); if (next) setDeviceSource(next.id); setDeviceStatus(''); setConnectionPage(''); }} disabled={portalBusy}>{wearableSources.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>{connectionPage ? <Button size="lg" asChild><a href={connectionPage} target="_blank" rel="noopener noreferrer"><ExternalLink/>Abrir portal ROOK</a></Button> : <Button disabled={portalBusy} onClick={() => void loadPortal()}>{portalBusy ? <LoaderCircle className="animate-spin motion-reduce:animate-none"/> : <RefreshCw/>}{portalBusy ? 'Carregando portal ROOK…' : 'Tentar carregar portal ROOK'}</Button>}</div><div className="flex flex-wrap items-center gap-2 mt-4"><code className="text-xs text-muted-foreground break-all">patient_id: {patientId}</code><Button variant="outline" size="icon" aria-label="Copiar patient_id" title="Copiar ID" onClick={() => void navigator.clipboard.writeText(patientId).then(() => toast.success('ID copiado.')).catch(() => toast.error('Não foi possível copiar o ID.'))}><Copy/></Button></div><div className="flex flex-wrap gap-3 mt-3"><Button variant="outline" disabled={evaluationBusy || wearableBusy} onClick={() => void syncWearable()}><RefreshCw/>{evaluationBusy ? 'Sincronizando…' : 'Sincronizar Wearable'}</Button></div>{deviceStatus && <p role="status" className="mt-3 text-sm">{deviceStatus}</p>}{remoteMetrics.length > 0 && <p className="mt-3 text-sm text-muted-foreground">{remoteMetrics.length} dias retornados pelo Render.</p>}</div><div><h3>Importação manual CSV</h3><p>Alternativa quando a conexão do dispositivo estiver indisponível. Selecione a origem e envie somente suas medições reais.</p><div className="flex flex-wrap items-center gap-3 mt-4"><select className="account-input" aria-label="Origem dos dados CSV" value={source} onChange={e => setSource(e.target.value)}>{['Garmin','Fitbit','Oura','Apple Health','Samsung Health'].map(s => <option key={s}>{s}</option>)}</select><input ref={csvRef} type="file" accept=".csv,text/csv" aria-label="Arquivo CSV do wearable" disabled={wearableBusy} onChange={e => void importWearable(e.target.files?.[0])} className="sr-only" tabIndex={-1}/><Button type="button" size="lg" className="w-full sm:w-auto" disabled={wearableBusy} onClick={() => csvRef.current?.click()}>{wearableBusy ? <LoaderCircle className="animate-spin motion-reduce:animate-none"/> : <Upload/>}{wearableBusy ? 'Enviando dados…' : 'Enviar arquivo CSV'}</Button></div><p>Uma linha por dia; datas AAAA-MM-DD. Sono em horas, frequência em bpm, VFC em ms e oxigenação (SpO₂) em %. Deixe células vazias quando não houver medição. Até 5 MB e 1.000 dias.</p><Button variant="outline" onClick={() => { const url = URL.createObjectURL(new Blob(['date,steps,resting_hr_bpm,sleep_duration_hours,hrv_rmssd_ms,spo2_pct\n'], { type: 'text/csv' })); const a = document.createElement('a'); a.href = url; a.download = 'modelo-wearable.csv'; a.click(); URL.revokeObjectURL(url); }}><Download/>Baixar modelo CSV</Button>{wearableBusy && <p role="status">Importando medições…</p>}</div></div>{wearableError && <p role="alert" className="patient-service-error">{wearableError}</p>}{wearableNotice && <p role="status" className="mt-4 text-success">{wearableNotice}</p>}{health.data?.wearables.map(record => <div className="patient-file-row" key={record.id}><Watch size={18}/><div><strong>{record.measured_on.split('-').reverse().join('/')} · {record.source.replace('export:', '')}</strong><p>{Object.entries(record.metrics && typeof record.metrics === 'object' && !Array.isArray(record.metrics) ? record.metrics : {}).map(([key, value]) => `${({ steps: 'Passos', resting_hr_bpm: 'FC repouso (bpm)', sleep_duration_hours: 'Sono (h)', hrv_rmssd_ms: 'VFC (ms)', spo2_pct: 'SpO₂ (%)' } as Record<string,string>)[key] || key}: ${value}`).join(' · ')}</p></div></div>)}</section>

    {reports.length > 0 && <section className="account-section"><h2>Laudos salvos</h2>{reports.map(report => <div className="patient-file-row" key={report.id}><FileText size={20}/><div className="min-w-0 flex-1"><strong>{report.filename}</strong><p>{report.collected_on.split('-').reverse().join('/')} · {report.exams.length} resultados · {report.document_patient || 'Identificação conferida pelo paciente'}</p></div><Button variant="outline" size="icon" aria-label={`Baixar ${report.filename}`} title="Baixar laudo" onClick={() => download(report.storage_path)}><Download/></Button></div>)}</section>}
    <Dialog open={importOpen} onOpenChange={setImportOpen}><DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto"><DialogTitle>Anexar exame à minha conta</DialogTitle><DialogDescription>Confira os resultados e confirme que o documento é seu antes de salvar.</DialogDescription><PdfImport persistent onImport={saveReport}/></DialogContent></Dialog>
  </div>;
}