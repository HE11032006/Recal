import { useEffect, useState } from "react";
import { api, type Profile } from "../api/client";
import { useLanguage } from "../i18n/LanguageContext";

export default function ProfilePage() {
  const { t, lang, setLang } = useLanguage();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [watch, setWatch] = useState<import("../api/client").WatchState | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api
      .getProfile()
      .then((p) => {
        setProfile(p);
        if ((p.language === "fr" || p.language === "en") && p.language !== lang) {
          setLang(p.language);
        }
      })
      .catch(() => null);
    api.getWatchState().then(setWatch).catch(() => null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refreshWatch() {
    const state = await api.getWatchState().catch(() => null);
    setWatch(state);
  }

  if (!profile) {
    return (
      <div className="flex flex-col gap-2">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="skeleton-shimmer h-40 rounded border border-outline-variant/30"
          />
        ))}
      </div>
    );
  }

  async function save() {
    if (!profile) return;
    setSaving(true);
    setMessage(null);
    try {
      const updated = await api.updateProfile({
        full_name: profile.full_name,
        language: profile.language,
        interests: profile.interests,
        countries: profile.countries,
        mobility_countries: profile.mobility_countries,
        study_level: profile.study_level,
        skills: profile.skills,
        relevance_threshold: profile.relevance_threshold,
        watch: profile.watch,
      });
      setProfile(updated);
      setMessage(t.profile.savedMsg);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : t.profile.saveErr);
    } finally {
      setSaving(false);
    }
  }

  async function runNow() {
    setRunning(true);
    try {
      const run = await api.createRun();
      setMessage(t.profile.runMsg(run.id, run.status, run.opportunities_found));
      await refreshWatch();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : t.profile.runErr);
    } finally {
      setRunning(false);
    }
  }

  const toggleList = (list: string[], item: string) =>
    list.includes(item) ? list.filter((i) => i !== item) : [...list, item];

  const dateLocale = t.locale;

  return (
    <div className="animate-fade-in flex flex-col gap-space-lg">
      <div className="flex items-end justify-between border-b border-outline-variant/30 pb-space-lg">
        <div className="flex flex-col gap-space-xs">
          <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
            {t.profile.kicker}
          </span>
          <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
            {t.profile.title}
          </h1>
        </div>
        <div className="flex items-center gap-space-sm">
          <button
            onClick={runNow}
            disabled={running}
            className="flex items-center gap-1.5 rounded border border-outline-variant/40 bg-surface-container px-space-md py-1.5 text-body-sm text-on-surface transition-all hover:bg-surface-high active:scale-95 disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-[16px] text-primary">
              {running ? "progress_activity" : "play_arrow"}
            </span>
            {running ? t.profile.running : t.profile.runBtn}
          </button>
          <button
            onClick={save}
            disabled={saving}
            className="rounded bg-primary px-space-lg py-1.5 font-medium text-on-primary transition-all hover:bg-primary-fixed hover:shadow-glow active:scale-95 disabled:opacity-50"
          >
            {saving ? t.profile.saving : t.profile.saveBtn}
          </button>
        </div>
      </div>

      {message && (
        <div className="animate-fade-in rounded border border-primary/40 bg-primary/10 p-space-md text-body-sm text-on-surface">
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 gap-space-lg lg:grid-cols-2">
        <div className="flex flex-col gap-space-lg rounded border border-outline-variant/40 bg-surface-low p-space-xl">
          <div className="flex items-center gap-space-md">
            <div className="flex h-12 w-12 items-center justify-center rounded border border-primary/40 bg-primary/15 font-mono text-lg font-semibold text-primary">
              {(profile.full_name || "R")
                .split(" ")
                .map((w) => w[0])
                .slice(0, 2)
                .join("")
                .toUpperCase()}
            </div>
            <div className="flex flex-col">
              <input
                value={profile.full_name}
                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                className="bg-transparent font-semibold tracking-tight text-on-surface focus:outline-none"
              />
              <span className="font-mono text-label-sm text-outline">ID: {profile.id}</span>
            </div>
          </div>

          <div className="flex flex-col gap-space-xs">
            <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
              {t.profile.langLabel}
            </span>
            <div className="grid grid-cols-2 gap-1 rounded border border-outline-variant/40 bg-surface-lowest p-1">
              {(["fr", "en"] as const).map((l) => (
                <button
                  key={l}
                  onClick={() => {
                    setProfile({ ...profile, language: l });
                    setLang(l);
                  }}
                  className={`rounded py-1.5 font-medium transition-all ${
                    profile.language === l
                      ? "bg-surface-high text-on-surface shadow-sm"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  {l === "fr" ? "FR Français" : "EN English"}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-space-xs">
            <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
              {t.profile.interests}
            </span>
            <input
              value={profile.interests.join(", ")}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  interests: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                })
              }
              placeholder={t.profile.interestsPh}
              className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface placeholder:text-outline focus:outline-none"
            />
          </div>

          <div className="flex flex-col gap-space-xs">
            <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
              {t.profile.skills}
            </span>
            <input
              value={profile.skills.join(", ")}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  skills: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                })
              }
              placeholder={t.profile.skillsPh}
              className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface placeholder:text-outline focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-space-md">
            <div className="flex flex-col gap-space-xs">
              <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                {t.profile.level}
              </span>
              <input
                value={profile.study_level}
                onChange={(e) => setProfile({ ...profile, study_level: e.target.value })}
                className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface focus:outline-none"
              />
            </div>
            <div className="flex flex-col gap-space-xs">
              <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                {t.profile.country}
              </span>
              <input
                value={profile.countries.join(", ")}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    countries: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                  })
                }
                className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface focus:outline-none"
              />
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-space-lg rounded border border-outline-variant/40 bg-surface-low p-space-xl">
          <div className="flex items-center justify-between">
            <span className="font-mono text-label-md uppercase tracking-wider text-on-surface">
              {t.profile.cyclesTitle}
            </span>
            <button
              onClick={() =>
                setProfile({
                  ...profile,
                  watch: { ...profile.watch, enabled: !profile.watch.enabled },
                })
              }
              className={`flex items-center gap-2 rounded border px-2.5 py-1 font-mono text-label-sm transition-all active:scale-95 ${
                profile.watch.enabled
                  ? "border-success/50 bg-success/15 text-success"
                  : "border-outline-variant/40 bg-surface-lowest text-outline"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  profile.watch.enabled ? "bg-success" : "bg-outline"
                }`}
              />
              {profile.watch.enabled ? t.profile.watchOn : t.profile.watchOff}
            </button>
          </div>

          <div className="flex flex-col gap-space-xs">
            <div className="flex justify-between font-mono text-label-sm">
              <span className="uppercase tracking-wider text-on-surface-variant">
                {t.profile.frequency}
              </span>
              <span className="text-on-surface">
                {profile.watch.frequency_minutes} {t.onboarding.minUnit}
              </span>
            </div>
            <input
              type="range"
              min={15}
              max={720}
              step={15}
              value={profile.watch.frequency_minutes}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  watch: {
                    ...profile.watch,
                    frequency_minutes: Number(e.target.value),
                  },
                })
              }
              className="accent-[#bac3ff]"
            />
          </div>

          <div className="flex flex-col gap-space-xs">
            <div className="flex justify-between font-mono text-label-sm">
              <span className="uppercase tracking-wider text-on-surface-variant">
                {t.profile.threshold}
              </span>
              <span className="text-on-surface">{profile.relevance_threshold}</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={profile.relevance_threshold}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  relevance_threshold: Number(e.target.value),
                })
              }
              className="accent-[#bac3ff]"
            />
          </div>

          <div className="flex flex-col gap-space-sm">
            <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
              {t.profile.typesWatched}
            </span>
            <div className="flex flex-wrap gap-1.5">
              {(
                ["hackathon", "internship", "fellowship", "scholarship", "conference", "certification"] as const
              ).map((type) => (
                <button
                  key={type}
                  onClick={() =>
                    setProfile({
                      ...profile,
                      watch: {
                        ...profile.watch,
                        opportunity_types: toggleList(profile.watch.opportunity_types, type),
                      },
                    })
                  }
                  className={`rounded border px-2.5 py-1 font-mono text-label-sm uppercase transition-all active:scale-95 ${
                    profile.watch.opportunity_types.includes(type)
                      ? "border-primary/60 bg-primary/15 text-primary"
                      : "border-outline-variant/40 bg-surface-lowest text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  {t.types[type]}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-space-xs">
            <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
              {t.profile.domains}
            </span>
            <textarea
              value={profile.watch.allowed_domains.join("\n")}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  watch: {
                    ...profile.watch,
                    allowed_domains: e.target.value
                      .split("\n")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  },
                })
              }
              rows={4}
              placeholder={"devpost.com\nmlh.io\nunstop.com"}
              className="rounded border-none bg-surface-lowest p-3 font-mono text-label-sm text-on-surface placeholder:text-outline focus:outline-none"
            />
            <p className="font-mono text-label-sm text-outline">{t.profile.domainsHint}</p>
          </div>

          <div className="mt-auto flex flex-col gap-2 rounded border border-outline-variant/30 bg-surface-lowest p-space-md font-mono text-label-sm">
            <span className="uppercase tracking-wider text-on-surface-variant">
              {t.profile.agentState}
            </span>
            {watch ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-outline">{t.profile.lastRun}</span>
                  <span className="text-on-surface">
                    {watch.last_run_at
                      ? new Date(watch.last_run_at).toLocaleString(dateLocale, {
                          day: "2-digit",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "—"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-outline">{t.profile.nextRun}</span>
                  <span className="text-on-surface">
                    {watch.next_run_at
                      ? new Date(watch.next_run_at).toLocaleString(dateLocale, {
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "—"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-outline">{t.profile.runsToday}</span>
                  <span className="text-on-surface">
                    {watch.runs_today} / {watch.daily_max_runs}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-outline">{t.profile.urlsAnalyzed}</span>
                  <span className="text-on-surface">{watch.processed_urls_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-outline">{t.profile.execution}</span>
                  <span className="flex items-center gap-1 text-success">
                    <span className="h-1.5 w-1.5 rounded-full bg-success" />
                    {t.profile.cloudLabel}
                  </span>
                </div>
              </>
            ) : (
              <span className="text-outline">{t.profile.stateOffline}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
