"use client";

import { useState } from "react";
import { Header } from "@/components/Header";

export default function IngestPage() {
  const [content, setContent] = useState("");
  const [sourceType, setSourceType] = useState("manual");
  const [sourceName, setSourceName] = useState("");
  const [url, setUrl] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
  };

  return (
    <div className="min-h-screen bg-swift-dark-slate">
      <Header variant="dark" />

      <main className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-white mb-8">Ingest Signal</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-swift-text-secondary mb-2">
              Content *
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste or type signal content..."
              rows={6}
              required
              minLength={20}
              className="w-full px-4 py-3 rounded-lg bg-swift-surface border border-swift-border text-white placeholder-swift-text-secondary focus:border-swift-electric-blue focus:outline-none focus:ring-2 focus:ring-swift-electric-blue/20"
            />
            <p className="text-xs text-swift-text-secondary mt-1">
              {content.length} / 10000 characters (min 20)
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-swift-text-secondary mb-2">
                Source Type *
              </label>
              <select
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-swift-surface border border-swift-border text-white focus:border-swift-electric-blue focus:outline-none"
              >
                <option value="manual">Manual</option>
                <option value="rss">RSS</option>
                <option value="news_api">News API</option>
                <option value="twitter">Twitter</option>
                <option value="social_media">Social Media</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-swift-text-secondary mb-2">
                Source Name
              </label>
              <input
                type="text"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                placeholder="e.g. Reuters"
                className="w-full px-4 py-3 rounded-lg bg-swift-surface border border-swift-border text-white placeholder-swift-text-secondary focus:border-swift-electric-blue focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-swift-text-secondary mb-2">
              URL (optional)
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-4 py-3 rounded-lg bg-swift-surface border border-swift-border text-white placeholder-swift-text-secondary focus:border-swift-electric-blue focus:outline-none"
            />
          </div>

          {submitted && (
            <div className="p-4 rounded-xl bg-green-500/20 border border-green-500/50 text-green-400">
              ✓ Signal ingested. Stay Ahead with Swift.
            </div>
          )}

          <button
            type="submit"
            className="w-full py-4 rounded-xl bg-swift-electric-blue text-white font-bold text-lg hover:bg-blue-600 transition-colors focus:outline-none focus:ring-2 focus:ring-swift-vibrant-orange"
          >
            Submit
          </button>
        </form>
      </main>
    </div>
  );
}
