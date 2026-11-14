import { useId, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useServerFn } from '@tanstack/react-start';
import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts';
import { Watch, HeartPulse, Footprints, Droplets, MoonStar } from 'lucide-react';
import { readPatientHealth } from '@/lib/patient.functions';
import { examKey, latestWearableMetrics } from '@/lib/patient-data';
import { mapApiExam } from '@/lib/exam-api';
import { componentName, examFeedback } from '@/lib/exam-feedback';
import { Button } from '@/components/ui/button';

function usePatientHealth(patientId: string) {
  const read = useServerFn(readPatientHealth);
  return useQuery({ queryKey: ['patient-health', patientId], queryFn: () => read() });
}
const br = (date: string) => date.split('-').reverse().join('/');

// Quatro métricas fixas do wearable exibidas abaixo do resumo dos componentes, nesta ordem.
export const OVERVIEW_WEARABLE_IDS = ['resting_hr_bpm', 'steps', 'spo2_pct', 'sleep_duration_hours'] as const;
const overviewLabels: Record<(typeof OVERVIEW_WEARABLE_IDS)[number], string> = {
  resting_hr_bpm: 'Frequência cardíaca média em repouso',
  steps: 'Passos diários',
  spo2_pct: 'Oxigenação no sangue',
  sleep_duration_hours: 'Horas de sono',
};
const metricIcons = { resting_hr_bpm: HeartPulse, steps: Footprints, spo2_pct: Droplets, sleep_duration_hours: MoonStar };

export function WearableStrip({ patientId }: { patientId: string }) {
  const health = usePatientHealth(patientId);
  const metrics = latestWearableMetrics(health.data?.wearables ?? []);
  const shown = OVERVIEW_WEARABLE_IDS.flatMap(id => metrics.filter(m => m.id.endsWith(`|${id}`)).map(m => ({ ...m, metricId: id, name: overviewLabels[id], Icon: metricIcons[id] })));
  return <section className="overview-wearables" aria-label="Últimos dados do wearable">
    {health.isPending ? <p className="text-sm text-muted-foreground">Carregando wearables…</p> : shown.length === 0
      ? <p className="text-sm text-muted-foreground flex items-center gap-2"><Watch size={16}/>Sem dados de wearable salvos. Ausência de dado não é valor zero.</p>
      : shown.map(m => <article key={m.id} className="overview-metric" data-metric={m.metricId}><div className="overview-metric-icon"><m.Icon size={24} strokeWidth={1.5} aria-hidden="true"/></div><span>{m.name}</span><strong>{m.value.toLocaleString('pt-BR')} <small>{m.unit}</small></strong><small>{br(m.date)} · {m.source}</small></article>)}
  </section>;
}

type Category = 'in' | 'out' | 'none';
const categories: { id: Category; label: string; color: string }[] = [
  { id: 'in', label: 'Dentro da referência', color: 'var(--donut-in)' },
  { id: 'out', label: 'Fora da referência', color: 'var(--donut-out)' },
  { id: 'none', label: 'Sem classificação disponível', color: 'var(--donut-none)' },
];

export function ResultsDonut({ patientId }: { patientId: string }) {
  const health = usePatientHealth(patientId);
  const [filter, setFilter] = useState<Category | null>(null);
  const [hover, setHover] = useState<Category | null>(null);
  const gradientId = useId().replace(/:/g, '');
  const items = useMemo(() => {
    const reports = [...(health.data?.reports ?? [])].sort((a, b) => b.collected_on.localeCompare(a.collected_on));
    const found = new Map<string, { name: string; date: string; label: string; category: Category }>();
    for (const report of reports) for (const raw of report.exams) {
      const exam = mapApiExam(raw as unknown as Record<string, unknown>);
      if (found.has(examKey(exam))) continue;
      const fb = examFeedback(exam);
      found.set(examKey(exam), { name: componentName(exam.name), date: report.collected_on, label: fb.label, category: fb.tone === 'success' ? 'in' : fb.tone === 'warning' ? 'out' : 'none' });
    }
    return [...found.values()];
  }, [health.data]);
  const data = categories.map(c => ({ ...c, value: items.filter(i => i.category === c.id).length }));
  const selected = data.find(d => d.id === (hover ?? filter));
  const total = items.length;
  if (health.isPending) return null;
  return <section className="overview-donut account-section">
    <div className="overview-donut-chart" role="img" aria-label={`${total} componentes: ${data.map(d => `${d.value} ${d.label.toLowerCase()}`).join(', ')}`}>
      <ResponsiveContainer width="100%" height="100%"><PieChart>
        <defs>{data.map(d => <linearGradient key={d.id} id={`${gradientId}-${d.id}`} x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor={`var(--donut-${d.id}-light)`}/><stop offset="100%" stopColor={d.color}/></linearGradient>)}</defs>
        <Pie data={total ? data.filter(d => d.value) : [{ id: 'empty', value: 1 }]} dataKey="value" nameKey="label" innerRadius="76%" outerRadius="94%" startAngle={90} endAngle={-270} paddingAngle={data.filter(d => d.value).length > 1 ? 5 : 0} cornerRadius={7} stroke="none" isAnimationActive={false} onMouseEnter={(d: { id?: Category }) => setHover(d.id ?? null)} onMouseLeave={() => setHover(null)} onClick={(d: { id?: Category }) => { const id = d.id; if (id && categories.some(c => c.id === id)) setFilter(f => f === id ? null : id); }}>
          {total ? data.filter(d => d.value).map(d => <Cell key={d.id} fill={`url(#${gradientId}-${d.id})`} opacity={!hover && !filter || (hover ?? filter) === d.id ? 1 : .35} cursor="pointer"/>) : <Cell fill="var(--border)"/>}
        </Pie>
      </PieChart></ResponsiveContainer>
      <div className="overview-donut-center" aria-hidden="true"><span>{selected ? 'COMPONENTES' : 'TOTAL'}</span><strong>{selected?.value ?? total}</strong><small>{selected ? `${total ? Math.round(selected.value / total * 100) : 0}% do total` : 'componentes'}</small></div>
    </div>
    <div className="overview-donut-summary">
      <h2>Resumo dos componentes</h2>
      <p className="text-xs text-muted-foreground">Cada componente conta uma vez, pelo resultado mais recente. Classificação conforme o laudo/serviço.</p>
      <div className="overview-legend">{data.map(d => <Button key={d.id} variant="ghost" className="overview-category" data-category={d.id} aria-pressed={filter === d.id} onMouseEnter={() => setHover(d.id)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(d.id)} onBlur={() => setHover(null)} onClick={() => setFilter(f => f === d.id ? null : d.id)}><i aria-hidden="true"/><span>{d.label}</span><strong>{d.value}</strong><small>{total ? Math.round(d.value / total * 100) : 0}%</small></Button>)}</div>
      {filter && <ul className="overview-list">{items.filter(i => i.category === filter).map(i => <li key={i.name + i.date}>{i.name} <small>· {i.label} · {br(i.date)}</small></li>)}</ul>}
    </div>
  </section>;
}
