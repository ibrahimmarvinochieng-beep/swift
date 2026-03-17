import React from "react";

interface BirdLogoProps {
  size?: "sm" | "md" | "lg";
  variant?: "dark" | "light";
  showStreak?: boolean;
  className?: string;
}

export function BirdLogo({ size = "md", variant = "dark", showStreak = true, className = "" }: BirdLogoProps) {
  const sizes = { sm: "w-6 h-6", md: "w-10 h-10", lg: "w-14 h-14" };
  const color = variant === "dark" ? "#1E3A5F" : "#FFFFFF";
  const streakColor = "#FF9500";

  return (
    <svg
      viewBox="0 0 40 40"
      className={`${sizes[size]} ${className}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Bird body - simplified swift in flight */}
      <path
        d="M8 22C8 22 12 12 20 14C28 16 32 22 32 22C32 22 28 18 20 18C12 18 8 22 8 22Z"
        fill={color}
      />
      <path
        d="M20 14L24 22L20 26L16 22L20 14Z"
        fill={color}
      />
      {/* Wing */}
      <path
        d="M8 22L4 18L2 20L6 24L8 22Z"
        fill={color}
      />
      <path
        d="M32 22L36 18L38 20L34 24L32 22Z"
        fill={color}
      />
      {/* Orange streak */}
      {showStreak && (
        <path
          d="M6 24L2 28L4 30L10 26L6 24Z"
          fill={streakColor}
          opacity={0.9}
        />
      )}
    </svg>
  );
}
