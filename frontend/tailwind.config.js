/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#A9DDF5",
        surface: "#FFFFFF",
        sidebar: "#DFF3FF",
        card: "rgba(255, 255, 255, 0.75)",
        cardLight: "#F8FAFC", 
        border: "rgba(255, 255, 255, 0.5)",
        primary: {
          light: "#46A6C9",
          DEFAULT: "#2C7DA0",
          dark: "#1B5E7A",
        },
        secondary: "#2C7DA0",
        success: "#059669",
        warning: "#D97706",
        danger: "#DC2626",
        text: {
          muted: "#00000099",
          DEFAULT: "#000000",
          accent: "#2C7DA0",
        }
      },
      boxShadow: {
        'soft': '0 4px 20px -5px rgba(44, 125, 160, 0.08)',
        'card': '0 2px 12px -2px rgba(44, 125, 160, 0.05)',
      },
      fontFamily: {
        sans: ['DM Sans', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      },
      backgroundImage: {
        'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.2))',
      }
    },
  },
  plugins: [],
}
