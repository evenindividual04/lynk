import type { Channel } from "../types/api";

const LI_NOTE_LIMIT = 300;

interface Props {
  channel: Channel;
  subject: string | null;
  body: string;
  onSubjectChange?: (v: string) => void;
  onBodyChange?: (v: string) => void;
  readOnly?: boolean;
}

export default function MessagePreview({
  channel,
  subject,
  body,
  onSubjectChange,
  onBodyChange,
  readOnly = false,
}: Props) {
  const isNote = channel === "li_connection_note";
  const charCount = body.length;
  const overLimit = isNote && charCount > LI_NOTE_LIMIT;

  return (
    <div className="space-y-3">
      {channel === "cold_email" && (
        <div>
          <label className="block text-xs text-gray-500 mb-1">Subject</label>
          <input
            type="text"
            value={subject ?? ""}
            readOnly={readOnly}
            onChange={(e) => onSubjectChange?.(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            placeholder="Email subject…"
          />
        </div>
      )}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="block text-xs text-gray-500">Message</label>
          {isNote && (
            <span className={`text-xs font-mono ${overLimit ? "text-red-600" : "text-gray-400"}`}>
              {charCount}/{LI_NOTE_LIMIT}
            </span>
          )}
        </div>
        <textarea
          value={body}
          readOnly={readOnly}
          onChange={(e) => onBodyChange?.(e.target.value)}
          rows={isNote ? 4 : 10}
          className={`w-full border rounded px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 ${
            overLimit ? "border-red-300 focus:ring-red-400" : "focus:ring-indigo-400"
          }`}
        />
        {overLimit && (
          <p className="text-xs text-red-500 mt-1">
            Over {LI_NOTE_LIMIT} character limit — LinkedIn will truncate this note.
          </p>
        )}
      </div>
    </div>
  );
}
