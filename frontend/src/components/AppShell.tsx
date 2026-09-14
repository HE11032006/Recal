import { useCallback, type CSSProperties } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useNewOpportunities } from "../hooks/useNewOpportunities";
import { useLanguage } from "../i18n/LanguageContext";

export function AppShell() {
  const { t } = useLanguage();
  const navItems = [
    { to: "/", label: t.nav.today, icon: "radar" },
    { to: "/saved", label: t.nav.saved, icon: "bookmark" },
    { to: "/profile", label: t.nav.profile, icon: "person" },
  ];
  const handleNew = useCallback(
    (count: number) => {
      window.recal?.notify("Recal", t.today.newToast(count));
      window.recal?.setBadge(count);
    },
    [t]
  );

  useNewOpportunities(handleNew);
  const location = useLocation();
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-surface">
      <div
        className="flex h-9 shrink-0 items-center gap-2 border-b border-outline-variant/30 bg-surface pl-3 pr-32"
        style={{ WebkitAppRegion: "drag" } as CSSProperties}
      >
        <img src="app-icon.png" alt="Recal" className="h-5 w-5 rounded-[3px]" draggable={false} />
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-outline">
          Recal
        </span>
      </div>
      <div className="flex min-h-0 flex-1">
        <nav className="flex w-14 flex-col items-center gap-space-md border-r border-outline-variant/30 bg-surface-low py-space-lg">
          <div className="mb-space-md flex h-8 w-8 items-center justify-center rounded border-primary/40 bg-primary/15">
            <span className="font-mono text-sm font-semibold text-primary">R</span>
          </div>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              title={item.label}
            className={({ isActive }) =>
              `flex h-10 w-10 items-center justify-center rounded border transition-all duration-150 active:scale-90 ${
                isActive
                  ? "border-outline-variant bg-surface-high text-on-surface shadow-glow-sm"
                  : "border-transparent text-outline hover:bg-surface-high/50 hover:text-on-surface"
              }`
            }
            >
              <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
            </NavLink>
          ))}
          <div className="mt-auto flex flex-col items-center gap-space-xs">
            <span className="h-1.5 w-1.5 rounded-full bg-success" />
            <span className="font-mono text-[9px] uppercase text-outline">LIVE</span>
          </div>
        </nav>
        <main className="flex-1 overflow-y-auto">
          <div
            key={location.pathname}
            className="animate-fade-in mx-auto max-w-6xl px-margin py-space-xl"
          >
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
