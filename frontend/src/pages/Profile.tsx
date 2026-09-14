import { useEffect, useState } from "react";
import { api, type Profile, type WatchState } from "../api/client";

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [watch, setWatch] = useState<WatchState | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.getProfile().then(setProfile).catch(() => null);
    api.getWatchState().then(setWatch).catch(() => null);
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
            className="h-40 animate-pulse rounded border border-outline-variant/30 bg-surface-low"
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
      setMessage("Profil synchronisé.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Erreur de sauvegarde");
    } finally {
      setSaving(false);
    }
  }

  async function runNow() {
    setRunning(true);
    try {
      const run = await api.createRun();
      setMessage(
        `Cycle lancé (${run.id.slice(0, 8)}…) — statut : ${run.status}. ${
          run.opportunities_found > 0 ? `${run.opportunities_found} opportunités trouvées.` : ""
        }`
      );
      await refreshWatch();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Erreur cycle");
    } finally {
      setRunning(false);
    }
  }

  const toggleList = (list: string[], item: string) =>
    list.includes(item) ? list.filter((i) => i !== item) : [...list, item];

  return (
    <div className="flex flex-col gap-space-lg">
      <div className="flex items-end justify-between border-b border-outline-variant/30 pb-space-lg">
        <div className="flex flex-col gap-space-xs">
          <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
            Console de configuration
          </span>
          <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
            Profil & Paramètres de Veille
          </h1>
        </div>
        <div className="flex items-center gap-space-sm">
          <button
            onClick={runNow}
            disabled={running}
            className="flex items-center gap-1.5 rounded border border-outline-variant/40 bg-surface-container px-space-md py-1.5 text-body-sm text-on-surface hover:bg-surface-high disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-[16px] text-primary">
              {running ? "progress_activity" : "play_arrow"}
            </span>
            {running ? "Cycle en cours…" : "Lancer un cycle maintenant"}
          </button>
          <button
            onClick={save}
            disabled={saving}
            className="rounded bg-primary px-space-lg py-1.5 font-medium text-on-primary hover:bg-primary-fixed disabled:opacity-50"
          >
            {saving ? "Sauvegarde…" : "Enregistrer"}
          </button>
        </div>
      </div>

      {message && (
        <div className="rounded border border-primary/40 bg-primary/10 p-space-md text-body-sm text-on-surface">
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
              Langue de l'interface
            </span>
            <div className="grid grid-cols-2 gap-1 rounded border border-outline-variant/40 bg-surface-lowest p-1">
              {(["fr", "en"] as const).map((lang) => (
                <button
                  key={lang}
                  onClick={() => setProfile({ ...profile, language: lang })}
                  className={`rounded py-1.5 font-medium transition-all ${
                    profile.language === lang
                      ? "bg-surface-high text-on-surface shadow-sm"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  {lang === "fr" ? "FR Français" : "EN English"}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-space-xs">
            <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
              Centres d'intérêt
            </span>
            <input
              value={profile.interests.join(", ")}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  interests: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                })
              }
              placeholder="IA, Web, Data…"
              className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface placeholder:text-outline focus:outline-none"
            />
          </div>

          <div className="flex flex-col gap-space-xs">
            <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
              Compétences & stack technique
            </span>
            <input
              value={profile.skills.join(", ")}
              onChange={(e) =>
                setProfile({
                  ...profile,
                  skills: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                })
              }
              placeholder="Python, React, Docker…"
              className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface placeholder:text-outline focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-space-md">
            <div className="flex flex-col gap-space-xs">
              <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                Niveau actuel
              </span>
              <input
                value={profile.study_level}
                onChange={(e) => setProfile({ ...profile, study_level: e.target.value })}
                className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface focus:outline-none"
              />
            </div>
            <div className="flex flex-col gap-space-xs">
              <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                Pays
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
              Configuration des cycles
            </span>
            <button
              onClick={() =>
                setProfile({
                  ...profile,
                  watch: { ...profile.watch, enabled: !profile.watch.enabled },
                })
              }
              className={`flex items-center gap-2 rounded border px-2.5 py-1 font-mono text-label-sm transition-colors ${
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
              {profile.watch.enabled ? "VEILLE ACTIVE" : "VEILLE EN PAUSE"}
            </button>
          </div>

          <div className="flex flex-col gap-space-xs">
            <div className="flex justify-between font-mono text-label-sm">
              <span className="uppercase tracking-wider text-on-surface-variant">
                Fréquence des cycles
              </span>
              <span className="text-on-surface">{profile.watch.frequency_minutes} min</span>
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
                Seuil de pertinence minimal
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
              Types surveillés
            </span>
            <div className="flex flex-wrap gap-1.5">
              {[
                "hackathon",
                "internship",
                "fellowship",
                "scholarship",
                "conference",
                "certification",
              ].map((type) => (
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
                  className={`rounded border px-2.5 py-1 font-mono text-label-sm uppercase transition-colors ${
                    profile.watch.opportunity_types.includes(type)
                      ? "border-primary/60 bg-primary/15 text-primary"
                      : "border-outline-variant/40 bg-surface-lowest text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-space-xs">
            <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
              Domaines autorisés
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
            <p className="font-mono text-label-sm text-outline">
              Un domaine par ligne. Vide = catalogue par défaut de l'agent.
            </p>
          </div>

          <div className="mt-auto flex flex-col gap-2 rounded border border-outline-variant/30 bg-surface-lowest p-space-md font-mono text-label-sm">
            <span className="uppercase tracking-wider text-on-surface-variant">
              État de l'agent
            </span>
            {watch ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-outline">DERNIER CYCLE</span>
                  <span className="text-on-surface">
                    {watch.last_run_at
                      ? new Date(watch.last_run_at).toLocaleString("fr-FR", {
                          day: "2-digit",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "—"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-outline">PROCHAIN CYCLE</span>
                  <span className="text-on-surface">
                    {watch.next_run_at
                      ? new Date(watch.next_run_at).toLocaleString("fr-FR", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "—"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-outline">CYCLES AUJOURD'HUI</span>
                  <span className="text-on-surface">
                    {watch.runs_today} / {watch.daily_max_runs}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-outline">URLS ANALYSÉES</span>
                  <span className="text-on-surface">{watch.processed_urls_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-outline">EXÉCUTION</span>
                  <span className="flex items-center gap-1 text-success">
                    <span className="h-1.5 w-1.5 rounded-full bg-success" />
                    CLOUD — EventBridge
                  </span>
                </div>
              </>
            ) : (
              <span className="text-outline">État indisponible — backend hors ligne ?</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
