import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Channel, MessageRead, MessageStatus } from "../types/api";
import StatusBadge from "../components/StatusBadge";

const CHANNEL_LABELS: Record<Channel, string> = {
  li_connection_note: "LI Note",
  li_dm: "LI DM",
  cold_email: "Email",
};

export default function MessagesOutbox() {
  const [statusFilter, setStatusFilter] = useState<MessageStatus | "">("");
  const [channelFilter, setChannelFilter] = useState<Channel | "">("");

  const { data: messages = [], isLoading } = useQuery<MessageRead[]>({
    queryKey: ["messages", statusFilter, channelFilter],
    queryFn: () => {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (channelFilter) params.set("channel", channelFilter);
      return api.get<MessageRead[]>(`/api/messages?${params}`);
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-gray-900">Outbox</h1>

      <div className="flex gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as MessageStatus | "")}
          className="border rounded px-3 py-1.5 text-sm"
        >
          <option value="">All statuses</option>
          {(["draft", "queued", "sent", "failed", "cancelled"] as MessageStatus[]).map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={channelFilter}
          onChange={(e) => setChannelFilter(e.target.value as Channel | "")}
          className="border rounded px-3 py-1.5 text-sm"
        >
          <option value="">All channels</option>
          {(Object.keys(CHANNEL_LABELS) as Channel[]).map((c) => (
            <option key={c} value={c}>{CHANNEL_LABELS[c]}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : messages.length === 0 ? (
        <p className="text-gray-400 text-sm">No messages yet. Draft one from a person's profile.</p>
      ) : (
        <div className="bg-white border rounded-lg divide-y">
          {messages.map((m) => (
            <div key={m.id} className="px-5 py-4 flex items-start gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Link
                    to={`/people/${m.person_id}`}
                    className="text-sm font-medium text-indigo-600 hover:underline"
                  >
                    Person #{m.person_id}
                  </Link>
                  <span className="text-xs text-gray-400">{CHANNEL_LABELS[m.channel]}</span>
                  <StatusBadge status={m.status} />
                </div>
                {m.subject && (
                  <p className="text-sm text-gray-700 font-medium truncate">{m.subject}</p>
                )}
                <p className="text-xs text-gray-400 truncate">{m.body.slice(0, 120)}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs text-gray-400">
                  {m.sent_at
                    ? `Sent ${new Date(m.sent_at).toLocaleDateString()}`
                    : `Created ${new Date(m.created_at).toLocaleDateString()}`}
                </p>
                {m.parent_message_id && (
                  <p className="text-xs text-gray-400 mt-0.5">follow-up</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
