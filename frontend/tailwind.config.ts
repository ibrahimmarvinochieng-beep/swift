import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        swift: {
          "electric-blue": "#007AFF",
          "vibrant-orange": "#FF9500",
          "bird-streak": "#FFF500",
          "sky-start": "#5EDFFF",
          "sky-end": "#00BFFF",
          "dark-slate": "#0A1628",
          surface: "#142338",
          border: "#1E3A5F",
          "text-primary": "#FFFFFF",
          "text-secondary": "#8BA3C7",
        },
      },
      fontFamily: {
        montserrat: ["var(--font-montserrat)", "sans-serif"],
      },
      backgroundImage: {
        "sky-gradient": "linear-gradient(135deg, #5EDFFF 0%, #00BFFF 50%, #FF9500 100%)",
        "sky-gradient-hero": "linear-gradient(180deg, #5EDFFF 0%, #00BFFF 60%, rgba(255,149,0,0.3) 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
