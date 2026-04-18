import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { TemplateDetail as TemplateDetailType } from "../types/api";

const PLACEHOLDERS = [
  "{{ person.first_name }}",
  "{{ person.last_name }}",
  "{{ person.full_name }}",
  "{{ person.current_position }}",
  "{{ person.headline }}",
  "{{ person.location }}",
  "{{ company.name }}",
];

export default function TemplateDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [newBody, setNewBody] = useState("");
  const [newSubject, setNewSubject] = useState("");
  const [newNotes, setNewNotes] = useState("");
  const [showAddVersion, setShowAddVersion] = useState(false);

  const { data, isLoading } = useQuery<TemplateDetailType>({
    queryKey: ["template", id],
    queryFn: () => api.get<TemplateDetailType>(`/api/templates/${id}`),
  });

  const addVersionMutation = useMutation({
    mutationFn: () =>
      api.post(`/api/templates/${id}/versions`, {
        body_template: newBody,
        subject_template: newSubject || null,
        notes: newNotes || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["template", id] });
      setNewBody(""); setNewSubject(""); setNewNotes("");
      setShowAddVersion(false);
    },
  });

  const setActiveMutation = useMutation({
    mutationFn: (versionId: number) =>
      api.patch(`/api/templates/${id}`, { active_version_id: versionId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["template", id] }),
  });

  if (isLoading) return <p className="text-gray-400 py-8 text-center">Loading…</p>;
  if (!data) return <p className="text-red-500 py-8 text-center">Template not found.</p>;

  const activeVersion = data.versions.find((v) => v.id === data.active_version_id);

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/templates" className="text-gray-400 hover:text-gray-600 text-sm">
          ← Templates
        </Link>
      </div>

      <div className="bg-white rounded-lg border p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">{data.name}</h1>
            <p className="text-sm text-gray-500 mt-1">
              {data.scenario.replace(/_/g, " ")} · {data.channel.replace(/_/g, " ")}
            </p>
          </div>
          <button
            onClick={() => setShowAddVersion(!showAddVersion)}
            className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50"
          >
            + New version
          </button>
        </div>

        {/* Placeholder reference */}
        <div>
          <p className="text-xs text-gray-500 mb-1 font-medium">Available placeholders</p>
          <div className="flex flex-wrap gap-1.5">
            {PLACEHOLDERS.map((p) => (
              <code key={p} className="text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">
                {p}
              </code>
            ))}
          </div>
        </div>

        {/* Active version */}
        {activeVersion && (
          <div className="bg-indigo-50 rounded-lg p-4 space-y-2">
            <p className="text-xs font-medium text-indigo-600">Active — v{activeVersion.version}</p>
            {activeVersion.subject_template && (
              <p className="text-sm text-gray-700">
                <span className="font-medium">Subject:</span> {activeVersion.subject_template}
              </p>
            )}
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{activeVersion.body_template}</pre>
          </div>
        )}

        {/* Add version form */}
        {showAddVersion && (
          <div className="border rounded-lg p-4 space-y-3">
            <h3 className="text-sm font-medium text-gray-800">Add new version</h3>
            {data.channel === "cold_email" && (
              <input
                type="text"
                value={newSubject}
                onChange={(e) => setNewSubject(e.target.value)}
                placeholder="Subject template"
                className="w-full border rounded px-3 py-2 text-sm"
              />
            )}
            <textarea
              value={newBody}
              onChange={(e) => setNewBody(e.target.value)}
              placeholder="Body template…"
              rows={8}
              className="w-full border rounded px-3 py-2 text-sm resize-none"
            />
            <input
              type="text"
              value={newNotes}
              onChange={(e) => setNewNotes(e.target.value)}
              placeholder="Change notes (optional)"
              className="w-full border rounded px-3 py-2 text-sm"
            />
            <div className="flex gap-3">
              <button
                onClick={() => addVersionMutation.mutate()}
                disabled={!newBody || addVersionMutation.isPending}
                className="px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                Save version
              </button>
              <button onClick={() => setShowAddVersion(false)} className="text-sm text-gray-500">
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Version history */}
        {data.versions.length > 1 && (
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">All versions</p>
            <div className="space-y-2">
              {[...data.versions].reverse().map((v) => (
                <div
                  key={v.id}
                  className={`flex items-center justify-between px-3 py-2 rounded border text-sm ${
                    v.id === data.active_version_id
                      ? "border-indigo-300 bg-indigo-50"
                      : "border-gray-200"
                  }`}
                >
                  <div>
                    <span className="font-medium text-gray-700">v{v.version}</span>
                    {v.notes && <span className="text-gray-400 ml-2 text-xs">{v.notes}</span>}
                  </div>
                  {v.id !== data.active_version_id && (
                    <button
                      onClick={() => setActiveMutation.mutate(v.id)}
                      className="text-xs text-indigo-600 hover:underline"
                    >
                      Set active
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
