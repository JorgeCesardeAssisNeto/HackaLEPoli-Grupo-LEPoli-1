import { describe, expect, it } from 'vitest';
import { dateSchema, latestWearableMetrics, examKey, reportSeries, saveReportSchema, wearableImportSchema, type PatientReport } from '@/lib/patient-data';
const exam = { name: 'Ferritina', rawResult: '97,5 ng/mL', value: 97.5, unit: 'ng/mL', reference: '15 a 150', method: '' };
describe('patient-owned clinical data', () => {
  it('keeps the historical collection classification instead of borrowing the latest status', () => {
    const older = { ...exam, value: 8, status_alterado: true, classificationCode: 'LOW' };
    const newer = { ...exam, status_alterado: false, classificationCode: 'NORMAL' };
    const reports = [older, newer].map((e, i) => ({ id: String(i), filename: 'exame.pdf', storage_path: '', document_patient: '', collected_on: i ? '2026-02-06' : '2026-01-06', laboratory: '', exams: [e] }));
    const points = reportSeries(reports, examKey(exam));
    expect(points[0]?.exam.classificationCode).toBe('LOW');
    expect(points[1]?.exam.classificationCode).toBe('NORMAL');
  });
  it('requires confirmation that the document belongs to the signed-in patient', () => {
    const data = { id: '11111111-1111-4111-8111-111111111111', filename: 'exame.pdf', patient: 'Paciente', laboratory: '', collected: '2026-01-06', exams: [exam], identityConfirmed: true };
    expect(saveReportSchema.safeParse(data).success).toBe(true);
    expect(saveReportSchema.safeParse({ ...data, identityConfirmed: false }).success).toBe(false);
  });
  it('uses only actual uploaded results, sorted by collection date', () => {
    const reports = ['2026-02-06', '2026-01-06'].map((date, i) => ({ id: String(i), filename: 'exame.pdf', storage_path: '', document_patient: '', collected_on: date, laboratory: '', exams: [{ ...exam, value: i ? 35 : 97.5 }] })) satisfies PatientReport[];
    expect(reportSeries(reports, examKey(exam)).map(point => point.value)).toEqual([35, 97.5]);
    expect(reportSeries([], examKey(exam))).toEqual([]);
  });
  it('never combines different units into the same history line', () => { expect(examKey(exam)).not.toBe(examKey({ ...exam, unit: 'µg/L' })); });
  it('rejects impossible dates rather than inventing collection dates', () => { expect(dateSchema.safeParse('2026-02-30').success).toBe(false); });
  it('validates real wearable imports and rejects sleep above 24 hours', () => {
    expect(wearableImportSchema.safeParse({ source: 'Garmin', records: [{ date: '2026-11-14', metrics: { steps: 4567, sleep_duration_hours: 7.5 } }] }).success).toBe(true);
    expect(wearableImportSchema.safeParse({ source: 'Garmin', records: [{ date: '2026-11-14', metrics: { sleep_duration_hours: 25 } }] }).success).toBe(false);
  });
  it('accepts blood oxygen as a percentage and rejects impossible saturation', () => {
    expect(wearableImportSchema.safeParse({ source: 'Fitbit', records: [{ date: '2026-11-14', metrics: { spo2_pct: 96.5 } }] }).success).toBe(true);
    expect(wearableImportSchema.safeParse({ source: 'Fitbit', records: [{ date: '2026-11-14', metrics: { spo2_pct: 101 } }] }).success).toBe(false);
  });
});
describe('wearable overview', () => {
  it('shows the latest recorded value per metric and source with original dates', () => {
    const result = latestWearableMetrics([
      { measured_on: '2026-11-13', source: 'export:Garmin', metrics: { steps: 4567, sleep_duration_hours: 7.5 } },
      { measured_on: '2026-11-14', source: 'export:Garmin', metrics: { steps: 6000 } },
    ]);
    expect(result.find(item => item.name === 'Passos')).toMatchObject({ value: 6000, date: '2026-11-14', source: 'Garmin', unit: 'passos' });
    expect(result.find(item => item.name === 'Duração do sono')).toMatchObject({ value: 7.5, date: '2026-11-13', unit: 'h' });
    expect(result).toHaveLength(2);
  });
  it('does not synthesize absent measurements or drop recorded zero values', () => {
    expect(latestWearableMetrics([])).toEqual([]);
    expect(latestWearableMetrics([{ measured_on: '2026-11-14', source: 'export:Fitbit', metrics: { steps: 0 } }]).map(item => item.value)).toEqual([0]);
  });
  it('exposes blood oxygen with its unit for the overview cards', () => {
    const result = latestWearableMetrics([{ measured_on: '2026-11-14', source: 'export:Garmin', metrics: { spo2_pct: 96.5 } }]);
    expect(result).toEqual([expect.objectContaining({ name: 'Oxigenação no sangue', value: 96.5, unit: '%' })]);
  });
});
describe('overview wearable cards', () => {
  it('fixes the four requested metrics in order', async () => {
    const { OVERVIEW_WEARABLE_IDS } = await import('@/components/patient-overview');
    expect([...OVERVIEW_WEARABLE_IDS]).toEqual(['resting_hr_bpm', 'steps', 'spo2_pct', 'sleep_duration_hours']);
  });
});
