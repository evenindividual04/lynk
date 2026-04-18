import type { MessageStatus } from "../types/api";

const COLORS: Record<MessageStatus, string> = {
  draft: "bg-gray-100 text-gray-600",
  queued: "bg-yellow-100 text-yellow-700",
  sent: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-gray-100 text-gray-400",
};

interface Props {
  status: MessageStatus;
}

export default function StatusBadge({ status }: Props) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${COLORS[status]}`}>
      {status}
    </span>
  );
}
