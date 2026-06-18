"use client";

import { Clock3 } from "lucide-react";
import { useEffect, useState } from "react";

import { getHistory, type GenerateEmailResponse, type HistoryItem } from "@/lib/api";

type HistoryPanelProps = {
  refreshKey: number;
  onSelect: (item: GenerateEmailResponse) => void;
};

export function HistoryPanel({ refreshKey, onSelect }: HistoryPanelProps) {
  const [items, setItems] = useState<HistoryItem[]>([]);

  useEffect(() => {
    let cancelled = false;
    getHistory()
      .then((response) => {
        if (!cancelled) setItems(response.items);
      })
      .catch(() => {
        if (!cancelled) setItems([]);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return (
    <section className="panel rounded-lg p-5">
      <div className="mb-4 flex items-center gap-2">
        <Clock3 size={18} className="text-cobalt" aria-hidden="true" />
        <h2 className="text-base font-black text-ink">History</h2>
      </div>
      <div className="space-y-2">
        {items.length ? (
          items.slice(0, 6).map((item) => (
            <button
              key={item.id}
              type="button"
              className="w-full rounded-lg border border-line bg-white p-3 text-left transition hover:border-cobalt hover:bg-slate-50"
              onClick={() =>
                onSelect({
                  subject: item.subject,
                  email: item.email,
                  included_facts: [],
                  missing_facts: [],
                  quality_scores: item.quality_scores,
                  attempt_count: 1,
                  model_used: item.model_used,
                  strategy_used: item.strategy,
                  needs_human_review: item.needs_human_review,
                  review_reasons: [],
                  hallucination_flag: false,
                  judge_reason: "",
                  prompt_version: ""
                })
              }
            >
              <div className="line-clamp-1 text-sm font-black text-slate-800">{item.subject}</div>
              <div className="mt-1 text-xs text-slate-500">
                {item.tone} · {item.quality_scores.overall.toFixed(1)} overall
              </div>
            </button>
          ))
        ) : (
          <div className="rounded-lg border border-dashed border-line bg-slate-50 p-4 text-sm text-slate-500">
            Saved generations appear after a successful run.
          </div>
        )}
      </div>
    </section>
  );
}
