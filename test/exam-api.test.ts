import { afterEach, describe, expect, it, vi } from 'vitest';
vi.mock('@/lib/health-api', () => ({ API_BASE: 'https://hackalepoli.onrender.com' }));
import { extractRemoteExam, loadComponentExplanations, mapExtractionResponse, mapApiExam, reviseImportedExam } from '@/lib/exam-api';
import { examFeedback } from '@/lib/exam-feedback';
import { saveReportSchema, examSchema } from '@/lib/patient-data';
import { reportFhir } from '@/lib/pdf-extraction';
afterEach(() => vi.unstubAllGlobals());
const payload = { motor: 'Local Offline (Fallback automático)', cabecalho: { paciente: 'Paciente sintético', data_coleta: '2026-11-14' }, exames: [
  { analito: 'Glicose', resultado_bruto: '0 mg/dL', valor_numerico: 0, unidade: 'mg/dL', valores_referencia: '70 a 99', status_alterado: true },
  { analito: 'Anticorpos', resultado_bruto: 'Não reagente', valor_numerico: null, status_alterado: false },
  { analito: 'Ferritina', resultado_bruto: '40 ng/mL', valor_numerico: 40, unidade: 'ng/mL', valores_referencia: '15 a 150', status_alterado: null },
] };
describe('Render document extraction contract', () => {
  it('does not attach a catalog classification to a different verified document range across storage and FHIR', () => {
    const report = mapExtractionResponse({ motor: 'open_health_pdf_extractor_v3', extracted_text_preview: 'Ferritina\nResultado: 18.5 ng/mL\nReferencia: 30 a 150 ng/mL', exames: [{ analito: 'ferritina', value: 18.5, unit: 'ng/mL', reference_range: '15 a 150 ng/mL', status: 'NORMAL' }] }, 'different-range.pdf');
    const exam = examSchema.parse(report.exams[0]);
    expect(exam).toMatchObject({ reference: '30 a 150 ng/mL', status_alterado: null, classificationCode: '' });
    expect(JSON.stringify(reportFhir(report))).toContain('Não foi possível classificar');
  });
  it('preserves explicit null numeric results instead of taking a secondary number', () => {
    expect(mapApiExam({ analito: 'Teste', resultado_bruto: '< 0,5 mg/L', valor_numerico: null, value: 0.5 }).value).toBeNull();
  });
  it('verifies references beyond the truncated provider preview using the uploaded full text without adding exams', () => {
    const report = mapExtractionResponse({ motor: 'open_health_pdf_extractor_v3', extracted_text_preview: 'Paciente: Teste', exames: [{ analito: 'creatinina', value: 0.82, unit: 'mg/dL', status: 'NORMAL' }] }, 'full.pdf', 'Laboratório Teste\nData da Coleta 14/11/2026\nCreatinina\nResultado: 0,82 mg/dL\nReferência: 0,6 a 1,2 mg/dL\nFerritina\nResultado: 18.5 ng/mL');
    expect(report.exams).toHaveLength(1);
    expect(report.exams[0]).toMatchObject({ value: 0.82, reference: '0,6 a 1,2 mg/dL', status_alterado: null });
    expect(report.collected).toBe('14/11/2026');
  });
  it('retains the exact reference from a pipe-delimited document row', () => {
    const report = mapExtractionResponse({ motor: 'open_health_pdf_extractor_v3', extracted_text_preview: 'Creatinina | 0,82 | mg/dL | 0,6 a 1,2', exames: [{ analito: 'creatinina', value: 0.82, unit: 'mg/dL', status: 'NORMAL' }] }, 'table.pdf');
    expect(report.exams[0]?.reference).toBe('0,6 a 1,2');
  });
  it('keeps absent v3 laboratory, collection date and reference unknown despite provider defaults through validation and FHIR', () => {
    const report = mapExtractionResponse({ motor: 'open_health_pdf_extractor_v3', extracted_text_preview: 'Paciente: Segundo paciente\nSodio\nResultado: 140 mmol/L', cabecalho: { laboratorio: 'Open Health Lab Integration', data_coleta: '2026-11-14' }, exames: [{ analito: 'sodio', value: 140, unit: 'mmol/L', reference_range: '135 a 145 mmol/L', status: 'NORMAL' }] }, 'second.pdf');
    expect(report.collected).toBe(''); expect(report.laboratory).toBe('');
    expect(report.exams[0]).toMatchObject({ value: 140, unit: 'mmol/L', reference: '', status_alterado: null });
    const first = report.exams[0]; if (!first) throw new Error('Missing component');
    expect(examFeedback(first)).toMatchObject({ label: 'Não foi possível classificar' });
    expect(saveReportSchema.safeParse({ ...report, identityConfirmed: true }).success).toBe(false);
    expect(JSON.stringify(reportFhir(report))).not.toContain('135 a 145');
    expect(JSON.stringify(reportFhir(report))).not.toContain('2026-11-14');
  });
  it('preserves v3 document laboratory, date, point decimals and exact units', () => {
    const report = mapExtractionResponse({ motor: 'open_health_pdf_extractor_v3', extracted_text_preview: 'Laboratorio: Teste ficticio\nData de coleta: 14/11/2026\nFerritina\nResultado: 18.5 ng/mL\nReferencia: 15 a 150 ng/mL', cabecalho: { laboratorio: 'Wrong lab', data_coleta: '2026-01-01' }, exames: [{ analito: 'ferritina', value: 18.5, unit: 'ng/mL', reference_range: '10 a 200', status: 'NORMAL' }] }, 'first.pdf');
    expect(report).toMatchObject({ laboratory: 'Teste ficticio', collected: '14/11/2026' });
    expect(report.exams[0]).toMatchObject({ value: 18.5, unit: 'ng/mL', reference: '15 a 150 ng/mL' });
  });
  it('rejects unverified v3 responses without document text', () => {
    expect(() => mapExtractionResponse({ motor: 'open_health_pdf_extractor_v3', exames: payload.exames }, 'a.pdf')).toThrow('Nenhum resultado foi importado');
  });
  it('retains the exact unit but clears stale provider classification when a reviewed result changes', () => {
    const exam = mapApiExam({ analito: 'ferritina', value: 18.5, unit: 'ng/mL', status: 'NORMAL', feedbackSource: 'render-api' });
    const revised = reviseImportedExam(exam, { rawResult: '8.5' });
    expect(revised).toMatchObject({ value: 8.5, unit: 'ng/mL', status_alterado: null, classificationCode: '' });
    expect(examFeedback(revised).label).toBe('Não foi possível classificar');
  });
  it('rejects the observed fixed hybrid example rather than storing it as extracted patient data', () => {
    expect(() => mapExtractionResponse({ motor: 'open_health_hybrid_extractor_v2', cabecalho: { paciente_nome: 'Paciente Open Health', laboratorio: 'Open Health Lab Integration' }, exames: payload.exames }, 'different.pdf')).toThrow('nenhum resultado foi importado');
  });
  it('maps new reference and status fields without overriding explicit null', () => {
    const row = { analito: 'glicose', value: 94, unit: 'mg/dL', reference_range: '70 a 99 mg/dL', status: 'NORMAL', feedbackSource: 'render-api' };
    expect(mapApiExam(row)).toMatchObject({ name: 'glicose', reference: '70 a 99 mg/dL', status_alterado: false, classificationCode: 'NORMAL' });
    expect(mapApiExam({ ...row, status_alterado: null }).status_alterado).toBeNull();
    expect(examFeedback(mapApiExam({ ...row, status: 'LOW' })).label).toBe('Abaixo da referência');
    expect(examFeedback(mapApiExam({ ...row, status: 'HIGH' })).label).toBe('Acima da referência');
  });
  it('sends arquivo and motor=nuvem without setting Content-Type or private credentials', async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)));
    vi.stubGlobal('fetch', fetcher);
    const file = new File(['%PDF-1.4'], 'digital.pdf', { type: 'application/pdf' });
    await extractRemoteExam(file);
    const call = fetcher.mock.calls[0]; if (!call) throw new Error('Missing request');
    const [url, options] = call;
    expect(url).toBe('https://hackalepoli.onrender.com/api/extrair');
    expect(options.method).toBe('POST'); expect(options.headers).toBeUndefined();
    expect(options.body.get('motor')).toBe('nuvem'); expect(options.body.get('arquivo').name).toBe('digital.pdf');
  });
  it('preserves zero and qualitative results', () => {
    const report = mapExtractionResponse(payload, 'scan.png');
    expect(report.exams[0]).toMatchObject({ name: 'Glicose', value: 0, rawResult: '0 mg/dL' });
    expect(report.exams[1]).toMatchObject({ name: 'Anticorpos', value: null, rawResult: 'Não reagente' });
    expect(report.warnings[0]).toContain('Local Offline');
  });
  it.each([[true, 'Fora da referência'], [false, 'Dentro da referência'], [null, 'Não foi possível classificar'], [undefined, 'Não foi possível classificar']] as const)('preserves status %s without numerical reclassification', (status, label) => {
    const report = mapExtractionResponse({ exames: [{ ...payload.exames[0], status_alterado: status }] }, 'digital.pdf');
    const exam = report.exams[0]; if (!exam) throw new Error('Missing component');
    expect(examFeedback(exam).label).toBe(label);
  });
  it('rejects empty extraction and reports real HTTP failures', async () => {
    expect(() => mapExtractionResponse({ exames: [] }, 'a.pdf')).toThrow('não retornou componentes');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 404 })));
    await expect(extractRemoteExam(new File(['pdf'], 'a.pdf'))).rejects.toThrow('HTTP 404');
  });
  it('preserves components when their knowledge requests fail', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 404 })));
    const report = await loadComponentExplanations(mapExtractionResponse(payload, 'a.pdf'));
    expect(report.exams.map(exam => exam.name)).toEqual(['Glicose', 'Anticorpos', 'Ferritina']);
    expect(report.exams[0]?.explanation).toContain('HTTP 404');
  });
  it('retains names, references, explanations and tri-state status across save/read validation and FHIR export', () => {
    const report = mapExtractionResponse(payload, 'a.pdf');
    const first = report.exams[0]; if (!first) throw new Error('Missing component');
    first.explanation = 'Resumo recebido do serviço';
    const saved = saveReportSchema.parse({ ...report, identityConfirmed: true });
    const read = JSON.parse(JSON.stringify(saved));
    read.exams = read.exams.map((exam: unknown) => examSchema.parse(exam));
    expect(read.exams).toEqual(report.exams);
    const entries = reportFhir(read);
    expect(entries[1]?.resource).toMatchObject({ code: { text: 'Glicose' }, valueQuantity: { value: 0, unit: 'mg/dL' }, referenceRange: [{ text: '70 a 99' }] });
    expect(JSON.stringify(entries)).toContain('Fora da referência');
    expect(JSON.stringify(entries)).toContain('Não reagente');
    expect(JSON.stringify(entries)).toContain('Não foi possível classificar');
  });
});