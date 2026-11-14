import { GitBranch, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  activeConfounderLabels,
  CAUSAL_QUESTIONS,
  type CausalQuestionAnswers,
} from '@/lib/causal-questions';

type CausalQuestionsProps = {
  answers: CausalQuestionAnswers;
  onChange: (next: CausalQuestionAnswers) => void;
  onEvaluate?: () => void;
  evaluating?: boolean;
  disabled?: boolean;
  compact?: boolean;
};

export function CausalQuestionsPanel({
  answers,
  onChange,
  onEvaluate,
  evaluating = false,
  disabled = false,
  compact = false,
}: CausalQuestionsProps) {
  const active = activeConfounderLabels(answers);

  return (
    <section aria-label="Perguntas da inferência causal" className="panel p-5 mb-4">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <GitBranch size={16} className="text-primary" />
            Perguntas da Inferência Causal (Camada 1 · Fatores de Confusão)
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            Wearables não capturam hábitos externos automaticamente. Suas respostas ajustam os 4 alvos clínicos da DAG causal para evitar falsos alarmes.
          </p>
        </div>
        {onEvaluate && (
          <Button size="sm" type="button" disabled={disabled || evaluating} onClick={onEvaluate}>
            <RefreshCw size={14} className={evaluating ? 'animate-spin motion-reduce:animate-none' : ''} />
            {evaluating ? 'Avaliando…' : 'Avaliar inferência causal'}
          </Button>
        )}
      </div>

      <div className={`grid grid-cols-1 ${compact ? '' : 'md:grid-cols-2'} gap-4`}>
        {CAUSAL_QUESTIONS.map(q => {
          const current = answers[q.key];
          return (
            <fieldset key={q.key} className="care-question rounded-md border border-border bg-muted/40 p-3.5">
              <legend className="px-1 text-foreground">{q.label}</legend>
              <p className="text-[11px] text-muted-foreground mt-1 mb-2.5 leading-relaxed">{q.hint}</p>
              <div className="flex flex-wrap gap-2">
                {q.options.map(option => {
                  const selected = current === option.value;
                  return (
                    <label
                      key={option.value}
                      className={`inline-flex items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs cursor-pointer transition-colors ${
                        selected
                          ? 'border-primary bg-accent text-foreground font-medium'
                          : 'border-border bg-card text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`causal-${q.key}`}
                        value={option.value}
                        checked={selected}
                        disabled={disabled || evaluating}
                        onChange={() => onChange({ ...answers, [q.key]: option.value })}
                        className="accent-[var(--primary)]"
                      />
                      <span>{option.label}</span>
                    </label>
                  );
                })}
              </div>
            </fieldset>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-2 mt-4 pt-3 border-t border-border text-xs">
        <span className="text-muted-foreground">Confundidores ativos na inferência:</span>
        {active.length === 0 ? (
          <span className="pill success">Nenhum confundidor agudo · Linha de base limpa</span>
        ) : (
          active.map(label => (
            <span key={label} className="pill warning">
              {label}
            </span>
          ))
        )}
      </div>
    </section>
  );
}
