import { useRef, useState } from 'react';
import { CheckCheck, FileText, Plus, ScanLine } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { componentName, examFeedback } from '@/lib/exam-feedback';
import { extractRemoteExam, loadComponentExplanations, reviseImportedExam } from '@/lib/exam-api';
import { type ExtractedReport } from '@/lib/pdf-extraction';

export function PdfImport({ onImport, persistent = false }: { onImport: (report: ExtractedReport, file: File) => void | Promise<void>; persistent?: boolean }) {
  const [file, setFile] = useState<File | null>(null);
  const [report, setReport] = useState<ExtractedReport | null>(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [transmissionConfirmed, setTransmissionConfirmed] = useState(false);
  const [serviceMessage, setServiceMessage] = useState('');
  const [excluded, setExcluded] = useState<number[]>([]);
  const request = useRef(0);
  async function read() {
    if (!file || busy || !transmissionConfirmed) return;
    const id = ++request.current;
    setBusy(true); setError(''); setReport(null); setConfirmed(false); setExcluded([]); setServiceMessage('');
    try { const result = await extractRemoteExam(file); if (id === request.current) { setReport(result); setServiceMessage('Consultando explicações dos componentes no Render…'); const enriched = await loadComponentExplanations(result); if (id === request.current) { setReport(enriched); setServiceMessage('Resultados preservados; disponibilidade das explicações indicada em cada componente.'); } } }
    catch (err) { if (id === request.current) setError(err instanceof Error ? err.message : 'Não foi possível ler este PDF.'); }
    finally { if (id === request.current) setBusy(false); }
  }
  return <div className="min-w-0 space-y-4">
    {!report && <><div className="file-drop"><FileText className="mx-auto mb-3 text-primary" size={32}/><label htmlFor="exam-file" className="block break-all">{file?.name ?? 'Selecione um laudo em PDF ou imagem'}</label><input id="exam-file" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/png,image/jpeg,image/webp" disabled={busy} onChange={event => { setFile(event.target.files?.[0] ?? null); setTransmissionConfirmed(false); setError(''); }}/></div><p className="text-xs leading-5 text-muted-foreground">O documento será enviado ao Render para extração. O serviço pode usar Gemini ou recorrer ao modo local; o motor informado será mostrado após a leitura.</p><label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={transmissionConfirmed} disabled={busy} onChange={event => setTransmissionConfirmed(event.target.checked)}/>Autorizo o envio deste documento ao serviço de extração no Render.</label><Button onClick={read} disabled={!file || busy || !transmissionConfirmed}><ScanLine/>{busy ? 'Analisando exame' : 'Analisar exame'}</Button></>}
    {busy && <p role="status" className="text-sm text-muted-foreground">Analisando exame</p>}
    {error && <p role="alert" className="text-sm text-danger">{error}</p>}
    {report && <><div className="flex items-center gap-2 text-success"><CheckCheck size={20}/><strong>{report.exams.length} resultados identificados</strong></div><div className="min-w-0 text-xs leading-6 break-words [overflow-wrap:anywhere]"><strong>{report.filename}</strong><br/>Paciente no documento: {report.patient || 'Não identificado'}<br/>Coleta: {report.collected || 'Não identificada'}{report.laboratory && <><br/>{report.laboratory}</>}</div>
      <div className="max-h-80 overflow-auto"><table className="lab-table"><thead><tr><th>Incluir</th><th>Biomarcador</th><th>Resultado</th><th>Unidade</th><th>Referência</th><th>Situação</th></tr></thead><tbody>{report.exams.map((exam, index) => <tr key={index}><td><input type="checkbox" checked={!excluded.includes(index)} aria-label={`Incluir ${exam.name}`} onChange={event => setExcluded(previous => event.target.checked ? previous.filter(i => i !== index) : [...previous, index])} /></td><td><input aria-label={`Biomarcador ${index + 1}`} className="w-36 border border-input rounded bg-background p-1" value={exam.name} onChange={event => setReport({ ...report, exams: report.exams.map((item, i) => i === index ? reviseImportedExam(item, { name: event.target.value }) : item) })}/></td><td><input aria-label={`Resultado ${index + 1}`} className="w-32 border border-input rounded bg-background p-1" value={exam.rawResult} onChange={event => { const rawResult = event.target.value; setReport({ ...report, exams: report.exams.map((item, i) => i === index ? reviseImportedExam(item, { rawResult }) : item) }); }}/></td><td>{exam.unit || '—'}</td><td><input aria-label={`Referência ${index + 1}`} className="w-48 border border-input rounded bg-background p-1" value={exam.reference} onChange={event => setReport({ ...report, exams: report.exams.map((item, i) => i === index ? reviseImportedExam(item, { reference: event.target.value }) : item) })}/></td><td><span className={`pill ${examFeedback(exam).tone}`}>{examFeedback(exam).label}</span><p className="text-xs text-muted-foreground mt-2">{examFeedback(exam).reason}</p></td></tr>)}</tbody></table></div>
      {report.exams.map((exam, index) => <p key={`explanation-${index}`} className="text-xs text-muted-foreground"><strong>{componentName(exam.name)}:</strong> {exam.explanation || 'Explicação indisponível; consultando serviço de conhecimento.'}</p>)}
      {serviceMessage && <p role="status" className="text-xs text-muted-foreground">{serviceMessage}</p>}
      {report.warnings.map(warning => <p key={warning} className="text-xs text-warning">{warning}</p>)}
      <p className="text-xs text-muted-foreground">Extração automática sujeita a erros; confira cada valor e referência no documento original. Sem diagnóstico ou certificação clínica. {persistent ? 'Após sua confirmação, o PDF e os resultados serão salvos na sua conta no Lovable Cloud.' : 'Resultados mantidos somente nesta sessão.'}</p>
       {persistent && <label className="block text-sm">Data de coleta<input type="date" className="account-input mt-2 w-full" aria-label="Data de coleta" value={/^\d{2}\/\d{2}\/\d{4}$/.test(report.collected) ? report.collected.split('/').reverse().join('-') : report.collected} onChange={event => setReport({ ...report, collected: event.target.value })}/></label>}
      <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)}/>Conferi os resultados e a identificação do paciente no PDF.</label>
      {persistent && <p className="text-xs text-muted-foreground">Ao salvar, confirmo que este laudo pertence a mim e autorizo o armazenamento na minha conta.</p>}
      <div className="flex flex-wrap gap-2"><Button variant="outline" disabled={busy} onClick={() => { setReport(null); setConfirmed(false); }}>Selecionar outro PDF</Button><Button disabled={!confirmed || busy} onClick={async () => {
        const exams = report.exams.filter((exam, index) => !excluded.includes(index) && exam.name.trim()).map(exam => ({ ...exam, name: componentName(exam.name) }));
        if (!exams.length) { setError('Selecione ao menos um resultado.'); return; }
        if (!file) return;
        if (persistent && !report.collected) { setError('A data de coleta não foi identificada. Informe a data real conforme o documento antes de salvar.'); return; }
        setBusy(true); setError('');
         try {
           let storedFile = file;
           if (persistent && !/\.pdf$/i.test(file.name)) {
             const { jsPDF } = await import('jspdf');
             const bitmap = await createImageBitmap(file);
             const canvas = document.createElement('canvas'); canvas.width = bitmap.width; canvas.height = bitmap.height;
             const context = canvas.getContext('2d'); if (!context) throw new Error('Não foi possível preparar a imagem para armazenamento.');
             context.drawImage(bitmap, 0, 0); bitmap.close();
             const pdf = new jsPDF({ orientation: canvas.width > canvas.height ? 'landscape' : 'portrait', unit: 'px', format: [canvas.width, canvas.height] });
             pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, canvas.width, canvas.height);
             storedFile = new File([pdf.output('blob')], `${file.name}.pdf`, { type: 'application/pdf' });
           }
           await onImport({ ...report, filename: storedFile.name, exams }, storedFile);
         } catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível salvar.'); } finally { setBusy(false); }
      }}><Plus/>{busy ? 'Salvando…' : persistent ? 'Salvar exames na minha conta' : 'Adicionar resultados à sessão'}</Button></div></>}
  </div>;
}