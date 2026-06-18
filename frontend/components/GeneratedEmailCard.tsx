"use client";

import { AlertTriangle, CheckCircle2, Clipboard, RotateCcw } from "lucide-react";
import { useState } from "react";

import type { GenerateEmailResponse } from "@/lib/api";
import { EvaluationBadge } from "./EvaluationBadge";

type GeneratedEmailCardProps = {
  result: GenerateEmailResponse | null;
  loading: boolean;
  onRegenerate: () => void;
};

export function GeneratedEmailCard({ result, loading, onRegenerate }: GeneratedEmailCardProps) {
  const [copied, setCopied] = useState(false);

  async function copyEmail() {
    if (!result) return;
    await navigator.clipboard.writeText(`Subject: ${result.subject}\n\n${result.email}`);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  if (loading) {
    return (
      <section className="panel min-h-[420px] rounded-lg p-6">
        <div className="flex h-full min-h-[360px] flex-col items-center justify-center text-center">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-slate-200 border-t-teal" />
          <h2 className="mt-5 text-xl font-black text-ink">Generating and evaluating</h2>
          <p className="mt-2 max-w-sm text-sm leading-6 text-slate-600">
            The backend is checking fact coverage, tone fit, and email structure before returning the final draft.
          </p>
        </div>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="panel min-h-[420px] rounded-lg p-6">
        <div className="flex h-full min-h-[360px] flex-col justify-center">
          <p className="text-sm font-bold uppercase text-cobalt">Output</p>
          <h2 className="mt-2 text-2xl font-black text-ink">Your generated email will appear here.</h2>
          <div className="mt-6 grid grid-cols-3 gap-3">
            {["Facts", "Tone", "Quality"].map((item) => (
              <div key={item} className="rounded-lg border border-dashed border-line bg-slate-50 p-3 text-sm font-bold text-slate-500">
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="panel rounded-lg p-5 sm:p-6">
      <div className="flex flex-col gap-3 border-b border-line pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase text-cobalt">Generated Email</p>
          <h2 className="mt-1 text-2xl font-black leading-tight text-ink">{result.subject}</h2>
          <p className="mt-2 text-sm text-slate-600">
            {result.model_used} · {result.strategy_used} · {result.attempt_count} attempt
            {result.attempt_count === 1 ? "" : "s"}
          </p>
        </div>
        <div className="flex gap-2">
          <button className="secondary-button" type="button" onClick={copyEmail}>
            <Clipboard size={17} aria-hidden="true" />
            {copied ? "Copied" : "Copy"}
          </button>
          <button className="secondary-button" type="button" onClick={onRegenerate}>
            <RotateCcw size={17} aria-hidden="true" />
            Regenerate
          </button>
        </div>
      </div>

      <div className="mt-5 rounded-lg border border-line bg-white p-4">
        <p className="whitespace-pre-wrap text-[0.95rem] leading-7 text-slate-800">{result.email}</p>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <EvaluationBadge label="Fact Recall" score={result.quality_scores.fact_recall_integration} />
        <EvaluationBadge label="Tone Fit" score={result.quality_scores.tone_audience_fit} />
        <EvaluationBadge label="Email Quality" score={result.quality_scores.professional_email_quality} />
        <EvaluationBadge label="Overall" score={result.quality_scores.overall} />
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
          <div className="flex items-center gap-2 text-sm font-black text-emerald-800">
            <CheckCircle2 size={17} aria-hidden="true" />
            Included Facts
          </div>
          <ul className="mt-3 space-y-2 text-sm text-emerald-900">
            {result.included_facts.length ? (
              result.included_facts.map((fact) => <li key={fact}>• {fact}</li>)
            ) : (
              <li>No included facts were reported.</li>
            )}
          </ul>
        </div>

        <div
          className={`rounded-lg border p-4 ${
            result.needs_human_review || result.missing_facts.length
              ? "border-amber-200 bg-amber-50"
              : "border-slate-200 bg-slate-50"
          }`}
        >
          <div className="flex items-center gap-2 text-sm font-black text-amber-800">
            <AlertTriangle size={17} aria-hidden="true" />
            Review Status
          </div>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {result.needs_human_review ? (
              result.review_reasons.slice(0, 4).map((reason) => <li key={reason}>• {reason}</li>)
            ) : (
              <li>No human review warning returned.</li>
            )}
          </ul>
        </div>
      </div>
    </section>
  );
}

