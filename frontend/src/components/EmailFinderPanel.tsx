import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../lib/api";
import type { EmailCandidateRead } from "../types/api";

interface Props {
  personId: number;
  onClose: () => void;
}

const SOURCE_LABEL: Record<string, string> = {
  csv: "CSV import",
  pattern_db: "Pattern DB",
  permutation: "Permutation",
  hunter: "Hunter.io",
  apollo: "Apollo.io",
  skrapp: "Skrapp.io",
  linkedin_contact: "LinkedIn",
  manual: "Manual",
};

function ConfidenceBadge({ value }: { value: number }) {
  const color = value >= 80 ? "bg-green-100 text-green-700" : value >= 50 ? "bg-yellow-100 text-yellow-700" : "bg-gray-100 text-gray-500";
  return <span className={`text-xs px-1.5 py-0.5 rounded ${color}`}>{value}%</span>;
}

export default function EmailFinderPanel({ personId, onClose }: Props) {
  const qc = useQueryClient();
  const [candidates, setCandidates] = useState<EmailCandidateRead[]>([]);
  const [error, setError] = useState<string | null>(null);

  const findMutation = useMutation({
    mutationFn: () => api.post<EmailCandidateRead[]>("/api/email-finder/find", { person_id: personId }),
    onSuccess: (data) => {
      setCandidates(data);
      setError(null);
    },
    onError: (e) => setError(e instanceof ApiError ? String((e.detail as { detail?: string })?.detail ?? e.message) : "Unknown error"),
  });

  const verifyMutation = useMutation({
    mutationFn: (id: number) => api.post<EmailCandidateRead>(`/api/email-finder/candidates/${id}/verify`, {}),
    onSuccess: (updated) =>
      setCandidates((prev) => prev.map((c) => (c.id === updated.id ? updated : c))),
  });

  const acceptMutation = useMutation({
    mutationFn: (id: number) => api.post<EmailCandidateRead>(`/api/email-finder/candidates/${id}/accept`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["person", String(personId)] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="font-semibold text-gray-900">Find Email Address</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>

        <div className="p-4 space-y-4">
          {error && <p className="text-sm text-red-600 bg-red-50 rounded p-2">{error}</p>}

          {candidates.length === 0 ? (
            <p className="text-sm text-gray-500">
              Runs 7 strategies: existing email, company pattern, permutations, Hunter.io, Apollo.io, Skrapp.io, LinkedIn. API-key strategies are skipped if the key is not configured.
            </p>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {candidates.map((c) => (
                <div key={c.id} className={`flex items-center justify-between gap-3 p-2 rounded border ${c.bounced ? "border-red-200 bg-red-50" : "border-gray-200"}`}>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-mono text-gray-800 truncate">{c.email}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-400">{SOURCE_LABEL[c.source] ?? c.source}</span>
                      <ConfidenceBadge value={c.confidence} />
                      {c.verified && <span className="text-xs text-green-600">✓ verified</span>}
                      {c.bounced && <span className="text-xs text-red-500">✗ bounced</span>}
                    </div>
                  </div>
                  <div className="flex gap-1.5 shrink-0">
                    {!c.verified && !c.bounced && (
                      <button
                        onClick={() => verifyMutation.mutate(c.id)}
                        disabled={verifyMutation.isPending}
                        className="text-xs px-2 py-1 border rounded text-gray-600 hover:bg-gray-50"
                      >
                        Verify
                      </button>
                    )}
                    {!c.bounced && (
                      <button
                        onClick={() => acceptMutation.mutate(c.id)}
                        disabled={acceptMutation.isPending}
                        className="text-xs px-2 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                      >
                        Use
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          <button
            onClick={() => findMutation.mutate()}
            disabled={findMutation.isPending}
            className="w-full py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-60"
          >
            {findMutation.isPending ? "Searching…" : candidates.length > 0 ? "Re-run search" : "Search for email"}
          </button>
        </div>
      </div>
    </div>
  );
}
