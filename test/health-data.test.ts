import { describe, expect, it } from 'vitest';
import { analytes, baseline, averageRestingHeartRate, restingDeviation, isAbnormal, history, telemetry, initialConsents, updateConsent } from '@/lib/health-data';
describe('Health briefing rules', () => {
  it('uses the individual baseline and seven-day deviation', () => { expect(baseline).toBe(68.3); expect(averageRestingHeartRate).toBe(74.5); expect(restingDeviation()).toBe(6.2); });
  it('flags erythrocytes at 4.91 above 4.80', () => { const item = analytes[0]; if (!item) throw new Error('Missing erythrocytes'); expect(item.value).toBe(4.91); expect(isAbnormal(item)).toBe(true); expect(isAbnormal({ ...item, value: 4.8 })).toBe(false); });
  it.each(analytes.slice(1))('keeps $name within the supplied normal range', item => { expect(isAbnormal(item)).toBe(false); expect(isAbnormal({ ...item, value: item.max + 1 })).toBe(true); });
  it('has 14 days from 68.2 to 75.1 bpm', () => { expect(telemetry).toHaveLength(14); expect(telemetry[0]?.fcr).toBe(68.2); expect(telemetry[13]?.fcr).toBe(75.1); });
  it('has ten collections with the stated three-year endpoints', () => { expect(history).toHaveLength(10); expect(history[0]).toEqual({ date: 'Out/23', ferritin: 35, glucose: 104 }); expect(history[9]).toEqual({ date: 'Jan/26', ferritin: 97.5, glucose: 92 }); });
  it('revokes access immediately without changing other institutions', () => { const next = updateConsent(initialConsents, 'Hospital Sírio-Libanês', false); expect(next[1]?.active).toBe(false); expect(next[0]?.active).toBe(true); expect(next[2]?.active).toBe(false); expect(initialConsents[1]?.active).toBe(true); });
});