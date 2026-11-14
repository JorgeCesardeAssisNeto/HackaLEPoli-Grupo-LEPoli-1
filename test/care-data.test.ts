import { describe, expect, it } from 'vitest';
import { answersSchema, needsUrgentCare, parseWearableCsv } from '@/lib/care-data';
const answers = { chest_pain: false, breathlessness: false, fainting: false, medication_change: false, fasting: false };
describe('patient safety questionnaire', () => {
  it.each(['chest_pain', 'breathlessness', 'fainting'] as const)('escalates a reported warning symptom: %s', key => { expect(needsUrgentCare({ ...answers, [key]: true })).toBe(true); });
  it('does not infer high risk from fasting or medication change alone', () => { expect(needsUrgentCare({ ...answers, fasting: true, medication_change: true })).toBe(false); });
  it('requires all answers without treating blanks as no', () => { expect(answersSchema.safeParse({ chest_pain: false }).success).toBe(false); });
});
describe('real wearable CSV', () => {
  it('imports actual measurements and omits missing values', () => { expect(parseWearableCsv('date,steps,resting_hr_bpm,sleep_duration_hours\n2026-11-14,4500,,7.5', 'Garmin').records).toEqual([{ date: '2026-11-14', metrics: { steps: 4500, sleep_duration_hours: 7.5 } }]); });
  it('handles semicolon-separated Brazilian decimals', () => { expect(parseWearableCsv('date;sleep_duration_hours\n2026-11-14;"7,5"', 'Fitbit').records[0]?.metrics.sleep_duration_hours).toBe(7.5); });
  it('rejects duplicate dates', () => { expect(() => parseWearableCsv('date,steps\n2026-11-14,1\n2026-11-14,2','Garmin')).toThrow('repetida'); });
  it('rejects invalid dates', () => { expect(() => parseWearableCsv('date,steps\n2026-02-30,1','Garmin')).toThrow(); });
  it('rejects sleep exceeding 24 hours', () => { expect(() => parseWearableCsv('date,sleep_duration_hours\n2026-11-14,25','Garmin')).toThrow(); });
  it('rejects unknown fields rather than silently losing measurements', () => { expect(() => parseWearableCsv('date,heart_rate\n2026-11-14,65','Garmin')).toThrow('colunas'); });
});