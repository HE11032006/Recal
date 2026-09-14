import type { Opportunity, OpportunityType } from "../api/client";
import { useLanguage } from "../i18n/LanguageContext";

export function TypeBadge({ type }: { type: OpportunityType }) {
  const { t } = useLanguage();
  const labels: Record<OpportunityType, string> = {
    hackathon: t.typeBadges.hackathon,
    internship: t.typeBadges.internship,
    fellowship: t.typeBadges.fellowship,
    scholarship: t.typeBadges.scholarship,
    conference: t.typeBadges.conference,
    certification: t.typeBadges.certification,
    other: t.typeBadges.other,
  };
  const tone =
    type === "hackathon"
      ? "text-primary"
      : type === "internship"
        ? "text-secondary-fixed-dim"
        : type === "fellowship"
          ? "text-success"
          : type === "scholarship"
            ? "text-warning"
            : type === "conference"
              ? "text-[#8fd4ff]"
              : type === "certification"
                ? "text-[#d4a8ff]"
                : "text-outline";
  return (
    <span
      className={`border border-outline-variant/50 bg-surface-lowest px-1.5 py-0.5 font-mono text-label-sm font-medium uppercase ${tone}`}
    >
      {labels[type]}
    </span>
  );
}

export function DeadlineBadge({ deadline }: { deadline: string | null }) {
  if (!deadline) {
    return (
      <span className="px-2 py-0.5 font-mono text-label-sm text-outline border border-outline-variant/40 bg-surface-container">
        —
      </span>
    );
  }
  const days = Math.ceil(
    (new Date(deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );
  const label = `J-${days}`;
  const date = new Date(deadline).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "short",
  });
  if (days < 0) {
    return (
      <div className="flex flex-col items-end gap-1">
        <span className="border border-outline-variant/40 bg-surface-container px-2 py-0.5 font-mono text-label-sm font-semibold text-outline line-through">
          {label}
        </span>
        <span className="font-mono text-label-sm text-outline">{date}</span>
      </div>
    );
  }
  if (days <= 7) {
    return (
      <div className="flex flex-col items-end gap-1">
        <span className="border border-[#832626] bg-[#3a1515] px-2 py-0.5 font-mono text-label-sm font-semibold text-[#ff8f8f]">
          {label}
        </span>
        <span className="font-mono text-label-sm text-outline">{date}</span>
      </div>
    );
  }
  if (days <= 30) {
    return (
      <div className="flex flex-col items-end gap-1">
        <span className="border border-[#6b4c19] bg-[#2d2210] px-2 py-0.5 font-mono text-label-sm font-semibold text-[#f7c06d]">
          {label}
        </span>
        <span className="font-mono text-label-sm text-outline">{date}</span>
      </div>
    );
  }
  return (
    <div className="flex flex-col items-end gap-1">
      <span className="border border-outline-variant/50 bg-surface-container px-2 py-0.5 font-mono text-label-sm font-semibold text-on-surface-variant">
        {label}
      </span>
      <span className="font-mono text-label-sm text-outline">{date}</span>
    </div>
  );
}

export function MatchLine({ score }: { score: number }) {
  const { t } = useLanguage();
  const strong = score >= 85;
  const medium = score >= 70;
  return (
    <div className="flex items-center justify-between font-mono text-label-sm">
      <div className={`flex items-center gap-1 ${strong ? "text-success" : medium ? "text-warning" : "text-outline"}`}>
        <span className="material-symbols-outlined text-[14px]">
          {strong ? "verified" : medium ? "check_circle" : "info"}
        </span>
        <span className="font-semibold uppercase">
          {strong ? t.card.matchStrong : medium ? t.card.matchMedium : t.card.matchWeak}
        </span>
      </div>
      <span className="text-outline">{t.card.compatPrefix} {Math.round(score)}%</span>
    </div>
  );
}

export function SegmentedBar({ value }: { value: number }) {
  const filled = Math.round((value / 100) * 10);
  return (
    <div className="flex h-1.5 w-full gap-0.5 bg-surface-lowest">
      {Array.from({ length: 10 }, (_, i) => (
        <div
          key={i}
          className={`h-full flex-1 ${i < filled ? "bg-primary" : "bg-surface-high"}`}
        />
      ))}
    </div>
  );
}

export function OpportunityCard({
  opportunity,
  selected,
  onSelect,
  action,
}: {
  opportunity: Opportunity;
  selected: boolean;
  onSelect: (id: string) => void;
  action?: { label: string; onClick: () => void; primary?: boolean };
}) {
  const { t } = useLanguage();
  return (
    <div
      onClick={() => onSelect(opportunity.id)}
      className={`flex cursor-pointer flex-col rounded-r p-space-lg transition-all duration-200 ease-out hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.995] ${
        selected
          ? "border-y border-r border-l-2 border-l-primary border-outline-variant/60 bg-surface-high shadow-glow-sm"
          : "border border-outline-variant/30 bg-surface-low hover:border-primary/40 hover:bg-surface-container hover:shadow-glow-sm"
      }`}
    >
      <div className="flex items-start justify-between gap-space-md">
        <div className="flex min-w-0 flex-1 flex-col gap-space-xs">
          <div className="flex items-center gap-space-sm">
            <TypeBadge type={opportunity.type} />
            <span className="font-mono text-label-sm text-outline uppercase">
              {opportunity.verified_at
                ? new Date(opportunity.verified_at).toLocaleDateString(t.locale)
                : ""}
            </span>
          </div>
          <h2 className="truncate font-semibold tracking-tight text-on-surface">
            {opportunity.title}
          </h2>
          <div className="flex flex-wrap items-center gap-1.5 text-body-sm text-on-surface-variant">
            {opportunity.organization && (
              <>
                <span className="font-medium text-on-surface">{opportunity.organization}</span>
                <span>·</span>
              </>
            )}
            <span className="truncate">{opportunity.summary.slice(0, 80)}…</span>
          </div>
        </div>
        <DeadlineBadge deadline={opportunity.deadline} />
      </div>
      <div className="mt-space-md flex flex-col gap-space-xs border-t border-outline-variant/30 pt-space-md">
        <MatchLine score={opportunity.relevance_score} />
        <div className="mt-1 flex flex-wrap gap-1.5">
          {opportunity.relevance_reasons.slice(0, 3).map((reason) => (
            <span
              key={reason}
              className="border border-outline-variant/40 bg-surface-low px-1.5 py-0.5 font-mono text-label-sm text-on-surface"
            >
              {reason.slice(0, 30)}
            </span>
          ))}
        </div>
      </div>
      <div className="mt-space-sm flex items-center justify-between">
        <div className="flex items-center gap-space-xs">
          {action && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                action.onClick();
              }}
              className={`rounded border px-2 py-0.5 font-mono text-label-sm transition-colors ${
                action.primary
                  ? "border-primary/50 bg-primary/15 text-primary hover:bg-primary/25"
                  : "border-outline-variant/40 bg-surface-container text-on-surface hover:bg-surface-high"
              }`}
            >
              {action.label}
            </button>
          )}
          <a
            href={opportunity.source_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="rounded border border-outline-variant/40 bg-surface-container px-2 py-0.5 font-mono text-label-sm text-on-surface transition-colors hover:border-primary/50 hover:text-primary"
          title={opportunity.source_url}
        >
          {t.card.openLink}
        </a>
        </div>
        <span className="flex items-center gap-1 font-mono text-label-sm text-primary">
          {t.card.detail}
          <span className="material-symbols-outlined text-[14px]">chevron_right</span>
        </span>
      </div>
    </div>
  );
}
