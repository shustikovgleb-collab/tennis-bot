from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    choosing_category = State()    # Выбор разряда
    confirm_more = State()         # Добавить ещё разряд?
    entering_name = State()        # ФИО
    entering_phone = State()       # Телефон
    entering_email = State()       # Email
    partner_check_1 = State()      # Есть партнёр для 1-го парного разряда?
    entering_partner_1 = State()   # ФИО партнёра для 1-го парного
    partner_check_2 = State()      # Есть партнёр для 2-го парного разряда?
    entering_partner_2 = State()   # ФИО партнёра для 2-го парного
