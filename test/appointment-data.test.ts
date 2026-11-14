import { describe, expect, it } from 'vitest';
import { appointmentDay, appointmentTime, availableSlots, type ConsultationSlot } from '../lib/appointment-data';

const slot: ConsultationSlot = { id: 'slot-1', doctor_id: 'doctor-1', starts_at: '2026-11-16T12:00:00Z', ends_at: '2026-11-16T12:30:00Z', modality: 'online', location: '', patient_id: null };
const now = Date.parse('2026-11-14T15:25:00Z');

describe('agenda do paciente', () => {
  it('apresenta apenas horários vagos do médico escolhido', () => {
    expect(availableSlots([slot, { ...slot, id: 'reserved', patient_id: 'another-patient' }, { ...slot, id: 'other-doctor', doctor_id: 'doctor-2' }], 'doctor-1', now).map(s => s.id)).toEqual(['slot-1']);
  });
  it('não oferece horários que já passaram', () => {
    expect(availableSlots([{ ...slot, starts_at: '2026-11-14T15:25:00Z' }], 'doctor-1', now)).toEqual([]);
  });
  it('organiza dias e horários pelo horário de Brasília', () => {
    expect(appointmentDay('2026-11-16T01:00:00Z')).toBe('2026-11-15');
    expect(appointmentTime(slot.starts_at)).toBe('09:00');
  });
});