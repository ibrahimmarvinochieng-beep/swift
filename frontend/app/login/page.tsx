import Link from "next/link";
import { Header } from "@/components/Header";
import { BirdLogo } from "@/components/BirdLogo";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-swift-dark-slate">
      <Header variant="dark" />

      <main className="flex flex-col items-center justify-center px-6 py-16">
        <div className="w-full max-w-md p-8 rounded-2xl bg-swift-surface border border-swift-border">
          <div className="flex flex-col items-center mb-8">
            <BirdLogo size="lg" variant="light" showStreak />
            <h1 className="text-2xl font-bold text-white mt-4">Welcome back</h1>
            <p className="text-swift-text-secondary text-sm">Stay Ahead with Swift.</p>
          </div>

          <form className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-swift-text-secondary mb-2">
                Username or email
              </label>
              <input
                type="text"
                placeholder="Enter your username"
                className="w-full px-4 py-3 rounded-lg bg-swift-dark-slate border border-swift-border text-white placeholder-swift-text-secondary focus:border-swift-electric-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-swift-text-secondary mb-2">
                Password
              </label>
              <input
                type="password"
                placeholder="Enter your password"
                className="w-full px-4 py-3 rounded-lg bg-swift-dark-slate border border-swift-border text-white placeholder-swift-text-secondary focus:border-swift-electric-blue focus:outline-none"
              />
            </div>
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-swift-text-secondary">
                <input type="checkbox" className="rounded" />
                Remember me
              </label>
              <Link href="#" className="text-swift-electric-blue hover:underline">
                Forgot password?
              </Link>
            </div>
            <button
              type="submit"
              className="w-full py-4 rounded-xl bg-swift-electric-blue text-white font-bold hover:bg-blue-600 transition-colors"
            >
              Log in
            </button>
          </form>

          <p className="mt-6 text-center text-swift-text-secondary text-sm">
            Don&apos;t have an account?{" "}
            <Link href="#" className="text-swift-vibrant-orange font-semibold hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
