import { createFileRoute } from "@tanstack/react-router";
import { Link, useHydrated } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { HeartPulse, UserRound, Stethoscope, ShieldCheck, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { supabase } from '@/integrations/supabase/client';
import welcome from '@/assets/health-welcome.jpg';

// The home route ships no og:image, so serve-time hosting can inject the
// project's social preview (explicit og:image or latest screenshot).
export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "Open Salus | Seu hub de saúde conectado" },
    { name: "description", content: "Hub pessoal e briefing clínico Open Salus: exames, sinais de wearables e consentimento em uma demonstração interativa do Desafio Rivio." },
    { property: "og:title", content: "Open Salus | Saúde conectada" },
    { property: "og:description", content: "Uma visão integrada para pacientes e médicos, com histórico, sinais de saúde e controle de consentimento." },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary_large_image" },
  ] }),
  component: Welcome,
});

function Welcome() {
 const hydrated = useHydrated();
 const { data: user } = useQuery({ queryKey: ['welcome-user'], enabled: hydrated, queryFn: async () => (await supabase.auth.getUser()).data.user });
 return <><header className="topbar"><div className="brand"><span className="brand-symbol"><HeartPulse/></span><span className="brand-title">Open Salus</span></div><Button asChild variant="outline"><Link to={user ? '/dashboard' : '/auth'}>{user ? 'Minha conta' : 'Entrar'}<ArrowRight/></Link></Button></header><main><section className="welcome"><img className="welcome-photo" src={welcome} width={1536} height={1024} alt="Médica conversando com uma paciente em um consultório"/><div className="welcome-content"><span className="eyebrow">SAÚDE CONECTADA. CUIDADO INTEGRAL.</span><h1>Open Salus</h1><p>Seu histórico de saúde e as pessoas que cuidam de você, mais próximos. Conecte-se ao seu médico com privacidade e controle sobre cada autorização.</p><div className="welcome-actions"><Button asChild size="lg"><Link to={user ? '/dashboard' : '/auth'}>{user ? 'Acessar minha conta' : 'Começar meu cuidado'}<ArrowRight/></Link></Button><Button asChild size="lg" variant="outline"><Link to="/demo">Conhecer a demonstração</Link></Button></div></div></section><section className="welcome-summary"><article><UserRound className="text-primary"/><h2>Para pacientes</h2><p>Uma conta, um ID exclusivo e a escolha de quem pode acompanhar seu cuidado.</p></article><article><Stethoscope className="text-primary"/><h2>Para médicos</h2><p>Solicite conexões pelo ID do paciente. O acesso começa com a autorização dele.</p></article><article><ShieldCheck className="text-primary"/><h2>Privacidade por princípio</h2><p>Autorizações revogáveis e administração restrita a pessoas convidadas.</p></article></section></main><footer className="workspace border-t border-border text-xs text-muted-foreground">Desafio Rivio · Exames e gráficos demonstrativos. Não substitui avaliação médica.</footer></>;
}
