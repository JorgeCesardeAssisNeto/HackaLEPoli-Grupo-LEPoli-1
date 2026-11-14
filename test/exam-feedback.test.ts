import { describe, expect, it, vi, afterEach } from 'vitest';
vi.mock('@/lib/health-api', () => ({ API_BASE: 'https://hackalepoli.onrender.com' }));
import { examFeedback, componentName } from '@/lib/exam-feedback';
import { mapApiExam, examServiceAvailability } from '@/lib/exam-api';
import { extractPage, reportFhir } from '@/lib/pdf-extraction';
afterEach(() => vi.unstubAllGlobals());
const row = { analito: 'Glicose', resultado_bruto: '90,5 mg/dL', unidade: 'mg/dL', valores_referencia: '70 a 99 mg/dL' };
describe('component identity and reference feedback', () => {
  it('associates a title above Resultado and preserves multiple components', () => {
    const exams = extractPage([{ text: 'Glicose', x: 20, y: 100 }, { text: 'Resultado: 90,5 mg/dL', x: 20, y: 80 }, { text: 'Referência: 70 a 99 mg/dL', x: 20, y: 60 }, { text: 'Ferritina', x: 20, y: 40 }, { text: 'Resultado: 12 ng/mL | 15 a 150 ng/mL', x: 20, y: 20 }]);
    expect(exams.map(exam => exam.name)).toEqual(['Glicose', 'Ferritina']);
    expect(exams[0]).toMatchObject({ value: 90.5, reference: '70 a 99 mg/dL' });
  });
  it.each(['Resultado', 'Valor', 'Unidade', 'Referência'])('never accepts header %s as a name', name => expect(componentName(name)).toBe('Componente não identificado — revisar extração'));
  it('maps analito without adding fasting context', () => expect(mapApiExam(row)).toMatchObject({ name: 'Glicose', originalName: 'Glicose', value: 90.5 }));
  it('maps nome_exame when analito is absent', () => expect(mapApiExam({ ...row, analito: undefined, nome_exame: 'Glicose' }).name).toBe('Glicose'));
  it('preserves false as valid within-reference feedback', () => expect(examFeedback(mapApiExam({ ...row, status_alterado: false })).label).toBe('Dentro da referência'));
  it('preserves null as indeterminate, not normal', () => expect(examFeedback(mapApiExam({ ...row, status_alterado: null })).label).toBe('Não foi possível classificar'));
  it('reports a below-reference value', () => expect(examFeedback(mapApiExam({ ...row, resultado_bruto: '60 mg/dL', status_alterado: true })).label).toBe('Abaixo da referência'));
  it('reports an above-reference value', () => expect(examFeedback(mapApiExam({ ...row, resultado_bruto: '110 mg/dL', status_alterado: true })).label).toBe('Acima da referência'));
  it.each([['< 90 mg/dL','Acima da referência'],['<= 90 mg/dL','Dentro da referência'],['> 90 mg/dL','Abaixo da referência'],['>= 90 mg/dL','Dentro da referência']])('handles bound %s', (reference,label) => expect(examFeedback(mapApiExam({ ...row, resultado_bruto: '90 mg/dL', valores_referencia: reference })).label).toBe(label));
  it('does not classify mismatched units', () => expect(examFeedback(mapApiExam({ ...row, valores_referencia: '3 a 5 mmol/L' })).reason).toContain('Unidades incompatíveis'));
  it('explains missing references', () => expect(examFeedback(mapApiExam({ ...row, valores_referencia: '' })).reason).toContain('não informada'));
  it('keeps a backend borderline-within result within reference', () => expect(examFeedback(mapApiExam({ ...row, codigo: 'LIMITROFE', status_alterado: false })).label).toBe('Dentro da referência'));
  it('exports correct name, value, reference and feedback after a JSON round trip', () => {
    const exam = JSON.parse(JSON.stringify(mapApiExam({ ...row, status_alterado: false })));
    const entries = reportFhir({ id: 'doc', patient: 'Fictício', filename: 'test.pdf', collected: '2026-11-14', laboratory: '', exams: [exam], warnings: [] });
    expect(entries[1]?.resource).toMatchObject({ code: { text: 'Glicose' }, valueQuantity: { value: 90.5, unit: 'mg/dL' }, referenceRange: [{ text: '70 a 99 mg/dL' }] });
    expect(JSON.stringify(entries)).toContain('Dentro da referência');
  });
  it('reports an interpretation route failure without deleting components', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 404 })));
    expect(await examServiceAvailability()).toContain('HTTP 404'); expect(mapApiExam(row).name).toBe('Glicose');
  });
});