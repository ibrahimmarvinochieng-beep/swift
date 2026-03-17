import Link from "next/link";
import { Header } from "@/components/Header";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#5EDFFF] via-[#00BFFF] to-[#FF9500]/30 relative overflow-hidden">
      {/* Blurred city skyline effect */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 1200 200%22%3E%3Crect fill=%22%23142338%22 width=%221200%22 height=%22200%22 opacity=%220.3%22/%3E%3Crect x=%220%22 y=%22120%22 width=%2280%22 height=%2280%22 fill=%22%231E3A5F%22/%3E%3Crect x=%22100%22 y=%22100%22 width=%22100%22 height=%22100%22 fill=%22%231E3A5F%22/%3E%3Crect x=%22220%22 y=%22130%22 width=%2260%22 height=%2270%22 fill=%22%231E3A5F%22/%3E%3Crect x=%22300%22 y=%2280%22 width=%22120%22 height=%22120%22 fill=%22%231E3A5F%22/%3E%3Crect x=%22440%22 y=%22140%22 width=%2290%22 height=%2260%22 fill=%22%231E3A5F%22/%3E%3Crect x=%22550%22 y=%2290%22 width=%22100%22 height=%22110%22 fill=%22%231E3A5F%22/%3E%3Crect x=%22670%22 y=%22120%22 width=%2270%22 height=%2280%22 fill=%22%231E3A5F%22/%3E%3Crect x=%22760%22 y=%22100%22 width=%22110%22 height=%22100%22 fill=%22%231E3A5F%22/%3E%3Crect x=%22890%22 y=%22130%22 width=%2280%22 height=%2270%22 fill=%22%231E3A5F%22/%3E%3Crect x=%22990%22 y=%22110%22 width=%2290%22 height=%2290%22 fill=%22%231E3A5F%22/%3E%3C/svg%3E')] bg-no-repeat bg-bottom bg-cover opacity-40" />

      <Header variant="light" />

      <main className="relative z-10 flex flex-col items-center justify-center px-6 py-24 text-center">
        <h1 className="text-5xl md:text-7xl font-bold text-white drop-shadow-lg mb-2">
          Swift
        </h1>
        <p className="text-2xl md:text-3xl font-bold text-[#FF9500] drop-shadow-md mb-8">
          Stay Ahead.
        </p>
        <p className="text-xl text-white/90 max-w-2xl mb-12">
          Event intelligence that keeps you ahead. Real-time alerts, AI classification, and actionable insights.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <Link
            href="/login"
            className="px-8 py-4 rounded-xl bg-white text-swift-dark-slate font-bold text-lg hover:bg-gray-100 transition-colors shadow-lg"
          >
            Start free trial
          </Link>
          <Link
            href="/events"
            className="px-8 py-4 rounded-xl bg-swift-vibrant-orange text-white font-bold text-lg hover:bg-orange-600 transition-colors shadow-lg border-2 border-white/30"
          >
            View demo
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 max-w-4xl">
          <div className="p-6 rounded-2xl bg-white/10 backdrop-blur border border-white/20 text-white">
            <div className="text-3xl mb-2">📡</div>
            <h3 className="font-bold text-lg mb-2">Real-time</h3>
            <p className="text-sm text-white/80">Events as they happen. No delay.</p>
          </div>
          <div className="p-6 rounded-2xl bg-white/10 backdrop-blur border border-white/20 text-white">
            <div className="text-3xl mb-2">🤖</div>
            <h3 className="font-bold text-lg mb-2">AI Classification</h3>
            <p className="text-sm text-white/80">42 categories. Automatic.</p>
          </div>
          <div className="p-6 rounded-2xl bg-white/10 backdrop-blur border border-white/20 text-white">
            <div className="text-3xl mb-2">🔔</div>
            <h3 className="font-bold text-lg mb-2">Alerts</h3>
            <p className="text-sm text-white/80">Telegram, Slack, email.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
