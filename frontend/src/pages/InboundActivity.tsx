import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { InboundEventRead, InboundKind } from "../types/api";

const KIND_LABEL: Record<InboundKind, string> = {
  reply: "Reply",
  bounce_hard: "Hard bounce",
  bounce_soft: "Soft bounce",
  opt_out: "Opt-out",
  auto_reply: "Auto-reply",
};

const KIND_COLOR: Record<InboundKind, string> = {
  reply: "bg-green-100 text-green-700",
  bounce_hard: "bg-red-100 text-red-700",
  bounce_soft: "bg-orange-100 text-orange-700",
  opt_out: "bg-purple-100 text-purple-700",
  auto_reply: "bg-gray-100 text-gray-500",
};

const KINDS: InboundKind[] = ["reply", "bounce_hard", "bounce_soft", "opt_out", "auto_reply"];

export default function InboundActivity() {
  const qc = useQueryClient();
  const [kindFilter, setKindFilter] = useState<InboundKind | "">("");
  const [processedFilter, setProcessedFilter] = useState<"" | "true" | "false">("");

  const params = new URLSearchParams({ limit: "100" });
  if (kindFilter) params.set("kind", kindFilter);
  if (processedFilter !== "") params.set("processed", processedFilter);

  const { data: events = [], isLoading } = useQuery<InboundEventRead[]>({
    queryKey: ["inbound", kindFilter, processedFilter],
    queryFn: () => api.get<InboundEventRead[]>(`/api/inbound/events?${params}`),
  });

  const markProcessedMutation = useMutation({
    mutationFn: (id: number) => api.post<InboundEventRead>(`/api/inbound/events/${id}/mark-processed`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inbound"] }),
  });

  const pollMutation = useMutation({
    mutationFn: () => api.post<{ status: string }>("/api/inbound/poll-now", {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inbound"] }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Inbound Activity</h1>
        <button
          onClick={() => pollMutation.mutate()}
          disabled={pollMutation.isPending}
          className="text-sm px-3 py-1.5 border rounded text-gray-600 hover:bg-gray-50 disabled:opacity-60"
        >
          {pollMutation.isPending ? "Polling…" : "Poll now"}
        </button>
      </div>

      <div className="flex gap-3 flex-wrap">
        <select
          value={kindFilter}
          onChange={(e) => setKindFilter(e.target.value as InboundKind | "")}
          className="border rounded px-3 py-1.5 text-sm"
        >
          <option value="">All types</option>
          {KINDS.map((k) => (
            <option key={k} value={k}>{KIND_LABEL[k]}</option>
          ))}
        </select>
        <select
          value={processedFilter}
          onChange={(e) => setProcessedFilter(e.target.value as "" | "true" | "false")}
          className="border rounded px-3 py-1.5 text-sm"
        >
          <option value="">All</option>
          <option value="false">Needs review</option>
          <option value="true">Processed</option>
        </select>
      </div>

      {isLoading ? (
        <p className="text-gray-400 text-sm py-8 text-center">Loading…</p>
      ) : events.length === 0 ? (
        <p className="text-gray-400 text-sm py-8 text-center">No inbound events found.</p>
      ) : (
        <div className="space-y-2">
          {events.map((e) => (
            <div
              key={e.id}
              className={`bg-white border rounded-lg p-4 flex items-start justify-between gap-4 ${
                e.kind === "opt_out" && !e.processed ? "border-purple-300" : "border-gray-200"
              }`}
            >
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${KIND_COLOR[e.kind]}`}>
                    {KIND_LABEL[e.kind]}
                  </span>
                  {!e.processed && <span className="text-xs text-orange-500 font-medium">Needs review</span>}
                </div>
                <p className="text-sm font-medium text-gray-700 truncate">{e.subject ?? "(no subject)"}</p>
                {e.from_address && <p className="text-xs text-gray-400 truncate">From: {e.from_address}</p>}
                {e.snippet && <p className="text-xs text-gray-500 line-clamp-2">{e.snippet}</p>}
                <p className="text-xs text-gray-300">{new Date(e.received_at).toLocaleString()}</p>
              </div>
              {!e.processed && (
                <button
                  onClick={() => markProcessedMutation.mutate(e.id)}
                  disabled={markProcessedMutation.isPending}
                  className="shrink-0 text-xs px-3 py-1.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-60"
                >
                  {e.kind === "opt_out" ? "Confirm opt-out" : "Mark reviewed"}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
