import { Header } from "@/components/Header";
import { EventCard } from "@/components/EventCard";
import { Notification } from "@/components/Notification";

const SAMPLE_EVENTS = [
  { id: "1", title: "Earthquake strikes central Chile", eventType: "POLITICS", source: "Reuters", timeAgo: "12 min ago", location: "Santiago, Chile", severity: 4, confidence: 87 },
  { id: "2", title: "Market volatility ahead as Fed signals rate decision", eventType: "BUSINESS", source: "Bloomberg", timeAgo: "28 min ago", location: "New York, USA", severity: 3, confidence: 92 },
  { id: "3", title: "Major tech conference announces AI keynote speakers", eventType: "TECH", source: "TechCrunch", timeAgo: "1 hr ago", location: "San Francisco", severity: 2, confidence: 78 },
  { id: "4", title: "Tropical storm approaches coastal region", eventType: "ENVIRONMENT", source: "Weather API", timeAgo: "2 hrs ago", location: "Miami, FL", severity: 5, confidence: 95 },
  { id: "5", title: "Healthcare reform bill passes committee vote", eventType: "POLITICS", source: "AP News", timeAgo: "3 hrs ago", severity: 2, confidence: 88 },
];

export default function EventsPage() {
  return (
    <div className="min-h-screen bg-swift-dark-slate">
      <Header variant="dark" />

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Sample notification */}
        <div className="fixed top-20 right-6 z-50">
          <Notification
            title="Breaking News"
            body="Market volatility ahead. 3 new high-severity events in your feed."
            timestamp="now"
            type="event"
          />
        </div>

        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold text-white">Event Feed</h1>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Search events..."
              className="px-4 py-2 rounded-lg bg-swift-surface border border-swift-border text-white placeholder-swift-text-secondary focus:border-swift-electric-blue focus:outline-none"
            />
            <select className="px-4 py-2 rounded-lg bg-swift-surface border border-swift-border text-white focus:border-swift-electric-blue focus:outline-none">
              <option>All types</option>
              <option>Politics</option>
              <option>Business</option>
              <option>Tech</option>
            </select>
            <select className="px-4 py-2 rounded-lg bg-swift-surface border border-swift-border text-white focus:border-swift-electric-blue focus:outline-none">
              <option>All severity</option>
              <option>Critical (5)</option>
              <option>High (4+)</option>
              <option>Elevated (3+)</option>
            </select>
          </div>
        </div>

        <div className="space-y-4">
          {SAMPLE_EVENTS.map((event) => (
            <EventCard key={event.id} {...event} />
          ))}
        </div>
      </main>
    </div>
  );
}
