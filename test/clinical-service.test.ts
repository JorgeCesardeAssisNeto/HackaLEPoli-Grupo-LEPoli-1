import { afterEach, describe, expect, it, vi } from 'vitest';
import { clinicalRequest } from '@/lib/clinical-service.server';
import { assertDemoPatient, causalContextSchema } from '@/lib/clinical-contract';

afterEach(() => vi.unstubAllGlobals());
describe('authenticated clinical contract', () => {
  it.each(['/causal/alerts/U0001', '/causal/evaluate/U0001?days=14', '/causal/alerts/a?new_status=RESOLVED', '/wearables/metrics/manual', '/wearables/metrics/patient?days=30', '/wearables/authorizer/patient/garmin', '/wearables/sync?patient_id=patient'])('adds a server service token to %s', async path => {
    const fetcher = vi.fn().mockResolvedValue(new Response('{}')); vi.stubGlobal('fetch', fetcher);
    await clinicalRequest(path, 'test-only-credential');
    const call = fetcher.mock.calls[0];
    if (!call) throw new Error('Expected an upstream request');
    expect(new Headers(call[1].headers).get('X-Service-Token')).toBe('test-only-credential');
    expect(call[1].signal).toBeInstanceOf(AbortSignal);
  });
  it('sends the exact lab payload for a 14-day evaluation', async () => {
    const context = causalContextSchema.parse({ ferritin_ng_ml: 18.5, biomarkers: [{ name: 'Ferritina', value: 18.5, unit: 'ng/mL', collected_on: '2026-11-14' }] });
    expect(context).toEqual({ ferritin_ng_ml: 18.5, biomarkers: [{ name: 'Ferritina', value: 18.5, unit: 'ng/mL', collected_on: '2026-11-14' }], caffeine_mg: 0, screen_time_min: 0, alcohol_units: 0 });
    const fetcher = vi.fn().mockResolvedValue(new Response('{}')); vi.stubGlobal('fetch', fetcher);
    await clinicalRequest('/causal/evaluate/U0001?days=14', 'test-only-credential', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(context) });
    expect(fetcher).toHaveBeenCalledWith('https://hackalepoli.onrender.com/causal/evaluate/U0001?days=14', expect.objectContaining({ method: 'POST', body: JSON.stringify(context) }));
  });
  it('does not invent missing ferritin', () => expect(causalContextSchema.parse({ biomarkers: [] })).not.toHaveProperty('ferritin_ng_ml'));
  it('preserves stated confounders', () => expect(causalContextSchema.parse({ biomarkers: [], caffeine_mg: 120, screen_time_min: 90, alcohol_units: 1 })).toMatchObject({ caffeine_mg: 120, screen_time_min: 90, alcohol_units: 1 }));
  it('rejects arbitrary patient IDs in demo tools', () => expect(() => assertDemoPatient('another-account')).toThrow());
  it('rejects missing credentials before requesting', async () => {
    const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher);
    await expect(clinicalRequest('/causal/alerts/U0001', '')).rejects.toThrow('Token'); expect(fetcher).not.toHaveBeenCalled();
  });
  it('reports rejected authentication rather than success', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"detail":"Invalid service token"}', { status: 401 })));
    await expect(clinicalRequest('/causal/alerts/U0001', 'test-only-credential')).rejects.toThrow('HTTP 401 — {"detail":"Invalid service token"}');
  });
  it('retains the exact missing-route error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"detail":"Not Found"}', { status: 404 })));
    await expect(clinicalRequest('/wearables/metrics/patient', 'test-only-credential')).rejects.toThrow('GET /wearables/metrics/patient: HTTP 404 — {"detail":"Not Found"}');
  });
});
