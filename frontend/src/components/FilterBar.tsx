import { useCallback } from "react";

const STAGES = [
  "not_contacted",
  "contacted_li",
  "contacted_email",
  "opened",
  "replied",
  "call_scheduled",
  "offer",
  "rejected",
  "bounced",
  "cold",
  "opted_out",
];

export interface Filters {
  q: string;
  company: string;
  stage: string;
  tag: string;
  connected_from: string;
  connected_to: string;
  sort: string;
}

interface Props {
  filters: Filters;
  onChange: (filters: Partial<Filters>) => void;
}

export default function FilterBar({ filters, onChange }: Props) {
  const handle = useCallback(
    (key: keyof Filters) =>
      (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
        onChange({ [key]: e.target.value }),
    [onChange],
  );

  return (
    <div
      className="flex flex-wrap gap-3 p-3 bg-white rounded-lg border border-gray-200"
      role="search"
    >
      <input
        type="text"
        placeholder="Search name or email…"
        value={filters.q}
        onChange={handle("q")}
        className="border rounded px-3 py-1.5 text-sm w-52"
        aria-label="Search"
      />
      <input
        type="text"
        placeholder="Company…"
        value={filters.company}
        onChange={handle("company")}
        className="border rounded px-3 py-1.5 text-sm w-40"
        aria-label="Company"
      />
      <select
        value={filters.stage}
        onChange={handle("stage")}
        className="border rounded px-3 py-1.5 text-sm"
        aria-label="Stage"
      >
        <option value="">All stages</option>
        {STAGES.map((s) => (
          <option key={s} value={s}>
            {s.replace(/_/g, " ")}
          </option>
        ))}
      </select>
      <input
        type="text"
        placeholder="Tag…"
        value={filters.tag}
        onChange={handle("tag")}
        className="border rounded px-3 py-1.5 text-sm w-32"
        aria-label="Tag"
      />
      <input
        type="date"
        value={filters.connected_from}
        onChange={handle("connected_from")}
        className="border rounded px-3 py-1.5 text-sm"
        aria-label="Connected from"
      />
      <input
        type="date"
        value={filters.connected_to}
        onChange={handle("connected_to")}
        className="border rounded px-3 py-1.5 text-sm"
        aria-label="Connected to"
      />
      <select
        value={filters.sort}
        onChange={handle("sort")}
        className="border rounded px-3 py-1.5 text-sm"
        aria-label="Sort"
      >
        <option value="created_at">Newest first</option>
        <option value="connected_date">Connected date</option>
        <option value="full_name">Name A–Z</option>
        <option value="priority">Priority</option>
      </select>
    </div>
  );
}
