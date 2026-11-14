import { componentName, componentExplanation, examFeedback } from '@/lib/exam-feedback';
import { FileText } from 'lucide-react';
import { type ExtractedReport } from '@/lib/pdf-extraction';

export function ImportedReports({ reports }: { reports: ExtractedReport[] }) {
  if (!reports.length) return null;
  return <section className="panel"><div className="panel-heading"><div><h2 className="flex items-center gap-2"><FileText size={18}/>Exames importados nesta sessão</h2><p>Extraídos dos seus PDFs · Separados dos dados de demonstração</p></div></div>{reports.map(report => <div key={report.id}>
    <div className="report-header flex-wrap"><strong className="break-all">{report.filename}</strong><span className="break-words">{report.patient || 'Paciente não identificado'} · Coleta {report.collected || 'não identificada'}</span></div>
    <div className="table-scroll"><table className="lab-table"><thead><tr><th>Biomarcador</th><th>Resultado</th><th>Referência do laudo</th><th>Comparação</th></tr></thead><tbody>{report.exams.map((exam, index) => { const status = examFeedback(exam); return <tr key={index}><td><strong>{componentName(exam.name)}</strong><p className="text-xs text-muted-foreground">{componentExplanation(exam)}</p><div className="loinc">{exam.feedbackSource === 'render-api' ? 'Extração Render' : 'PDF local'} · Sem LOINC validado</div></td><td className="tabular-nums">{exam.rawResult}{exam.unit && !exam.rawResult.includes(exam.unit) ? ` ${exam.unit}` : ''}</td><td>{exam.reference || 'Não identificada'}</td><td><span className={`pill ${status.tone}`}>{status.label}</span><p className="text-xs text-muted-foreground mt-2">{status.reason}</p></td></tr>; })}</tbody></table></div>
  </div>)}<div className="table-foot">Conferência humana necessária · Sem diagnóstico · Não altera os gráficos e alertas demonstrativos.</div></section>;
}