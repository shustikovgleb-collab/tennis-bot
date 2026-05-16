import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import ADMIN_CHAT_ID
from states import RegistrationStates
from keyboards.reply import (
    CATEGORIES,
    PAIR_CATEGORIES,
    get_category_keyboard,
    get_yes_no_keyboard,
    remove_keyboard,
    category_key_by_text,
)
from utils.sheets import save_registration

logger = logging.getLogger(__name__)
router = Router()

# ─────────────────────────────────────────────
# Текст приветствия
# ─────────────────────────────────────────────
WELCOME_TEXT = (
    "👋 Добрый день!\n\n"
    "Добро пожаловать на регистрацию в\n"
    "<b>🏆 Кубок Южной Звезды & БКС Ультима</b>\n\n"
    "Пожалуйста, выберите <b>разряд</b> для участия.\n"
    "Можно выбрать несколько — нажимайте по одному:"
)


def build_admin_message(data: dict, user) -> str:
    """Формирует сообщение для организатора."""
    from keyboards.reply import CATEGORIES as CAT
    cats = "\n    • ".join(CAT[k] for k in data.get("categories", []))

    p1 = data.get("partner_1_name")
    p1s = data.get("partner_1_status")
    p2 = data.get("partner_2_name")
    p2s = data.get("partner_2_status")

    partner_block = ""
    if p1:
        partner_block += f"\n🤝 Партнёр (разряд 1): {p1} ({p1s})"
    if p2:
        partner_block += f"\n🤝 Партнёр (разряд 2): {p2} ({p2s})"

    username = f"@{user.username}" if user.username else f"ID: {user.id}"

    return (
        "🎾 <b>Новая заявка на турнир!</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>ФИО:</b> {data.get('name')}\n"
        f"📞 <b>Телефон:</b> {data.get('phone')}\n"
        f"📧 <b>Email:</b> {data.get('email')}\n"
        f"🏆 <b>Разряды:</b>\n    • {cats}"
        f"{partner_block}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💬 Telegram: {username}"
    )


def get_pair_categories(selected: list[str]) -> list[str]:
    """Возвращает список выбранных парных разрядов."""
    return [k for k in selected if k in PAIR_CATEGORIES]


# ─────────────────────────────────────────────
# /start — приветствие
# ─────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(categories=[])
    await message.answer(
        WELCOME_TEXT,
        reply_markup=get_category_keyboard([]),
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.choosing_category)


# ─────────────────────────────────────────────
# Выбор разряда
# ─────────────────────────────────────────────
@router.message(RegistrationStates.choosing_category)
async def handle_category_choice(message: Message, state: FSMContext):
    key = category_key_by_text(message.text or "")

    if key is None:
        await message.answer(
            "⚠️ Пожалуйста, выберите разряд из списка ниже.",
            reply_markup=get_category_keyboard(
                (await state.get_data()).get("categories", [])
            )
        )
        return

    data = await state.get_data()
    selected: list = data.get("categories", [])

    if key in selected:
        await message.answer(
            f"✅ Этот разряд уже добавлен.\n\nХотите добавить ещё разряд?",
            reply_markup=get_yes_no_keyboard()
        )
        await state.set_state(RegistrationStates.confirm_more)
        return

    selected.append(key)
    await state.update_data(categories=selected)

    selected_names = "\n• ".join(CATEGORIES[k] for k in selected)
    await message.answer(
        f"✅ Добавлен разряд:\n<b>{CATEGORIES[key]}</b>\n\n"
        f"<b>Ваш список ({len(selected)}):</b>\n• {selected_names}\n\n"
        "Хотите добавить ещё разряд?",
        reply_markup=get_yes_no_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.confirm_more)


# ─────────────────────────────────────────────
# Добавить ещё разряд?
# ─────────────────────────────────────────────
@router.message(RegistrationStates.confirm_more, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_confirm_more(message: Message, state: FSMContext):
    if message.text == "✅ Да":
        data = await state.get_data()
        await message.answer(
            "Выберите ещё один разряд:",
            reply_markup=get_category_keyboard(data.get("categories", []))
        )
        await state.set_state(RegistrationStates.choosing_category)
    else:
        await message.answer(
            "📝 Отлично! Теперь заполним контактные данные.\n\n"
            "Введите ваше <b>Фамилию Имя Отчество</b>:",
            reply_markup=remove_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(RegistrationStates.entering_name)


@router.message(RegistrationStates.confirm_more)
async def handle_confirm_more_invalid(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, нажмите <b>Да</b> или <b>Нет</b>.",
                         reply_markup=get_yes_no_keyboard(), parse_mode="HTML")


# ─────────────────────────────────────────────
# ФИО
# ─────────────────────────────────────────────
@router.message(RegistrationStates.entering_name)
async def handle_name(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""

    if len(name.split()) < 2:
        await message.answer(
            "⚠️ Пожалуйста, введите <b>Фамилию и Имя</b> (минимум два слова).",
            parse_mode="HTML"
        )
        return

    await state.update_data(name=name)
    await message.answer(
        f"✅ ФИО: <b>{name}</b>\n\n"
        "Введите ваш <b>контактный телефон</b>:\n"
        "<i>Пример: +7 999 123-45-67</i>",
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.entering_phone)


# ─────────────────────────────────────────────
# Телефон
# ─────────────────────────────────────────────
@router.message(RegistrationStates.entering_phone)
async def handle_phone(message: Message, state: FSMContext):
    phone = message.text.strip() if message.text else ""

    # Базовая валидация: хотя бы 7 цифр
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 7:
        await message.answer(
            "⚠️ Введите корректный номер телефона.\n"
            "<i>Пример: +7 999 123-45-67</i>",
            parse_mode="HTML"
        )
        return

    await state.update_data(phone=phone)
    await message.answer(
        f"✅ Телефон: <b>{phone}</b>\n\n"
        "Введите ваш <b>адрес электронной почты</b>:",
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.entering_email)


# ─────────────────────────────────────────────
# Email
# ─────────────────────────────────────────────
@router.message(RegistrationStates.entering_email)
async def handle_email(message: Message, state: FSMContext):
    email = message.text.strip() if message.text else ""

    if "@" not in email or "." not in email.split("@")[-1]:
        await message.answer(
            "⚠️ Введите корректный email.\n<i>Пример: ivan@mail.ru</i>",
            parse_mode="HTML"
        )
        return

    await state.update_data(email=email)

    data = await state.get_data()
    pairs = get_pair_categories(data.get("categories", []))

    if pairs:
        # Есть парные разряды — спрашиваем про первый
        pair_name = CATEGORIES[pairs[0]]
        await state.update_data(
            pair_queue=pairs,
            partner_1_name="",
            partner_1_status="",
            partner_2_name="",
            partner_2_status="",
        )
        await message.answer(
            f"✅ Email: <b>{email}</b>\n\n"
            f"У вас выбран парный разряд:\n<b>{pair_name}</b>\n\n"
            "У вас <b>есть партнёр</b> для этого разряда?",
            reply_markup=get_yes_no_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(RegistrationStates.partner_check_1)
    else:
        await finish_registration(message, state)


# ─────────────────────────────────────────────
# Партнёр для 1-го парного разряда
# ─────────────────────────────────────────────
@router.message(RegistrationStates.partner_check_1, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_partner_check_1(message: Message, state: FSMContext):
    data = await state.get_data()
    pairs: list = data.get("pair_queue", [])
    pair_name = CATEGORIES[pairs[0]]

    if message.text == "✅ Да":
        await message.answer(
            f"Укажите <b>ФИО партнёра</b> для разряда:\n<b>{pair_name}</b>",
            reply_markup=remove_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(RegistrationStates.entering_partner_1)
    else:
        await state.update_data(partner_1_status="Ищем партнёра")
        await _check_second_pair(message, state)


@router.message(RegistrationStates.partner_check_1)
async def handle_partner_check_1_invalid(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, нажмите <b>Да</b> или <b>Нет</b>.",
                         reply_markup=get_yes_no_keyboard(), parse_mode="HTML")


@router.message(RegistrationStates.entering_partner_1)
async def handle_partner_name_1(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""
    if len(name.split()) < 2:
        await message.answer(
            "⚠️ Введите <b>Фамилию и Имя</b> партнёра (минимум два слова).",
            parse_mode="HTML"
        )
        return

    await state.update_data(partner_1_name=name, partner_1_status="Указан")
    await message.answer(
        f"✅ Партнёр: <b>{name}</b>\n"
        "⚠️ <i>Вашему партнёру тоже необходимо пройти регистрацию.</i>",
        parse_mode="HTML"
    )
    await _check_second_pair(message, state)


async def _check_second_pair(message: Message, state: FSMContext):
    """Проверяем, есть ли второй парный разряд."""
    data = await state.get_data()
    pairs: list = data.get("pair_queue", [])

    if len(pairs) >= 2:
        pair_name = CATEGORIES[pairs[1]]
        await message.answer(
            f"У вас также выбран парный разряд:\n<b>{pair_name}</b>\n\n"
            "У вас <b>есть партнёр</b> для этого разряда?",
            reply_markup=get_yes_no_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(RegistrationStates.partner_check_2)
    else:
        await finish_registration(message, state)


# ─────────────────────────────────────────────
# Партнёр для 2-го парного разряда
# ─────────────────────────────────────────────
@router.message(RegistrationStates.partner_check_2, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_partner_check_2(message: Message, state: FSMContext):
    data = await state.get_data()
    pairs: list = data.get("pair_queue", [])
    pair_name = CATEGORIES[pairs[1]]

    if message.text == "✅ Да":
        await message.answer(
            f"Укажите <b>ФИО партнёра</b> для разряда:\n<b>{pair_name}</b>",
            reply_markup=remove_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(RegistrationStates.entering_partner_2)
    else:
        await state.update_data(partner_2_status="Ищем партнёра")
        await finish_registration(message, state)


@router.message(RegistrationStates.partner_check_2)
async def handle_partner_check_2_invalid(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, нажмите <b>Да</b> или <b>Нет</b>.",
                         reply_markup=get_yes_no_keyboard(), parse_mode="HTML")


@router.message(RegistrationStates.entering_partner_2)
async def handle_partner_name_2(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""
    if len(name.split()) < 2:
        await message.answer(
            "⚠️ Введите <b>Фамилию и Имя</b> партнёра (минимум два слова).",
            parse_mode="HTML"
        )
        return

    await state.update_data(partner_2_name=name, partner_2_status="Указан")
    await message.answer(
        f"✅ Партнёр: <b>{name}</b>\n"
        "⚠️ <i>Вашему партнёру тоже необходимо пройти регистрацию.</i>",
        parse_mode="HTML"
    )
    await finish_registration(message, state)


# ─────────────────────────────────────────────
# Завершение регистрации
# ─────────────────────────────────────────────
async def finish_registration(message: Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user

    # Сохраняем в Google Sheets
    saved = save_registration(data, user)

    # Сообщение пользователю
    await message.answer(
        "🎾 <b>Благодарим Вас!</b>\n\n"
        "✅ Ваша заявка принята.\n\n"
        "С Вами свяжется директор турнира\n"
        "<b>Денис Соколов</b>.\n\n"
        "Удачи на турнире! 🏆",
        reply_markup=remove_keyboard(),
        parse_mode="HTML"
    )

    # Уведомление организатору
    if saved:
        try:
            bot: Bot = message.bot
            admin_text = build_admin_message(data, user)
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление организатору: {e}")

    await state.clear()
