import { BottomAction } from "../components/BottomAction";
import { SafetyNote } from "../components/SafetyNote";
import { StarGuide } from "../components/StarGuide";

interface WelcomeScreenProps {
  onStart: () => void;
}

export function WelcomeScreen({ onStart }: WelcomeScreenProps) {
  return (
    <section className="screen welcome-screen screen-enter">
      <div className="welcome-screen__guide">
        <StarGuide size="hero" />
      </div>
      <div className="welcome-screen__copy">
        <p className="eyebrow">Mini App</p>
        <h1>Astra Tarot</h1>
        <p className="lead">
          Я ваша звезда-проводник. Помогу выбрать расклад и бережно посмотреть на ситуацию через символы Таро.
        </p>
        <SafetyNote />
      </div>
      <BottomAction primaryLabel="Начать" onPrimary={onStart} />
    </section>
  );
}
