import type { Opportunity } from "./client";

const ITEMS_KEY = "recal:cache:opportunities";
const AT_KEY = "recal:cache:at";
const MAX_CACHED = 50;

export interface CachedFeed {
  items: Opportunity[];
  at: string | null;
}

/** Mémorise le dernier flux réussi pour le mode hors-ligne. */
export function writeCache(items: Opportunity[]): void {
  try {
    localStorage.setItem(ITEMS_KEY, JSON.stringify(items.slice(0, MAX_CACHED)));
    localStorage.setItem(AT_KEY, new Date().toISOString());
  } catch {
    /* stockage plein ou indisponible : pas de cache, pas d'erreur */
  }
}

/** Relit le dernier flux connu (vide si jamais synchronisé). */
export function readCache(): CachedFeed {
  try {
    const raw = localStorage.getItem(ITEMS_KEY);
    const at = localStorage.getItem(AT_KEY);
    if (!raw) return { items: [], at: null };
    const items = JSON.parse(raw) as Opportunity[];
    if (!Array.isArray(items)) return { items: [], at: null };
    return { items, at };
  } catch {
    return { items: [], at: null };
  }
}
