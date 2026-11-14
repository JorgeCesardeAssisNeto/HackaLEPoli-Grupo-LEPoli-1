import { describe, it, expect } from 'vitest';
import { registrationSchema, connectionSchema } from '@/lib/account-schema';
const base = { display_name: 'Pessoa Teste', email: 'test@example.com', password: 'abcdefgh', account_role: 'patient', consent: true };
describe('Account rules', () => {
 it('accepts patient signup with name, email, password and consent', () => { expect(registrationSchema.parse(base).account_role).toBe('patient'); });
 it('requires data consent', () => { expect(registrationSchema.safeParse({ ...base, consent: false }).success).toBe(false); });
 it('accepts doctor signup with the same fields', () => { expect(registrationSchema.parse({ ...base, account_role: 'doctor' }).account_role).toBe('doctor'); });
 it('requires an invitation for admin signup', () => { expect(registrationSchema.safeParse({ ...base, account_role: 'admin' }).success).toBe(false); });
 it('requires a full patient ID', () => { expect(connectionSchema.safeParse('U0001').success).toBe(false); expect(connectionSchema.parse('a138cc23-61f1-43d3-a389-082d0115610d')).toBe('a138cc23-61f1-43d3-a389-082d0115610d'); });
});
