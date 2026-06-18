type EvaluationBadgeProps = {
  label: string;
  score: number;
};

function scoreClasses(score: number) {
  if (score >= 8.2) {
    return "border-emerald-200 bg-emerald-50 text-emerald-900";
  }
  if (score >= 7.5) {
    return "border-amber-200 bg-amber-50 text-amber-900";
  }
  return "border-rose-200 bg-rose-50 text-rose-900";
}

export function EvaluationBadge({ label, score }: EvaluationBadgeProps) {
  return (
    <div className={`rounded-lg border px-3 py-3 shadow-sm ${scoreClasses(score)}`}>
      <div className="text-[0.68rem] font-black uppercase leading-tight tracking-normal">{label}</div>
      <div className="mt-2 flex items-end justify-between gap-2">
        <div className="text-2xl font-black leading-none">{score.toFixed(1)}</div>
        <div className="h-1.5 flex-1 rounded-full bg-black/10">
          <div className="h-1.5 rounded-full bg-current" style={{ width: `${Math.max(4, Math.min(score * 10, 100))}%` }} />
        </div>
      </div>
    </div>
  );
}
