import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useServerFn } from '@tanstack/react-start';
import { CalendarDays, Clock3, Check, Video, MapPin, X, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { readAppointments, bookAppointment, cancelAppointment } from '@/lib/appointments.functions';
import { appointmentDate, appointmentDay, appointmentTime, availableSlots, type ConsultationSlot } from '@/lib/appointment-data';

export function PatientAppointments({ patientId, doctors }: { patientId: string; doctors: { id: string; name: string }[] }) {
  const read = useServerFn(readAppointments), book = useServerFn(bookAppointment), cancel = useServerFn(cancelAppointment);
  const client = useQueryClient();
  const queryKey = ['appointments', patientId];
  const agenda = useQuery({ queryKey, queryFn: () => read(), refetchInterval: 30000 });
  const [doctorId, setDoctorId] = useState(''), [day, setDay] = useState(''), [slotId, setSlotId] = useState('');
  const [confirmation, setConfirmation] = useState<{ slot: ConsultationSlot; cancel: boolean } | null>(null);
  const [busy, setBusy] = useState(false), [notice, setNotice] = useState(''), [error, setError] = useState('');
  const activeDoctor = doctors.some(d => d.id === doctorId) ? doctorId : doctors[0]?.id ?? '';
  const slots = availableSlots(agenda.data ?? [], activeDoctor);
  const days = [...new Set(slots.map(s => appointmentDay(s.starts_at)))];
  const activeDay = days.includes(day) ? day : days[0] ?? '';
  const daySlots = slots.filter(s => appointmentDay(s.starts_at) === activeDay);
  const selected = daySlots.find(s => s.id === slotId);
  const appointments = (agenda.data ?? []).filter(s => s.patient_id === patientId && Date.parse(s.ends_at) > Date.now());
  const doctorName = (id: string) => doctors.find(d => d.id === id)?.name ?? 'Médico da consulta';

  async function confirm() {
    if (!confirmation || busy) return;
    setBusy(true); setError(''); setNotice('');
    try {
      await (confirmation.cancel ? cancel({ data: confirmation.slot.id }) : book({ data: confirmation.slot.id }));
      setNotice(confirmation.cancel ? 'Consulta cancelada.' : 'Consulta agendada.');
      setSlotId(''); setConfirmation(null);
      await client.invalidateQueries({ queryKey });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível concluir o agendamento.');
      setConfirmation(null);
      await client.invalidateQueries({ queryKey });
    } finally { setBusy(false); }
  }

  return <section className="account-section" aria-label="Agendamento de consultas">
    <div className="section-heading mt-0"><h2 className="flex items-center gap-2"><CalendarDays className="text-primary"/>Agendar consulta</h2><span className="text-xs text-muted-foreground">Horário de Brasília</span></div>
    {agenda.isPending ? <p role="status">Carregando a agenda…</p> : agenda.isError ? <div role="alert"><p>{agenda.error.message}</p><Button variant="outline" onClick={() => agenda.refetch()}><RefreshCw/>Tentar novamente</Button></div> : <>
      {doctors.length === 0 ? <div className="patient-empty"><CalendarDays size={30}/><h3>Nenhum médico conectado</h3><p>Uma conexão autorizada com seu médico é necessária para consultar a agenda.</p></div> : <>
        <label className="flex flex-col gap-2 max-w-md"><span className="text-sm font-medium">Médico</span><select aria-label="Médico para consulta" className="account-input w-full" value={activeDoctor} onChange={e => { setDoctorId(e.target.value); setDay(''); setSlotId(''); setNotice(''); setError(''); }}>{doctors.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select></label>
        {slots.length === 0 ? <div className="patient-empty"><Clock3 size={28}/><h3>Sem horários disponíveis</h3><p>Este médico ainda não disponibilizou dias e horários livres para consulta.</p></div> : <div className="grid gap-6 mt-6 md:grid-cols-2">
          <div><h3 className="mb-3">Dias disponíveis</h3><div className="flex flex-wrap gap-2">{days.map(date => { const start = slots.find(s => appointmentDay(s.starts_at) === date)?.starts_at; return start && <Button key={date} variant={activeDay === date ? 'default' : 'outline'} aria-pressed={activeDay === date} onClick={() => { setDay(date); setSlotId(''); }}>{appointmentDate(start)}</Button>; })}</div></div>
          <div><h3 className="mb-3">Horários livres</h3><div className="flex flex-wrap gap-2">{daySlots.map(s => <Button key={s.id} variant={slotId === s.id ? 'default' : 'outline'} aria-pressed={slotId === s.id} onClick={() => setSlotId(s.id)}><Clock3/>{appointmentTime(s.starts_at)} – {appointmentTime(s.ends_at)}</Button>)}</div>
            {selected && <div className="mt-4"><p className="flex gap-2 items-center text-sm">{selected.modality === 'online' ? <Video size={16}/> : <MapPin size={16}/>} {selected.modality === 'online' ? 'Consulta online' : 'Consulta presencial'}</p>{selected.location && <p className="text-sm break-words mt-2">{selected.location}</p>}<Button className="mt-4" disabled={busy} onClick={() => setConfirmation({ slot: selected, cancel: false })}><Check/>Agendar este horário</Button></div>}
          </div>
        </div>}
      </>}
      <div className="mt-6"><h3>Minhas próximas consultas</h3>{appointments.length === 0 ? <p className="text-sm text-muted-foreground mt-2">Você ainda não tem consultas agendadas.</p> : appointments.map(s => <article key={s.id} className="flex flex-wrap items-center gap-4 border-b border-border py-5"><CalendarDays className="text-primary"/><div className="min-w-0 flex-1"><strong className="break-words">{doctorName(s.doctor_id)}</strong><p>{appointmentDate(s.starts_at)} · {appointmentTime(s.starts_at)} – {appointmentTime(s.ends_at)}</p><p className="text-sm break-words">{s.modality === 'online' ? 'Online' : 'Presencial'}{s.location ? ` · ${s.location}` : ''}</p></div>{Date.parse(s.starts_at) > Date.now() && <Button variant="outline" disabled={busy} onClick={() => setConfirmation({ slot: s, cancel: true })}><X/>Cancelar consulta</Button>}</article>)}</div>
    </>}
    {notice && <p role="status" className="mt-4 text-primary">{notice}</p>}{error && <p role="alert" className="mt-4 text-destructive">{error}</p>}
    <Dialog open={confirmation !== null} onOpenChange={open => { if (!open && !busy) setConfirmation(null); }}><DialogContent><DialogTitle>{confirmation?.cancel ? 'Cancelar consulta?' : 'Confirmar agendamento'}</DialogTitle><DialogDescription>{confirmation && `${doctorName(confirmation.slot.doctor_id)} · ${appointmentDate(confirmation.slot.starts_at)} · ${appointmentTime(confirmation.slot.starts_at)} (Brasília)`}</DialogDescription><div className="flex flex-wrap justify-end gap-3"><Button variant="outline" disabled={busy} onClick={() => setConfirmation(null)}>Voltar</Button><Button disabled={busy} variant={confirmation?.cancel ? 'destructive' : 'default'} onClick={confirm}>{busy ? 'Aguarde…' : confirmation?.cancel ? 'Confirmar cancelamento' : 'Confirmar consulta'}</Button></div></DialogContent></Dialog>
  </section>;
}