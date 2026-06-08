interface TelegramUser {
  id?: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
}

interface TelegramHapticFeedback {
  impactOccurred(style: "light" | "medium" | "heavy" | "rigid" | "soft"): void;
  notificationOccurred(type: "error" | "success" | "warning"): void;
  selectionChanged(): void;
}

interface TelegramWebApp {
  initData: string;
  initDataUnsafe?: {
    user?: TelegramUser;
  };
  ready(): void;
  expand(): void;
  close(): void;
  sendData(data: string): void;
  setHeaderColor(color: string): void;
  setBackgroundColor(color: string): void;
  HapticFeedback?: TelegramHapticFeedback;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

export function getTelegramWebApp(): TelegramWebApp | undefined {
  return window.Telegram?.WebApp;
}

export function initTelegramApp(): void {
  const tg = getTelegramWebApp();

  if (!tg) {
    return;
  }

  tg.ready();
  tg.expand();
  tg.setHeaderColor("#08030f");
  tg.setBackgroundColor("#08030f");
}

export function isTelegram(): boolean {
  return Boolean(getTelegramWebApp()?.initData);
}

export function getTelegramUser(): TelegramUser | undefined {
  return getTelegramWebApp()?.initDataUnsafe?.user;
}

export function getTelegramInitData(): string {
  return getTelegramWebApp()?.initData ?? "";
}

export function hapticFeedback(type: "tap" | "success" | "error" = "tap"): void {
  const haptics = getTelegramWebApp()?.HapticFeedback;

  if (!haptics) {
    return;
  }

  if (type === "success" || type === "error") {
    haptics.notificationOccurred(type);
    return;
  }

  haptics.impactOccurred("light");
}

export function closeApp(): void {
  getTelegramWebApp()?.close();
}

export function sendSpreadPayload(spread: string, question: string): void {
  const tg = getTelegramWebApp();

  if (!tg) {
    return;
  }

  // Future switch: enable tg.sendData when the bot should receive selection payloads directly.
  tg.sendData(JSON.stringify({ action: "select_spread", spread, question }));
}
