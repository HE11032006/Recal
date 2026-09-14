/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Palette Stitch — système design Recal
        surface: {
          DEFAULT: "#111317",
          dim: "#111317",
          bright: "#37393d",
          lowest: "#0c0e11",
          low: "#1a1c1f",
          DEFAULT: "#1e2023",
          high: "#282a2d",
          highest: "#333538",
        },
        "on-surface": {
          DEFAULT: "#e2e2e6",
          variant: "#c5c5d8",
        },
        outline: {
          DEFAULT: "#8e8fa1",
          variant: "#444655",
        },
        primary: {
          DEFAULT: "#bac3ff",
          container: "#7287ff",
          fixed: "#dee0ff",
          "fixed-dim": "#bac3ff",
        },
        "on-primary": {
          DEFAULT: "#001f90",
          container: "#001a7f",
        },
        secondary: {
          DEFAULT: "#c0c6d8",
          container: "#424958",
          fixed: "#dce2f5",
          "fixed-dim": "#c0c6d8",
        },
        "on-secondary": {
          DEFAULT: "#29313e",
          container: "#b1b8ca",
          fixed: "#151c29",
          "fixed-variant": "#404755",
        },
        tertiary: {
          DEFAULT: "#ffb68f",
          container: "#e66f1e",
        },
        "on-tertiary": {
          DEFAULT: "#542100",
          container: "#491c00",
        },
        error: {
          DEFAULT: "#ffb4ab",
          container: "#93000a",
        },
        "on-error": "#690005",
        success: "#27c93f",
        warning: "#f7c06d",
        "inverse-surface": "#e2e2e6",
        "inverse-on-surface": "#2f3034",
        "inverse-primary": "#2d4ce2",
        background: "#111317",
        "on-background": "#e2e2e6",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        DEFAULT: "0.125rem",
        lg: "0.25rem",
        xl: "0.5rem",
        full: "0.75rem",
      },
      spacing: {
        gutter: "1rem",
        "space-xs": "0.25rem",
        "space-sm": "0.5rem",
        "space-md": "0.75rem",
        "space-lg": "1rem",
        "space-xl": "1.5rem",
        margin: "1.5rem",
      },
    },
  },
  plugins: [],
};
