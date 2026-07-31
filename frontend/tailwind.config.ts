import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      boxShadow: {
        glow: "0 0 0 1px rgba(255,255,255,0.08), 0 24px 80px rgba(8, 15, 29, 0.45)",
      },
      backgroundImage: {
        "courseiq-grid":
          "radial-gradient(circle at top, rgba(255,255,255,0.12), transparent 40%), linear-gradient(180deg, rgba(7,10,18,0.2), rgba(7,10,18,0.65))",
      },
    },
  },
  plugins: [],
};

export default config;
