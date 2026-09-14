/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Tokens résolus via variables CSS : `:root` = thème clair (Convex
        // cream paper), `.dark` = thème sombre. Le choix utilisateur commute
        // toute l'interface sans recharger.
        surface: {
          DEFAULT: "rgb(var(--c-surface) / <alpha-value>)",
          dim: "rgb(var(--c-surface-dim) / <alpha-value>)",
          bright: "rgb(var(--c-surface-bright) / <alpha-value>)",
          lowest: "rgb(var(--c-surface-lowest) / <alpha-value>)",
          low: "rgb(var(--c-surface-low) / <alpha-value>)",
          container: "rgb(var(--c-surface-container) / <alpha-value>)",
          high: "rgb(var(--c-surface-high) / <alpha-value>)",
          highest: "rgb(var(--c-surface-highest) / <alpha-value>)",
        },
        "on-surface": {
          DEFAULT: "rgb(var(--c-on-surface) / <alpha-value>)",
          variant: "rgb(var(--c-on-surface-variant) / <alpha-value>)",
        },
        outline: {
          DEFAULT: "rgb(var(--c-outline) / <alpha-value>)",
          variant: "rgb(var(--c-outline-variant) / <alpha-value>)",
        },
        primary: {
          DEFAULT: "rgb(var(--c-primary) / <alpha-value>)",
          container: "rgb(var(--c-primary-container) / <alpha-value>)",
          fixed: "rgb(var(--c-primary-fixed) / <alpha-value>)",
          "fixed-dim": "rgb(var(--c-primary-fixed-dim) / <alpha-value>)",
          vivid: "rgb(var(--c-primary-vivid) / <alpha-value>)",
        },
        "on-primary": {
          DEFAULT: "rgb(var(--c-on-primary) / <alpha-value>)",
          container: "rgb(var(--c-on-primary-container) / <alpha-value>)",
        },
        secondary: {
          DEFAULT: "rgb(var(--c-secondary) / <alpha-value>)",
          container: "rgb(var(--c-secondary-container) / <alpha-value>)",
          fixed: "rgb(var(--c-secondary-fixed) / <alpha-value>)",
          "fixed-dim": "rgb(var(--c-secondary-fixed-dim) / <alpha-value>)",
        },
        "on-secondary": {
          DEFAULT: "rgb(var(--c-on-secondary) / <alpha-value>)",
          container: "rgb(var(--c-on-secondary-container) / <alpha-value>)",
          fixed: "rgb(var(--c-on-secondary-fixed) / <alpha-value>)",
          "fixed-variant": "rgb(var(--c-on-secondary-fixed-variant) / <alpha-value>)",
        },
        tertiary: {
          DEFAULT: "rgb(var(--c-tertiary) / <alpha-value>)",
          container: "rgb(var(--c-tertiary-container) / <alpha-value>)",
        },
        "on-tertiary": {
          DEFAULT: "rgb(var(--c-on-tertiary) / <alpha-value>)",
          container: "rgb(var(--c-on-tertiary-container) / <alpha-value>)",
        },
        error: {
          DEFAULT: "rgb(var(--c-error) / <alpha-value>)",
          container: "rgb(var(--c-error-container) / <alpha-value>)",
        },
        "on-error": "rgb(var(--c-on-error) / <alpha-value>)",
        success: "rgb(var(--c-success) / <alpha-value>)",
        warning: "rgb(var(--c-warning) / <alpha-value>)",
        "inverse-surface": "rgb(var(--c-inverse-surface) / <alpha-value>)",
        "inverse-on-surface": "rgb(var(--c-inverse-on-surface) / <alpha-value>)",
        "inverse-primary": "rgb(var(--c-inverse-primary) / <alpha-value>)",
        background: "rgb(var(--c-background) / <alpha-value>)",
        "on-background": "rgb(var(--c-on-background) / <alpha-value>)",
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
      boxShadow: {
        glow: "0 0 0 rgba(0, 0, 0, 0)",
        "glow-sm": "0 0 0 rgba(0, 0, 0, 0)",
        lift: "0 0 0 rgba(0, 0, 0, 0)",
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
