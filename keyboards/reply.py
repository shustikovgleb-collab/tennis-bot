from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Все доступные разряды
CATEGORIES = {
    "1": "🎾 Мужской одиночный любительский (Masters)",
    "2": "🎾 Мужской одиночный любительский (Tour)",
    "3": "🎾 Женский одиночный любительский (Tour)",
    "4": "👫 Женский парный любительский",
    "5": "👫 Смешанный парный (Masters) — средний и высокий уровень",
}

# Парные разряды (для логики с партнёром)
PAIR_CATEGORIES = {"4", "5"}


def get_category_keyboard(selected: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура выбора разряда. Уже выбранные помечаются ✅"""
    buttons = []
    for key, name in CATEGORIES.items():
        prefix = "✅ " if key in selected else ""
        buttons.append([KeyboardButton(text=f"{prefix}{name}")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_yes_no_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
        ],
        resize_keyboard=True
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def category_key_by_text(text: str) -> str | None:
    """Возвращает ключ разряда по тексту кнопки (игнорируя ✅ в начале)"""
    clean = text.removeprefix("✅ ")
    for key, name in CATEGORIES.items():
        if name == clean:
            return key
    return None
