import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "var(--border)",
        background: "var(--background)",
        surface: "var(--surface)",
        foreground: "var(--foreground)",
        muted: "var(--muted)",
        accent: "var(--accent)",
        accentForeground: "var(--accent-foreground)",
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
      },
      boxShadow: {
        panel: "0 10px 30px rgba(17, 17, 17, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
