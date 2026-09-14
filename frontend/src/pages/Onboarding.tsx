import { useState, type CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Profile } from "../api/client";

const INTERESTS = [
  "IA",
  "Web",
  "Data",
  "Mobile",
  "Cybersécurité",
  "Cloud",
  "DevOps",
  "Design",
  "Blockchain",
  "Robotique",
];

const STUDY_LEVELS = ["Licence 1", "Licence 2", "Licence 3", "Master 1", "Master 2", "PhD"];

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [language, setLanguage] = useState<"fr" | "en">("fr");
  const [fullName, setFullName] = useState("");
  const [interests, setInterests] = useState<string[]>([]);
  const [studyLevel, setStudyLevel] = useState("");
  const [country, setCountry] = useState("");
  const [frequency, setFrequency] = useState(60);
  const [types, setTypes] = useState<string[]>([
    "hackathon",
    "internship",
    "fellowship",
    "scholarship",
    "conference",
    "certification",
  ]);
  const [launching, setLaunching] = useState(false);
  const [launchStep, setLaunchStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const toggle = (list: string[], item: string, setter: (v: string[]) => void) => {
    setter(list.includes(item) ? list.filter((i) => i !== item) : [...list, item]);
  };

  async function launch() {
    // Flag posé immédiatement : un rechargement pendant l'analyse ne
    // renvoie jamais l'utilisateur à la case départ.
    localStorage.setItem("recal:onboarded", "true");
    setLaunching(true);
    setError(null);
    try {
      await api.updateProfile({
        full_name: fullName,
        language,
        interests: interests.length ? interests : ["tech"],
        countries: country ? [country] : [],
        study_level: studyLevel,
        watch: {
          enabled: true,
          frequency_minutes: frequency,
          allowed_domains: [],
          opportunity_types: types,
          max_queries_per_run: 3,
          max_results_per_query: 5,
          minimum_relevance_score: null,
          daily_max_runs: 12,
        },
      } as Partial<Profile>);
      setLaunchStep(1);
      await new Promise((r) => setTimeout(r, 800));
      setLaunchStep(2);
      // Cycle lancé avec timeout : ne bloque pas l'onboarding si l'analyse
      // prend plusieurs minutes (Parallel + Claude réels = 1-3 min).
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 60000);
      try {
        await api.createRun(controller.signal);
      } catch (e) {
        // 409 = cycle déjà en cours ou quota : le cloud prend le relai.
        setError(
          e instanceof Error && e.message.includes("Cycle ignoré")
            ? `${e.message} — le cycle cloud planifié prend le relai.`
            : "L'analyse continue en arrière-plan (cloud) — l'agent a déjà été configuré."
        );
      } finally {
        clearTimeout(timeout);
      }
      setLaunchStep(3);
      await new Promise((r) => setTimeout(r, 1200));
      setLaunchStep(4);
      await new Promise((r) => setTimeout(r, 700));
      navigate("/", { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
      setLaunching(false);
    }
  }

  if (launching) {
    const steps = [
      "Initialisation de l'agent…",
      "Recherche sur le web en cours…",
      "Analyse des opportunités avec Claude…",
      "Calcul des scores de pertinence…",
      "Premier flux compilé !",
    ];
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-surface px-6 pt-9">
        <div
          className="fixed left-0 right-0 top-0 h-9 border-b border-outline-variant/30 bg-surface"
          style={{ WebkitAppRegion: "drag" } as CSSProperties}
        />
        <div className="flex flex-col gap-space-lg w-full max-w-md">
          <div className="flex items-center gap-space-sm">
            <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
            <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
              Compilation du premier flux
            </span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
            L'agent Recal se met au travail.
          </h1>
          <div className="flex flex-col gap-space-md">
            {steps.map((label, i) => (
              <div key={label} className="flex items-center gap-space-sm">
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded border ${
                    i < launchStep
                      ? "border-success/50 bg-success/15 text-success"
                      : i === launchStep
                        ? "border-primary/60 bg-primary/10 text-primary animate-pulse"
                        : "border-outline-variant/40 text-outline"
                  }`}
                >
                  <span className="material-symbols-outlined text-[13px]">
                    {i < launchStep ? "check" : i === launchStep ? "progress_activity" : "radio_button_unchecked"}
                  </span>
                </span>
                <span
                  className={`text-body-md ${
                    i <= launchStep ? "text-on-surface" : "text-outline"
                  }`}
                >
                  {label}
                </span>
              </div>
            ))}
          </div>
          {error && (
            <div className="border border-error/40 bg-error-container/30 rounded p-space-md text-body-sm text-error">
              {error} — le cycle cloud prendra le relai.
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface pt-9">
      <div
        className="fixed left-0 right-0 top-0 h-9 border-b border-outline-variant/30 bg-surface"
        style={{ WebkitAppRegion: "drag" } as CSSProperties}
      />
      <div className="h-1 w-full bg-surface-lowest">
        <div
          className="h-full bg-primary transition-all duration-500"
          style={{ width: `${(step / 4) * 100}%` }}
        />
      </div>
      <div className="mx-auto flex w-full max-w-xl flex-1 flex-col justify-center px-6 py-space-xl">
        {step === 1 && (
          <div className="flex flex-col gap-space-lg">
            <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
              Étape 1 sur 4 · Bienvenue
            </span>
            <h1 className="text-3xl font-semibold tracking-tight text-on-surface">
              Ton agent de veille personnel.
            </h1>
            <p className="text-body-lg leading-relaxed text-on-surface-variant">
              Recal scrute le web, filtre les opportunités étudiantes (hackathons, bourses,
              fellowships, stages) et élimine le bruit grâce à Claude.
            </p>
            <div className="flex flex-col gap-space-xs">
              <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                Langue
              </span>
              <div className="grid grid-cols-2 gap-1 rounded border border-outline-variant/40 bg-surface-lowest p-1">
                {(["fr", "en"] as const).map((lang) => (
                  <button
                    key={lang}
                    type="button"
                    onClick={() => setLanguage(lang)}
                    className={`flex items-center justify-center gap-2 rounded py-1.5 font-medium transition-all ${
                      language === lang
                        ? "bg-surface-high text-on-surface shadow-sm"
                        : "text-on-surface-variant hover:text-on-surface"
                    }`}
                  >
                    {language === lang && <span className="h-1.5 w-1.5 rounded-full bg-primary" />}
                    {lang === "fr" ? "FR Français" : "EN English"}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-space-xs">
              <span className="flex items-center justify-between font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                Identité
                <span className="text-primary">REQUIS</span>
              </span>
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="ex. Alexandre Laurent"
                className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface placeholder:text-outline focus:bg-surface-low focus:outline-none"
              />
            </div>
            <button
              onClick={() => fullName.trim() && setStep(2)}
              disabled={!fullName.trim()}
              className="h-12 rounded bg-primary font-medium text-on-primary transition-all hover:bg-primary-fixed disabled:opacity-40"
            >
              Commencer la configuration
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="flex flex-col gap-space-lg">
            <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
              Étape 2 sur 4 · Profil académique
            </span>
            <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
              Calibre le radar de l'agent.
            </h1>
            <div className="flex flex-col gap-space-xs">
              <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                Centres d'intérêt
              </span>
              <div className="flex flex-wrap gap-1.5">
                {INTERESTS.map((interest) => (
                  <button
                    key={interest}
                    type="button"
                    onClick={() => toggle(interests, interest, setInterests)}
                    className={`rounded border px-2.5 py-1 font-mono text-label-sm transition-colors ${
                      interests.includes(interest)
                        ? "border-primary/60 bg-primary/15 text-primary"
                        : "border-outline-variant/40 bg-surface-lowest text-on-surface-variant hover:text-on-surface"
                    }`}
                  >
                    {interest}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-space-xs">
              <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                Niveau d'études
              </span>
              <select
                value={studyLevel}
                onChange={(e) => setStudyLevel(e.target.value)}
                className="h-11 rounded border-none bg-surface-lowest px-3 text-on-surface focus:outline-none"
              >
                <option value="">Sélectionner…</option>
                {STUDY_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-space-xs">
              <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                Pays de rattachement
              </span>
              <input
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                placeholder="ex. Côte d'Ivoire"
                className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface placeholder:text-outline focus:outline-none"
              />
            </div>
            <div className="flex gap-space-sm">
              <button
                onClick={() => setStep(1)}
                className="h-12 rounded border border-outline-variant/50 px-4 text-on-surface-variant hover:text-on-surface"
              >
                Retour
              </button>
              <button
                onClick={() => interests.length && setStep(3)}
                disabled={!interests.length}
                className="h-12 flex-1 rounded bg-primary font-medium text-on-primary transition-all hover:bg-primary-fixed disabled:opacity-40"
              >
                Continuer
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="flex flex-col gap-space-lg">
            <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
              Étape 3 sur 4 · Paramètres de veille
            </span>
            <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
              Définis le rythme d'analyse.
            </h1>
            <div className="flex flex-col gap-space-xs">
              <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                Fréquence des cycles
              </span>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 60, label: "Toutes les heures", tag: "RECOMMANDÉ" },
                  { value: 180, label: "Toutes les 3 heures", tag: "ÉCONOME" },
                  { value: 720, label: "2 fois par jour", tag: "DISCRET" },
                ].map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setFrequency(option.value)}
                    className={`flex flex-col gap-1 rounded border p-space-md text-left transition-colors ${
                      frequency === option.value
                        ? "border-primary/60 bg-primary/10"
                        : "border-outline-variant/40 bg-surface-lowest hover:border-outline-variant/70"
                    }`}
                  >
                    <span className="font-mono text-label-sm text-outline">{option.tag}</span>
                    <span className="text-body-md font-medium text-on-surface">{option.label}</span>
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-space-xs">
              <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                Types d'opportunités
              </span>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: "hackathon", label: "Hackathons", icon: "emoji_events" },
                  { id: "internship", label: "Stages & Jobs", icon: "work" },
                  { id: "fellowship", label: "Fellowships", icon: "school" },
                  { id: "scholarship", label: "Bourses", icon: "payments" },
                  { id: "conference", label: "Conférences", icon: "groups" },
                  { id: "certification", label: "Certifications", icon: "workspace_premium" },
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => toggle(types, t.id, setTypes)}
                    className={`flex items-center justify-between rounded border p-space-md transition-colors ${
                      types.includes(t.id)
                        ? "border-primary/60 bg-primary/10"
                        : "border-outline-variant/40 bg-surface-lowest"
                    }`}
                  >
                    <span className="flex items-center gap-space-sm text-body-md text-on-surface">
                      <span className="material-symbols-outlined text-[18px] text-outline">
                        {t.icon}
                      </span>
                      {t.label}
                    </span>
                    <span
                      className={`h-4 w-4 rounded-sm border ${
                        types.includes(t.id)
                          ? "border-primary bg-primary"
                          : "border-outline-variant"
                      }`}
                    >
                      {types.includes(t.id) && (
                        <span className="material-symbols-outlined text-[12px] text-on-primary">
                          check
                        </span>
                      )}
                    </span>
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-space-sm">
              <button
                onClick={() => setStep(2)}
                className="h-12 rounded border border-outline-variant/50 px-4 text-on-surface-variant hover:text-on-surface"
              >
                Retour
              </button>
              <button
                onClick={() => types.length && setStep(4)}
                disabled={!types.length}
                className="h-12 flex-1 rounded bg-primary font-medium text-on-primary transition-all hover:bg-primary-fixed disabled:opacity-40"
              >
                Prêt pour compilation
              </button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="flex flex-col gap-space-lg">
            <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
              Étape 4 sur 4 · Récapitulatif
            </span>
            <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
              Configuration vérifiée.
            </h1>
            <div className="flex flex-col gap-2 rounded border border-outline-variant/40 bg-surface-lowest p-space-md font-mono text-label-sm">
              <div className="flex justify-between">
                <span className="text-outline">AGENT</span>
                <span className="text-on-surface">{fullName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-outline">INTÉRÊTS</span>
                <span className="text-on-surface">{interests.join(", ")}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-outline">NIVEAU</span>
                <span className="text-on-surface">{studyLevel || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-outline">FRÉQUENCE</span>
                <span className="text-on-surface">{frequency} min</span>
              </div>
              <div className="flex justify-between">
                <span className="text-outline">TYPES</span>
                <span className="text-on-surface">{types.join(", ")}</span>
              </div>
            </div>
            <div className="flex gap-space-sm">
              <button
                onClick={() => setStep(3)}
                className="h-12 rounded border border-outline-variant/50 px-4 text-on-surface-variant hover:text-on-surface"
              >
                Retour
              </button>
              <button
                onClick={launch}
                className="h-12 flex-1 rounded bg-primary font-medium text-on-primary transition-all hover:bg-primary-fixed"
              >
                Lancer l'agent
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
