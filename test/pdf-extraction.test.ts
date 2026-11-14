import { describe, expect, it } from 'vitest';
import { extractPage, parseNumber, referenceStatus, reportFhir, splitResult, type ExtractedExam } from '@/lib/pdf-extraction';

const exam = (value: number | null, reference: string): ExtractedExam => ({ name: 'Ferritina', rawResult: String(value), value, reference, unit: 'ng/mL', method: '' });
describe('supplied PDF extraction rules', () => {
  it('separates multiple biomarkers, result, unit and reference in one PDF table', () => {
    const cells = [
      { text: 'Exame / Analito', x: 20, y: 100 }, { text: 'Material / Método', x: 160, y: 100 }, { text: 'Resultado', x: 300, y: 100 }, { text: 'Valores de Referência', x: 400, y: 100 },
      { text: 'Ferritina', x: 20, y: 80 }, { text: 'Soro', x: 160, y: 80 }, { text: '97,5 ng/mL', x: 300, y: 80 }, { text: '15,0 a 150,0', x: 400, y: 80 },
      { text: 'Vitamina D', x: 20, y: 60 }, { text: '32 ng/mL', x: 300, y: 60 }, { text: '20 a 60', x: 400, y: 60 },
    ];
    const results = extractPage(cells);
    expect(results).toHaveLength(2);
    expect(results[0]).toMatchObject({ name: 'Ferritina', value: 97.5, unit: 'ng/mL', reference: '15,0 a 150,0' });
    expect(results[1]).toMatchObject({ name: 'Vitamina D', value: 32, reference: '20 a 60' });
  });
  it('preserves Brazilian thousands and decimal values', () => { expect(parseNumber('274.000')).toBe(274000); expect(parseNumber('1.602,5')).toBe(1602.5); expect(splitResult('0 ng/mL').value).toBe(0); });
  it('keeps multiline names intact and does not confuse pg units with page footers', () => {
    const results = extractPage([
      { text: 'Exame', x: 20, y: 100 }, { text: 'Resultado', x: 300, y: 100 }, { text: 'Referência', x: 400, y: 100 },
      { text: 'Hormônio Tireoestimulante', x: 20, y: 85 }, { text: 'Ultrassensível (TSH)', x: 20, y: 75 }, { text: '2,0 mUI/L', x: 300, y: 80 }, { text: '0,4 a 4,0', x: 400, y: 80 },
      { text: 'HCM', x: 20, y: 60 }, { text: '29,2 pg', x: 300, y: 60 }, { text: '27 a 32 pg', x: 400, y: 60 },
    ]);
    expect(results.map(item => item.name)).toEqual(['Hormônio Tireoestimulante Ultrassensível (TSH)', 'HCM']);
    expect(results[1]?.unit).toBe('pg');
  });
  it('does not turn censored or qualitative results into exact quantities', () => { expect(splitResult('< 5 ng/mL').value).toBeNull(); expect(splitResult('Não reagente').value).toBeNull(); });
  it('compares strict and inclusive reference limits correctly', () => { expect(referenceStatus(exam(3, '< 3,0'))).toBe('Alterado'); expect(referenceStatus(exam(3, 'Até 3,0'))).toBe('Normal'); expect(referenceStatus(exam(4.91, '3,80 a 4,80'))).toBe('Alterado'); });
  it('leaves ambiguous and missing references for human review', () => { expect(referenceStatus(exam(32, ''))).toBe('Conferir'); expect(referenceStatus(exam(32, 'Homens: 10 a 20 | Mulheres: 20 a 40'))).toBe('Conferir'); });
  it('keeps imported patient identity and provenance separate from demo FHIR', () => {
    const entries = reportFhir({ id: 'document-1', filename: 'exams.pdf', patient: 'Paciente do documento', collected: '06/01/2026', laboratory: '', exams: [exam(97.5, '15 a 150')], warnings: [] });
    expect(entries[0]?.resource).toMatchObject({ resourceType: 'Patient', name: [{ text: 'Paciente do documento' }] });
    expect(entries[1]?.resource).toMatchObject({ status: 'preliminary', subject: { reference: 'urn:uuid:patient-document-1' }, code: { text: 'Ferritina' }, valueQuantity: { value: 97.5 }, meta: { tag: [{ system: 'urn:open-health:source', code: 'local-pdf' }] } });
  });
});