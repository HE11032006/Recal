declare interface Window {
  recal?: {
    notify: (title: string, body: string) => Promise<boolean>;
    setBadge: (count: number) => Promise<boolean>;
    setTheme?: (theme: "light" | "dark") => Promise<boolean>;
    isDesktop: boolean;
  };
}
