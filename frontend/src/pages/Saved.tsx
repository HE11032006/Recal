import { useEffect, useState } from "react";
import { api, type Opportunity } from "../api/client";
import { OpportunityCard } from "../components/OpportunityCard";

const STATUS_TABS = [
  { id: "all", label: "Tout" },
  { id: "new", label: "Nouveau" },
  { id: "saved", label: "Sauvé" },
  { id: "dismissed", label: "Passé" },
];

export default function Saved() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState<"score" | "deadline">("score");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listOpportunities({ page: 1, page_size: 100 })
      .then((page) => {
        setOpportunities(page.items);
        setSelectedId(page.items[0]?.id ?? null);
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = opportunities
    .filter((o) => (statusFilter === "all" ? true : o.status === statusFilter))
    .sort((a, b) => {
      if (sortBy === "score") return b.relevance_score - a.relevance_score;
      if (!a.deadline) return 1;
      if (!b.deadline) return -1;
      return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
    });

  async function act(id: string, action: "saved" | "dismissed") {
    await api.submitFeedback(id, action).catch(() => null);
    setOpportunities((list) =>
      list.map((o) => (o.id === id ? { ...o, status: action } : o))
    );
  }

  return (
    <div className="flex flex-col gap-space-lg">
      <div className="flex flex-wrap items-end justify-between gap-space-md border-b border-outline-variant/30 pb-space-lg">
        <div className="flex flex-col gap-space-xs">
          <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
            Registre local
          </span>
          <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
            Opportunités Sauvegardées
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
            {sortBy === "score" ? "Tri : pertinence" : "Tri : deadline"}
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex flex-col gap-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-24 animate-pulse rounded border border-outline-variant/30 bg-surface-low"
            />
          ))}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="flex flex-col items-center gap-space-md rounded border border-outline-variant/30 bg-surface-low py-space-xl text-center">
          <span className="material-symbols-outlined text-[32px] text-outline">bookmark</span>
          <p className="text-body-lg text-on-surface-variant">
            Aucune opportunité dans cette catégorie.
          </p>
        </div>
      )}

      <div className="flex flex-col gap-space-sm">
        {filtered.map((opportunity) => (
          <div key={opportunity.id} className="relative">
            <OpportunityCard
              opportunity={opportunity}
              selected={opportunity.id === selectedId}
              onSelect={setSelectedId}
            />
            <div className="absolute bottom-space-md right-space-lg flex gap-space-xs">
              {opportunity.status === "saved" ? (
                <button
                  onClick={() => act(opportunity.id, "dismissed")}
                  className="rounded border border-outline-variant/40 bg-surface-container px-2 py-1 font-mono text-label-sm text-on-surface hover:bg-surface-high"
                >
                  ARCHIVER
                </button>
              ) : (
                <button
                  onClick={() => act(opportunity.id, "saved")}
                  className="rounded border border-primary/50 bg-primary/15 px-2 py-1 font-mono text-label-sm text-primary hover:bg-primary/25"
                >
                  SAUVER
                </button>
              )}
              <a
                href={opportunity.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded border border-outline-variant/40 bg-surface-container px-2 py-1 font-mono text-label-sm text-on-surface hover:bg-surface-high"
              >
                OUVRIR ↗
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
