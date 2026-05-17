/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(217 19% 27%)",
        input: "hsl(217 19% 27%)",
        ring: "hsl(212 95% 68%)",
        background: "hsl(222 47% 7%)",
        foreground: "hsl(210 40% 96%)",
        card: {
          DEFAULT: "hsl(222 47% 11%)",
          foreground: "hsl(210 40% 96%)",
        },
        muted: {
          DEFAULT: "hsl(217 19% 20%)",
          foreground: "hsl(215 20% 65%)",
        },
        primary: {
          DEFAULT: "hsl(212 95% 68%)",
          foreground: "hsl(222 47% 11%)",
        },
        destructive: {
          DEFAULT: "hsl(0 72% 51%)",
          foreground: "hsl(210 40% 98%)",
        },
        success: {
          DEFAULT: "hsl(142 71% 45%)",
          foreground: "hsl(210 40% 98%)",
        },
      },
      borderRadius: {
        lg: "0.5rem",
        md: "0.375rem",
        sm: "0.25rem",
      },
    },
  },
  plugins: [],
};
