import Link from "next/link";

interface EventCardProps {
  id: string;
  title: string;
  eventType: string;
  source: string;
  timeAgo: string;
  location?: string;
  severity: number;
  confidence?: number;
}

const severityColors: Record<number, string> = {
  1: "bg-swift-text-secondary",
  2: "bg-blue-400",
  3: "bg-swift-vibrant-orange",
  4: "bg-orange-500",
  5: "bg-red-500",
};

export function EventCard({ id, title, eventType, source, timeAgo, location, severity, confidence }: EventCardProps) {
  return (
    <Link
      href={`/events/${id}`}
      className="block p-4 rounded-xl bg-swift-surface border border-swift-border hover:border-swift-electric-blue transition-colors hover:shadow-lg"
    >
      <div className="flex gap-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold flex-shrink-0 ${severityColors[severity] || severityColors[1]}`}>
          {severity}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-white truncate">{title}</h3>
          <p className="text-swift-text-secondary text-sm mt-0.5">
            {eventType} · {source} · {timeAgo}
          </p>
          {location && <p className="text-swift-text-secondary text-sm">{location}</p>}
          {confidence !== undefined && (
            <p className="text-swift-text-secondary text-xs mt-1">Confidence: {confidence}%</p>
          )}
        </div>
      </div>
    </Link>
  );
}
