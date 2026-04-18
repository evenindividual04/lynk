interface Props {
  page: number;
  pageSize: number;
  total: number;
  onPage: (page: number) => void;
}

export default function Pagination({ page, pageSize, total, onPage }: Props) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center gap-2 text-sm">
      <button
        onClick={() => onPage(page - 1)}
        disabled={page <= 1}
        className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-50"
      >
        ←
      </button>
      <span className="text-gray-600">
        {page} / {totalPages} ({total} total)
      </span>
      <button
        onClick={() => onPage(page + 1)}
        disabled={page >= totalPages}
        className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-50"
      >
        →
      </button>
    </div>
  );
}
