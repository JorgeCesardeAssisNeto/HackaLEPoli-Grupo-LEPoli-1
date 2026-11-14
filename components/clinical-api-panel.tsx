import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Activity, Check, HeartPulse, LoaderCircle, Plus, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { alertTone, healthApi, LOCAL_SYNTHETIC, manualMetricSchema } from '@/lib/health-api';
import { causalContextSchema } from '@/lib/clinical-contract';
import {
  causalAnswersToFactors,
  defaultCausalAnswers,
  type CausalQuestionAnswers,
} from '@/lib/causal-questions';
import { CausalQuestionsPanel } from '@/components/causal-questions';
import { analytes } from '@/lib/health-data';
import { supabase } from '@/integrations/supabase/client';

const fields = [
  { key: 'steps', label: 'Passos', step: '1', min: 0 },
  { key: 'resting_hr_bpm', label: 'FC de repouso (bpm)', step: '0.1', min: 0.1 },
  { key: 'sleep_duration_hours', label: 'Sono (horas)', step: '0.1', min: 0, max: 24 },
  { key: 'caffeine_mg', label: 'Cafeína (mg)', step: '0.1', min: 0 },
  { key: 'hrv_rmssd_ms', label: 'HRV RMSSD (ms)', step: '0.1', min: 0 },
  { key: 'screen_time_min', label: 'Tempo de tela (min)', step: '0.1', min: 0 },
  { key: 'alcohol_units', label: 'Álcool (unidades)', step: '0.1', min: 0 },
  { key: 'sleep_stage_deep_pct', label: 'Sono profundo (%)', step: '0.1', min: 0, max: 100 },
] as const;
const errorToast = (error: Error) => toast.error(error.message || 'Não foi possível concluir a operação.');

function buildCausalContext(id: string, answers: CausalQuestionAnswers) {
  const factors = causalAnswersToFactors(answers);
  return causalContextSchema.parse({
    biomarkers: id === 'U0001'
      ? analytes.map(a => ({ name: a.name, value: a.value, unit: a.unit, collected_on: '2026-01-06' }))
      : [],
    ferritin_ng_ml: id === 'U0001' ? 97.5 : null,
    ...factors,
  });
}

export function ClinicalApiPanel({
  doctor,
  causalAnswers,
  onCausalAnswersChange,
}: {
  doctor: boolean;
  causalAnswers?: CausalQuestionAnswers;
  onCausalAnswersChange?: (next: CausalQuestionAnswers) => void;
}) {
  const [enabled, setEnabled] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const [patientId, setPatientId] = useState('U0001');
  const [draftId, setDraftId] = useState('U0001');
  const [manualOpen, setManualOpen] = useState(false);
  const [resolving, setResolving] = useState<string | null>(null);
  const [internalAnswers, setInternalAnswers] = useState<CausalQuestionAnswers>(defaultCausalAnswers);
  const answers = causalAnswers ?? internalAnswers;
  const setAnswers = onCausalAnswersChange ?? setInternalAnswers;
  const queryClient = useQueryClient();
  useEffect(() => {
    setEnabled(true);
    void supabase.auth.getSession().then(({ data }) => setSignedIn(Boolean(data.session)));
    const { data } = supabase.auth.onAuthStateChange((_event, session) => setSignedIn(Boolean(session)));
    return () => data.subscription.unsubscribe();
  }, []);
  const activeSession = signedIn || LOCAL_SYNTHETIC;
  const health = useQuery({ queryKey: ['api-health'], queryFn: ({ signal }) => healthApi.health(signal), enabled, retry: 1, refetchInterval: 60000 });
  const metrics = useQuery({ queryKey: ['api-metrics'], queryFn: ({ signal }) => healthApi.metrics(signal), enabled, retry: 1, refetchInterval: 60000 });
  const alerts = useQuery({ queryKey: ['api-alerts', patientId], queryFn: ({ signal }) => healthApi.alerts(patientId, signal), enabled: enabled && activeSession, retry: 1 });
  useEffect(() => { const error = health.error || metrics.error || alerts.error; if (error) errorToast(error); }, [health.error, metrics.error, alerts.error]);
  async function refresh(id: string) {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['api-alerts', id] }),
      queryClient.invalidateQueries({ queryKey: ['api-metrics'] }),
      queryClient.invalidateQueries({ queryKey: ['api-health'] }),
    ]);
  }
  const evaluation = useMutation({
    mutationFn: (id: string) => healthApi.evaluate(id, buildCausalContext(id, answers)),
    onSuccess: async (_, id) => {
      await refresh(id);
      toast.success('Avaliação de 14 dias com inferência causal concluída. Alertas atualizados.');
    },
    onError: errorToast,
  });
  const resolution = useMutation({
    mutationFn: ({ alertId }: { alertId: string; patientId: string }) => healthApi.resolve(alertId),
    onSuccess: async (_, vars) => { await refresh(vars.patientId); toast.success('Alerta marcado como resolvido.'); },
    onError: errorToast, onSettled: () => setResolving(null),
  });
  const ingestion = useMutation({ mutationFn: healthApi.ingest, onSuccess: async (_, metric) => { await refresh(metric.patient_id); setManualOpen(false); toast.success('Métrica de teste registrada na API. Alertas atualizados.'); }, onError: errorToast });
  const busy = !activeSession || evaluation.isPending || resolution.isPending || ingestion.isPending;
  const online = activeSession && alerts.isSuccess && !alerts.error;
  const error = health.error || metrics.error || alerts.error;
  return <section aria-label="Integração clínica" className="my-5">
    <div className="section-heading !mt-0 flex-wrap">
      <h2><Activity/>Integração clínica</h2>
      <div className="flex flex-wrap items-center gap-2">
        <span role="status" className={`pill ${online ? 'success' : health.isError ? 'danger' : 'neutral'}`}>
          {alerts.isFetching ? <LoaderCircle size={12} className="animate-spin motion-reduce:animate-none"/> : <span className="status-dot"/>}{!activeSession ? 'Login necessário' : online ? (LOCAL_SYNTHETIC && !signedIn ? 'Simulação local · sintética' : 'Autenticada · demonstração') : alerts.isError ? 'Indisponível' : 'Conectando…'}
        </span>
        <span className="pill neutral">{metrics.isError ? 'Alertas pendentes indisponíveis' : metrics.data ? `${metrics.data.pending_clinical_alerts} alertas pendentes · Sistema` : 'Carregando métricas…'}</span>
        <Button variant="outline" size="sm" disabled={busy} onClick={() => setManualOpen(true)}><Plus/>Inserir métrica manual</Button>
        <Button size="sm" disabled={busy} onClick={() => evaluation.mutate(patientId)}>{evaluation.isPending ? <LoaderCircle className="animate-spin motion-reduce:animate-none"/> : <RefreshCw/>}{evaluation.isPending ? 'Avaliando…' : 'Forçar avaliação'}</Button>
      </div>
    </div>
    <form className="flex flex-wrap items-end gap-2 mb-4" onSubmit={event => { event.preventDefault(); const id = draftId.trim(); if (id) setPatientId(id); }}>
      <div className="space-y-2 w-64 max-w-full"><Label htmlFor="api-patient">ID do paciente na API</Label><Input id="api-patient" value={draftId} onChange={event => setDraftId(event.target.value)} required disabled={busy}/></div>
      <Button variant="outline" size="sm" type="submit" disabled={busy || !draftId.trim()}>Consultar alertas</Button>
      <span className="text-xs text-muted-foreground pb-2 break-all">Paciente consultado: {patientId}</span>
    </form>
    <CausalQuestionsPanel
      answers={answers}
      onChange={setAnswers}
      onEvaluate={() => evaluation.mutate(patientId)}
      evaluating={evaluation.isPending}
      disabled={busy}
    />
    {error && <div role="alert" className="flex flex-wrap items-center gap-3 mb-3 text-sm text-danger"><span>{error.message}</span><Button variant="outline" size="sm" disabled={health.isFetching || metrics.isFetching || alerts.isFetching} onClick={() => refresh(patientId)}><RefreshCw/>Tentar novamente</Button></div>}
    {!activeSession && <p className="text-sm text-muted-foreground">Entre na sua conta para consultar alertas e enviar dados de demonstração.</p>}
    {activeSession && alerts.isPending && <p role="status" className="flex items-center gap-2 text-sm text-muted-foreground"><LoaderCircle size={16} className="animate-spin motion-reduce:animate-none"/>Carregando alertas…</p>}
    {alerts.isSuccess && alerts.data.length === 0 && <p className="text-sm text-muted-foreground">Nenhum alerta retornado para {patientId}.</p>}
    <div className="space-y-3">{alerts.data?.map(alert => <article className="panel p-4" key={alert.id}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2"><HeartPulse size={16} className="text-primary"/><h3 className="text-sm font-semibold break-all">{alert.target_id}</h3><span className={`pill ${alertTone(alert.alert_level)}`}>{alert.alert_level}</span><span className={`pill ${alert.status === 'RESOLVED' ? 'success' : 'neutral'}`}>{alert.status === 'RESOLVED' ? 'Resolvido' : alert.status}</span></div>
        {doctor && alert.status !== 'RESOLVED' && <Button variant="outline" size="sm" disabled={busy} aria-label={`Marcar como resolvido ${alert.target_id}`} onClick={() => { setResolving(alert.id); resolution.mutate({ alertId: alert.id, patientId }); }}>{resolving === alert.id ? <LoaderCircle className="animate-spin motion-reduce:animate-none"/> : <Check/>}Marcar como resolvido</Button>}
      </div>
      <p className="text-sm leading-6 mt-3 whitespace-pre-wrap break-words">{alert.clinical_rationale}</p>
      {alert.recommended_action && <p className="text-xs text-muted-foreground mt-2 break-words">{alert.recommended_action}</p>}
    </article>)}</div>
    <p className="text-xs text-muted-foreground mt-3">Alertas da API · Saída demonstrativa do modelo, não diagnóstico. Os exames e gráficos abaixo permanecem ilustrativos.</p>
    <Dialog open={manualOpen} onOpenChange={open => { if (!ingestion.isPending) setManualOpen(open); }}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-lg"><DialogHeader><DialogTitle>Inserir métrica manual</DialogTitle><DialogDescription>Modo de testes · Dados enviados à API para o paciente {patientId}. Use somente dados fictícios.</DialogDescription></DialogHeader>
        <form className="space-y-4" onSubmit={event => {
          event.preventDefault(); const form = new FormData(event.currentTarget);
          const values = Object.fromEntries(fields.map(field => [field.key, Number(form.get(field.key))]));
          const result = manualMetricSchema.safeParse({ ...values, patient_id: patientId, date: String(form.get('date')) });
          if (!result.success) { toast.error('Confira os valores das métricas antes de enviar.'); return; }
          ingestion.mutate(result.data);
        }}>
          <div className="space-y-2"><Label htmlFor="metric-date">Data</Label><Input id="metric-date" name="date" type="date" required disabled={ingestion.isPending}/></div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">{fields.map(field => <div className="space-y-2" key={field.key}><Label htmlFor={`metric-${field.key}`}>{field.label}</Label><Input id={`metric-${field.key}`} name={field.key} type="number" step={field.step} min={field.min} max={'max' in field ? field.max : undefined} required disabled={ingestion.isPending}/></div>)}</div>
          <Button type="submit" disabled={ingestion.isPending}>{ingestion.isPending ? <LoaderCircle className="animate-spin motion-reduce:animate-none"/> : <Plus/>}{ingestion.isPending ? 'Enviando…' : 'Enviar métrica de teste'}</Button>
        </form>
      </DialogContent>
    </Dialog>
  </section>;
}
