/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        rail: "#12131A",
        "rail-hover": "#1B1D27",
        "rail-border": "#23252F",
        "rail-muted": "#8A8FA3",
        canvas: "#F6F7F9",
        surface: "#FFFFFF",
        border: "#E4E6EB",
        ink: "#12131A",
        "ink-muted": "#6C7080",
        "ink-faint": "#9498A6",
        accent: "#5B4FE9",
        "accent-hover": "#4C3FDB",
        "accent-soft": "#EFEDFD",
        success: "#12805C",
        "success-soft": "#E6F6EF",
        warning: "#B15C00",
        "warning-soft": "#FFF3E0",
        danger: "#C1291D",
        "danger-soft": "#FDECEA",
      },
      fontFamily: {
        sans: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16, 18, 26, 0.04)",
        popover: "0 4px 16px rgba(16, 18, 26, 0.10)",
      },
    },
  },
  plugins: [],
}
