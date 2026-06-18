"use client";

import { ClipboardCheck, FileText, MailCheck } from "lucide-react";
import { useState } from "react";

import { EmailForm } from "@/components/EmailForm";
import { GeneratedEmailCard } from "@/components/GeneratedEmailCard";
import { HistoryPanel } from "@/components/HistoryPanel";
import { generateEmail, type GenerateEmailPayload, type GenerateEmailResponse } from "@/lib/api";

export function EmailGeneratorShell() {
  const [result, setResult] = useState<GenerateEmailResponse | null>(null);
  const [lastPayload, setLastPayload] = useState<GenerateEmailPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyRefresh, setHistoryRefresh] = useState(0);

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
    <main className="mx-auto min-h-screen w-full max-w-7xl px-3 py-4 sm:px-5 sm:py-6 lg:px-8">
      <header className="app-header mb-5 rounded-lg p-5 sm:p-6 lg:p-7">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-lg border border-white/20 bg-white/10">
              <MailCheck size={24} aria-hidden="true" />
            </div>
            <h1 className="text-3xl font-black tracking-normal sm:text-4xl">Email Generation Assistant</h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-white/80">
              Draft concise professional emails with required facts, tone control, and quality scoring in one workspace.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="toolbar-chip">
              <FileText size={15} aria-hidden="true" />
              Intent
            </span>
            <span className="toolbar-chip">
              <ClipboardCheck size={15} aria-hidden="true" />
              Facts
            </span>
            <span className="toolbar-chip">
              <MailCheck size={15} aria-hidden="true" />
              Tone
            </span>
          </div>
        </div>
      </header>

      {error ? (
        <div className="mb-5 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm font-bold text-rose-800">{error}</div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-[minmax(340px,0.82fr)_minmax(0,1.18fr)] lg:items-start">
        <div className="space-y-5">
          <EmailForm onSubmit={submit} loading={loading} />
          <HistoryPanel refreshKey={historyRefresh} onSelect={setResult} />
        </div>
        <GeneratedEmailCard result={result} loading={loading} onRegenerate={regenerate} />
      </div>
    </main>
  );
}
