import { afterEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({ getSession: vi.fn(), call: vi.fn(), authorize: vi.fn() }));
vi.mock('@/integrations/supabase/client', () => ({ supabase: { auth: { getSession: mocks.getSession } } }));
vi.mock('@/lib/clinical.functions', () => ({ callDemoClinical: mocks.call, authorizeWearable: mocks.authorize }));
import { API_BASE, alertTone, healthApi, manualMetricSchema } from '@/lib/health-api';
afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks(); });
const alert = { id: 'alert-1', target_id: 'METABOLIC', alert_level: 'WARNING', clinical_rationale: 'Test', status: 'RESOLVED' };
function signedIn() { mocks.getSession.mockResolvedValue({ data: { session: { user: { id: 'test' } } } }); }
describe('FastAPI integration', () => {
  it.each([['INFO', 'neutral'], ['WARNING', 'warning'], ['CRITICAL', 'danger']])('maps severity %s to %s', (level, tone) => expect(alertTone(level)).toBe(tone));
  it('reads public health and operational metrics', async () => {
    const fetcher = vi.fn().mockResolvedValueOnce(new Response('{}')).mockResolvedValueOnce(new Response(JSON.stringify({ pending_clinical_alerts: 7 })));
    vi.stubGlobal('fetch', fetcher); await healthApi.health(); expect(await healthApi.metrics()).toEqual({ pending_clinical_alerts: 7 });
    expect(fetcher.mock.calls.map(call => call[0])).toEqual([`${API_BASE}/health`, `${API_BASE}/metrics`]);
  });
  it('requires a frontend session before a protected request', async () => {
    mocks.getSession.mockResolvedValue({ data: { session: null } });
    await expect(healthApi.evaluate('U0001')).rejects.toThrow('Entre'); expect(mocks.call).not.toHaveBeenCalled();
  });
  it('reads scoped alerts through authenticated RPC', async () => {
    signedIn(); mocks.call.mockResolvedValue([alert]); expect(await healthApi.alerts('U0001')).toEqual([alert]);
    expect(mocks.call).toHaveBeenCalledWith({ data: { action: 'alerts', patientId: 'U0001' } });
  });
  it('resolves through authenticated RPC', async () => {
    signedIn(); mocks.call.mockResolvedValue(alert); await healthApi.resolve('alert-1');
    expect(mocks.call).toHaveBeenCalledWith({ data: { action: 'resolve', alertId: 'alert-1' } });
  });
  it('passes laboratory context to the authenticated evaluation', async () => {
    signedIn(); mocks.call.mockResolvedValue({});
    const context = { ferritin_ng_ml: 18.5, biomarkers: [{ name: 'Ferritina', value: 18.5, unit: 'ng/mL', collected_on: '2026-11-14' }] };
    await healthApi.evaluate('U0001', context); expect(mocks.call).toHaveBeenCalledWith({ data: { action: 'evaluate', patientId: 'U0001', context } });
  });
  it('validates and forwards manual metrics', async () => {
    signedIn(); mocks.call.mockResolvedValue({});
    const metric = { patient_id: 'U0001', date: '2026-11-12', steps: 2500, resting_hr_bpm: 78, sleep_duration_hours: 5, caffeine_mg: 0, hrv_rmssd_ms: 30, screen_time_min: 0, alcohol_units: 0, sleep_stage_deep_pct: 10 };
    await healthApi.ingest(metric); expect(mocks.call).toHaveBeenCalledWith({ data: { action: 'ingest', metric } });
    expect(manualMetricSchema.safeParse({ ...metric, steps: -1 }).success).toBe(false);
  });
  it('keeps sandbox authorization separate', async () => {
    mocks.authorize.mockResolvedValue({ authorization: { connected: true, mode: 'sandbox_fallback' }, error: null });
    expect(await healthApi.authorize('demo', 'health_connect')).toMatchObject({ mode: 'sandbox_fallback' });
    expect(mocks.authorize).toHaveBeenCalledWith({ data: { source: 'health_connect' } });
  });
});
