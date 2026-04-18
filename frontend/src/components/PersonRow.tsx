import { Link } from "react-router-dom";
import type { PersonRead } from "../types/api";

interface Props {
  person: PersonRead;
}

const STAGE_COLORS: Record<string, string> = {
  not_contacted: "bg-gray-100 text-gray-600",
  contacted_li: "bg-blue-100 text-blue-700",
  replied: "bg-green-100 text-green-700",
  offer: "bg-purple-100 text-purple-700",
  rejected: "bg-red-100 text-red-600",
};

export default function PersonRow({ person }: Props) {
  const stageClass =
    STAGE_COLORS[person.stage] ?? "bg-yellow-100 text-yellow-700";

  return (
    <tr className="hover:bg-gray-50 border-b border-gray-100">
      <td className="px-4 py-3">
        <Link
          to={`/people/${person.id}`}
          className="font-medium text-indigo-600 hover:underline"
        >
          {person.full_name}
        </Link>
        {person.headline && (
          <p className="text-xs text-gray-500 truncate max-w-xs">
            {person.headline}
          </p>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {person.current_position_title ?? "—"}
      </td>
      <td className="px-4 py-3">
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full ${stageClass}`}
        >
          {person.stage.replace(/_/g, " ")}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {person.connected_date ?? "—"}
      </td>
      <td className="px-4 py-3 text-xs text-gray-400">
        {person.source.replace(/_/g, " ")}
      </td>
    </tr>
  );
}
