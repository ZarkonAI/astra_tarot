import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "../components/AppShell";
import { getSpread } from "../data/spreads";
import { createReading } from "../services/readingsApi";
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
    setScreen("spread");
  }

  function submitReading() {
    if (isLoading) {
      return;
    }

    hapticFeedback("tap");
    setIsLoading(true);
    setError(undefined);
    setScreen("ritual");

    const requestId = activeRequestRef.current + 1;
    activeRequestRef.current = requestId;

    createReading({
      spread: selectedSpread.slug,
      question,
      initData: getTelegramInitData(),
    })
      .then((reading) => {
        if (activeRequestRef.current !== requestId) return;
        setResult(reading);
        hapticFeedback("success");
        setScreen("result");
      })
      .catch(() => {
        if (activeRequestRef.current !== requestId) return;
        hapticFeedback("error");
        setError("Звезда-проводник не смогла получить ответ. Попробуйте ещё раз.");
        setScreen("spread");
      })
      .finally(() => {
        if (activeRequestRef.current === requestId) {
          setIsLoading(false);
        }
      });
  }

  function goHome() {
    hapticFeedback("tap");
    setError(undefined);
    setScreen("home");
  }

  function newReading() {
    hapticFeedback("tap");
    setError(undefined);
    setScreen("spread");
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
      {screen === "ritual" && <RitualScreen />}
      {screen === "result" && result && <ResultScreen result={result} onHome={goHome} onNewReading={newReading} />}
    </AppShell>
  );
}
