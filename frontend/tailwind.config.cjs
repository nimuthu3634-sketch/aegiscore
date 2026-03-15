/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          orange: "#FF7A1A",
          black: "#111111",
          surface: "#1A1A1A",
          muted: "#D9D9D9",
          light: "#F3F3F3",
          white: "#FFFFFF",
        },
      },
      boxShadow: {
        panel: "0 20px 40px -24px rgba(17, 17, 17, 0.35)",
        premium: "0 30px 70px -34px rgba(17, 17, 17, 0.42)",
        soft: "0 14px 28px -22px rgba(17, 17, 17, 0.2)",
        float: "0 18px 36px -26px rgba(255, 122, 26, 0.35)",
      },
      fontFamily: {
        sans: ['"Aptos"', '"Segoe UI"', "sans-serif"],
        mono: ['"JetBrains Mono"', "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
