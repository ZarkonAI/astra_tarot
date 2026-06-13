from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TarotCard:
    number: int
    slug: str
    title: str
    archetype: str
    light: str
    shadow: str
    symbol: str
    image_path: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


CARD_BACK_ORNATE = "assets/background/card_back_ornate.webp"


def build_public_asset_url(public_base_url: str, image_path: str) -> str:
    base_url = (public_base_url or "").strip()
    clean_path = image_path.strip().lstrip("/")
    if not base_url:
        return clean_path
    return f"{base_url.rstrip('/')}/{clean_path}"


MAJOR_ARCANA: tuple[TarotCard, ...] = (
    TarotCard(0, "fool", "Шут", "начало пути", "свобода, доверие, свежий взгляд", "хаос, наивность, поспешность", "путник у края", CARD_BACK_ORNATE),
    TarotCard(1, "magician", "Маг", "воля и мастерство", "инициатива, фокус, действие", "манипуляция, суета, рассеянность", "жезл и стол мастера", CARD_BACK_ORNATE),
    TarotCard(2, "high_priestess", "Жрица", "тайное знание", "интуиция, тишина, глубина", "закрытость, сомнение, пассивность", "лунная завеса", CARD_BACK_ORNATE),
    TarotCard(3, "empress", "Императрица", "рост и плодородие", "забота, изобилие, творчество", "излишества, зависимость от комфорта", "сад и корона", CARD_BACK_ORNATE),
    TarotCard(4, "emperor", "Император", "порядок и опора", "границы, структура, ответственность", "жесткость, контроль, упрямство", "трон и камень", CARD_BACK_ORNATE),
    TarotCard(5, "hierophant", "Верховный жрец", "традиция и смысл", "наставничество, вера, ценности", "догматизм, чужие правила", "ключи знания", "assets/cards/card_hierophant.webp"),
    TarotCard(6, "lovers", "Влюбленные", "выбор сердца", "согласие, близость, честность", "сомнение, зависимость, раздвоенность", "союз и свет", "assets/cards/card_lovers.webp"),
    TarotCard(7, "chariot", "Колесница", "движение и победа", "направление, дисциплина, рывок", "напор, конфликт, потеря курса", "колесница со сфинксами", "assets/cards/card_chariot.webp"),
    TarotCard(8, "justice", "Справедливость", "равновесие и закон", "ясность, честность, последствия", "холодность, обвинение, перекос", "меч и весы", "assets/cards/card_justice.webp"),
    TarotCard(9, "hermit", "Отшельник", "внутренний поиск", "мудрость, пауза, самопознание", "изоляция, усталость, отдаление", "фонарь в темноте", "assets/cards/card_hermit.webp"),
    TarotCard(10, "wheel_of_fortune", "Колесо Фортуны", "цикл перемен", "поворот, шанс, движение жизни", "нестабильность, зависание, случайность", "вращающееся колесо", "assets/cards/card_wheel.webp"),
    TarotCard(11, "strength", "Сила", "мягкая власть", "смелость, терпение, прирученная энергия", "давление, гордыня, сдержанный гнев", "лев и ладонь", "assets/cards/card_strength.webp"),
    TarotCard(12, "hanged_man", "Повешенный", "новый взгляд", "пауза, принятие, переоценка", "застой, жертвенность, бессилие", "перевернутый свет", "assets/cards/card_hanged.webp"),
    TarotCard(13, "death", "Смерть", "завершение и переход", "обновление, отпускание, честная точка", "страх перемен, цепляние, резкость", "белая роза", "assets/cards/card_death.webp"),
    TarotCard(14, "temperance", "Умеренность", "исцеление баланса", "мера, гармония, спокойная настройка", "затягивание, размытость, компромисс любой ценой", "две чаши", "assets/cards/card_temperance.webp"),
    TarotCard(15, "devil", "Дьявол", "сила привязок", "осознание желаний, энергия, честность с тенью", "зависимость, соблазн, самообман", "цепи и факел", "assets/cards/card_devil.webp"),
    TarotCard(16, "tower", "Башня", "разрушение иллюзий", "освобождение, правда, резкая ясность", "кризис, сопротивление, гордость", "молния и башня", "assets/cards/card_tower.webp"),
    TarotCard(17, "star", "Звезда", "надежда и проводничество", "вдохновение, доверие, исцеление", "идеализация, ожидание чуда, отрыв от земли", "звездная вода", "assets/cards/card_star.webp"),
    TarotCard(18, "moon", "Луна", "туман подсознания", "чуткость, сны, тонкие сигналы", "страхи, иллюзии, тревожные фантазии", "ночная дорога", "assets/cards/card_moon.webp"),
    TarotCard(19, "sun", "Солнце", "ясность и жизнь", "радость, открытость, успех", "самоуверенность, слепое пятно, выгорание", "солнечный круг", "assets/cards/card_sun.webp"),
    TarotCard(20, "judgement", "Суд", "пробуждение", "призвание, итог, новый уровень", "самокритика, вина, страх оценки", "труба пробуждения", "assets/cards/card_judgement.webp"),
    TarotCard(21, "world", "Мир", "целостность", "завершение, зрелость, интеграция", "незавершенность, распыление, усталый финал", "венок мира", "assets/cards/card_world.webp"),
)


REQUIRED_CARD_FIELDS = {"number", "slug", "title", "archetype", "light", "shadow", "symbol", "image_path"}
