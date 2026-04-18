import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { PersonDetail as PersonDetailType, TagRead, NoteRead } from "../types/api";
import TagChip from "../components/TagChip";

const STAGES = [
  "not_contacted", "contacted_li", "contacted_email", "contacted_both",
  "opened", "replied", "call_scheduled", "offer", "rejected", "bounced",
  "cold", "opted_out",
];

export default function PersonDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [newTag, setNewTag] = useState("");
  const [newNote, setNewNote] = useState("");

  const { data, isLoading } = useQuery<PersonDetailType>({
    queryKey: ["person", id],
    queryFn: () => api.get<PersonDetailType>(`/api/people/${id}`),
  });

  const stageMutation = useMutation({
    mutationFn: (stage: string) => api.patch(`/api/people/${id}`, { stage }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["person", id] }),
  });

  const addTagMutation = useMutation({
    mutationFn: (name: string) =>
      api.post<TagRead>(`/api/people/${id}/tags`, { name }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["person", id] });
      setNewTag("");
    },
  });

  const removeTagMutation = useMutation({
    mutationFn: (tagId: number) =>
      api.delete(`/api/people/${id}/tags/${tagId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["person", id] }),
  });

  const addNoteMutation = useMutation({
    mutationFn: (body: string) =>
      api.post<NoteRead>(`/api/people/${id}/notes`, { body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["person", id] });
      setNewNote("");
    },
  });

  if (isLoading) return <p className="text-gray-400 py-12 text-center">Loading…</p>;
  if (!data) return <p className="text-red-500 py-12 text-center">Person not found.</p>;

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/people" className="text-gray-400 hover:text-gray-600 text-sm">
          ← People
        </Link>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">{data.full_name}</h1>
          {data.headline && <p className="text-gray-500 text-sm mt-1">{data.headline}</p>}
          {data.location && <p className="text-gray-400 text-xs">{data.location}</p>}
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-gray-500">LinkedIn</span>
            <a
              href={data.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-indigo-600 hover:underline truncate"
            >
              {data.linkedin_url}
            </a>
          </div>
          {data.email && (
            <div>
              <span className="text-gray-500">Email</span>
              <p className="text-gray-800">{data.email}</p>
            </div>
          )}
          {data.current_position_title && (
            <div>
              <span className="text-gray-500">Position</span>
              <p className="text-gray-800">{data.current_position_title}</p>
            </div>
          )}
          {data.connected_date && (
            <div>
              <span className="text-gray-500">Connected</span>
              <p className="text-gray-800">{data.connected_date}</p>
            </div>
          )}
        </div>

        <div>
          <label className="text-sm text-gray-500 block mb-1">Stage</label>
          <select
            value={data.stage}
            onChange={(e) => stageMutation.mutate(e.target.value)}
            className="border rounded px-3 py-1.5 text-sm"
          >
            {STAGES.map((s) => (
              <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm text-gray-500 block mb-2">Tags</label>
          <div className="flex flex-wrap gap-2 mb-2">
            {data.tags.map((t) => (
              <TagChip
                key={t.id}
                name={t.name}
                color={t.color}
                onRemove={() => removeTagMutation.mutate(t.id)}
              />
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              placeholder="Add tag…"
              className="border rounded px-3 py-1.5 text-sm w-40"
              onKeyDown={(e) => {
                if (e.key === "Enter" && newTag.trim()) {
                  addTagMutation.mutate(newTag.trim());
                }
              }}
            />
            <button
              onClick={() => newTag.trim() && addTagMutation.mutate(newTag.trim())}
              className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700"
            >
              Add
            </button>
          </div>
        </div>

        <div>
          <label className="text-sm text-gray-500 block mb-2">Notes</label>
          <div className="space-y-2 mb-3">
            {data.notes.map((n) => (
              <div key={n.id} className="bg-gray-50 rounded p-3 text-sm text-gray-700">
                <p>{n.body}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(n.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <textarea
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="Add a note…"
              rows={2}
              className="border rounded px-3 py-1.5 text-sm flex-1 resize-none"
            />
            <button
              onClick={() => newNote.trim() && addNoteMutation.mutate(newNote.trim())}
              className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 self-end"
            >
              Add
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
