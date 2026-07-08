import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "../components/AppShell";
import { getSpread } from "../data/spreads";
import { createReading } from "../services/api";
import { getTelegramInitData, getTelegramUser, hapticFeedback, initTelegramApp } from "../services/telegram";
import { HomeScreen } from "../screens/HomeScreen";
import { ResultScreen } from "../screens/ResultScreen";
import { RitualScreen } from "../screens/RitualScreen";
import { SpreadScreen } from "../screens/SpreadScreen";
import { WelcomeScreen } from "../screens/WelcomeScreen";
import type { AppScreen, ReadingResult, SpreadConfig } from "../types";

const WELCOME_STORAGE_KEY = "astra_tarot_welcome_seen";

function getInitialScreen(): AppScreen {
  if (window.location.search.includes("debugWelcome=1")) {
    window.localStorage.removeItem(WELCOME_STORAGE_KEY);
    return "welcome";
  }

  return window.localStorage.getItem(WELCOME_STORAGE_KEY) === "true" ? "home" : "welcome";
}

function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

function randomDelaySeconds(minSeconds: number, maxSeconds: number): number {
  const lower = Math.max(0, Math.min(minSeconds, maxSeconds));
  const upper = Math.max(0, Math.max(minSeconds, maxSeconds));
  return lower + Math.random() * (upper - lower);
}

function getRitualDelayBySpread(spread: SpreadConfig): number {
  if (spread.slug === "daily_card") {
    return randomDelaySeconds(3, 5) * 1000;
  }
  if (spread.slug === "quick") {
    return randomDelaySeconds(4, 7) * 1000;
  }
  return randomDelaySeconds(6, 10) * 1000;
}


function cleanDisplayText(value: string): string {
  return String(value || "")
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`([^`]*)`/g, "$1")
    .replace(/\*\*([^*\n]+)\*\*/g, "$1")
    .replace(/__([^_\n]+)__/g, "$1")
    .replace(/\*\*|__/g, "")
    .split("\n")
    .map((line) => line
      .replace(/^\s*(?:-{3,}|_{3,}|\*{3,})\s*$/, "")
      .replace(/^\s{0,3}#{1,6}\s*/, "")
      .replace(/^\s*>\s?/, "")
      .replace(/^\s*[-*\u2022]\s+/, "")
      .replace(/^\s*\d+[.)]\s+/, "")
      .trimEnd())
    .filter((line) => !/(behavior|let's rephrase|rephrase|we must not use|english|hebrew|but we must|openrouter|fallback|api error)/i.test(line))
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function cleanReadingResult(reading: ReadingResult): ReadingResult {
  return {
    ...reading,
    spreadTitle: cleanDisplayText(reading.spreadTitle),
    question: cleanDisplayText(reading.question),
    interpretation: cleanDisplayText(reading.interpretation),
    guideAdvice: cleanDisplayText(reading.guideAdvice),
    disclaimer: cleanDisplayText(reading.disclaimer),
    cards: reading.cards.map((card) => ({
      ...card,
      position: cleanDisplayText(card.position),
      title: cleanDisplayText(card.title),
      meaning: cleanDisplayText(card.meaning),
    })),
  };
}

export function App() {
  const [screen, setScreen] = useState<AppScreen>(getInitialScreen);
  const [selectedSpread, setSelectedSpread] = useState<SpreadConfig>(() => getSpread("daily_card"));
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<ReadingResult | null>(null);
  const [error, setError] = useState<string>();
  const [isLoading, setIsLoading] = useState(false);
  const activeRequestRef = useRef(0);

  const user = useMemo(() => getTelegramUser(), []);

  useEffect(() => {
    initTelegramApp();
  }, []);

  function startApp() {
    window.localStorage.setItem(WELCOME_STORAGE_KEY, "true");
    hapticFeedback("tap");
    setScreen("home");
  }

  function selectSpread(spread: SpreadConfig) {
    hapticFeedback("tap");
    setSelectedSpread(spread);
    setQuestion("");
    setError(undefined);
    if (spread.slug === "daily_card") {
      submitReadingForSpread(spread, "");
      return;
    }
    setScreen("spread");
  }

  function submitReadingForSpread(spread: SpreadConfig, readingQuestion: string) {
    if (isLoading) {
      return;
    }

    hapticFeedback("tap");
    setIsLoading(true);
    setError(undefined);
    setScreen("ritual");

    const requestId = activeRequestRef.current + 1;
    activeRequestRef.current = requestId;

    const readingPromise = createReading({
      spread: spread.slug,
      question: readingQuestion,
      initData: getTelegramInitData(),
      telegramUser: user ?? null,
    });
    const ritualDelayPromise = sleep(getRitualDelayBySpread(spread));

    Promise.all([readingPromise, ritualDelayPromise])
      .then(([reading]) => {
        if (activeRequestRef.current !== requestId) return;
        setResult(cleanReadingResult(reading));
        hapticFeedback("success");
        setScreen("result");
      })
      .catch((readingError) => {
        if (activeRequestRef.current !== requestId) return;
        hapticFeedback("error");
        setError(readingError instanceof Error ? readingError.message : "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0440\u0430\u0441\u043a\u043b\u0430\u0434. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0435\u0449\u0435 \u0440\u0430\u0437.");
      })
      .finally(() => {
        if (activeRequestRef.current === requestId) {
          setIsLoading(false);
        }
      });
  }

  function submitReading() {
    submitReadingForSpread(selectedSpread, question);
  }

  function goHome() {
    activeRequestRef.current += 1;
    hapticFeedback("tap");
    setError(undefined);
    setIsLoading(false);
    setScreen("home");
  }

  function newReading() {
    hapticFeedback("tap");
    setError(undefined);
    setScreen("spread");
  }

  function leaveRitual() {
    activeRequestRef.current += 1;
    hapticFeedback("tap");
    setError(undefined);
    setIsLoading(false);
    setScreen(selectedSpread.slug === "daily_card" ? "home" : "spread");
  }

  return (
    <AppShell>
      {screen === "welcome" && <WelcomeScreen onStart={startApp} />}
      {screen === "home" && <HomeScreen firstName={user?.first_name} onSelectSpread={selectSpread} />}
      {screen === "spread" && (
        <SpreadScreen
          spread={selectedSpread}
          question={question}
          error={error}
          isLoading={isLoading}
          onQuestionChange={setQuestion}
          onBack={goHome}
          onSubmit={submitReading}
        />
      )}
      {screen === "ritual" && <RitualScreen spread={selectedSpread} error={error} onBack={leaveRitual} />}
      {screen === "result" && result && <ResultScreen result={result} onHome={goHome} onNewReading={newReading} />}
    </AppShell>
  );
}




