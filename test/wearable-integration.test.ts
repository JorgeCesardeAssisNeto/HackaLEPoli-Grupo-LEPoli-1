import { describe, expect, it } from 'vitest';
import { authorizationState, authorizerSchema, latestCausalContext, wearableSources, activeWearablePatientId, assertCallbackPatient, assertRealWearableSync, parseRemoteWearables, WEARABLE_POLL_INTERVAL, WEARABLE_POLL_DURATION, WEARABLE_HISTORY_DAYS, wearableSyncSchema } from '@/lib/wearable-integration';

describe('updated wearable integration', () => {
  it.each(['sandbox_seeded', 'sandbox_fallback', 'simulated', 'demo', 'synthetic', 'mock', undefined])('rejects non-real sync mode %s before displaying readings or evaluating labs', mode => {
    expect(() => assertRealWearableSync({ status: 'success', patient_id: 'owner', records_processed: 7, alerts_generated: 3, mode })).toThrow('dados de teste');
  });
  it('accepts explicitly live synchronization', () => {
    expect(() => assertRealWearableSync({ status: 'success', patient_id: 'owner', records_processed: 1, alerts_generated: 0, mode: 'live' })).not.toThrow();
  });
  it('requests thirty days of wearable history', () => expect(WEARABLE_HISTORY_DAYS).toBe(30));
  it('preserves provider sandbox sync counters and optional connection portal', () => {
    expect(wearableSyncSchema.parse({ status: 'success', patient_id: 'owner', records_processed: 7, alerts_generated: 3, mode: 'sandbox_seeded' })).toMatchObject({ records_processed: 7, alerts_generated: 3, mode: 'sandbox_seeded' });
    const auth = authorizerSchema.parse({ authorization_url: null, connection_page_url: 'https://connections.rook-connect.review/owner', mode: 'sandbox_fallback' });
    expect(authorizationState(auth)).toBe('demonstration');
    expect(auth.connection_page_url).toBe('https://connections.rook-connect.review/owner');
    expect(authorizerSchema.safeParse({ connection_page_url: 'javascript:alert(1)' }).success).toBe(false);
  });
  it('supports all seven requested manufacturer identifiers', () => {
    expect(wearableSources.map(source => source.id)).toEqual(['garmin', 'fitbit', 'oura', 'polar', 'whoop', 'apple_health', 'health_connect']);
  });
  it('keeps sandbox success distinct from a synchronized personal device', () => {
    expect(authorizationState(authorizerSchema.parse({ connected: true, authorization_url: null, mode: 'sandbox_fallback' }))).toBe('demonstration');
    expect(authorizationState(authorizerSchema.parse({ connected: true, authorization_url: null, mode: 'mobile' }))).toBe('connected');
  });
  it('requires a safe OAuth URL and does not infer connection from HTTP success', () => {
    expect(authorizerSchema.safeParse({ authorization_url: 'javascript:alert(1)' }).success).toBe(false);
    expect(authorizationState(authorizerSchema.parse({ authorization_url: 'https://example.org/oauth' }))).toBe('oauth');
    expect(authorizationState(authorizerSchema.parse({}))).toBe('unconnected');
  });
  it('uses latest saved ferritin and hemoglobin with exact values and dates, without inventing codes or confounders', () => {
    const report = { id: '1', filename: 'lab.pdf', storage_path: '', document_patient: '', laboratory: '', collected_on: '2026-11-14', exams: [{ name: 'Ferritina', value: 18.5, unit: 'ng/mL', rawResult: '', reference: '', method: '' }, { name: 'Hemoglobina', value: 12, unit: 'g/dL', rawResult: '', reference: '', method: '' }] };
    const context = latestCausalContext([{ ...report, collected_on: '2026-11-13', exams: [{ ...report.exams[0], name: 'Ferritina', value: 40, unit: 'ng/mL', rawResult: '', reference: '', method: '' }] }, report]);
    expect(context).toEqual({ ferritin_ng_ml: 18.5, biomarkers: [{ name: 'Ferritina', value: 18.5, unit: 'ng/mL', collected_on: '2026-11-14' }, { name: 'Hemoglobina', value: 12, unit: 'g/dL', collected_on: '2026-11-14' }] });
    expect(latestCausalContext([{ ...report, exams: [{ ...report.exams[0], name: 'Ferritina', value: 18.5, unit: 'mg/L', rawResult: '', reference: '', method: '' }] }]).ferritin_ng_ml).toBeNull();
  });
  it('uses the logged-in identity instead of the fallback', () => expect(activeWearablePatientId('real-user')).toBe('real-user'));
  it('uses the specified fallback only without a user', () => expect(activeWearablePatientId(null)).toBe('e4a7a8d2-1b1e-4c7b-8b9a-112233445566'));
  it('polls every five seconds for two minutes', () => { expect(WEARABLE_POLL_INTERVAL).toBe(5000); expect(WEARABLE_POLL_DURATION).toBe(120000); });
  it('refuses a callback for another account', () => { expect(() => assertCallbackPatient('owner', 'other')).toThrow(); expect(assertCallbackPatient('owner', 'owner')).toBe('owner'); });
  it('rejects measurements belonging to another patient', () => expect(() => parseRemoteWearables([{ patient_id: 'other', date: '2026-11-14', steps: 100 }], 'owner')).toThrow());
  it('preserves zeros and absent metrics without synthesis', () => expect(parseRemoteWearables([{ patient_id: 'owner', date: '2026-11-14', steps: 0, hrv_rmssd_ms: null }], 'owner')).toEqual([{ patient_id: 'owner', date: '2026-11-14', steps: 0, hrv_rmssd_ms: null }]));
});