import { useEffect, useRef } from "react";
import { api } from "../api/client";

const POLL_INTERVAL_MS = 60_000;

/**
 * Détecte les nouvelles opportunités détectées par l'agent (cloud ou manuel)
 * depuis la dernière visite. Notifie via toast natif et met à jour le badge
 * du tray. Ne déclenche rien au premier chargement (état initial de référence).
 */
export function useNewOpportunities(onNew: (count: number) => void) {
  const lastSeenRef = useRef<string>(
    localStorage.getItem("recal:lastSeen") ?? ""
  );
  const onNewRef = useRef(onNew);
  onNewRef.current = onNew;

  useEffect(() => {
    let cancelled = false;

    const check = async (isFirst: boolean) => {
      try {
        const since = lastSeenRef.current || new Date(0).toISOString();
        const page = await api.listOpportunities({ since, page_size: 50 });
        if (cancelled) return;
        if (page.items.length > 0 && !isFirst) {
          onNewRef.current(page.items.length);
        }
        const now = new Date().toISOString();
        lastSeenRef.current = now;
        localStorage.setItem("recal:lastSeen", now);
      } catch {
        /* backend hors ligne : silencieux, on retentera */
      }
    };

    void check(true);
    const interval = setInterval(() => void check(false), POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);
}
