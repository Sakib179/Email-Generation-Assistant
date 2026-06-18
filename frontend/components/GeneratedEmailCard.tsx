"use client";

import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Clipboard,
  ListChecks,
  MailOpen,
  Pencil,
  RotateCcw,
  ShieldCheck,
  Target,
  X
} from "lucide-react";
import { useEffect, useState } from "react";

import type { GenerateEmailResponse } from "@/lib/api";
import { EvaluationBadge } from "./EvaluationBadge";

type GeneratedEmailCardProps = {
  result: GenerateEmailResponse | null;
  loading: boolean;
  onRegenerate: () => void;
};

export function GeneratedEmailCard({ result, loading, onRegenerate }: GeneratedEmailCardProps) {
  const [copied, setCopied] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editedSubject, setEditedSubject] = useState("");
  const [editedEmail, setEditedEmail] = useState("");

  useEffect(() => {
    if (!result) {
      setEditedSubject("");
      setEditedEmail("");
      setEditing(false);
      return;
    }
    setEditedSubject(result.subject);
    setEditedEmail(result.email);
    setEditing(false);
  }, [result]);

  async function copyEmail() {
    if (!result) return;
    await navigator.clipboard.writeText(`Subject: ${editedSubject || result.subject}\n\n${editedEmail || result.email}`);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  function resetEdits() {
    if (!result) return;
    setEditedSubject(result.subject);
    setEditedEmail(result.email);
  }

  if (loading) {
    return (
      <section className="panel min-h-[460px] rounded-lg p-5 sm:p-6">
        <div className="flex h-full min-h-[360px] flex-col items-center justify-center text-center">
          <div className="relative h-16 w-16">
            <div className="absolute inset-0 rounded-lg border border-line bg-white shadow-panel" />
            <div className="absolute inset-3 animate-spin rounded-full border-4 border-slate-200 border-t-teal" />
          </div>
          <h2 className="mt-5 text-xl font-black text-ink">Generating and evaluating</h2>
          <div className="mt-5 w-full max-w-md space-y-2">
            <div className="h-3 rounded-full bg-slate-100">
              <div className="h-3 w-2/3 rounded-full bg-teal" />
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="h-10 rounded-lg bg-slate-100" />
              <div className="h-10 rounded-lg bg-slate-100" />
              <div className="h-10 rounded-lg bg-slate-100" />
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="panel min-h-[460px] overflow-hidden rounded-lg">
        <div className="border-b border-line bg-slate-50 px-5 py-4">
          <p className="section-kicker">
            <MailOpen size={15} aria-hidden="true" />
            Output
          </p>
        </div>
        <div className="flex min-h-[390px] flex-col justify-center p-5 sm:p-7">
          <div className="max-w-xl">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-lg border border-line bg-white text-cobalt shadow-sm">
              <MailOpen size={26} aria-hidden="true" />
            </div>
            <h2 className="text-2xl font-black text-ink">Generated email preview</h2>
            <div className="mt-6 rounded-lg border border-dashed border-line bg-white p-4">
              <div className="h-3 w-3/5 rounded-full bg-slate-200" />
              <div className="mt-5 space-y-3">
                <div className="h-3 rounded-full bg-slate-100" />
                <div className="h-3 w-11/12 rounded-full bg-slate-100" />
                <div className="h-3 w-4/5 rounded-full bg-slate-100" />
              </div>
              <div className="mt-6 h-3 w-1/3 rounded-full bg-slate-200" />
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="panel overflow-hidden rounded-lg">
      <div className="border-b border-line bg-slate-50 p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="section-kicker">
              <MailOpen size={15} aria-hidden="true" />
              Generated Email
            </p>
            {editing ? (
              <input
                className="field mt-2 text-xl font-black leading-tight sm:text-2xl"
                value={editedSubject}
                onChange={(event) => setEditedSubject(event.target.value)}
                maxLength={250}
                aria-label="Edit generated email subject"
              />
            ) : (
              <h2 className="mt-2 text-2xl font-black leading-tight text-ink">{editedSubject || result.subject}</h2>
            )}
            <p className="mt-2 text-sm font-semibold text-slate-600">
              {result.strategy_used} strategy - {result.attempt_count} attempt
              {result.attempt_count === 1 ? "" : "s"}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:flex">
            {editing ? (
              <>
                <button className="secondary-button" type="button" onClick={() => setEditing(false)}>
                  <Check size={17} aria-hidden="true" />
                  Done
                </button>
                <button className="secondary-button" type="button" onClick={resetEdits}>
                  <X size={17} aria-hidden="true" />
                  Reset
                </button>
              </>
            ) : (
              <button className="secondary-button" type="button" onClick={() => setEditing(true)}>
                <Pencil size={17} aria-hidden="true" />
                Edit
              </button>
            )}
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
      </div>

      <div className="p-5 sm:p-6">
        {result.intent || result.key_facts.length ? (
          <div className="mb-5 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
            {result.intent ? (
              <div className="rounded-lg border border-line bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-black text-cobalt">
                  <Target size={17} aria-hidden="true" />
                  Intent
                </div>
                <p className="mt-3 text-sm font-semibold leading-6 text-slate-700">{result.intent}</p>
              </div>
            ) : null}

            {result.key_facts.length ? (
              <div className="rounded-lg border border-line bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-black text-cobalt">
                  <ListChecks size={17} aria-hidden="true" />
                  Key Facts
                </div>
                <ul className="mt-3 space-y-2 text-sm font-semibold text-slate-700">
                  {result.key_facts.map((fact) => (
                    <li key={fact}>- {fact}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : null}

        <div className="rounded-lg border border-line bg-white p-4 shadow-sm sm:p-5">
          {editing ? (
            <textarea
              className="field min-h-[320px] resize-y border-0 bg-slate-50 text-[0.96rem] leading-7 shadow-none focus:bg-white"
              value={editedEmail}
              onChange={(event) => setEditedEmail(event.target.value)}
              maxLength={8000}
              aria-label="Edit generated email body"
            />
          ) : (
            <p className="whitespace-pre-wrap text-[0.96rem] leading-7 text-slate-800">{editedEmail || result.email}</p>
          )}
        </div>
        {editing ? (
          <p className="mt-3 text-sm font-semibold text-slate-500">
            Edits are local to this draft. Copy uses your edited subject and body.
          </p>
        ) : null}

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
                result.included_facts.map((fact) => <li key={fact}>- {fact}</li>)
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
              {result.needs_human_review ? <AlertTriangle size={17} aria-hidden="true" /> : <ShieldCheck size={17} aria-hidden="true" />}
              Review Status
            </div>
            <ul className="mt-3 space-y-2 text-sm text-slate-700">
              {result.needs_human_review ? (
                result.review_reasons.slice(0, 4).map((reason) => <li key={reason}>- {reason}</li>)
              ) : (
                <li>No human review warning returned.</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
