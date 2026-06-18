type EvaluationBadgeProps = {
  label: string;
  score: number;
};

function scoreClasses(score: number) {
  if (score >= 8.2) {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }
  if (score >= 7.5) {
    return "border-amber-200 bg-amber-50 text-amber-800";
  }
  return "border-rose-200 bg-rose-50 text-rose-800";
}

export function EvaluationBadge({ label, score }: EvaluationBadgeProps) {
  return (
    <div className={`rounded-lg border px-3 py-2 ${scoreClasses(score)}`}>
      <div className="text-[0.68rem] font-bold uppercase leading-tight tracking-normal">{label}</div>
      <div className="mt-1 text-lg font-black leading-none">{score.toFixed(1)}</div>
    </div>
  );
}

