/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080e1a",
        sidebar: "#060b14",
        card: "#0d1829",
        border: "#1a2e4a",
        primary: {
          light: "#60a5fa",
          DEFAULT: "#2563eb",
          dark: "#1d4ed8",
        },
        secondary: "#7c3aed",
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444",
        text: {
          muted: "#4d7aaa",
          DEFAULT: "#e8f0fa",
          accent: "#c8d6e8",
        }
      },
      fontFamily: {
        sans: ['DM Sans', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      },
      backgroundImage: {
        'glass-gradient': 'linear-gradient(135deg, rgba(13, 24, 41, 0.8), rgba(15, 30, 51, 0.6))',
      }
    },
  },
  plugins: [],
}
