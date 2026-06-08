interface QuestionBoxProps {
  value: string;
  onChange: (value: string) => void;
}

export function QuestionBox({ value, onChange }: QuestionBoxProps) {
  return (
    <label className="question-box">
      <span>Ваш вопрос</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Например: на что мне обратить внимание в этой ситуации?"
        maxLength={600}
        rows={5}
      />
      <small>Вопрос необязателен. Лучше формулировать спокойно, без ожидания точного предсказания.</small>
    </label>
  );
}
