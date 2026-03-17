"use client";

import { BirdLogo } from "./BirdLogo";

interface NotificationProps {
  title: string;
  body: string;
  timestamp?: string;
  type?: "event" | "success" | "warning" | "error";
  onClose?: () => void;
}

export function Notification({ title, body, timestamp = "now", type = "event", onClose }: NotificationProps) {
  const accentColors = {
    event: "border-l-swift-vibrant-orange",
    success: "border-l-green-500",
    warning: "border-l-swift-vibrant-orange",
    error: "border-l-red-500",
  };

  return (
    <div
      className={`flex gap-3 p-4 rounded-xl bg-swift-dark-slate border border-swift-border border-l-4 ${accentColors[type]} shadow-lg min-w-[320px] max-w-[400px]`}
    >
      <div className="flex-shrink-0">
        <BirdLogo size="sm" variant="light" showStreak />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <span className="font-bold text-white text-sm">{title}</span>
          <span className="text-swift-text-secondary text-xs flex-shrink-0">{timestamp}</span>
        </div>
        <p className="text-swift-text-secondary text-sm mt-0.5">{body}</p>
        <p className="text-swift-vibrant-orange text-xs font-semibold mt-2">Stay Ahead with Swift.</p>
      </div>
      {onClose && (
        <button onClick={onClose} className="text-swift-text-secondary hover:text-white text-lg leading-none">
          ×
        </button>
      )}
    </div>
  );
}
