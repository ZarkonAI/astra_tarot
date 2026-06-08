interface SafetyNoteProps {
  variant?: "default" | "love" | "money";
}

const notes = {
  default: "Расклады носят развлекательный и рефлексивный характер и не заменяют помощь специалиста.",
  love: "Расклад не должен заменять честный разговор, заботу о себе и уважение личных границ.",
  money: "Это не финансовая рекомендация, а символический взгляд на ситуацию.",
};

export function SafetyNote({ variant = "default" }: SafetyNoteProps) {
  return <p className="safety-note">{notes[variant]}</p>;
}
