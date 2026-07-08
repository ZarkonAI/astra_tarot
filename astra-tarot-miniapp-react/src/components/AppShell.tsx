import type { ReactNode } from "react";
import { getApiDebugLabel, shouldShowApiDebug } from "../services/api";
import { isTelegram } from "../services/telegram";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const debugLabel = shouldShowApiDebug() ? getApiDebugLabel() : !isTelegram() ? "Browser preview" : "";

  return (
    <div className="app-shell">
      <div className="cosmic-field" aria-hidden="true" />
      {debugLabel && <div className="debug-badge">{debugLabel}</div>}
      <main className="app-viewport">{children}</main>
    </div>
  );
}
