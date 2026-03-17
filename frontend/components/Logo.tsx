export function Logo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="relative w-10 h-10 rounded-lg bg-gradient-to-br from-swift-sky-start to-swift-sky-end flex items-center justify-center">
        <svg
          viewBox="0 0 24 24"
          className="w-6 h-6 text-white drop-shadow-sm"
          fill="currentColor"
        >
          <path d="M12 2C8 2 5 5 5 9c0 4 3 7 7 7s7-3 7-7c0-4-3-7-7-7zm0 2c2.8 0 5 2.2 5 5s-2.2 5-5 5-5-2.2-5-5 2.2-5 5-5zm-4 10c-1.1 0-2 .9-2 2v4c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2v-4c0-1.1-.9-2-2-2H8zm0 2h8v4H8v-4z" />
        </svg>
        <div className="absolute -right-1 -bottom-1 w-3 h-3 rounded-full bg-swift-vibrant-orange" />
      </div>
      <div>
        <span className="font-bold text-white text-lg">Swift</span>
        <span className="block text-swift-vibrant-orange text-xs font-semibold -mt-0.5">
          Stay Ahead.
        </span>
      </div>
    </div>
  );
}
