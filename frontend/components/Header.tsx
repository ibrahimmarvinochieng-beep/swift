"use client";

import Link from "next/link";
import { BirdLogo } from "./BirdLogo";

interface HeaderProps {
  variant?: "dark" | "light";
  showNav?: boolean;
}

export function Header({ variant = "dark", showNav = true }: HeaderProps) {
  const isDark = variant === "dark";
  const textColor = isDark ? "text-swift-text-primary" : "text-white";
  const linkHover = isDark ? "hover:text-swift-electric-blue" : "hover:text-swift-bird-streak";

  return (
    <header className={`flex items-center justify-between px-6 py-4 ${isDark ? "bg-swift-dark-slate" : "bg-transparent"}`}>
      <Link href="/" className="flex items-center gap-2">
        <BirdLogo size="md" variant={variant} showStreak />
        <div>
          <span className={`font-bold text-lg ${textColor}`}>Swift</span>
          <span className={`block text-sm font-semibold ${isDark ? "text-swift-vibrant-orange" : "text-swift-bird-streak"}`}>
            Stay Ahead.
          </span>
        </div>
      </Link>

      {showNav && (
        <nav className="flex items-center gap-2">
          <Link href="/events" className={`px-3 py-1.5 rounded text-sm font-medium ${textColor} ${linkHover} transition-colors`}>
            Events
          </Link>
          <Link href="/ingest" className={`px-3 py-1.5 rounded text-sm font-medium ${textColor} ${linkHover} transition-colors`}>
            Ingest
          </Link>
          <Link href="/login" className={`px-4 py-2 rounded-lg text-sm font-bold ${isDark ? "bg-swift-electric-blue text-white hover:bg-blue-600" : "bg-white text-swift-dark-slate hover:bg-gray-100"} transition-colors`}>
            Log in
          </Link>
          <Link href="/login" className={`px-4 py-2 rounded-lg text-sm font-bold ${isDark ? "bg-swift-vibrant-orange text-white hover:bg-orange-600" : "bg-swift-bird-streak text-swift-dark-slate hover:bg-yellow-200"} transition-colors`}>
            Sign up
          </Link>
        </nav>
      )}
    </header>
  );
}
