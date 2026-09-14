import { useEffect, useMemo, useState } from "react";
import { api, type Opportunity } from "../api/client";
import { OpportunityCard, SegmentedBar, TypeBadge } from "../components/OpportunityCard";

export default function Today() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [selected, setSelected] = useState<Opportunity | null>(null);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listOpportunities({ page: 1, page_size: 50 })
      .then((page) => setOpportunities(page.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Erreur API"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    if (filter === "all") return opportunities;
    return opportunities.filter((o) => o.type === filter);
  }, [opportunities, filter]);

  async function act(id: string, action: "saved" | "dismissed") {
    await api.submitFeedback(id, action).catch(() => null);
    setOpportunities((list) =>
      list.map((o) => (o.id === id ? { ...o, status: action } : o))
    );
    setSelected((current) => (current && current.id === id ? { ...current, status: action } : current));
  }

  const tabs = [
    { id: "all", label: `Tous (${opportunities.length})` },
    { id: "hackathon", label: "Hackathons" },
    { id: "internship", label: "Stages" },
    { id: "fellowship", label: "Fellowships" },
    { id: "scholarship", label: "Bourses" },
    { id: "conference", label: "Conférences" },
    { id: "certification", label: "Certifs" },
  ];

  return (
    <div className="flex flex-col gap-space-lg">
      <div className="flex flex-wrap items-end justify-between gap-space-md border-b border-outline-variant/30 pb-space-lg">
        <div className="flex flex-col gap-space-xs">
          <div className="flex items-center gap-space-sm">
            <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
              Flux de veille prioritaire
            </span>
            <span className="text-outline-variant">/</span>
            <span className="font-mono text-label-sm text-primary">
              {new Date().toLocaleDateString("fr-FR", {
                weekday: "long",
                day: "numeric",
                month: "long",
              })}
            </span>
          </div>
          <div className="flex items-center gap-space-md">
            <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
              Aujourd'hui
            </h1>
            {opportunities.length > 0 && (
              <div className="flex items-center gap-1.5 rounded border border-outline-variant/40 bg-surface-high px-2 py-0.5">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
                <span className="font-mono text-label-sm font-medium text-on-surface">
                  {opportunities.filter((o) => o.status === "new").length} nouvelles
                </span>
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-space-sm rounded border border-outline-variant/40 bg-surface-lowest p-0.5">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              className={`rounded px-space-md py-1 font-mono text-label-sm transition-colors ${
                filter === tab.id
                  ? "border border-outline-variant/40 bg-surface-high font-medium text-on-surface"
                  : "text-outline hover:text-on-surface"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="grid grid-cols-1 gap-space-md lg:grid-cols-2">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-40 animate-pulse rounded border border-outline-variant/30 bg-surface-low"
            />
          ))}
        </div>
      )}

      {error && !loading && (
        <div className="rounded border border-error/40 bg-error-container/20 p-space-lg text-body-md text-error">
          {error} — vérifie que le backend tourne (uvicorn port 8787).
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center gap-space-md rounded border border-outline-variant/30 bg-surface-low py-space-xl text-center">
          <span className="material-symbols-outlined text-[32px] text-outline">radar</span>
          <p className="text-body-lg text-on-surface-variant">
            Rien de nouveau pour l'instant.
          </p>
          <p className="font-mono text-label-sm text-outline">
            Ton agent continue d'analyser — prochain cycle planifié.
          </p>
        </div>
      )}

      {!error && filtered.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-space-md lg:grid-cols-2">
            {filtered.map((opportunity) => (
              <OpportunityCard
                key={opportunity.id}
                opportunity={opportunity}
                selected={false}
                onSelect={() => setSelected(opportunity)}
              />
            ))}
          </div>
          <div className="flex items-center justify-between rounded border border-outline-variant/30 bg-surface-lowest p-space-md font-mono text-label-sm text-outline">
            <div className="flex items-center gap-space-sm">
              <span className="h-2 w-2 rounded-full bg-primary/50" />
              <span>
                Cycle automatique actif —{" "}
                <span className="font-medium text-on-surface">cloud</span>
              </span>
            </div>
            <span>{opportunities.length} SOURCES FILTRÉES</span>
          </div>
        </>
      )}

      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-8"
          onClick={() => setSelected(null)}
        >
          <div
            className="flex max-h-[85vh] w-full max-w-3xl flex-col overflow-hidden rounded border border-outline-variant/50 bg-surface-low shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-outline-variant/30 bg-surface-lowest px-space-lg py-space-md">
              <div className="flex items-center gap-space-sm">
                <span className="h-2 w-2 rounded-full bg-success" />
                <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                  Analyse de l'agent
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => act(selected.id, "saved")}
                  className="flex items-center gap-1 rounded border border-outline-variant/40 bg-surface-container px-2 py-1 font-mono text-label-sm text-on-surface transition-colors hover:bg-surface-high"
                >
                  <span className="material-symbols-outlined text-[15px]">bookmark</span>
                  Sauver
                </button>
                <button
                  onClick={() => setSelected(null)}
                  className="rounded p-1 text-outline transition-colors hover:bg-surface-container hover:text-on-surface"
                  title="Fermer"
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>
            </div>

            <div className="flex flex-col gap-space-xl overflow-y-auto p-space-xl">
              <div className="flex flex-col gap-space-xs">
                <div className="flex items-center gap-2">
                  <TypeBadge type={selected.type} />
                </div>
                <h3 className="text-xl font-semibold tracking-tight text-on-surface">
                  {selected.title}
                </h3>
                {selected.organization && (
                  <p className="text-body-md text-outline">
                    Organisé par{" "}
                    <strong className="font-medium text-on-surface">
                      {selected.organization}
                    </strong>
                  </p>
                )}
              </div>

              <div className="grid grid-cols-3 gap-space-xs rounded border border-outline-variant/30 bg-surface-lowest p-space-sm">
                <div className="flex flex-col rounded bg-surface-low p-2">
                  <span className="font-mono text-label-sm uppercase text-outline">Type</span>
                  <span className="mt-0.5 font-medium text-on-surface">{selected.type}</span>
                </div>
                <div className="flex flex-col rounded bg-surface-low p-2">
                  <span className="font-mono text-label-sm uppercase text-outline">Score</span>
                  <span className="mt-0.5 font-medium text-on-surface">
                    {Math.round(selected.relevance_score)}%
                  </span>
                </div>
                <div className="flex flex-col rounded bg-surface-low p-2">
                  <span className="font-mono text-label-sm uppercase text-[#ff8f8f]">
                    Deadline
                  </span>
                  <span className="mt-0.5 font-semibold text-[#ff8f8f]">
                    {selected.deadline
                      ? new Date(selected.deadline).toLocaleDateString("fr-FR")
                      : "—"}
                  </span>
                </div>
              </div>

              <div className="flex flex-col gap-space-xs">
                <h4 className="flex items-center gap-1.5 font-mono text-label-md uppercase tracking-wider text-on-surface">
                  <span className="h-1.5 w-1.5 bg-primary" />
                  Résumé de l'opportunité
                </h4>
                <p className="text-justify leading-relaxed text-body-md text-on-surface-variant">
                  {selected.summary}
                </p>
              </div>

              {Object.keys(selected.eligibility).length > 0 && (
                <div className="flex flex-col gap-space-sm">
                  <h4 className="flex items-center gap-1.5 font-mono text-label-md uppercase tracking-wider text-on-surface">
                    <span className="h-1.5 w-1.5 bg-primary" />
                    Critères d'éligibilité
                  </h4>
                  <div className="flex flex-col gap-2 rounded border border-outline-variant/30 bg-surface-lowest p-space-md">
                    {Object.entries(selected.eligibility).map(([key, value]) => (
                      <div
                        key={key}
                        className="flex items-start gap-space-sm text-body-sm text-on-surface"
                      >
                        <span className="material-symbols-outlined mt-0.5 text-[16px] text-success">
                          check_box
                        </span>
                        <div className="flex-1">
                          <span className="font-medium capitalize">{key} :</span>{" "}
                          {String(value)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex flex-col gap-space-md rounded border border-outline-variant/40 bg-surface-container p-space-lg">
                <div className="flex items-center justify-between border-b border-outline-variant/30 pb-space-sm">
                  <div className="flex items-center gap-space-xs">
                    <span className="material-symbols-outlined text-[18px] text-primary">
                      psychology
                    </span>
                    <span className="font-mono text-label-md font-semibold uppercase text-on-surface">
                      Analyse de pertinence
                    </span>
                  </div>
                  <span className="font-mono text-label-sm text-success">
                    CONFIANCE {Math.round(selected.confidence_score)}%
                  </span>
                </div>
                <div className="flex flex-col gap-space-md">
                  <div className="flex flex-col gap-1">
                    <div className="flex justify-between font-mono text-label-sm">
                      <span className="text-on-surface-variant">
                        Score global de compatibilité
                      </span>
                      <span className="font-semibold text-on-surface">
                        {Math.round(selected.relevance_score)}%
                      </span>
                    </div>
                    <SegmentedBar value={selected.relevance_score} />
                  </div>
                  <div className="flex flex-col gap-1">
                    <div className="flex justify-between font-mono text-label-sm">
                      <span className="text-on-surface-variant">Confiance de l'analyse</span>
                      <span className="font-semibold text-on-surface">
                        {Math.round(selected.confidence_score)}%
                      </span>
                    </div>
                    <SegmentedBar value={selected.confidence_score} />
                  </div>
                </div>
                {selected.relevance_reasons.length > 0 && (
                  <div className="rounded-r border-l-2 border-l-primary bg-surface-lowest/80 p-space-md">
                    <span className="mb-1 block font-mono text-label-sm uppercase text-primary">
                      Avis d'adéquation :
                    </span>
                    <ul className="flex list-disc flex-col gap-1 pl-4 text-body-sm leading-normal text-on-surface">
                      {selected.relevance_reasons.map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between gap-space-sm border-t border-outline-variant/30 bg-surface-lowest p-space-lg">
              <a
                href={selected.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-1 items-center justify-center gap-2 rounded bg-primary px-space-lg py-2 font-medium text-on-primary shadow-sm transition-colors hover:bg-primary-fixed"
              >
                Ouvrir le site officiel
                <span className="material-symbols-outlined text-[16px]">open_in_new</span>
              </a>
              <button
                onClick={() => act(selected.id, "saved")}
                className="flex items-center gap-1.5 rounded border border-outline-variant/40 bg-surface-container px-space-md py-2 text-on-surface transition-colors hover:bg-surface-high"
              >
                <span className="material-symbols-outlined text-[18px]">bookmark</span>
                Sauvegarder
              </button>
              <button
                onClick={() => {
                  act(selected.id, "dismissed");
                  setSelected(null);
                }}
                className="rounded border border-outline-variant/30 px-space-md py-2 text-outline transition-colors hover:border-error/40 hover:bg-error-container/20 hover:text-error"
              >
                Passer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
