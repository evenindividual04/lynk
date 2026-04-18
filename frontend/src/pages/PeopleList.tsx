import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { PeopleListResponse } from "../types/api";
import FilterBar, { type Filters } from "../components/FilterBar";
import PersonRow from "../components/PersonRow";
import Pagination from "../components/Pagination";

const DEFAULT_FILTERS: Filters = {
  q: "",
  company: "",
  stage: "",
  tag: "",
  connected_from: "",
  connected_to: "",
  sort: "created_at",
};

function buildQuery(filters: Filters, page: number, pageSize: number): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.company) params.set("company", filters.company);
  if (filters.stage) params.set("stage", filters.stage);
  if (filters.tag) params.set("tag", filters.tag);
  if (filters.connected_from) params.set("connected_from", filters.connected_from);
  if (filters.connected_to) params.set("connected_to", filters.connected_to);
  if (filters.sort) params.set("sort", filters.sort);
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  return params.toString();
}

export default function PeopleList() {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const handleFilterChange = useCallback((updates: Partial<Filters>) => {
    setFilters((prev) => ({ ...prev, ...updates }));
    setPage(1);
  }, []);

  const queryString = buildQuery(filters, page, pageSize);

  const { data, isLoading, isError } = useQuery<PeopleListResponse>({
    queryKey: ["people", queryString],
    queryFn: () => api.get<PeopleListResponse>(`/api/people?${queryString}`),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">People</h1>
        {data && (
          <span className="text-sm text-gray-500">{data.total} total</span>
        )}
      </div>

      <FilterBar filters={filters} onChange={handleFilterChange} />

      {isLoading && (
        <p className="text-center text-gray-400 py-12">Loading…</p>
      )}
      {isError && (
        <p className="text-center text-red-500 py-12">Failed to load people.</p>
      )}

      {data && (
        <>
          {data.items.length === 0 ? (
            <div className="text-center py-20 text-gray-400">
              <p className="text-4xl mb-3">🔍</p>
              <p className="text-lg">No people found.</p>
              <p className="text-sm mt-1">
                Try importing your LinkedIn connections or adjusting filters.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    <th className="px-4 py-3">Name</th>
                    <th className="px-4 py-3">Position</th>
                    <th className="px-4 py-3">Stage</th>
                    <th className="px-4 py-3">Connected</th>
                    <th className="px-4 py-3">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((p) => (
                    <PersonRow key={p.id} person={p} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <Pagination
            page={page}
            pageSize={pageSize}
            total={data.total}
            onPage={setPage}
          />
        </>
      )}
    </div>
  );
}
