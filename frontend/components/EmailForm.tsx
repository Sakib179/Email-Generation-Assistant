"use client";

import { Minus, Plus, Send } from "lucide-react";
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
  const [intent, setIntent] = useState("Follow up after yesterday's client meeting");
  const [facts, setFacts] = useState(["Discussed website redesign", "Client requested a timeline", "Proposal will be sent by Friday"]);
  const [tone, setTone] = useState("Formal");
  const [strategy, setStrategy] = useState<StrategyName>("advanced");
  const [model, setModel] = useState("");
  const [error, setError] = useState("");

  const cleanFacts = useMemo(() => facts.map((fact) => fact.trim()).filter(Boolean), [facts]);

  function updateFact(index: number, value: string) {
    setFacts((current) => current.map((fact, itemIndex) => (itemIndex === index ? value : fact)));
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
    <form className="panel rounded-lg p-5 sm:p-6" onSubmit={handleSubmit}>
      <div className="flex flex-col gap-2 border-b border-line pb-5">
        <p className="text-xs font-bold uppercase text-cobalt">Inputs</p>
        <h2 className="text-2xl font-black text-ink">Compose a professional email</h2>
      </div>

      <div className="mt-5 space-y-5">
        <label className="block">
          <span className="text-sm font-bold text-slate-700">Intent</span>
          <textarea
            className="field mt-2 min-h-[92px] resize-y"
            value={intent}
            onChange={(event) => setIntent(event.target.value)}
            maxLength={1000}
            placeholder="Follow up after client meeting"
            required
          />
        </label>

        <div>
          <div className="mb-2 flex items-center justify-between gap-3">
            <label className="text-sm font-bold text-slate-700">Key Facts</label>
            <button className="icon-button" type="button" onClick={addFact} aria-label="Add key fact" title="Add key fact">
              <Plus size={18} aria-hidden="true" />
            </button>
          </div>
          <div className="space-y-2">
            {facts.map((fact, index) => (
              <div key={index} className="flex gap-2">
                <input
                  className="field"
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

        <label className="block">
          <span className="text-sm font-bold text-slate-700">Tone</span>
          <select className="field mt-2" value={tone} onChange={(event) => setTone(event.target.value)} required>
            {TONES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <div>
          <span className="text-sm font-bold text-slate-700">Strategy</span>
          <div className="mt-2 grid grid-cols-2 gap-2 rounded-lg border border-line bg-slate-50 p-1">
            {(["advanced", "simple"] as StrategyName[]).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setStrategy(option)}
                className={`rounded-md px-3 py-2 text-sm font-black capitalize transition ${
                  strategy === option ? "bg-white text-teal shadow-sm" : "text-slate-600 hover:bg-white"
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <label className="block">
          <span className="text-sm font-bold text-slate-700">Model Override</span>
          <input
            className="field mt-2"
            value={model}
            onChange={(event) => setModel(event.target.value)}
            placeholder="Optional Groq model ID"
            maxLength={120}
          />
        </label>
      </div>

      {error ? <div className="mt-5 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm font-bold text-rose-800">{error}</div> : null}

      <button className="primary-button mt-6 w-full" type="submit" disabled={loading}>
        <Send size={18} aria-hidden="true" />
        {loading ? "Working" : "Generate Email"}
      </button>
    </form>
  );
}

