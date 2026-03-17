"use client";

import Link from "next/link";
import { Logo } from "./Logo";

export function AppHeader() {
  return (
    <header className="sticky top-0 z-50 bg-swift-dark-slate/95 backdrop-blur border-b border-swift-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-4">
            <Logo />
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              href="/events"
              className="text-swift-text-secondary hover:text-white transition-colors text-sm font-medium"
            >
              Events
            </Link>
            <Link
              href="/ingest"
              className="text-swift-text-secondary hover:text-white transition-colors text-sm font-medium"
            >
              Ingest
            </Link>
            <Link
              href="/login"
              className="bg-swift-electric-blue hover:bg-swift-electric-blue/90 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors"
            >
              Sign In
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
