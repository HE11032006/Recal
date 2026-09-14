import { useSyncExternalStore } from "react";

export type Theme = "light" | "dark";

const STORAGE_KEY = "recal:theme";

export function initialTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
    if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) return "dark";
  } catch {
    /* stockage indisponible : thème clair par défaut */
  }
  return "light";
}

let current: Theme | null = null;
const listeners = new Set<() => void>();

function currentTheme(): Theme {
  if (current === null) {
    current = initialTheme();
    applyTheme(current);
  }
  return current;
}

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark");
  try {
    window.recal?.setTheme?.(theme)?.catch(() => undefined);
  } catch {
    /* hors Electron : rien à synchroniser */
  }
}

export function setTheme(theme: Theme) {
  current = theme;
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    /* stockage indisponible : thème session uniquement */
  }
  applyTheme(theme);
  listeners.forEach((notify) => notify());
}

function subscribe(notify: () => void) {
  listeners.add(notify);
  return () => {
    listeners.delete(notify);
  };
}

export function useTheme(): { theme: Theme; setTheme: (t: Theme) => void } {
  const theme = useSyncExternalStore(subscribe, currentTheme, currentTheme);
  return { theme, setTheme };
}
