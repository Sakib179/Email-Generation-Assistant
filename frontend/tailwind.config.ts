import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#18212f",
        mist: "#f6f8fb",
        line: "#d8e0ea",
        teal: "#0f766e",
        cobalt: "#2757a6",
        amber: "#b7791f",
        rose: "#be123c"
      },
      boxShadow: {
        panel: "0 14px 40px rgba(24, 33, 47, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;

