import asyncio
import os
import uuid
import re
import html
import time

from ai import (
    interpret_natal_chart,
    interpret_sun_sign,
    interpret_moon_sign,
    interpret_ascendant,
    interpret_compatibility,
    interpret_month_forecast
)

from database import (
    init_db,
    save_user,
    save_spread,
    get_user_spreads,
    get_users_count,
    get_spreads_count,
    get_recent_spreads,
    get_recent_users,
    get_spread_type_stats,
    get_top_users,
    get_recent_payments,
    get_payments_stats,
    get_sales_funnel,
    get_all_user_ids,
    can_use_free_spread,
    mark_free_spread_used,
    get_balance,
    spend_balance,
    add_balance,
    save_birth_profile,
    save_birth_interpretation,
    get_birth_profile,
    delete_birth_profile
)

from astrology.calculator import zodiac_sign

from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from yookassa import Configuration, Payment

load_dotenv("/opt/bots/astrology_bot/.env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
YOOKASSA_RETURN_URL = os.getenv("YOOKASSA_RETURN_URL")

if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY:
    Configuration.account_id = YOOKASSA_SHOP_ID
    Configuration.secret_key = YOOKASSA_SECRET_KEY

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

session = AiohttpSession(proxy=PROXY_URL)
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

class AdminStates(StatesGroup):
    awaiting_broadcast_text = State()
    awaiting_broadcast_confirm = State()
    awaiting_balance_grant = State()
    awaiting_balance_writeoff = State()


class AstrologyStates(StatesGroup):
    awaiting_natal_chart_owner = State()
    awaiting_natal_chart_saved_choice = State()
    awaiting_natal_chart_data = State()
    awaiting_natal_chart_decode_choice = State()
    awaiting_sun_sign_preview = State()
    awaiting_sun_sign_confirm = State()
    awaiting_sun_sign_date = State()
    awaiting_moon_sign_preview = State()
    awaiting_moon_sign_confirm = State()
    awaiting_moon_sign_data = State()
    awaiting_ascendant_preview = State()
    awaiting_ascendant_confirm = State()
    awaiting_ascendant_data = State()
    awaiting_compatibility_preview = State()
    awaiting_compatibility_confirm = State()
    awaiting_compatibility_data = State()
    awaiting_month_forecast_preview = State()
    awaiting_month_forecast_confirm = State()
    awaiting_month_forecast_date = State()
    awaiting_my_birth_profile = State()




def markdown_bold_to_html(text):
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = text.replace("<b>", "___B_OPEN___").replace("</b>", "___B_CLOSE___")
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = text.replace("___B_OPEN___", "<b>").replace("___B_CLOSE___", "</b>")
    return text

def get_main_keyboard(user_id):
    keyboard = [
        [KeyboardButton(text="⭐ Натальная карта")],
        [KeyboardButton(text="❤️ Совместимость"), KeyboardButton(text="🔮 Прогноз на месяц")],
        [KeyboardButton(text="☀️ Солнечный знак"), KeyboardButton(text="🌙 Лунный знак")],
        [KeyboardButton(text="⬆️ Асцендент"), KeyboardButton(text="🗂 Мои данные")],
        [KeyboardButton(text="💎 Баланс"), KeyboardButton(text="ℹ️ О боте")]
    ]

    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton(text="⚙️ Админка")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="📈 Статистика")],
        [KeyboardButton(text="📜 Последние операции"), KeyboardButton(text="📊 Популярность")],
        [KeyboardButton(text="📣 Рассылка"), KeyboardButton(text="🎁 Акции")],
        [KeyboardButton(text="💰 Платежи")],
        [KeyboardButton(text="📈 Воронка"), KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="➕ Начислить баланс"), KeyboardButton(text="➖ Списать баланс")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)




shop_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🪙 Купить 1 кредит — 99 ₽")],
        [KeyboardButton(text="💎 Купить 5 кредитов — 299 ₽")],
        [KeyboardButton(text="✨ Купить 10 кредитов — 499 ₽")],
        [KeyboardButton(text="👑 Купить 20 кредитов — 799 ₽")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)


broadcast_confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Отправить"), KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True
)


promo_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎁 Акция: 5 кредитов")],
        [KeyboardButton(text="✨ Напомнить про лунный знак")],
        [KeyboardButton(text="❤️ Напомнить про совместимость")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

natal_owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Для меня")],
        [KeyboardButton(text="👥 Для другого человека")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)


natal_saved_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Использовать сохранённую карту")],
        [KeyboardButton(text="✏️ Изменить данные")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

natal_decode_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👀 Пример расшифровки")],
        [KeyboardButton(text="✨ Открыть расшифровку (3 кредита)")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

natal_decode_paid_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📖 Открыть расшифровку")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

natal_data_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

my_data_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⭐ Открыть мою карту")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

sun_preview_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✨ Получить разбор")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

product_confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Да")],
        [KeyboardButton(text="⬅️ Отмена")]
    ],
    resize_keyboard=True
)





async def ask_product_confirm(message: Message, state: FSMContext, confirm_state, title: str, cost: int):
    balance = await get_balance(message.from_user.id)

    if message.from_user.id != ADMIN_ID and balance < cost:
        await state.clear()
        await no_access_message(message)
        await message.answer("Главное меню", reply_markup=get_main_keyboard(message.from_user.id))
        return

    await state.set_state(confirm_state)

    balance_text = "админ-доступ ∞" if message.from_user.id == ADMIN_ID else f"{balance} кредит(ов)"

    await message.answer(
        f"{title}\n\n"
        f"Стоимость разбора: <b>{cost}</b> кредит(а)\n"
        f"Ваш баланс: <b>{balance_text}</b>\n\n"
        f"Списать кредиты и продолжить?",
        parse_mode="HTML",
        reply_markup=product_confirm_keyboard
    )


def parse_birth_datetime_place_strict(text: str) -> dict:
    from datetime import datetime

    parts = [x.strip() for x in text.split(",", 2)]

    if len(parts) != 3:
        raise ValueError("format")

    birth_date, birth_time, birth_place = parts

    if not birth_place or len(birth_place) < 2:
        raise ValueError("place")

    try:
        datetime.strptime(birth_date, "%d.%m.%Y")
    except ValueError:
        raise ValueError("date")

    try:
        datetime.strptime(birth_time, "%H:%M")
    except ValueError:
        raise ValueError("time")

    return {
        "birth_date": birth_date,
        "birth_time": birth_time,
        "birth_place": birth_place,
    }


async def strict_birth_input_error(message: Message):
    await message.answer(
        "⚠️ <b>Неверный формат данных</b>\n\n"
        "Введите строго в формате:\n\n"
        "<b>ДД.ММ.ГГГГ, ЧЧ:ММ, город</b>",
        parse_mode="HTML",
        reply_markup=natal_data_keyboard
    )


async def user_has_spread_access(user_id):
    if user_id == ADMIN_ID:
        return True

    if user_id == ADMIN_ID:
        return True

    if await can_use_free_spread(user_id):
        return True

    if await get_balance(user_id) > 0:
        return True

    return False


async def charge_user_for_spread(user_id):
    if user_id == ADMIN_ID:
        return

    if await can_use_free_spread(user_id):
        await mark_free_spread_used(user_id)
    elif await get_balance(user_id) > 0:
        await spend_balance(user_id)




async def no_access_message(message: Message):
    await message.answer(
        "💎 Бесплатный кредит уже использован.\n\n"
        "Доступные тарифы:\n"
        "• 1 кредит — 99 ₽\n"
        "• 5 кредитов — 299 ₽\n"
        "• 10 кредитов — 499 ₽\n"
        "• 20 кредитов — 799 ₽\n\n"
        "Пополните баланс и возвращайтесь за новым кредитом ✨"
    )


@dp.message(CommandStart())
async def start(message: Message):
    await save_user(message.from_user)

    await message.answer(
        "✨ <b>Астронум</b>\n\n"
        "AI-астрологический бот для самопознания, отношений и персональных прогнозов.\n\n"
        "⭐ <b>Натальная карта</b> — главный продукт Астронума: подробная карта личности по дате, времени и месту рождения.\n\n"
        "<b>Также доступны:</b>\n"
        "❤️ Совместимость\n"
        "🔮 Прогноз на месяц\n"
        "☀️ Солнечный знак\n"
        "🌙 Лунный знак\n"
        "⬆️ Асцендент\n\n"
        "💎 Новым пользователям доступен 1 бесплатный кредит.\n\n"
        "Выберите интересующий раздел ниже 👇",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


@dp.message(F.text.startswith("/give"))
async def admin_give_balance(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    parts = message.text.split()

    if len(parts) != 3:
        await message.answer(
            "Формат команды:\n"
            "/give USER_ID COUNT\n\n"
            "Пример:\n"
            "/give 185955220 5"
        )
        return

    try:
        target_user_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        await message.answer("USER_ID и COUNT должны быть числами.")
        return

    if amount <= 0:
        await message.answer("COUNT должен быть больше 0.")
        return

    await add_balance(target_user_id, amount)

    await message.answer(
        f"✅ Начислено {amount} кредит(ов).\n"
        f"Пользователь: {target_user_id}"
    )

    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=(
                f"💎 Оплата успешно получена!\n\n"
                f"На баланс зачислено: {amount} кредит(ов).\n\n"
                f"✨ Выберите интересующий раздел в меню."
            )
        )
    except Exception:
        pass



@dp.message(F.text == "⬅️ Назад")
@dp.message(F.text == "↩️ Назад")
@dp.message(F.text == "⬅ Назад")
async def global_back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Главное меню",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


@dp.message(F.text == "🗂 Мои данные")
async def my_birth_profile(message: Message, state: FSMContext):
    await safe_delete_current_message(message)
    await save_user(message.from_user)

    profile = await get_birth_profile(message.from_user.id)

    if not profile:
        await state.set_state(AstrologyStates.awaiting_my_birth_profile)
        await message.answer(
            "🗂 <b>Моя карта</b>\n\n"
            "Сохранённой карты пока нет.\n\n"
            "Введите данные в формате:\n\n"
            "<b>ДД.ММ.ГГГГ, ЧЧ:ММ, город</b>",
            parse_mode="HTML",
            reply_markup=natal_data_keyboard
        )
        return

    await message.answer(
        "🗂 <b>Моя карта</b>\n\n"
        f"📅 Дата: <b>{profile['birth_date']}</b>\n"
        f"🕒 Время: <b>{profile['birth_time']}</b>\n"
        f"📍 Место: <b>{profile['birth_place']}</b>\n\n"
        "Чтобы обновить данные, просто снова нажмите «🗂 Мои данные» после удаления старой записи.\n\n"
        "Команда для удаления:\n"
        "<b>/delete_my_data</b>",
        parse_mode="HTML",
        reply_markup=my_data_keyboard
    )



@dp.message(F.text == "⭐ Открыть мою карту")
async def open_my_saved_chart(message: Message, state: FSMContext):
    await safe_delete_current_message(message)
    await save_user(message.from_user)

    profile = await get_birth_profile(message.from_user.id)

    if not profile:
        await message.answer(
            "🗂 Сохранённых данных пока нет. Нажмите «🗂 Мои данные» и введите дату, время и место рождения.",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    data = {
        "birth_date": profile["birth_date"],
        "birth_time": profile["birth_time"],
        "birth_place": profile["birth_place"],
    }

    if profile["chart_json"]:
        import json
        data["chart"] = json.loads(profile["chart_json"])

    input_text = f"{data['birth_date']}, {data['birth_time']}, {data['birth_place']}"
    await send_natal_chart_result(message, state, data, input_text, save_profile=False)


@dp.message(Command("delete_my_data"))
async def delete_my_data(message: Message):
    await delete_birth_profile(message.from_user.id)
    await message.answer("🗑 Сохранённая карта удалена.")


@dp.message(F.text == "⬅️ Назад")
async def universal_back_from_my_data(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is not None:
        return

    await message.answer(
        "Главное меню",
        reply_markup=get_main_keyboard(message.from_user.id)
    )





@dp.message(AstrologyStates.awaiting_my_birth_profile, F.text == "⬅️ Назад")
async def my_birth_profile_back(message: Message, state: FSMContext):
    await safe_delete_current_message(message)
    await state.clear()
    await message.answer(
        "Главное меню",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


@dp.message(AstrologyStates.awaiting_my_birth_profile)
async def process_my_birth_profile(message: Message, state: FSMContext):
    try:
        parsed = parse_birth_datetime_place_strict(message.text)
    except ValueError:
        await strict_birth_input_error(message)
        return

    from astrology.real_chart import calculate_real_chart

    progress_msg = await message.answer("⭐ Рассчитываю и сохраняю вашу карту...")

    try:
        chart = calculate_real_chart(parsed["birth_date"], parsed["birth_time"], parsed["birth_place"])
        await save_birth_profile(
            user_id=message.from_user.id,
            birth_date=parsed["birth_date"],
            birth_time=parsed["birth_time"],
            birth_place=parsed["birth_place"],
            chart=chart
        )
    except Exception as e:
        await message.answer(f"Не удалось сохранить карту. Ошибка: {e}")
        return
    finally:
        try:
            await progress_msg.delete()
        except Exception:
            pass

    await state.clear()

    await message.answer(
        "✅ <b>Карта сохранена</b>\n\n"
        f"📅 Дата: <b>{parsed['birth_date']}</b>\n"
        f"🕒 Время: <b>{parsed['birth_time']}</b>\n"
        f"📍 Место: <b>{parsed['birth_place']}</b>\n\n"
        "Теперь вы можете открыть сохранённую карту без повторного расчёта.",
        parse_mode="HTML",
        reply_markup=my_data_keyboard
    )


@dp.message(F.text == "💎 Баланс")
async def balance(message: Message):
    await safe_delete_current_message(message)
    await save_user(message.from_user)

    balance_count = await get_balance(message.from_user.id)

    await message.answer(
        f"💎 <b>Баланс кредитов</b>\n\n"
        f"На счету: <b>{balance_count}</b> кредит(ов)\n\n"
        f"<b>Стоимость разборов:</b>\n"
        f"⭐ Натальная карта — <b>3 кредита</b>\n"
        f"❤️ Совместимость — <b>2 кредита</b>\n"
        f"🔮 Прогноз на месяц — <b>2 кредита</b>\n"
        f"☀️ Солнечный знак — <b>1 кредит</b>\n"
        f"🌙 Лунный знак — <b>1 кредит</b>\n"
        f"⬆️ Асцендент — <b>1 кредит</b>\n\n"
        f"Кредиты можно использовать в любом разделе.\n"
        f"Для новых пользователей доступен 1 бесплатный кредит.",
        reply_markup=shop_keyboard,
        parse_mode="HTML"
    )




def create_yookassa_payment(user_id: int, count: int, amount_rub: int):
    payment = Payment.create({
        "amount": {
            "value": f"{amount_rub}.00",
            "currency": "RUB"
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": YOOKASSA_RETURN_URL
        },
        "description": f"Астронум: {count} кредит(ов)",
        "metadata": {
            "user_id": str(user_id),
            "count": str(count)
        }
    }, str(uuid.uuid4()))

    return payment


@dp.message(F.text.contains("Купить 1 кредит"))
async def buy_one_spread(message: Message):
    await safe_delete_current_message(message)
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        await message.answer("Оплата временно недоступна. Не найдены данные ЮKassa.")
        return

    try:
        payment = create_yookassa_payment(message.from_user.id, 1, 99)
        url = payment.confirmation.confirmation_url
    except Exception as e:
        await message.answer(f"Не удалось создать платёж. Ошибка: {e}")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к оплате", url=url)]
        ]
    )

    await message.answer(
        "🪙 1 кредит\n\n"
        "Стоимость: 99 ₽\n\n"
        "Нажмите кнопку ниже и выберите удобный способ оплаты: карта, СБП, SberPay или другой доступный способ.",
        reply_markup=keyboard
    )


@dp.message(F.text.contains("Купить 5 кредитов"))
async def buy_five_spreads(message: Message):
    await safe_delete_current_message(message)
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        await message.answer("Оплата временно недоступна. Не найдены данные ЮKassa.")
        return

    try:
        payment = create_yookassa_payment(message.from_user.id, 5, 299)
        url = payment.confirmation.confirmation_url
    except Exception as e:
        await message.answer(f"Не удалось создать платёж. Ошибка: {e}")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к оплате", url=url)]
        ]
    )

    await message.answer(
        "💎 5 кредитов\n\n"
        "Стоимость: 299 ₽\n\n"
        "Нажмите кнопку ниже и выберите удобный способ оплаты: карта, СБП, SberPay или другой доступный способ.",
        reply_markup=keyboard
    )




@dp.message(F.text.contains("Купить 10 кредитов"))
async def buy_ten_spreads(message: Message):
    await safe_delete_current_message(message)
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        await message.answer("Оплата временно недоступна. Не найдены данные ЮKassa.")
        return

    try:
        payment = create_yookassa_payment(message.from_user.id, 10, 499)
        url = payment.confirmation.confirmation_url
    except Exception as e:
        await message.answer(f"Не удалось создать платёж. Ошибка: {e}")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к оплате", url=url)]
        ]
    )

    await message.answer(
        "✨ 10 кредитов\n\n"
        "Стоимость: 499 ₽\n\n"
        "Выгодный пакет для нескольких вопросов: отношения, работа, деньги и личные ситуации.\n\n"
        "Нажмите кнопку ниже и выберите удобный способ оплаты.",
        reply_markup=keyboard
    )


@dp.message(F.text.contains("Купить 20 кредитов"))
async def buy_twenty_spreads(message: Message):
    await safe_delete_current_message(message)
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        await message.answer("Оплата временно недоступна. Не найдены данные ЮKassa.")
        return

    try:
        payment = create_yookassa_payment(message.from_user.id, 20, 799)
        url = payment.confirmation.confirmation_url
    except Exception as e:
        await message.answer(f"Не удалось создать платёж. Ошибка: {e}")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к оплате", url=url)]
        ]
    )

    await message.answer(
        "👑 20 кредитов\n\n"
        "Стоимость: 799 ₽\n\n"
        "Самый выгодный пакет для тех, кто планирует несколько кредитов.\n\n"
        "Нажмите кнопку ниже и выберите удобный способ оплаты.",
        reply_markup=keyboard
    )






async def safe_delete_current_message(message: Message):
    try:
        await message.delete()
    except Exception:
        pass

async def cleanup_natal_messages(message: Message, state: FSMContext, delete_current: bool = True):
    data = await state.get_data()
    ids = data.get("natal_cleanup_message_ids", [])

    for message_id in ids:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message_id)
        except Exception:
            pass

    if delete_current:
        try:
            await message.delete()
        except Exception:
            pass

    await state.update_data(natal_cleanup_message_ids=[])


async def remember_natal_message(state: FSMContext, sent_message: Message):
    data = await state.get_data()
    ids = data.get("natal_cleanup_message_ids", [])
    ids.append(sent_message.message_id)
    await state.update_data(natal_cleanup_message_ids=ids)





def data_hash(data: dict) -> str:
    import hashlib
    import json
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]

async def send_natal_card_image(message: Message, chart: dict, user_id: int):
    from astrology.real_chart import generate_chart_png
    from astrology.chart_html_renderer import build_natal_card_image

    os.makedirs("/opt/bots/astrology_bot/data/charts", exist_ok=True)

    ts = int(time.time())
    cache_dir = "/opt/bots/astrology_bot/data/cache/cards"
    os.makedirs(cache_dir, exist_ok=True)

    cache_key = f"{user_id}_{data_hash(chart)}"
    card_path = f"{cache_dir}/natal_card_{cache_key}.png"
    wheel_path = f"/opt/bots/astrology_bot/data/charts/wheel_{user_id}_{ts}.png"

    await bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")

    if not os.path.exists(card_path):
        generate_chart_png(chart, wheel_path)
        await asyncio.to_thread(build_natal_card_image, chart, wheel_path, card_path)

    try:
        await message.answer_photo(photo=FSInputFile(card_path))
    finally:
        try:
            os.remove(wheel_path)
        except Exception:
            pass

async def send_natal_chart_result(message: Message, state: FSMContext, data: dict, input_text: str, save_profile: bool = False):
    user_id = message.from_user.id

    existing_chart = data.get("chart")

    progress_msg = None
    if existing_chart:
        progress_msg = await message.answer(
            "⭐ Открываю сохранённую карту...",
            reply_markup=get_main_keyboard(user_id)
        )
    else:
        progress_msg = await message.answer(
            "⭐ Рассчитываю реальные положения планет...",
            reply_markup=get_main_keyboard(user_id)
        )

    try:
        from astrology.real_chart import calculate_real_chart

        chart = existing_chart
        if not chart:
            await bot.send_chat_action(chat_id=message.chat.id, action="typing")
            await asyncio.sleep(0.2)
            chart = await asyncio.to_thread(
                calculate_real_chart,
                data["birth_date"],
                data["birth_time"],
                data["birth_place"]
            )

        if save_profile:
            await save_birth_profile(
                user_id=user_id,
                birth_date=data["birth_date"],
                birth_time=data["birth_time"],
                birth_place=data["birth_place"],
                chart=chart
            )

        try:
            await progress_msg.delete()
        except Exception:
            pass

        planets = {pl["name"]: pl for pl in chart["planets"]}
        sun = planets.get("Солнце")
        moon = planets.get("Луна")
        asc = chart["ascendant"]
        mc = chart["mc"]

        planet_lines = (
            "☉ Солнце ............. 🔒\n"
            "☽ Луна ............... 🔒\n"
            "☿ Меркурий ........... 🔒\n"
            "♀ Венера ............. 🔒\n"
            "♂ Марс ............... 🔒\n"
            "♃ Юпитер ............. 🔒\n"
            "♄ Сатурн ............. 🔒\n"
        )

        aspects_count = len(chart.get("aspects", []))

        house_lines = (
            "⬆ Асцендент .......... 🔒\n"
            "MC ................... 🔒\n"
            "🏠 Дома .............. 🔒\n"
            "✨ Аспекты ........... 🔒\n"
            "💎 Доминирующая планета 🔒\n"
        )

        profile = await get_birth_profile(user_id)
        saved_interpretation = None

        is_own_saved_chart = (
            profile
            and profile["birth_date"] == data["birth_date"]
            and profile["birth_time"] == data["birth_time"]
            and profile["birth_place"] == data["birth_place"]
        )

        if is_own_saved_chart and profile["natal_interpretation"]:
            saved_interpretation = profile["natal_interpretation"]

        await state.update_data(
            natal_decode_data=data,
            natal_decode_chart=chart,
            natal_decode_input=input_text,
            natal_saved_interpretation=saved_interpretation
        )
        await state.set_state(AstrologyStates.awaiting_natal_chart_decode_choice)

        saved_text = "✅ Данные сохранены в «🗂 Мои данные».\n\n" if save_profile else ""
        decode_text = (
            "✅ <b>Полная расшифровка уже куплена</b>\n\n"
            "Нажмите кнопку ниже, чтобы открыть её снова."
            if saved_interpretation else
""
        )
        decode_markup = natal_decode_paid_keyboard if saved_interpretation else natal_decode_keyboard

        await message.answer(
            "⭐ <b>Натальная карта построена</b>\n\n"
            f"{saved_text}"
            f"📅 Дата: <b>{data['birth_date']}</b>\n"
            f"🕒 Время: <b>{data['birth_time']}</b>\n"
            f"📍 Место: <b>{data['birth_place']}</b>\n\n"
            "🔐 <b>Ваша карта рассчитана</b>\n\n"
            f"{planet_lines}\n"
            f"{house_lines}\n"
            "━━━━━━━━━━━━━━\n\n"
            "🔓 <b>Открыть полную расшифровку — 3 кредита</b>\n\n"
            "• психологический портрет\n"
            "• отношения и любовь\n"
            "• карьера и деньги\n"
            "• предназначение\n"
            "• скрытые таланты\n\n"
            f"{decode_text}",
            parse_mode="HTML",
            reply_markup=decode_markup
        )

    except Exception as e:
        await message.answer(f"Не удалось построить карту. Ошибка: {e}", reply_markup=get_main_keyboard(user_id))
        await state.clear()
        return


@dp.message(F.text == "⭐ Натальная карта")
async def astrology_natal_chart(message: Message, state: FSMContext):
    await save_user(message.from_user)

    await state.set_state(AstrologyStates.awaiting_natal_chart_owner)

    sent = await message.answer(
        "⭐ <b>Натальная карта</b>\n\n"
        "Для кого построить карту?",
        parse_mode="HTML",
        reply_markup=natal_owner_keyboard
    )
    await remember_natal_message(state, sent)


@dp.message(AstrologyStates.awaiting_natal_chart_owner, F.text == "👤 Для меня")
async def natal_chart_for_me(message: Message, state: FSMContext):
    await cleanup_natal_messages(message, state)
    profile = await get_birth_profile(message.from_user.id)

    if profile:
        data = {
            "birth_date": profile["birth_date"],
            "birth_time": profile["birth_time"],
            "birth_place": profile["birth_place"],
        }

        if profile["chart_json"]:
            import json
            data["chart"] = json.loads(profile["chart_json"])

        input_text = f"{data['birth_date']}, {data['birth_time']}, {data['birth_place']}"

        if data.get("chart"):
            sent = await message.answer(
                "✅ <b>У вас уже есть готовая натальная карта</b>\n\n"
                f"📅 Дата: <b>{data['birth_date']}</b>\n"
                f"🕒 Время: <b>{data['birth_time']}</b>\n"
                f"📍 Место: <b>{data['birth_place']}</b>\n\n"
                "Открываю сохранённую карту без повторного расчёта.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard(message.from_user.id)
            )
            await remember_natal_message(state, sent)
        else:
            await message.answer(
                "🗂 <b>Использую сохранённые данные</b>\n\n"
                f"📅 Дата: <b>{data['birth_date']}</b>\n"
                f"🕒 Время: <b>{data['birth_time']}</b>\n"
                f"📍 Место: <b>{data['birth_place']}</b>\n\n"
                "Рассчитываю карту впервые.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard(message.from_user.id)
            )

        await send_natal_chart_result(message, state, data, input_text, save_profile=not bool(data.get("chart")))

        try:
            await sent.delete()
        except Exception:
            pass

        return

    await state.update_data(natal_save_profile=True)
    await state.set_state(AstrologyStates.awaiting_natal_chart_data)

    sent = await message.answer(
        "👤 <b>Натальная карта для меня</b>\n\n"
        "Введите данные в формате:\n\n"
        "<b>ДД.ММ.ГГГГ, ЧЧ:ММ, город</b>",
        parse_mode="HTML",
        reply_markup=natal_data_keyboard
    )
    await remember_natal_message(state, sent)


@dp.message(AstrologyStates.awaiting_natal_chart_owner, F.text == "👥 Для другого человека")
async def natal_chart_for_other(message: Message, state: FSMContext):
    await cleanup_natal_messages(message, state)
    await state.update_data(natal_save_profile=False)
    await state.set_state(AstrologyStates.awaiting_natal_chart_data)

    sent = await message.answer(
        "👥 <b>Натальная карта для другого человека</b>\n\n"
        "Введите данные в формате:\n\n"
        "<b>ДД.ММ.ГГГГ, ЧЧ:ММ, город</b>",
        parse_mode="HTML",
        reply_markup=natal_data_keyboard
    )
    await remember_natal_message(state, sent)



@dp.message(AstrologyStates.awaiting_natal_chart_owner, F.text == "⬅️ Назад")
@dp.message(AstrologyStates.awaiting_natal_chart_saved_choice, F.text == "⬅️ Назад")
@dp.message(AstrologyStates.awaiting_natal_chart_decode_choice, F.text == "⬅️ Назад")
async def natal_chart_back_to_main(message: Message, state: FSMContext):
    await cleanup_natal_messages(message, state)
    await state.clear()

    await message.answer(
        "Главное меню",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


@dp.message(AstrologyStates.awaiting_natal_chart_data, F.text == "⬅️ Назад")
async def natal_chart_data_back_to_choice(message: Message, state: FSMContext):
    await cleanup_natal_messages(message, state)

    await state.set_state(AstrologyStates.awaiting_natal_chart_owner)

    sent = await message.answer(
        "⭐ <b>Натальная карта</b>\n\n"
        "Для кого построить карту?",
        parse_mode="HTML",
        reply_markup=natal_owner_keyboard
    )
    await remember_natal_message(state, sent)


@dp.message(AstrologyStates.awaiting_natal_chart_owner)
@dp.message(AstrologyStates.awaiting_natal_chart_saved_choice)
async def natal_chart_choice_fallback(message: Message):
    await message.answer("Выберите вариант кнопкой ниже.")

@dp.message(F.text == "☀️ Солнечный знак")
async def astrology_sun_sign(message: Message, state: FSMContext):
    await save_user(message.from_user)
    balance = await get_balance(message.from_user.id)

    await state.set_state(AstrologyStates.awaiting_sun_sign_preview)

    await message.answer(
        "☀️ <b>Солнечный знак</b>\n\n"
        "Ваш базовый архетип личности.\n\n"
        "<b>Что входит:</b>\n"
        "• Главные черты характера\n"
        "• Сильные стороны\n"
        "• Возможные слабости\n"
        "• Поведение в отношениях\n"
        "• Рекомендации\n\n"
        "💰 <b>Стоимость:</b> 1 кредит\n"
        f"💎 <b>Ваш баланс:</b> {balance} кредит(ов)",
        parse_mode="HTML",
        reply_markup=sun_preview_keyboard
    )


@dp.message(AstrologyStates.awaiting_sun_sign_preview, F.text == "⬅️ Назад")
async def sun_preview_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=get_main_keyboard(message.from_user.id))


@dp.message(AstrologyStates.awaiting_sun_sign_preview, F.text == "✨ Получить разбор")
async def sun_preview_get_ask_confirm(message: Message, state: FSMContext):
    await ask_product_confirm(message, state, AstrologyStates.awaiting_sun_sign_confirm, "☀️ <b>Солнечный знак</b>", 1)


@dp.message(AstrologyStates.awaiting_sun_sign_confirm, F.text == "✅ Да")
async def sun_preview_get(message: Message, state: FSMContext):
    if not await user_has_spread_access(message.from_user.id):
        await state.clear()
        await no_access_message(message)
        return


    profile = await get_birth_profile(message.from_user.id)

    if profile:
        try:
            data = zodiac_sign(profile["birth_date"])
        except Exception:
            await message.answer("⚠️ В сохранённой карте некорректная дата. Обновите данные через «🗂 Мои данные».")
            return

        await message.answer("☀️ Использую сохранённую карту и готовлю солнечный знак...")

        try:
            await bot.send_chat_action(chat_id=message.chat.id, action="typing")
            interpretation = await interpret_sun_sign(data)
        except Exception as e:
            await message.answer(f"Не удалось подготовить кредит. Ошибка: {e}")
            return

        await save_spread(message.from_user.id, "Солнечный знак", profile["birth_date"], profile["birth_date"], interpretation)
        await charge_user_for_spread(message.from_user.id)

        await message.answer(
            f"☀️ <b>Солнечный знак</b>\n\n"
            f"📅 Дата рождения: <b>{data['birth_date']}</b>\n"
            f"♈ Знак: <b>{data['sign']}</b>\n\n"
            f"{markdown_bold_to_html(interpretation)}",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        await state.clear()
        return

    await state.set_state(AstrologyStates.awaiting_sun_sign_date)

    await message.answer(
        "☀️ <b>Солнечный знак</b>\n\n"
        "Введите дату рождения в формате:\n\n"
        "<b>ДД.ММ.ГГГГ</b>",
        parse_mode="HTML"
    )



@dp.message(F.text == "🌙 Лунный знак")
async def astrology_moon_sign(message: Message, state: FSMContext):
    await save_user(message.from_user)
    balance = await get_balance(message.from_user.id)

    await state.set_state(AstrologyStates.awaiting_moon_sign_preview)

    await message.answer(
        "🌙 <b>Лунный знак</b>\n\n"
        "Ваш внутренний эмоциональный мир.\n\n"
        "<b>Что входит:</b>\n"
        "• Эмоции и чувства\n"
        "• Реакции на стресс\n"
        "• Потребности в отношениях\n"
        "• Скрытые стороны личности\n"
        "• Рекомендации\n\n"
        "💰 <b>Стоимость:</b> 1 кредит\n"
        f"💎 <b>Ваш баланс:</b> {balance} кредит(ов)",
        parse_mode="HTML",
        reply_markup=sun_preview_keyboard
    )


@dp.message(AstrologyStates.awaiting_moon_sign_preview, F.text == "⬅️ Назад")
async def moon_preview_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=get_main_keyboard(message.from_user.id))


@dp.message(AstrologyStates.awaiting_moon_sign_preview, F.text == "✨ Получить разбор")
async def moon_preview_get_ask_confirm(message: Message, state: FSMContext):
    await ask_product_confirm(message, state, AstrologyStates.awaiting_moon_sign_confirm, "🌙 <b>Лунный знак</b>", 1)


@dp.message(AstrologyStates.awaiting_moon_sign_confirm, F.text == "✅ Да")
async def moon_preview_get(message: Message, state: FSMContext):
    if not await user_has_spread_access(message.from_user.id):
        await state.clear()
        await no_access_message(message)
        return


    profile = await get_birth_profile(message.from_user.id)

    if profile:
        data = {"birth_date": profile["birth_date"], "birth_time": profile["birth_time"]}

        await message.answer("🌙 Использую сохранённую карту и готовлю лунный знак...")

        try:
            await bot.send_chat_action(chat_id=message.chat.id, action="typing")
            interpretation = await interpret_moon_sign(data)
        except Exception as e:
            await message.answer(f"Не удалось подготовить кредит. Ошибка: {e}")
            return

        await save_spread(message.from_user.id, "Лунный знак", f"{data['birth_date']}, {data['birth_time']}", f"{data['birth_date']}, {data['birth_time']}", interpretation)
        await charge_user_for_spread(message.from_user.id)

        await message.answer(
            f"🌙 <b>Лунный знак</b>\n\n"
            f"📅 Дата: <b>{data['birth_date']}</b>\n"
            f"🕒 Время: <b>{data['birth_time']}</b>\n\n"
            f"{markdown_bold_to_html(interpretation)}",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        await state.clear()
        return

    await state.set_state(AstrologyStates.awaiting_moon_sign_data)

    await message.answer(
        "🌙 <b>Лунный знак</b>\n\n"
        "Введите данные в формате:\n\n"
        "<b>ДД.ММ.ГГГГ, ЧЧ:ММ</b>",
        parse_mode="HTML"
    )



@dp.message(F.text == "⬆️ Асцендент")
async def astrology_ascendant(message: Message, state: FSMContext):
    await save_user(message.from_user)
    balance = await get_balance(message.from_user.id)

    await state.set_state(AstrologyStates.awaiting_ascendant_preview)

    await message.answer(
        "⬆️ <b>Асцендент</b>\n\n"
        "Первое впечатление, которое вы производите на людей.\n\n"
        "<b>Что входит:</b>\n"
        "• Ваш внешний образ\n"
        "• Манера общения\n"
        "• Как вас воспринимают окружающие\n"
        "• Сильные стороны проявления\n"
        "• Рекомендации\n\n"
        "💰 <b>Стоимость:</b> 1 кредит\n"
        f"💎 <b>Ваш баланс:</b> {balance} кредит(ов)",
        parse_mode="HTML",
        reply_markup=sun_preview_keyboard
    )


@dp.message(AstrologyStates.awaiting_ascendant_preview, F.text == "⬅️ Назад")
async def asc_preview_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=get_main_keyboard(message.from_user.id))


@dp.message(AstrologyStates.awaiting_ascendant_preview, F.text == "✨ Получить разбор")
async def asc_preview_get_ask_confirm(message: Message, state: FSMContext):
    await ask_product_confirm(message, state, AstrologyStates.awaiting_ascendant_confirm, "⬆️ <b>Асцендент</b>", 1)


@dp.message(AstrologyStates.awaiting_ascendant_confirm, F.text == "✅ Да")
async def asc_preview_get(message: Message, state: FSMContext):
    if not await user_has_spread_access(message.from_user.id):
        await state.clear()
        await no_access_message(message)
        return


    profile = await get_birth_profile(message.from_user.id)

    if profile:
        data = {"birth_date": profile["birth_date"], "birth_time": profile["birth_time"], "birth_place": profile["birth_place"]}

        await message.answer("⬆️ Использую сохранённую карту и готовлю асцендент...")

        try:
            await bot.send_chat_action(chat_id=message.chat.id, action="typing")
            interpretation = await interpret_ascendant(data)
        except Exception as e:
            await message.answer(f"Не удалось подготовить кредит. Ошибка: {e}")
            return

        input_text = f"{data['birth_date']}, {data['birth_time']}, {data['birth_place']}"
        await save_spread(message.from_user.id, "Асцендент", input_text, input_text, interpretation)
        await charge_user_for_spread(message.from_user.id)

        await message.answer(
            f"⬆️ <b>Асцендент</b>\n\n"
            f"📅 Дата: <b>{data['birth_date']}</b>\n"
            f"🕒 Время: <b>{data['birth_time']}</b>\n"
            f"📍 Место: <b>{data['birth_place']}</b>\n\n"
            f"{markdown_bold_to_html(interpretation)}",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        await state.clear()
        return

    await state.set_state(AstrologyStates.awaiting_ascendant_data)

    await message.answer(
        "⬆️ <b>Асцендент</b>\n\n"
        "Введите данные в формате:\n\n"
        "<b>ДД.ММ.ГГГГ, ЧЧ:ММ, город</b>",
        parse_mode="HTML"
    )


@dp.message(AstrologyStates.awaiting_sun_sign_confirm, F.text == "⬅️ Отмена")
@dp.message(AstrologyStates.awaiting_moon_sign_confirm, F.text == "⬅️ Отмена")
@dp.message(AstrologyStates.awaiting_ascendant_confirm, F.text == "⬅️ Отмена")
async def small_product_confirm_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=get_main_keyboard(message.from_user.id))


@dp.message(F.text == "❤️ Совместимость")
async def astrology_compatibility(message: Message, state: FSMContext):
    await save_user(message.from_user)
    balance = await get_balance(message.from_user.id)

    await state.set_state(AstrologyStates.awaiting_compatibility_preview)

    await message.answer(
        "❤️ <b>Совместимость</b>\n\n"
        "Астрологический анализ отношений двух людей.\n\n"
        "<b>Что входит:</b>\n"
        "• Эмоциональная совместимость\n"
        "• Сильные стороны союза\n"
        "• Возможные конфликты\n"
        "• Потенциал отношений\n"
        "• Рекомендации\n\n"
        "💰 <b>Стоимость:</b> 2 кредита\n"
        f"💎 <b>Ваш баланс:</b> {balance} кредит(ов)",
        parse_mode="HTML",
        reply_markup=sun_preview_keyboard
    )


@dp.message(AstrologyStates.awaiting_compatibility_preview, F.text == "⬅️ Назад")
async def compatibility_preview_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=get_main_keyboard(message.from_user.id))


@dp.message(AstrologyStates.awaiting_compatibility_preview, F.text == "✨ Получить разбор")
async def compatibility_preview_get_ask_confirm(message: Message, state: FSMContext):
    await ask_product_confirm(message, state, AstrologyStates.awaiting_compatibility_confirm, "❤️ <b>Совместимость</b>", 2)


@dp.message(AstrologyStates.awaiting_compatibility_confirm, F.text == "✅ Да")
async def compatibility_preview_get(message: Message, state: FSMContext):
    balance = await get_balance(message.from_user.id)
    if message.from_user.id != ADMIN_ID and balance < 2:
        await state.clear()
        await no_access_message(message)
        return


    await state.set_state(AstrologyStates.awaiting_compatibility_data)

    await message.answer(
        "❤️ <b>Совместимость</b>\n\n"
        "Введите данные двух людей в формате:\n\n"
        "<b>ДД.ММ.ГГГГ, город</b>\n"
        "<b>ДД.ММ.ГГГГ, город</b>",
        parse_mode="HTML"
    )



@dp.message(F.text == "🔮 Прогноз на месяц")
async def astrology_month_forecast(message: Message, state: FSMContext):
    await save_user(message.from_user)
    balance = await get_balance(message.from_user.id)

    await state.set_state(AstrologyStates.awaiting_month_forecast_preview)

    await message.answer(
        "🔮 <b>Прогноз на месяц</b>\n\n"
        "Персональный астрологический прогноз на ближайшие 30 дней.\n\n"
        "<b>Что входит:</b>\n"
        "• Общий фон месяца\n"
        "• Любовь и отношения\n"
        "• Работа и финансы\n"
        "• Благоприятные периоды\n"
        "• Рекомендации\n\n"
        "💰 <b>Стоимость:</b> 2 кредита\n"
        f"💎 <b>Ваш баланс:</b> {balance} кредит(ов)",
        parse_mode="HTML",
        reply_markup=sun_preview_keyboard
    )


@dp.message(AstrologyStates.awaiting_month_forecast_preview, F.text == "⬅️ Назад")
async def month_forecast_preview_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=get_main_keyboard(message.from_user.id))


@dp.message(AstrologyStates.awaiting_month_forecast_preview, F.text == "✨ Получить разбор")
async def month_forecast_preview_get_ask_confirm(message: Message, state: FSMContext):
    await ask_product_confirm(message, state, AstrologyStates.awaiting_month_forecast_confirm, "🔮 <b>Прогноз на месяц</b>", 2)


@dp.message(AstrologyStates.awaiting_month_forecast_confirm, F.text == "✅ Да")
async def month_forecast_preview_get(message: Message, state: FSMContext):
    balance = await get_balance(message.from_user.id)
    if message.from_user.id != ADMIN_ID and balance < 2:
        await state.clear()
        await no_access_message(message)
        return


    profile = await get_birth_profile(message.from_user.id)

    if profile:
        try:
            data = zodiac_sign(profile["birth_date"])
        except Exception:
            await message.answer("⚠️ В сохранённой карте некорректная дата. Обновите данные через «🗂 Мои данные».")
            return

        await message.answer("🔮 Использую сохранённую карту и готовлю прогноз на месяц...")

        try:
            await bot.send_chat_action(chat_id=message.chat.id, action="typing")
            interpretation = await interpret_month_forecast(data)
        except Exception as e:
            await message.answer(f"Не удалось подготовить прогноз. Ошибка: {e}")
            return

        await save_spread(message.from_user.id, "Прогноз на месяц", data["birth_date"], data["birth_date"], interpretation)
        await charge_user_for_spread(message.from_user.id)
        await charge_user_for_spread(message.from_user.id)

        await message.answer(
            f"🔮 <b>Прогноз на месяц</b>\n\n"
            f"📅 Дата рождения: <b>{data['birth_date']}</b>\n"
            f"♈ Знак: <b>{data['sign']}</b>\n\n"
            f"{markdown_bold_to_html(interpretation)}",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        await state.clear()
        return

    await state.set_state(AstrologyStates.awaiting_month_forecast_date)

    await message.answer(
        "🔮 <b>Прогноз на месяц</b>\n\n"
        "Введите дату рождения в формате:\n\n"
        "<b>ДД.ММ.ГГГГ</b>",
        parse_mode="HTML"
    )


@dp.message(F.text == "📜 История")
async def history(message: Message):
    await safe_delete_current_message(message)
    await save_user(message.from_user)

    spreads = await get_user_spreads(message.from_user.id, limit=5)

    if not spreads:
        await message.answer(
            "📜 История пока пустая.\n\n"
            "Сделайте кредит, и он появится здесь."
        )
        return

    text = "📜 <b>История операций</b>\n\n"

    emoji_map = {
        "Натальная карта": "🔢",
        "Солнечный знак": "🛣",
        "Совместимость": "❤️",
        "Лунный знак": "✨",
        "Асцендент": "🎯",
    }

    for idx, spread in enumerate(spreads, start=1):
        spread_type = spread.get("spread_type", "Разбор")
        question = spread.get("question") or spread.get("input_data") or "—"
        emoji = emoji_map.get(spread_type, "🔢")

        text += (
            f"{idx}. {emoji} <b>{spread_type}</b>\n"
            f"📅 {question}\n\n"
        )

    await message.answer(text, parse_mode="HTML")


@dp.message(AstrologyStates.awaiting_sun_sign_confirm, F.text == "⬅️ Отмена")
@dp.message(AstrologyStates.awaiting_moon_sign_confirm, F.text == "⬅️ Отмена")
@dp.message(AstrologyStates.awaiting_ascendant_confirm, F.text == "⬅️ Отмена")
@dp.message(AstrologyStates.awaiting_compatibility_confirm, F.text == "⬅️ Отмена")
@dp.message(AstrologyStates.awaiting_month_forecast_confirm, F.text == "⬅️ Отмена")
async def product_confirm_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=get_main_keyboard(message.from_user.id))


@dp.message(F.text == "ℹ️ О боте")
async def about(message: Message):
    await safe_delete_current_message(message)
    await message.answer(
        "ℹ️ <b>О боте</b>\n\n"
        "✨ <b>Астронум</b> — AI-астрологический бот по западной астрологии.\n\n"
        "Он помогает посмотреть на себя, отношения и ближайший период через символический язык астрологии.\n\n"
        "<b>Главный продукт:</b>\n"
        "⭐ Натальная карта — персональная карта личности по дате, времени и месту рождения.\n\n"
        "<b>Быстрые разборы:</b>\n"
        "❤️ Совместимость\n"
        "🔮 Прогноз на месяц\n"
        "☀️ Солнечный знак\n"
        "🌙 Лунный знак\n"
        "⬆️ Асцендент\n\n"
        "Разборы предназначены для самопознания, рефлексии и развлечения. Они не являются медицинской, юридической, финансовой или психологической консультацией.",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


@dp.message(F.text == "⚙️ Админка")
async def admin_panel(message: Message):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    await message.answer("⚙️ Админка", reply_markup=admin_keyboard)



@dp.message(AstrologyStates.awaiting_natal_chart_data, F.text == "⬅️ Назад")
async def natal_chart_data_back_to_choice(message: Message, state: FSMContext):
    await cleanup_natal_messages(message, state)

    await state.set_state(AstrologyStates.awaiting_natal_chart_owner)

    sent = await message.answer(
        "⭐ <b>Натальная карта</b>\n\n"
        "Для кого построить карту?",
        parse_mode="HTML",
        reply_markup=natal_owner_keyboard
    )
    await remember_natal_message(state, sent)


@dp.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message):
    await safe_delete_current_message(message)

    await message.answer(
        "👇",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

    try:
        await asyncio.sleep(1)
        await message.bot.delete_message(message.chat.id, message.message_id + 1)
    except Exception:
        pass


@dp.message(F.text == "📈 Статистика")
async def admin_stats(message: Message):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    await message.answer(
        "📈 Статистика Astronum\n\n"
        f"👥 Пользователей: {await get_users_count()}\n"
        f"📜 Разборов: {await get_spreads_count()}\n"
        f"💎 Формат: платные функции по балансу"
    )


@dp.message(F.text == "👥 Пользователи")
async def admin_users(message: Message):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    users = await get_recent_users(limit=10)

    if not users:
        await message.answer("Пользователей пока нет.")
        return

    text = "👥 Последние пользователи:\n\n"

    for user in users:
        username = user["username"] or "без username"
        first_name = user["first_name"] or "без имени"

        text += (
            f"ID: {user['user_id']}\n"
            f"Имя: {first_name}\n"
            f"Username: @{username}\n"
            f"Дата: {user['created_at']}\n\n"
        )

    await message.answer(text)


@dp.message(F.text == "📜 Последние операции")
async def admin_recent_spreads(message: Message):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    spreads = await get_recent_spreads(limit=10)

    if not spreads:
        await message.answer("Разборов пока нет.")
        return

    text = "📜 Последние операции:\n\n"

    for spread in spreads:
        username = spread["username"] or "без username"
        first_name = spread["first_name"] or "без имени"

        text += (
            f"#{spread['id']} — {spread['spread_type']}\n"
            f"Пользователь: {first_name} / @{username}\n"
            f"ID: {spread['user_id']}\n"
            f"Вопрос: {spread['question']}\n"
            f"Дата: {spread['created_at']}\n\n"
        )

    await message.answer(text)


@dp.message(F.text == "📊 Популярность")
async def admin_popularity(message: Message):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    stats = await get_spread_type_stats()

    if not stats:
        await message.answer("📊 Пока нет данных по функциям.")
        return

    text = "📊 Популярность функций:\n\n"

    for item in stats:
        text += f"{item['spread_type']}: {item['count']}\n"

    await message.answer(text)





@dp.message(F.text == "💰 Платежи")
async def admin_payments(message: Message):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    stats = await get_payments_stats()
    payments = await get_recent_payments(limit=10)

    text = (
        "💰 <b>Платежи</b>\n\n"
        f"📅 <b>Сегодня</b>\n"
        f"• Платежей: <b>{stats['today_count']}</b>\n"
        f"• Сумма: <b>{stats['today_amount']} ₽</b>\n"
        f"• Разборов куплено: <b>{stats['today_spreads']}</b>\n\n"
        f"📊 <b>Всего</b>\n"
        f"• Платежей: <b>{stats['total_count']}</b>\n"
        f"• Сумма: <b>{stats['total_amount']} ₽</b>\n"
        f"• Разборов куплено: <b>{stats['total_spreads']}</b>\n\n"
    )

    if payments:
        text += "🧾 <b>Последние 10 платежей</b>\n\n"

        for payment in payments:
            username = payment["username"] or "без username"
            first_name = payment["first_name"] or "без имени"

            text += (
                f"👤 {first_name} / @{username}\n"
                f"ID: <code>{payment['user_id']}</code>\n"
                f"Сумма: <b>{payment['amount']} ₽</b>\n"
                f"Разборов: <b>{payment['spreads_added']}</b>\n"
                f"Дата: {payment['created_at']}\n\n"
            )
    else:
        text += "Платежей пока нет."

    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "🎁 Акции")
async def admin_promos(message: Message):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    await message.answer(
        "🎁 Выбери готовую акцию для рассылки:",
        reply_markup=promo_keyboard
    )


@dp.message(F.text == "🎁 Акция: 5 кредитов")
async def promo_five_spreads(message: Message, state: FSMContext):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        return

    broadcast_text = (
        "🎁 <b>Специальное предложение</b>\n\n"
        "Получите пакет из <b>5 астрологических кредитов</b> по выгодной цене.\n\n"
        "Подходит для тех, кто хочет изучить разные стороны своей личности или проверить совместимость с близкими людьми.\n\n"
        "✨ Больше возможностей для самопознания в одном пакете."
    )



    await state.clear()


    await state.update_data(broadcast_text=broadcast_text)



    await message.answer(


        "📣 Предпросмотр акции:\n\n"


        f"{broadcast_text}\n\n"


        "Отправить?",


        reply_markup=broadcast_confirm_keyboard,


        parse_mode="HTML"


    )



    await state.set_state(AdminStates.awaiting_broadcast_confirm)


@dp.message(F.text == "✨ Напомнить про лунный знак")
async def promo_personal_qualities(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    broadcast_text = (
        "✨ <b>А вы уже смотрели раздел «Лунный знак»?</b>\n\n"
        "Этот кредит помогает лучше понять:\n\n"
        "• сильные стороны характера;\n"
        "• особенности общения;\n"
        "• внутренние ресурсы;\n"
        "• направления для развития.\n\n"
        "Введите дату рождения и получите персональный AI-кредит."
    )



    await state.clear()


    await state.update_data(broadcast_text=broadcast_text)



    await message.answer(


        "📣 Предпросмотр акции:\n\n"


        f"{broadcast_text}\n\n"


        "Отправить?",


        reply_markup=broadcast_confirm_keyboard,


        parse_mode="HTML"


    )



    await state.set_state(AdminStates.awaiting_broadcast_confirm)


@dp.message(F.text == "❤️ Напомнить про совместимость")
async def promo_compatibility(message: Message, state: FSMContext):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        return

    broadcast_text = (
        "❤️ <b>Проверьте совместимость</b>\n\n"
        "Введите данные двух людей и получите астрологический кредит совместимости.\n\n"
        "Раздел поможет взглянуть на отношения с новой стороны и лучше понять особенности взаимодействия друг с другом.\n\n"
        "✨ Интересно как для романтических отношений, так и для дружбы."
    )



    await state.clear()


    await state.update_data(broadcast_text=broadcast_text)



    await message.answer(


        "📣 Предпросмотр акции:\n\n"


        f"{broadcast_text}\n\n"


        "Отправить?",


        reply_markup=broadcast_confirm_keyboard,


        parse_mode="HTML"


    )



    await state.set_state(AdminStates.awaiting_broadcast_confirm)



@dp.message(F.text == "📈 Воронка")
async def admin_sales_funnel(message: Message):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    funnel = await get_sales_funnel()

    await message.answer(
        "📈 Воронка продаж\n\n"
        f"👥 Пользователей всего: {funnel['users_count']}\n"
        
        f"📜 Пользователей с использованием: {funnel['analysis_users']}\n"
        f"📊 Всего использований: {funnel['analyses_count']}\n"
        f"💰 Совершили покупку: {funnel['paying_users']}\n"
        f"🧾 Всего платежей: {funnel['payments_count']}\n\n"
        f"📜 Конверсия в использование: {funnel['conversion_to_analysis']}%\n"
        f"💰 Конверсия в покупку: {funnel['conversion_to_payment']}%"
    )



@dp.message(F.text == "🏆 Топ")
async def admin_top_users(message: Message):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    data = await get_top_users(10)

    text = "🏆 Топ пользователей\n\n"

    text += "💰 По покупкам:\n"
    if data["top_payers"]:
        for i, user in enumerate(data["top_payers"], start=1):
            name = user["username"] or user["first_name"] or str(user["user_id"])
            text += (
                f"{i}. {name} — {user['total_amount']} ₽ "
                f"({user['payments_count']} платежей, {user['total_spreads']} кредитов)\n"
            )
    else:
        text += "Пока нет покупок.\n"

    text += "\n📜 По использованиям:\n"
    if data["top_spreads"]:
        for i, user in enumerate(data["top_spreads"], start=1):
            name = user["username"] or user["first_name"] or str(user["user_id"])
            text += f"{i}. {name} — {user['spreads_count']} кредитов\n"
    else:
        text += "Пока нет кредитов.\n"

    await message.answer(text)


@dp.message(F.text == "📣 Рассылка")
async def admin_broadcast_start(message: Message, state: FSMContext):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    await state.clear()
    await state.set_state(AdminStates.awaiting_broadcast_text)

    await message.answer(
        "📣 Введи текст рассылки.\n\n"
        "Следующее сообщение будет отправлено всем пользователям."
    )





@dp.message(F.text == "➕ Начислить баланс")
async def admin_balance_grant_start(message: Message, state: FSMContext):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    await state.clear()
    await state.set_state(AdminStates.awaiting_balance_grant)
    await message.answer("Введите USER_ID и количество кредитов:\n\nПример:\n185955220 5")


@dp.message(F.text == "➖ Списать баланс")
async def admin_balance_writeoff_start(message: Message, state: FSMContext):
    await safe_delete_current_message(message)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return

    await state.clear()
    await state.set_state(AdminStates.awaiting_balance_writeoff)
    await message.answer("Введите USER_ID и количество кредитов для списания:\n\nПример:\n185955220 5")


@dp.message(AdminStates.awaiting_balance_grant)
async def admin_balance_grant_process(message: Message, state: FSMContext):

    try:
        target_user_id, amount = map(int, message.text.split())
    except Exception:
        await message.answer("Неверный формат. Пример: 185955220 5", reply_markup=admin_keyboard)
        return

    if amount <= 0:
        await message.answer("Количество должно быть больше 0.", reply_markup=admin_keyboard)
        return

    await add_balance(target_user_id, amount)

    await message.answer(
        f"✅ Начислено {amount} кредит(ов).\nПользователь: {target_user_id}",
        reply_markup=admin_keyboard
    )
    await state.clear()

    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=(
                f"💎 Вам начислено: {amount} кредит(ов).\n\n"
                f"✨ Выберите интересующий раздел в меню."
            )
        )
    except Exception:
        pass


@dp.message(AdminStates.awaiting_balance_writeoff)
async def admin_balance_writeoff_process(message: Message, state: FSMContext):

    try:
        target_user_id, amount = map(int, message.text.split())
    except Exception:
        await message.answer("Неверный формат. Пример: 185955220 5", reply_markup=admin_keyboard)
        return

    if amount <= 0:
        await message.answer("Количество должно быть больше 0.", reply_markup=admin_keyboard)
        return

    current_balance = await get_balance(target_user_id)

    if current_balance < amount:
        await message.answer(
            f"Недостаточно кредитов на балансе. Сейчас: {current_balance}",
            reply_markup=admin_keyboard
        )
        return

    for _ in range(amount):
        await spend_balance(target_user_id)

    await message.answer(
        f"✅ Списано {amount} кредит(ов).\nПользователь: {target_user_id}",
        reply_markup=admin_keyboard
    )
    await state.clear()



@dp.message(AdminStates.awaiting_broadcast_text, F.text == "❌ Отмена")
async def cancel_broadcast_text_input(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.clear()
    await message.answer("❌ Рассылка отменена.", reply_markup=admin_keyboard)


@dp.message(AdminStates.awaiting_broadcast_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(broadcast_text=message.text)

    await message.answer(
        "📣 Предпросмотр рассылки:\n\n"
        f"{message.text}\n\n"
        "Отправить?",
        reply_markup=broadcast_confirm_keyboard
    )

    await state.set_state(AdminStates.awaiting_broadcast_confirm)


@dp.message(AdminStates.awaiting_broadcast_confirm, F.text == "✅ Отправить")
async def confirm_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    text_to_send = data.get("broadcast_text")

    if not text_to_send:
        await state.clear()
        await message.answer("Нет активной рассылки.", reply_markup=admin_keyboard)
        return

    user_ids = await get_all_user_ids()
    success = 0
    failed = 0

    await message.answer(f"📣 Начинаю рассылку по {len(user_ids)} пользователям...")

    for target_user_id in user_ids:
        try:
            await bot.send_message(chat_id=target_user_id, text=text_to_send, parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await state.clear()

    await message.answer(
        "📣 Рассылка завершена.\n\n"
        f"✅ Успешно: {success}\n"
        f"❌ Ошибок: {failed}",
        reply_markup=admin_keyboard
    )


@dp.message(AdminStates.awaiting_broadcast_confirm, F.text == "❌ Отмена")
async def cancel_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.clear()
    await message.answer("❌ Рассылка отменена.", reply_markup=admin_keyboard)







@dp.message(AstrologyStates.awaiting_natal_chart_data, F.text == "⬅️ Назад")
async def natal_chart_data_back(message: Message, state: FSMContext):
    await cleanup_natal_messages(message, state)

    await state.set_state(AstrologyStates.awaiting_natal_chart_owner)

    sent = await message.answer(
        "⭐ <b>Натальная карта</b>\n\n"
        "Для кого построить карту?",
        parse_mode="HTML",
        reply_markup=natal_owner_keyboard
    )
    await remember_natal_message(state, sent)






@dp.message(AstrologyStates.awaiting_natal_chart_decode_choice, F.text == "👀 Пример расшифровки")
async def natal_chart_decode_example(message: Message):
    card_path = "/opt/bots/astrology_bot/data/examples/natal_example_card.png"

    if os.path.exists(card_path):
        await message.answer_photo(photo=FSInputFile(card_path))

    await message.answer(
        "👀 <b>Пример полной расшифровки</b>\n\n"
        "После открытия вы получите:\n\n"
        "⭐ Полный психологический портрет\n"
        "❤️ Анализ отношений и эмоциональных сценариев\n"
        "💼 Карьерные сильные стороны и таланты\n"
        "🎯 Главные задачи и точки роста\n"
        "✨ Разбор ключевых аспектов карты\n"
        "🪐 Интерпретацию реальных положений планет\n\n"
        "Каждая расшифровка создаётся индивидуально по вашей дате, времени и месту рождения.\n\n"
        "💎 Стоимость полной расшифровки: <b>3 кредита</b>",
        parse_mode="HTML",
        reply_markup=natal_decode_keyboard
    )


@dp.message(AstrologyStates.awaiting_natal_chart_decode_choice, F.text == "📖 Открыть расшифровку")
async def natal_chart_open_saved_decode(message: Message, state: FSMContext):
    state_data = await state.get_data()

    data = state_data.get("natal_decode_data")
    interpretation = state_data.get("natal_saved_interpretation")

    if not data or not interpretation:
        await message.answer(
            "⚠️ Сохранённая расшифровка не найдена. Постройте натальную карту заново.",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    await message.answer(
        f"⭐ <b>Полная расшифровка натальной карты</b>\n\n"
        f"📅 Дата: <b>{data['birth_date']}</b>\n"
        f"🕒 Время: <b>{data['birth_time']}</b>\n"
        f"📍 Место: <b>{data['birth_place']}</b>\n\n"
        f"{markdown_bold_to_html(interpretation)}",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

    await state.clear()


@dp.message(AstrologyStates.awaiting_natal_chart_decode_choice, F.text == "✨ Открыть расшифровку (3 кредита)")
async def natal_chart_paid_decode(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        balance = await get_balance(user_id)
        if balance < 3:
            await message.answer(
                "💎 Для полной расшифровки натальной карты нужно <b>3 кредита</b>.\n\n"
                f"Ваш баланс: <b>{balance}</b>\n\n"
                "Пополните баланс и возвращайтесь к расшифровке.",
                parse_mode="HTML",
                reply_markup=shop_keyboard
            )
            return

        for _ in range(3):
            await spend_balance(user_id)

    await cleanup_natal_messages(message, state, delete_current=True)
    progress_msg = await message.answer(
        "🔓 Расшифровываю натальную карту...",
        reply_markup=ReplyKeyboardRemove()
    )

    state_data = await state.get_data()
    data = state_data.get("natal_decode_data")
    chart = state_data.get("natal_decode_chart")
    input_text = state_data.get("natal_decode_input", "")

    if not data or not chart:
        await message.answer("⚠️ Данные карты не найдены. Постройте натальную карту заново.")
        await state.clear()
        return

    data["chart"] = chart

    try:
        await progress_msg.delete()
    except Exception:
        pass

    try:
        await send_natal_card_image(message, chart, user_id)
    except Exception as e:
        await message.answer(f"Карта рассчитана, но изображение не удалось создать: {e}")

    decode_progress_msg = await message.answer("🔓 Готовлю полную расшифровку натальной карты...")

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        interpretation = await interpret_natal_chart(data)
    except Exception as e:
        await message.answer(f"Не удалось подготовить расшифровку. Ошибка: {e}")
        return

    await save_spread(user_id, "Полная натальная карта", input_text, input_text, interpretation)

    profile = await get_birth_profile(user_id)
    if (
        profile
        and profile["birth_date"] == data["birth_date"]
        and profile["birth_time"] == data["birth_time"]
        and profile["birth_place"] == data["birth_place"]
    ):
        await save_birth_interpretation(user_id, interpretation)

    try:
        await decode_progress_msg.delete()
    except Exception:
        pass

    await message.answer(
        f"⭐ <b>Полная расшифровка натальной карты</b>\n\n"
        f"📅 Дата: <b>{data['birth_date']}</b>\n"
        f"🕒 Время: <b>{data['birth_time']}</b>\n"
        f"📍 Место: <b>{data['birth_place']}</b>\n\n"
        f"{markdown_bold_to_html(interpretation)}",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(user_id)
    )

    await state.clear()


@dp.message(AstrologyStates.awaiting_natal_chart_decode_choice)
async def natal_chart_decode_choice_fallback(message: Message):
    await message.answer("Выберите действие кнопкой ниже.", reply_markup=natal_decode_keyboard)


@dp.message(AstrologyStates.awaiting_natal_chart_data)
async def process_natal_chart_data(message: Message, state: FSMContext):
    try:
        data = parse_birth_datetime_place_strict(message.text)
    except ValueError:
        await strict_birth_input_error(message)
        return

    state_data = await state.get_data()
    save_profile = bool(state_data.get("natal_save_profile", False))

    await cleanup_natal_messages(message, state)

    await send_natal_chart_result(
        message=message,
        state=state,
        data=data,
        input_text=message.text,
        save_profile=save_profile
    )


@dp.message(AstrologyStates.awaiting_sun_sign_date)
async def process_sun_sign_date(message: Message, state: FSMContext):
    user_id = message.from_user.id

    try:
        data = zodiac_sign(message.text)
    except Exception:
        await message.answer("⚠️ Введите дату в формате ДД.ММ.ГГГГ")
        return

    await message.answer("☀️ Рассчитываю солнечный знак...")

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        interpretation = await interpret_sun_sign(data)
    except Exception as e:
        await message.answer(f"Не удалось подготовить кредит. Ошибка: {e}")
        return

    await save_spread(user_id, "Солнечный знак", data["birth_date"], data["birth_date"], interpretation)
    await charge_user_for_spread(user_id)

    await message.answer(
        f"☀️ <b>Солнечный знак</b>\n\n"
        f"📅 Дата рождения: <b>{data['birth_date']}</b>\n"
        f"♈ Знак: <b>{data['sign']}</b>\n\n"
        f"{markdown_bold_to_html(interpretation)}",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(message.from_user.id)
    )
    await state.clear()


@dp.message(AstrologyStates.awaiting_moon_sign_data)
async def process_moon_sign_data(message: Message, state: FSMContext):
    user_id = message.from_user.id

    parts = [x.strip() for x in message.text.split(",", 1)]
    if len(parts) != 2:
        await message.answer("⚠️ Введите данные в формате: ДД.ММ.ГГГГ, ЧЧ:ММ")
        return

    data = {"birth_date": parts[0], "birth_time": parts[1]}

    await message.answer("🌙 Готовлю кредит лунного знака...")

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        interpretation = await interpret_moon_sign(data)
    except Exception as e:
        await message.answer(f"Не удалось подготовить кредит. Ошибка: {e}")
        return

    await save_spread(user_id, "Лунный знак", message.text, message.text, interpretation)
    await charge_user_for_spread(user_id)

    await message.answer(
        f"🌙 <b>Лунный знак</b>\n\n"
        f"📅 Дата: <b>{data['birth_date']}</b>\n"
        f"🕒 Время: <b>{data['birth_time']}</b>\n\n"
        f"{markdown_bold_to_html(interpretation)}",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(message.from_user.id)
    )
    await state.clear()


@dp.message(AstrologyStates.awaiting_ascendant_data)
async def process_ascendant_data(message: Message, state: FSMContext):
    user_id = message.from_user.id

    try:
        data = parse_birth_datetime_place_strict(message.text)
    except ValueError:
        await strict_birth_input_error(message)
        return

    await message.answer("⬆️ Готовлю кредит асцендента...")

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        interpretation = await interpret_ascendant(data)
    except Exception as e:
        await message.answer(f"Не удалось подготовить кредит. Ошибка: {e}")
        return

    await save_spread(user_id, "Асцендент", message.text, message.text, interpretation)
    await charge_user_for_spread(user_id)

    await message.answer(
        f"⬆️ <b>Асцендент</b>\n\n"
        f"📅 Дата: <b>{data['birth_date']}</b>\n"
        f"🕒 Время: <b>{data['birth_time']}</b>\n"
        f"📍 Место: <b>{data['birth_place']}</b>\n\n"
        f"{markdown_bold_to_html(interpretation)}",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(message.from_user.id)
    )
    await state.clear()


@dp.message(AstrologyStates.awaiting_compatibility_data)
async def process_compatibility_data(message: Message, state: FSMContext):
    user_id = message.from_user.id

    parts = [x.strip() for x in message.text.splitlines() if x.strip()]
    if len(parts) != 2:
        await message.answer(
            "⚠️ Введите данные в формате:\n\n"
            "ДД.ММ.ГГГГ, город\n"
            "ДД.ММ.ГГГГ, город"
        )
        return

    data = {"person_1": parts[0], "person_2": parts[1]}

    await message.answer("❤️ Готовлю совместимость...")

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        interpretation = await interpret_compatibility(data)
    except Exception as e:
        await message.answer(f"Не удалось подготовить кредит. Ошибка: {e}")
        return

    await save_spread(user_id, "Совместимость", message.text, message.text, interpretation)
    await charge_user_for_spread(user_id)
    await charge_user_for_spread(user_id)

    await message.answer(
        f"❤️ <b>Совместимость</b>\n\n"
        f"👤 Первый человек: <b>{data['person_1']}</b>\n"
        f"👤 Второй человек: <b>{data['person_2']}</b>\n\n"
        f"{markdown_bold_to_html(interpretation)}",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(message.from_user.id)
    )
    await state.clear()


@dp.message(AstrologyStates.awaiting_month_forecast_date)
async def process_month_forecast_date(message: Message, state: FSMContext):
    user_id = message.from_user.id

    try:
        data = zodiac_sign(message.text)
    except Exception:
        await message.answer("⚠️ Введите дату в формате ДД.ММ.ГГГГ")
        return

    await message.answer("🔮 Готовлю прогноз на месяц...")

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        interpretation = await interpret_month_forecast(data)
    except Exception as e:
        await message.answer(f"Не удалось подготовить прогноз. Ошибка: {e}")
        return

    await save_spread(user_id, "Прогноз на месяц", data["birth_date"], data["birth_date"], interpretation)
    await charge_user_for_spread(user_id)
    await charge_user_for_spread(user_id)

    await message.answer(
        f"🔮 <b>Прогноз на месяц</b>\n\n"
        f"📅 Дата рождения: <b>{data['birth_date']}</b>\n"
        f"♈ Знак: <b>{data['sign']}</b>\n\n"
        f"{markdown_bold_to_html(interpretation)}",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(message.from_user.id)
    )
    await state.clear()


@dp.message()
async def fallback(message: Message):
    await message.answer("Нажми /start чтобы открыть меню.")


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
