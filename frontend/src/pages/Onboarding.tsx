import { useEffect, useState, type CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import { api, BACKEND_OFFLINE, type Profile } from "../api/client";
import { useLanguage } from "../i18n/LanguageContext";

const TYPE_META = [
  { id: "hackathon", icon: "emoji_events" },
  { id: "internship", icon: "work" },
  { id: "fellowship", icon: "school" },
  { id: "scholarship", icon: "payments" },
  { id: "conference", icon: "groups" },
  { id: "certification", icon: "workspace_premium" },
] as const;

export default function Onboarding() {
  const navigate = useNavigate();
  const { t, setLang } = useLanguage();
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

  function pickLanguage(lang: "fr" | "en") {
    setLanguage(lang);
    setLang(lang);
  }

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
            ? t.onboarding.errSkipped(e.message)
            : t.onboarding.errBackground
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
      setError(
        e instanceof Error && e.message === BACKEND_OFFLINE
          ? t.common.offlineTitle
          : (e instanceof Error ? e.message : t.onboarding.errUnknown)
        );
      setLaunching(false);
    }
  }

  // Vérifier si déjà onboarded au montage (pour éviter le re-onboarding au rechargement)
  useEffect(() => {
    if (localStorage.getItem("recal:onboarded") === "true") {
      navigate("/", { replace: true });
    }
  }, [navigate]);

  if (launching) {
    const steps = t.onboarding.launchSteps;
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-surface px-6 pt-9">
        <div
          className="fixed left-0 right-0 top-0 flex h-9 items-center gap-2 border-b border-outline-variant/30 bg-surface pl-3 pr-32"
          style={{ WebkitAppRegion: "drag" } as CSSProperties}
        >
          <img src="app-icon.png" alt="Recal" className="h-5 w-5 rounded-[3px]" draggable={false} />
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-outline">Recal</span>
        </div>
        <div className="animate-fade-in flex flex-col gap-space-lg w-full max-w-md">
          <div className="flex items-center gap-space-sm">
            <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
            <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
              {t.onboarding.compiling}
            </span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
            {t.onboarding.working}
          </h1>
          <div className="flex flex-col gap-space-md">
            {steps.map((label, i) => (
              <div key={label} className="animate-rise flex items-center gap-space-sm" style={{ animationDelay: `${i * 60}ms` }}>
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded border transition-all duration-200 ${
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
            <div className="animate-fade-in border border-error/40 bg-error-container/30 rounded p-space-md text-body-sm text-error">
              {error} — le cycle cloud planifié prend le relai.
            </div>
          )}
        </div>
      </div>
    );
  }

  const freqOptions = [
    { value: 60, label: t.onboarding.freqHourly, tag: t.onboarding.freqHourlyTag },
    { value: 180, label: t.onboarding.freq3h, tag: t.onboarding.freq3hTag },
    { value: 720, label: t.onboarding.freq2x, tag: t.onboarding.freq2xTag },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-surface pt-9">
      <div
        className="fixed left-0 right-0 top-0 flex h-9 items-center gap-2 border-b border-outline-variant/30 bg-surface pl-3 pr-32"
        style={{ WebkitAppRegion: "drag" } as CSSProperties}
      >
        <img src="app-icon.png" alt="Recal" className="h-5 w-5 rounded-[3px]" draggable={false} />
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-outline">Recal</span>
      </div>
      <div className="h-1 w-full bg-surface-lowest">
        <div
          className="h-full bg-primary transition-all duration-500"
          style={{ width: `${(step / 4) * 100}%` }}
        />
      </div>
      <div className="mx-auto flex w-full max-w-xl flex-1 flex-col justify-center px-6 py-space-xl">
        <div key={step} className="animate-rise flex flex-col gap-space-lg">
          {step === 1 && (
            <div className="flex flex-col gap-space-lg">
              <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
                {t.onboarding.stepOf(1)} · {t.onboarding.s1kicker}
              </span>
              <h1 className="text-3xl font-semibold tracking-tight text-on-surface">
                {t.onboarding.s1title}
              </h1>
              <p className="text-body-lg leading-relaxed text-on-surface-variant">
                {t.onboarding.s1desc}
              </p>
              <div className="flex flex-col gap-space-xs">
                <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                  {t.onboarding.language}
                </span>
                <div className="grid grid-cols-2 gap-1 rounded border border-outline-variant/40 bg-surface-lowest p-1">
                  {(["fr", "en"] as const).map((lang) => (
                    <button
                      key={lang}
                      type="button"
                      onClick={() => pickLanguage(lang)}
                      className={`flex items-center justify-center gap-2 rounded py-1.5 px-3 font-medium transition-all ${
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
                  {t.onboarding.identity}
                  <span className="text-primary">REQUIS</span>
                </span>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder={t.onboarding.namePlaceholder}
                  className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface placeholder:text-outline focus:bg-surface-low focus:outline-none"
                />
              </div>
              <button
                onClick={() => fullName.trim() && setStep(2)}
                disabled={!fullName.trim()}
                className="h-12 rounded bg-primary font-medium text-on-primary transition-all duration-150 hover:bg-primary-fixed hover:shadow-glow active:scale-[0.99] disabled:opacity-40"
              >
                {t.onboarding.start}
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="flex flex-col gap-space-lg">
              <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
                {t.onboarding.stepOf(2)} · {t.onboarding.s2kicker}
              </span>
              <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
                {t.onboarding.s2title}
              </h1>
              <div className="flex flex-col gap-space-xs">
                <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                  {t.onboarding.interests}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {t.onboarding.interestOptions.map((interest) => (
                    <button
                      key={interest}
                      type="button"
                      onClick={() => toggle(interests, interest, setInterests)}
                      className={`rounded border px-2.5 py-1 font-mono text-label-sm transition-colors active:scale-95 ${
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
                  {t.onboarding.studyLevel}
                </span>
                <select
                  value={studyLevel}
                  onChange={(e) => setStudyLevel(e.target.value)}
                  className="h-11 rounded border-none bg-surface-lowest px-3 text-on-surface focus:outline-none"
                >
                  <option value="">{t.onboarding.selectPlaceholder}</option>
                  {t.onboarding.studyOptions.map((level) => (
                    <option key={level} value={level}>
                      {level}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-space-xs">
                <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                  {t.onboarding.country}
                </span>
                <input
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder={t.onboarding.countryPlaceholder}
                  className="h-11 rounded border-none bg-surface-lowest px-3.5 text-on-surface placeholder:text-outline focus:outline-none"
                />
              </div>
              <div className="flex gap-space-sm">
                <button
                  onClick={() => setStep(1)}
                  className="h-12 rounded border border-outline-variant/50 px-4 text-on-surface-variant transition-colors hover:text-on-surface active:scale-95"
                >
                  {t.onboarding.back}
                </button>
                <button
                  onClick={() => interests.length && setStep(3)}
                  disabled={!interests.length}
                  className="h-12 flex-1 rounded bg-primary font-medium text-on-primary transition-all duration-150 hover:bg-primary-fixed hover:shadow-glow active:scale-[0.99] disabled:opacity-40"
                >
                  {t.onboarding.continue}
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="flex flex-col gap-space-lg">
              <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
                {t.onboarding.stepOf(3)} · {t.onboarding.s3kicker}
              </span>
              <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
                {t.onboarding.s3title}
              </h1>
              <div className="flex flex-col gap-space-xs">
                <span className="font-mono text-label-sm uppercase tracking-wider text-on-surface-variant">
                  {t.onboarding.frequency}
                </span>
                <div className="grid grid-cols-3 gap-2">
                  {freqOptions.map((option) => (
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
                  {t.onboarding.watchTypes}
                </span>
                <div className="flex flex-col gap-2">
                  {TYPE_META.map((meta) => (
                    <button
                      key={meta.id}
                      type="button"
                      onClick={() => toggle(types, meta.id, setTypes)}
                      className={`flex items-center justify-between rounded border p-space-md transition-colors ${
                        types.includes(meta.id)
                          ? "border-primary/60 bg-primary/10"
                          : "border-outline-variant/40 bg-surface-lowest"
                      }`}
                    >
                      <span className="flex items-center gap-space-sm text-body-md text-on-surface">
                        <span className="material-symbols-outlined text-[18px] text-outline">
                          {meta.icon}
                        </span>
                        {t.types[meta.id as keyof typeof t.types]}
                      </span>
                      <span
                        className={`h-4 w-4 rounded-sm border ${
                          types.includes(meta.id)
                            ? "border-primary bg-primary"
                            : "border-outline-variant"
                        }`}
                      >
                        {types.includes(meta.id) && (
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
                  className="h-12 rounded border border-outline-variant/50 px-4 text-on-surface-variant transition-colors hover:text-on-surface active:scale-95"
                >
                  {t.onboarding.back}
                </button>
                <button
                  onClick={() => types.length && setStep(4)}
                  disabled={!types.length}
                  className="h-12 flex-1 rounded bg-primary font-medium text-on-primary transition-all duration-150 hover:bg-primary-fixed hover:shadow-glow active:scale-[0.99] disabled:opacity-40"
                >
                  {t.onboarding.ready}
                </button>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="flex flex-col gap-space-lg">
              <span className="font-mono text-label-sm uppercase tracking-wider text-outline">
                {t.onboarding.stepOf(4)} · {t.onboarding.s4kicker}
              </span>
              <h1 className="text-2xl font-semibold tracking-tight text-on-surface">
                {t.onboarding.s4title}
              </h1>
              <div className="flex flex-col gap-2 rounded border border-outline-variant/40 bg-surface-lowest p-space-md font-mono text-label-sm">
                <div className="flex justify-between">
                  <span className="text-outline">{t.onboarding.recapAgent}</span>
                  <span className="text-on-surface">{fullName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-outline">{t.onboarding.recapInterests}</span>
                  <span className="text-on-surface">{interests.join(", ")}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-outline">{t.onboarding.recapLevel}</span>
                  <span className="text-on-surface">{studyLevel || t.onboarding.recapEmpty}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-outline">{t.onboarding.recapFreq}</span>
                  <span className="text-on-surface">{frequency} {t.onboarding.minUnit}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-outline">{t.onboarding.recapTypes}</span>
                  <span className="text-on-surface">{types.join(", ")}</span>
                </div>
              </div>
              <div className="flex gap-space-sm">
                <button
                  onClick={() => setStep(3)}
                  className="h-12 rounded border border-outline-variant/50 px-4 text-on-surface-variant transition-all hover:text-on-surface active:scale-95"
                >
                  {t.onboarding.back}
                </button>
                <button
                  onClick={launch}
                  className="h-12 flex-1 rounded bg-primary font-medium text-on-primary transition-all duration-150 hover:bg-primary-fixed hover:shadow-glow active:scale-[0.99]"
                >
                  {t.onboarding.launch}
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}