"use client";

import { Clock3, MailOpen, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { deleteHistoryItem, getHistory, type GenerateEmailResponse, type HistoryItem } from "@/lib/api";

type HistoryPanelProps = {
  refreshKey: number;
  onSelect: (item: GenerateEmailResponse) => void;
};

export function HistoryPanel({ refreshKey, onSelect }: HistoryPanelProps) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    getHistory()
      .then((response) => {
        if (!cancelled) {
          setItems(response.items);
          setError("");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setItems([]);
          setError("Could not load history.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  async function handleDelete(itemId: number) {
    setDeletingId(itemId);
    setError("");
    try {
      await deleteHistoryItem(itemId);
      setItems((currentItems) => currentItems.filter((item) => item.id !== itemId));
    } catch {
      setError("Could not delete this history item.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="panel overflow-hidden rounded-lg">
      <div className="flex items-center justify-between border-b border-line bg-slate-50 px-5 py-4">
        <div className="flex items-center gap-2">
          <Clock3 size={18} className="text-cobalt" aria-hidden="true" />
          <h2 className="text-base font-black text-ink">History</h2>
        </div>
        <span className="rounded-md bg-white px-2 py-1 text-xs font-black text-slate-500">{items.length}</span>
      </div>
      <div className="max-h-[360px] space-y-2 overflow-y-auto p-3">
        {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-bold text-red-700">{error}</div> : null}
        {items.length ? (
          items.map((item) => (
            <div
              key={item.id}
              className="group flex items-stretch overflow-hidden rounded-lg border border-line bg-white shadow-sm transition hover:border-cobalt hover:bg-slate-50"
            >
              <button
                type="button"
                className="min-w-0 flex-1 p-3 text-left"
                onClick={() =>
                  onSelect({
                    intent: item.intent,
                    key_facts: item.key_facts,
                    subject: item.subject,
                    email: item.email,
                    included_facts: item.included_facts,
                    missing_facts: item.missing_facts,
                    quality_scores: item.quality_scores,
                    attempt_count: item.attempt_count,
                    model_used: item.model_used,
                    strategy_used: item.strategy,
                    needs_human_review: item.needs_human_review,
                    review_reasons: item.review_reasons,
                    hallucination_flag: item.hallucination_flag,
                    judge_reason: item.judge_reason,
                    prompt_version: item.prompt_version
                  })
                }
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-cobalt group-hover:bg-blue-50">
                    <MailOpen size={16} aria-hidden="true" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="line-clamp-1 text-sm font-black text-slate-800">{item.subject}</div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-500">
                      <span>{item.tone}</span>
                      <span className="rounded-md bg-slate-100 px-2 py-0.5 text-slate-700">{item.quality_scores.overall.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
              </button>
              <button
                type="button"
                className="flex w-12 shrink-0 items-center justify-center border-l border-line text-slate-400 transition hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                aria-label={`Delete history item: ${item.subject}`}
                disabled={deletingId === item.id}
                onClick={() => handleDelete(item.id)}
                title="Delete history item"
              >
                <Trash2 size={16} aria-hidden="true" />
              </button>
            </div>
          ))
        ) : (
          <div className="rounded-lg border border-dashed border-line bg-slate-50 p-4 text-sm font-semibold text-slate-500">
            Saved generations appear here after a successful run.
          </div>
        )}
      </div>
    </section>
  );
}
