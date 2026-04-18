import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { Channel, MessageRead, PersonRead, Scenario, SendResponse } from "../types/api";
import MessagePreview from "./MessagePreview";
import ScenarioPicker from "./ScenarioPicker";

interface Props {
  person: PersonRead;
  onClose: () => void;
}

export default function MessageComposer({ person, onClose }: Props) {
  const qc = useQueryClient();
  const [scenario, setScenario] = useState<Scenario>("ps_outreach");
  const [channel, setChannel] = useState<Channel>("li_dm");
  const [customInstructions, setCustomInstructions] = useState("");
  const [draft, setDraft] = useState<MessageRead | null>(null);
  const [subject, setSubject] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [copied, setCopied] = useState(false);

  const draftMutation = useMutation({
    mutationFn: () =>
      api.post<MessageRead>("/api/messages/draft", {
        person_id: person.id,
        channel,
        scenario,
        custom_instructions: customInstructions || null,
      }),
    onSuccess: (msg) => {
      setDraft(msg);
      setSubject(msg.subject);
      setBody(msg.body);
    },
  });

  const updateMutation = useMutation({
    mutationFn: () =>
      api.patch<MessageRead>(`/api/messages/${draft!.id}`, {
        subject: subject ?? undefined,
        body,
      }),
  });

  const sendMutation = useMutation({
    mutationFn: async () => {
      await updateMutation.mutateAsync();
      return api.post<SendResponse>(`/api/messages/${draft!.id}/send`, {});
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages", person.id] });
      qc.invalidateQueries({ queryKey: ["person", String(person.id)] });
      onClose();
    },
  });

  const markSentMutation = useMutation({
    mutationFn: async () => {
      await updateMutation.mutateAsync();
      return api.post<MessageRead>(`/api/messages/${draft!.id}/mark-sent`, {});
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messages", person.id] });
      qc.invalidateQueries({ queryKey: ["person", String(person.id)] });
      onClose();
    },
  });

  const handleCopyMarkSent = async () => {
    await navigator.clipboard.writeText(body);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    markSentMutation.mutate();
  };

  const isLi = channel === "li_connection_note" || channel === "li_dm";

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Draft message — {person.full_name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">
            ×
          </button>
        </div>

        <div className="p-6 space-y-5">
          {!draft && (
            <>
              <ScenarioPicker
                scenario={scenario}
                channel={channel}
                onScenarioChange={setScenario}
                onChannelChange={setChannel}
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Additional instructions (optional)
                </label>
                <textarea
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                  rows={2}
                  placeholder="e.g. mention their recent blog post about X…"
                  className="w-full border rounded px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-indigo-400"
                />
              </div>
              <button
                onClick={() => draftMutation.mutate()}
                disabled={draftMutation.isPending}
                className="w-full py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm font-medium disabled:opacity-50"
              >
                {draftMutation.isPending ? "Generating…" : "Generate draft with Claude"}
              </button>
              {draftMutation.isError && (
                <p className="text-sm text-red-500">
                  {draftMutation.error instanceof Error ? draftMutation.error.message : "Generation failed"}
                </p>
              )}
            </>
          )}

          {draft && (
            <>
              <MessagePreview
                channel={channel}
                subject={subject}
                body={body}
                onSubjectChange={setSubject}
                onBodyChange={setBody}
              />

              <div className="flex gap-3">
                {isLi ? (
                  <button
                    onClick={handleCopyMarkSent}
                    disabled={markSentMutation.isPending}
                    className="flex-1 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm font-medium disabled:opacity-50"
                  >
                    {copied ? "✓ Copied!" : "Copy to clipboard + mark sent"}
                  </button>
                ) : (
                  <button
                    onClick={() => sendMutation.mutate()}
                    disabled={sendMutation.isPending}
                    className="flex-1 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm font-medium disabled:opacity-50"
                  >
                    {sendMutation.isPending ? "Sending…" : "Send email"}
                  </button>
                )}
                <button
                  onClick={() => { setDraft(null); setBody(""); setSubject(null); }}
                  className="px-4 py-2 border rounded text-sm text-gray-600 hover:bg-gray-50"
                >
                  Regenerate
                </button>
              </div>

              {sendMutation.isError && (
                <p className="text-sm text-red-500">
                  {sendMutation.error instanceof Error ? sendMutation.error.message : "Send failed"}
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
