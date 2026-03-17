import Link from "next/link";
import { Header } from "@/components/Header";

export default function EventDetailPage({ params }: { params: { id: string } }) {
  const event = {
    id: params.id,
    title: "Earthquake strikes central Chile",
    eventType: "POLITICS",
    description: "A magnitude 6.2 earthquake struck central Chile near Santiago, causing widespread power outages and structural damage. Emergency services are responding. No casualties reported yet.",
    source: "Reuters",
    timeAgo: "12 min ago",
    location: "Santiago, Chile",
    severity: 4,
    confidence: 87,
    sources: ["Reuters", "AP News"],
  };

  return (
    <div className="min-h-screen bg-swift-dark-slate">
      <Header variant="dark" />

      <main className="max-w-3xl mx-auto px-6 py-8">
        <Link href="/events" className="text-swift-electric-blue hover:underline text-sm mb-6 inline-block">
          ← Back to Events
        </Link>

        <div className="p-6 rounded-xl bg-swift-surface border border-swift-border">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-swift-vibrant-orange flex items-center justify-center text-white text-xl font-bold flex-shrink-0">
              {event.severity}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{event.title}</h1>
              <p className="text-swift-text-secondary mt-2">
                {event.eventType} · {event.source} · {event.timeAgo}
              </p>
              {event.location && (
                <p className="text-swift-text-secondary mt-1">📍 {event.location}</p>
              )}
            </div>
          </div>

          <p className="mt-6 text-white leading-relaxed">{event.description}</p>

          <div className="mt-6 flex flex-wrap gap-2">
            {event.sources.map((s) => (
              <span key={s} className="px-3 py-1 rounded-lg bg-swift-border text-swift-text-secondary text-sm">
                {s}
              </span>
            ))}
          </div>

          <div className="mt-8 flex gap-3">
            <button className="px-4 py-2 rounded-lg bg-swift-electric-blue text-white font-medium hover:bg-blue-600 transition-colors">
              Share
            </button>
            <button className="px-4 py-2 rounded-lg bg-swift-vibrant-orange text-white font-medium hover:bg-orange-600 transition-colors">
              Create alert rule
            </button>
            <button className="px-4 py-2 rounded-lg border border-swift-border text-swift-text-secondary hover:text-white transition-colors">
              Export
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
