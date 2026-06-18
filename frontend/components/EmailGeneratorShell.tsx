"use client";

import { Activity, AlertCircle, CheckCircle2, Server } from "lucide-react";
import { useEffect, useState } from "react";

import { EmailForm } from "@/components/EmailForm";
import { GeneratedEmailCard } from "@/components/GeneratedEmailCard";
import { HistoryPanel } from "@/components/HistoryPanel";
import { generateEmail, getHealth, type GenerateEmailPayload, type GenerateEmailResponse, type HealthResponse } from "@/lib/api";

export function EmailGeneratorShell() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState("");
  const [result, setResult] = useState<GenerateEmailResponse | null>(null);
  const [lastPayload, setLastPayload] = useState<GenerateEmailPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyRefresh, setHistoryRefresh] = useState(0);

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then((data) => {
        if (!cancelled) {
          setHealth(data);
          setHealthError("");
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setHealthError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function submit(payload: GenerateEmailPayload) {
    setLoading(true);
    setError("");
    setLastPayload(payload);
    try {
      const response = await generateEmail(payload);
      setResult(response);
      setHistoryRefresh((value) => value + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setLoading(false);
    }
  }

  function regenerate() {
    if (lastPayload) {
      void submit(lastPayload);
    }
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-col gap-4 border-b border-line pb-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-sm font-bold text-slate-700">
            <Activity size={16} className="text-teal" aria-hidden="true" />
            Groq-backed AI writing assistant
          </div>
          <h1 className="text-3xl font-black tracking-normal text-ink sm:text-4xl">Email Generation Assistant</h1>
          <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
            Generate professional English emails from intent, required facts, and tone, then review quality scores before sending.
          </p>
        </div>

        <div className="rounded-lg border border-line bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-black text-ink">
            <Server size={17} className="text-cobalt" aria-hidden="true" />
            Model Status
          </div>
          {health ? (
            <div className="mt-2 space-y-1 text-sm text-slate-600">
              <div className="flex items-center gap-2">
                {health.groq_api_key_configured ? (
                  <CheckCircle2 size={16} className="text-teal" aria-hidden="true" />
                ) : (
                  <AlertCircle size={16} className="text-amber" aria-hidden="true" />
                )}
                <span>{health.groq_api_key_configured ? "Groq key configured" : "Groq key missing"}</span>
              </div>
              <div>{health.primary_model}</div>
              <div>{health.prompt_version}</div>
            </div>
          ) : (
            <div className="mt-2 text-sm text-slate-500">{healthError || "Checking API"}</div>
          )}
        </div>
      </header>

      {error ? (
        <div className="mb-5 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm font-bold text-rose-800">{error}</div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-[minmax(340px,0.82fr)_minmax(0,1.18fr)]">
        <div className="space-y-5">
          <EmailForm onSubmit={submit} loading={loading} />
          <HistoryPanel refreshKey={historyRefresh} onSelect={setResult} />
        </div>
        <GeneratedEmailCard result={result} loading={loading} onRegenerate={regenerate} />
      </div>
    </main>
  );
}

