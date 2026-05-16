import json
import logging
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_CREDENTIALS_JSON, SPREADSHEET_ID

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "Дата и время",
    "Telegram ID",
    "Username",
    "ФИО",
    "Телефон",
    "Email",
    "Разряды",
    "Партнёр (разряд 1)",
    "Статус партнёра 1",
    "Партнёр (разряд 2)",
    "Статус партнёра 2",
]


def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    try:
        sheet = spreadsheet.worksheet("Заявки")
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title="Заявки", rows=1000, cols=20)
        sheet.append_row(HEADERS)
        # Форматируем заголовок жирным
        sheet.format("A1:K1", {"textFormat": {"bold": True}})

    return sheet


def save_registration(data: dict, user) -> bool:
    """
    Сохраняет заявку в Google Sheets.
    data: словарь с данными из FSM
    user: объект User из Telegram
    """
    try:
        sheet = get_sheet()

        from keyboards.reply import CATEGORIES
        categories_str = ", ".join(
            CATEGORIES[k] for k in data.get("categories", [])
        )

        partner1 = data.get("partner_1_name", "")
        partner1_status = data.get("partner_1_status", "")
        partner2 = data.get("partner_2_name", "")
        partner2_status = data.get("partner_2_status", "")

        row = [
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            str(user.id),
            f"@{user.username}" if user.username else "—",
            data.get("name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            categories_str,
            partner1,
            partner1_status,
            partner2,
            partner2_status,
        ]

        sheet.append_row(row)
        logger.info(f"Заявка сохранена: {user.id} — {data.get('name')}")
        return True

    except Exception as e:
        logger.error(f"Ошибка записи в Sheets: {e}")
        return False
