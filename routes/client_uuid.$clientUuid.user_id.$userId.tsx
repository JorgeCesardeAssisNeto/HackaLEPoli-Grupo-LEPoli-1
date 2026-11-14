import { createFileRoute, Link, useNavigate } from '@tanstack/react-router';
import { useEffect, useRef, useState } from 'react';
import { useServerFn } from '@tanstack/react-start';
import { useQueryClient } from '@tanstack/react-query';
import { toast, Toaster } from 'sonner';
import { supabase } from '@/integrations/supabase/client';
import { synchronizeWearable } from '@/lib/clinical.functions';
import { assertCallbackPatient } from '@/lib/wearable-integration';
import { Button } from '@/components/ui/button';

export const Route = createFileRoute('/client_uuid/$clientUuid/user_id/$userId')({
  head: () => ({ meta: [
    { title: 'Retorno da conexão ROOK | Open Salus' },
    { name: 'description', content: 'Retorno da autorização de dispositivos e sincronização segura da sua conta.' },
    { property: 'og:title', content: 'Conexão ROOK | Open Salus' },
    { property: 'og:description', content: 'Retorno da autorização do wearable.' },
    { property: 'og:type', content: 'website' }, { name: 'twitter:card', content: 'summary' },
  ] }), component: WearableCallback,
});

function WearableCallback() {
  const { userId } = Route.useParams();
  const sync = useServerFn(synchronizeWearable), navigate = useNavigate(), client = useQueryClient();
  const started = useRef(false);
  const [message, setMessage] = useState('Verificando autorização do wearable…');
  const [needsLogin, setNeedsLogin] = useState(false);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void (async () => {
      try {
        const { data } = await supabase.auth.getSession();
        if (!data.session) {
          sessionStorage.setItem('rook-pending-callback', userId);
          setNeedsLogin(true); setMessage('Entre na sua conta para concluir a sincronização.'); return;
        }
        assertCallbackPatient(data.session.user.id, userId);
        const result = await sync({ data: { callbackUserId: userId, transmitReports: sessionStorage.getItem(`rook-report-consent:${userId}`) === 'true' } });
        if (result.error || !result.result) throw new Error(result.error || 'Sincronização não concluída.');
        client.setQueryData(['rook-sync', userId], result.result);
        await Promise.all([client.invalidateQueries({ queryKey: ['patient-health', userId] }), client.invalidateQueries({ queryKey: ['api-metrics'] }), client.invalidateQueries({ queryKey: ['api-alerts', userId] })]);
        sessionStorage.setItem('rook-return-message', 'Wearable conectado com sucesso!');
      } catch (error) {
        const text = error instanceof Error ? error.message : 'Falha ao sincronizar o wearable.';
        toast.error(text); sessionStorage.setItem('rook-return-error', text);
      }
      await navigate({ to: '/dashboard', replace: true });
    })();
  }, [userId, sync, navigate, client]);
  return <main className="workspace"><Toaster richColors/><h1>Conexão do wearable</h1><p role="status" className="my-4">{message}</p>{needsLogin && <Button asChild><Link to="/auth">Entrar</Link></Button>}</main>;
}