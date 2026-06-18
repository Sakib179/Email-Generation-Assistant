"use client";

import { ListChecks, Minus, Plus, Send, SlidersHorizontal, Target } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import type { GenerateEmailPayload, StrategyName } from "@/lib/api";

const TONES = [
  "Formal",
  "Casual",
  "Urgent",
  "Empathetic",
  "Persuasive",
  "Polite but Firm",
  "Concise Executive",
  "Friendly Professional"
];

type EmailFormProps = {
  onSubmit: (payload: GenerateEmailPayload) => void;
  loading: boolean;
};

export function EmailForm({ onSubmit, loading }: EmailFormProps) {
  const [intent, setIntent] = useState("");
  const [facts, setFacts] = useState([""]);
  const [tone, setTone] = useState("Formal");
  const [strategy, setStrategy] = useState<StrategyName>("advanced");
  const [model, setModel] = useState("");
  const [error, setError] = useState("");

  const cleanFacts = useMemo(() => facts.map((fact) => fact.trim()).filter(Boolean), [facts]);

  function updateFact(index: number, value: string) {
    setFacts((current) => {
      const next = current.map((fact, itemIndex) => (itemIndex === index ? value : fact));
      const isLastRow = index === current.length - 1;
      if (isLastRow && value.trim() && current.length < 15) {
        next.push("");
      }
      return next;
    });
  }

  function addFact() {
    setFacts((current) => [...current, ""]);
  }

  function removeFact(index: number) {
    setFacts((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!intent.trim()) {
      setError("Intent is required.");
      return;
    }
    if (!cleanFacts.length) {
      setError("At least one key fact is required.");
      return;
    }
    if (!tone) {
      setError("Tone is required.");
      return;
    }
    setError("");
    onSubmit({
      intent: intent.trim(),
      key_facts: cleanFacts,
      tone,
      strategy,
      model: model.trim() || undefined
    });
  }

  return (
    <form className="panel rounded-lg p-4 sm:p-5" onSubmit={handleSubmit}>
      <div className="flex items-start justify-between gap-4 border-b border-line pb-4">
        <div>
          <p className="section-kicker">
            <Target size={15} aria-hidden="true" />
            Inputs
          </p>
          <h2 className="mt-2 text-2xl font-black leading-tight text-ink">Compose email</h2>
        </div>
        <div className="rounded-lg border border-line bg-slate-50 px-3 py-2 text-center">
          <div className="text-lg font-black leading-none text-teal">{cleanFacts.length}</div>
          <div className="mt-1 text-[0.68rem] font-black uppercase text-slate-500">Facts</div>
        </div>
      </div>

      <div className="mt-5 space-y-5">
        <label className="block">
          <span className="flex items-center gap-2 text-sm font-black text-slate-800">
            <Target size={16} className="text-cobalt" aria-hidden="true" />
            Intent
          </span>
          <div className="mt-2 rounded-lg border border-line bg-white p-1.5 shadow-sm">
            <textarea
              className="field min-h-[108px] resize-y border-0 bg-slate-50 shadow-none focus:bg-white"
              value={intent}
              onChange={(event) => setIntent(event.target.value)}
              maxLength={1000}
              placeholder="Follow up after client meeting"
              required
            />
          </div>
        </label>

        <div>
          <div className="mb-2 flex items-center justify-between gap-3">
            <label className="flex items-center gap-2 text-sm font-black text-slate-800">
              <ListChecks size={16} className="text-cobalt" aria-hidden="true" />
              Key Facts
            </label>
            <button className="secondary-button px-3 py-2" type="button" onClick={addFact}>
              <Plus size={17} aria-hidden="true" />
              Add
            </button>
          </div>
          <div className="space-y-2 rounded-lg border border-line bg-white p-2 shadow-sm">
            {facts.map((fact, index) => (
              <div key={index} className="flex gap-2 rounded-lg bg-slate-50 p-1.5">
                <div className="flex h-10 w-8 shrink-0 items-center justify-center rounded-md bg-white text-sm font-black text-slate-500">
                  {index + 1}
                </div>
                <input
                  className="field border-0 bg-transparent px-2 shadow-none focus:bg-white"
                  value={fact}
                  onChange={(event) => updateFact(index, event.target.value)}
                  maxLength={500}
                  placeholder={`Key fact ${index + 1}`}
                />
                <button
                  className="icon-button shrink-0"
                  type="button"
                  onClick={() => removeFact(index)}
                  disabled={facts.length === 1}
                  aria-label="Remove key fact"
                  title="Remove key fact"
                >
                  <Minus size={18} aria-hidden="true" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-black text-slate-800">Tone</span>
            <select className="field mt-2" value={tone} onChange={(event) => setTone(event.target.value)} required>
              {TONES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <div>
            <span className="text-sm font-black text-slate-800">Strategy</span>
            <div className="mt-2 grid grid-cols-2 gap-1 rounded-lg border border-line bg-slate-100 p-1">
              {(["advanced", "simple"] as StrategyName[]).map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setStrategy(option)}
                  className={`rounded-md px-3 py-[0.68rem] text-sm font-black capitalize transition ${
                    strategy === option ? "bg-white text-teal shadow-sm" : "text-slate-600 hover:bg-white"
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        </div>

        <details className="rounded-lg border border-line bg-slate-50 p-3">
          <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-black text-slate-700">
            <SlidersHorizontal size={16} className="text-cobalt" aria-hidden="true" />
            Advanced options
          </summary>
          <label className="mt-3 block">
            <span className="muted-label">Model Override</span>
            <input
              className="field mt-2"
              value={model}
              onChange={(event) => setModel(event.target.value)}
              placeholder="Optional Groq model ID"
              maxLength={120}
            />
          </label>
        </details>
      </div>

      {error ? <div className="mt-5 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm font-bold text-rose-800">{error}</div> : null}

      <button className="primary-button mt-6 w-full" type="submit" disabled={loading}>
        <Send size={18} aria-hidden="true" />
        {loading ? "Working" : "Generate Email"}
      </button>
    </form>
  );
}
