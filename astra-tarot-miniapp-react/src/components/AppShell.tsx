import type { ReactNode } from "react";
import { isTelegram } from "../services/telegram";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <div className="cosmic-field" aria-hidden="true" />
      {!isTelegram() && <div className="debug-badge">Browser preview</div>}
      <main className="app-viewport">{children}</main>
    </div>
  );
}
