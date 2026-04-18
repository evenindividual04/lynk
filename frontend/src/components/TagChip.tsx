interface Props {
  name: string;
  color?: string | null;
  onRemove?: () => void;
}

export default function TagChip({ name, color, onRemove }: Props) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
      style={{ backgroundColor: color ?? "#e0e7ff", color: "#3730a3" }}
    >
      {name}
      {onRemove && (
        <button
          onClick={onRemove}
          className="ml-0.5 hover:text-red-500"
          aria-label={`Remove ${name}`}
        >
          ×
        </button>
      )}
    </span>
  );
}
