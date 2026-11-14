import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import {
  activeConfounderLabels,
  causalAnswersToFactors,
  defaultCausalAnswers,
} from '@/lib/causal-questions';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children }: { children: React.ReactNode }) => <a>{children}</a>,
}));

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      onAuthStateChange: vi.fn(() => ({ data: { subscription: { unsubscribe: vi.fn() } } })),
    },
  },
}));

import { HealthWorkspace } from '@/components/health-workspace';

beforeAll(() => {
  if (!('ResizeObserver' in globalThis)) {
    globalThis.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  }
});

afterEach(() => {
  cleanup();
});

describe('inferência causal e limpeza do workspace', () => {
  it('mapeia respostas dos 5 fatores de confusão para os limiares da DAG', () => {
    expect(causalAnswersToFactors(defaultCausalAnswers)).toEqual({
      caffeine_mg: 0,
      screen_time_min: 45,
      alcohol_units: 0,
      steps: 7800,
      workout_minutes: 30,
      sleep_duration_hours: 6.8,
    });
    expect(activeConfounderLabels(defaultCausalAnswers)).toEqual([]);

    const confounded = {
      caffeine: 'high' as const,
      screenTime: 'high' as const,
      alcohol: 'light' as const,
      activity: 'sedentary' as const,
      shortSleep: 'short' as const,
    };

    expect(causalAnswersToFactors(confounded)).toEqual({
      caffeine_mg: 120,
      screen_time_min: 160,
      alcohol_units: 1,
      steps: 4200,
      workout_minutes: 0,
      sleep_duration_hours: 5.2,
    });
    expect(activeConfounderLabels(confounded)).toEqual([
      'Cafeína > 90 mg',
      'Tela noturna > 130 min',
      'Consumo de álcool',
      'Baixo movimento (< 6.500 passos)',
      'Sono curto (< 6h)',
    ]);
  });

  it('remove medicações/vacinas e sincroniza perguntas causais com o Cockpit do Médico', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <HealthWorkspace />
      </QueryClientProvider>,
    );

    expect(screen.getByText('Exames laboratoriais')).toBeInTheDocument();
    expect(
      screen.getByText(/Perguntas da Inferência Causal \(Camada 1 · Fatores de Confusão\)/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Medicações/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Vacinas/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByLabelText(/Elevado \(120 mg/i));
    expect(screen.getByText('Cafeína > 90 mg')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Cockpit do Médico/i }));
    expect(screen.getByText('WearableBridge AI')).toBeInTheDocument();
    expect(screen.getAllByText('Cafeína > 90 mg').length).toBeGreaterThanOrEqual(2);
  });
});
