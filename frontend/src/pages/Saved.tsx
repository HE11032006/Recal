import { useEffect, useState } from "react";
import { api, BACKEND_OFFLINE, type Opportunity } from "../api/client";
import { readCache, writeCache } from "../api/cache";
import { OpportunityCard } from "../components/OpportunityCard";
import { useLanguage } from "../i18n/LanguageContext";

export default function Saved() {
  const { t } = useLanguage();
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState<"score" | "deadline">("score");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cachedAt, setCachedAt] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setCachedAt(null);
    api
      .listOpportunities({ page: 1, page_size: 100 })
      .then((page) => {
        setOpportunities(page.items);
        setSelectedId(page.items[0]?.id ?? null);
        writeCache(page.items);
      })
      .catch((e) => {
        if (e instanceof Error && e.message === BACKEND_OFFLINE) {
          const cached = readCache();
          if (cached.items.length > 0) {
            setOpportunities(cached.items);
            setSelectedId(cached.items[0]?.id ?? null);
            setCachedAt(cached.at);
            return;
          }
          setError(BACKEND_OFFLINE);
          return;
        }
        setError(t.common.requestFailed);
      })
      .finally(() => setLoading(false));
  }, [reloadKey, t]);

  const STATUS_TABS = [
    { id: "all", label: t.saved.tabAll },
    { id: "new", label: t.saved.tabNew },
    { id: "saved", label: t.saved.tabSaved },
    { id: "dismissed", label: t.saved.tabDismissed },
  ];

  const filtered = opportunities
    .filter((o) => (statusFilter === "all" ? true : o.status === statusFilter))
    .sort((a, b) => {
      if (sortBy === "score") return b.relevance_score - a.relevance_score;
      if (!a.deadline) return 1;
      if (!b.deadline) return -1;
      return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
    });

  async function act(id: string, action: "saved" | "dismissed") {
    const previous = opportunities;
    setOpportunities((list) =>
      list.map((o) => (o.id === id ? { ...o, status: action } : o))
    );
    try {
      await api.submitFeedback(id, action);
    } catch {
      setOpportunities(previous);
    }
  }

  return (
    <div className="flex flex-col gap-space-lg">
      <div className="flex flex-wrap items-end justify-between gap-space-md border-b border-outline-variant/30 pb-space-lg">
        <div className="flex flex-col gap-space-xs">
          <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
            {t.saved.kicker}
          </span>
          <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
            {t.saved.title}
          </h1>
        </div>
        <div className="flex items-center gap-space-sm">
          <div className="flex items-center gap-1 rounded border border-outline-variant/40 bg-surface-lowest p-0.5">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`rounded px-space-md py-1 font-mono text-label-sm transition-colors ${
                  statusFilter === tab.id
                    ? "bg-surface-high font-medium text-on-surface"
                    : "text-outline hover:text-on-surface"
                }`}
              >
                {tab.label} (
                {tab.id === "all"
                  ? opportunities.length
                  : opportunities.filter((o) => o.status === tab.id).length}
                )
              </button>
            ))}
          </div>
          <button
            onClick={() => setSortBy(sortBy === "score" ? "deadline" : "score")}
            className="flex items-center gap-1.5 rounded border border-outline-variant/40 bg-surface-container px-space-md py-1.5 text-body-sm text-on-surface transition-colors hover:bg-surface-high"
          >
            <span className="material-symbols-outlined text-[16px] text-outline">swap_vert</span>
            {sortBy === "score" ? t.saved.sortScore : t.saved.sortDeadline}
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex flex-col gap-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="skeleton-shimmer h-24 rounded border border-outline-variant/30"
            />
          ))}
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center gap-space-md rounded border border-outline-variant/30 bg-surface-low py-space-xl text-center">
          <span className="material-symbols-outlined text-[32px] text-outline">bookmark</span>
          <p className="text-body-lg text-on-surface-variant">{t.saved.empty}</p>
        </div>
      )}

      {error && !loading && (
        <div className="animate-fade-in flex flex-col items-center gap-space-md rounded-xl border border-outline-variant bg-surface-low px-space-xl py-space-xl text-center">
          <span className="material-symbols-outlined text-[32px] text-outline">
            {error === BACKEND_OFFLINE ? "cloud_off" : "error"}
          </span>
          <p className="text-body-lg font-medium text-on-surface">
            {error === BACKEND_OFFLINE ? t.common.offlineTitle : t.common.requestFailed}
          </p>
          {error === BACKEND_OFFLINE && (
            <p className="max-w-md font-mono text-label-sm text-outline">{t.common.offlineBody}</p>
          )}
          <button
            onClick={() => setReloadKey((k) => k + 1)}
            className="flex items-center gap-1.5 rounded-lg bg-primary px-space-lg py-2 font-medium text-on-primary transition-all hover:bg-primary-fixed active:scale-95"
          >
            <span className="material-symbols-outlined text-[16px]">refresh</span>
            {t.common.retry}
          </button>
        </div>
      )}

      <div className="flex flex-col gap-space-sm">
        {cachedAt && (
          <div className="animate-fade-in flex flex-wrap items-center justify-between gap-space-sm rounded-xl border border-warning/40 bg-warning/10 px-space-lg py-space-md">
            <div className="flex items-center gap-space-sm">
              <span className="material-symbols-outlined text-[18px] text-warning">cloud_off</span>
              <span className="font-mono text-label-sm font-medium uppercase tracking-wider text-on-surface">
                {t.common.offlineBanner}
              </span>
              <span className="font-mono text-label-sm text-outline">
                {t.common.lastSync} :{" "}
                {new Date(cachedAt).toLocaleString(t.locale, {
                  day: "2-digit",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
            <button
              onClick={() => setReloadKey((k) => k + 1)}
              className="flex items-center gap-1.5 rounded-lg border border-warning/50 px-space-md py-1.5 font-mono text-label-sm text-on-surface transition-all hover:bg-warning/15 active:scale-95"
            >
              <span className="material-symbols-outlined text-[16px]">refresh</span>
              {t.common.retry}
            </button>
          </div>
        )}
        {filtered.map((opportunity, index) => (
          <div
            key={opportunity.id}
            className="animate-rise"
            style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }}
          >
            <OpportunityCard
              opportunity={opportunity}
              selected={opportunity.id === selectedId}
              onSelect={setSelectedId}
              action={
                opportunity.status === "saved"
                  ? { label: t.saved.archive, onClick: () => act(opportunity.id, "dismissed") }
                  : {
                      label: t.saved.save,
                      onClick: () => act(opportunity.id, "saved"),
                      primary: true,
                    }
              }
            />
          </div>
        ))}
      </div>
    </div>
  );
}
