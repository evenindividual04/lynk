import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { Channel, Scenario, TemplateRead } from "../types/api";

const SCENARIO_LABELS: Record<Scenario, string> = {
  ps_outreach: "PS Outreach",
  research_gsoc: "Research/GSoC",
  referral_request: "Referral",
  info_call: "Info Call",
  alumni: "Alumni",
  founder: "Founder",
};

const CHANNEL_LABELS: Record<Channel, string> = {
  li_connection_note: "LI Note",
  li_dm: "LI DM",
  cold_email: "Cold Email",
};

export default function TemplatesList() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<Scenario | "">("");
  const [channelFilter, setChannelFilter] = useState<Channel | "">("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: "",
    scenario: "ps_outreach" as Scenario,
    channel: "cold_email" as Channel,
    subject_template: "",
    body_template: "",
  });

  const { data: templates = [], isLoading } = useQuery<TemplateRead[]>({
    queryKey: ["templates", filter, channelFilter],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filter) params.set("scenario", filter);
      if (channelFilter) params.set("channel", channelFilter);
      return api.get<TemplateRead[]>(`/api/templates?${params}`);
    },
  });

  const createMutation = useMutation({
    mutationFn: () => api.post("/api/templates", form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["templates"] });
      setShowCreate(false);
      setForm({ name: "", scenario: "ps_outreach", channel: "cold_email", subject_template: "", body_template: "" });
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Templates</h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700"
        >
          + New template
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as Scenario | "")}
          className="border rounded px-3 py-1.5 text-sm"
        >
          <option value="">All scenarios</option>
          {(Object.keys(SCENARIO_LABELS) as Scenario[]).map((s) => (
            <option key={s} value={s}>{SCENARIO_LABELS[s]}</option>
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

      {/* Create form */}
      {showCreate && (
        <div className="bg-white border rounded-lg p-5 space-y-3">
          <h2 className="font-medium text-gray-800">New template</h2>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Template name"
            className="w-full border rounded px-3 py-2 text-sm"
          />
          <div className="flex gap-3">
            <select
              value={form.scenario}
              onChange={(e) => setForm({ ...form, scenario: e.target.value as Scenario })}
              className="flex-1 border rounded px-3 py-1.5 text-sm"
            >
              {(Object.keys(SCENARIO_LABELS) as Scenario[]).map((s) => (
                <option key={s} value={s}>{SCENARIO_LABELS[s]}</option>
              ))}
            </select>
            <select
              value={form.channel}
              onChange={(e) => setForm({ ...form, channel: e.target.value as Channel })}
              className="flex-1 border rounded px-3 py-1.5 text-sm"
            >
              {(Object.keys(CHANNEL_LABELS) as Channel[]).map((c) => (
                <option key={c} value={c}>{CHANNEL_LABELS[c]}</option>
              ))}
            </select>
          </div>
          {form.channel === "cold_email" && (
            <input
              type="text"
              value={form.subject_template}
              onChange={(e) => setForm({ ...form, subject_template: e.target.value })}
              placeholder="Subject template (e.g. Interest in {{ company.name }})"
              className="w-full border rounded px-3 py-2 text-sm"
            />
          )}
          <textarea
            value={form.body_template}
            onChange={(e) => setForm({ ...form, body_template: e.target.value })}
            placeholder="Body template — use {{ person.first_name }}, {{ company.name }} etc."
            rows={6}
            className="w-full border rounded px-3 py-2 text-sm resize-none"
          />
          <div className="flex gap-3">
            <button
              onClick={() => createMutation.mutate()}
              disabled={!form.name || !form.body_template || createMutation.isPending}
              className="px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50"
            >
              Create
            </button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-gray-500">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Template list */}
      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : templates.length === 0 ? (
        <p className="text-gray-400 text-sm">
          No templates yet.{" "}
          <button onClick={() => setShowCreate(true)} className="text-indigo-600 hover:underline">
            Create one
          </button>{" "}
          or run <code className="text-xs bg-gray-100 px-1 rounded">uv run python scripts/seed_templates.py</code>.
        </p>
      ) : (
        <div className="space-y-2">
          {templates.map((t) => (
            <Link
              key={t.id}
              to={`/templates/${t.id}`}
              className="block bg-white border rounded-lg px-5 py-4 hover:border-indigo-300 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900 text-sm">{t.name}</span>
                <div className="flex gap-2">
                  <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded">
                    {SCENARIO_LABELS[t.scenario]}
                  </span>
                  <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">
                    {CHANNEL_LABELS[t.channel]}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
