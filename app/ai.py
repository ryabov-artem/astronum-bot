import os
from dotenv import load_dotenv
import httpx
from openai import AsyncOpenAI

load_dotenv("/opt/bots/astrology_bot/.env")

PROXY_URL = os.getenv("PROXY_URL")
http_client = httpx.AsyncClient(proxy=PROXY_URL) if PROXY_URL else None

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    http_client=http_client
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

SYSTEM_PROMPT = (
    "Ты — эксперт по западной астрологии и психологическим интерпретациям. "
    "Пиши на русском языке, тепло, уверенно и кратко. "
    "Используй HTML-разметку Telegram: <b>жирный текст</b>. "
    "Не используй Markdown и символы **. "
    "Не давай медицинские, юридические или финансовые гарантии. "
    "Не предлагай пользователю функции, которых нет в меню бота. "
    "Доступные разделы: Натальная карта, Солнечный знак, Лунный знак, Асцендент, Совместимость, Прогноз на месяц. "
    "Не пиши финальные фразы вроде «если хотите, я могу...». "
    "Соблюдай лимит: натальная карта до 1800 символов, остальные разделы до 1200 символов."
)


def trim_answer(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text

    cut = text[:limit]
    last = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))

    if last > int(limit * 0.6):
        return cut[:last + 1].rstrip()

    return cut.rstrip()


async def ask_gpt(prompt: str, limit: int = 1200) -> str:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return trim_answer(response.choices[0].message.content, limit)


async def interpret_natal_chart(data: dict) -> str:
    chart = data.get("chart")
    if chart:
        from astrology.real_chart import format_chart_for_prompt
        chart_text = format_chart_for_prompt(chart)
    else:
        chart_text = ""

    prompt = (
        "Раздел: ⭐ Натальная карта. Это главный премиальный раздел. Ответ 1900–2300 символов, не больше.\n\n"
        "Используй только реальные астрологические данные ниже. Не выдумывай положения планет, знаки, дома, ASC, MC и аспекты.\n"
        "Пиши понятно для обычного пользователя, а не как технический астрологический отчёт.\n"
        "Астрологические термины можно использовать, но всегда объясняй их простыми словами.\n\n"
        f"{chart_text}\n\n"
        "Структура ответа строго такая:\n"
        "<b>⭐ Личность и характер</b> — Солнце, Асцендент, доминирующие энергии: как человек проявляется, его сильные и теневые стороны.\n"
        "<b>🌙 Эмоции и внутренний мир</b> — Луна, эмоциональные потребности, реакции на стресс и способ восстановления.\n"
        "<b>❤️ Любовь и отношения</b> — Венера, 7 дом и важные аспекты: как человек строит близость, что ему важно в партнёрстве.\n"
        "<b>💼 Карьера и реализация</b> — MC, 10 дом, Марс и сильные стороны: где легче проявиться и какой стиль работы подходит.\n"
        "<b>🎁 Таланты и сильные стороны</b> — Юпитер, доминирующие планеты и гармоничные аспекты: природные способности и ресурсы.\n"
        "<b>🎯 Главные жизненные уроки</b> — Сатурн и напряжённые аспекты: зоны роста без фатализма и запугивания.\n"
        "<b>🧭 Персональная рекомендация</b> — конкретный совет по карте.\n\n"
        "Пиши персонально, тепло и конкретно. Не обещай судьбу, брак, богатство или гарантированные события."
    )

    return await ask_gpt(prompt, limit=2300)


async def interpret_sun_sign(data: dict) -> str:
    prompt = (
        "Раздел: ☀️ Солнечный знак. Ответ 700–1000 символов, не больше 1200.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Солнечный знак: {data.get('sign')}\n\n"
        "Раскрой: суть знака, как человек проявляется, сильные качества, теневая сторона, короткий совет. "
        "Не повторяй формат натальной карты."
    )
    return await ask_gpt(prompt, limit=1200)


async def interpret_moon_sign(data: dict) -> str:
    prompt = (
        "Раздел: 🌙 Лунный знак. Ответ 700–1000 символов, не больше 1200.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Время рождения: {data.get('birth_time')}\n\n"
        "Раскрой: эмоциональная природа, ощущение безопасности, реакция на стресс, близость, восстановление. "
        "Не уходи в карьеру и деньги."
    )
    return await ask_gpt(prompt, limit=1200)


async def interpret_ascendant(data: dict) -> str:
    prompt = (
        "Раздел: ⬆️ Асцендент. Ответ 700–1000 символов, не больше 1200.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Время рождения: {data.get('birth_time')}\n"
        f"Место рождения: {data.get('birth_place')}\n\n"
        "Раскрой: первое впечатление, стиль поведения, социальная маска, сильная сторона образа, риск и совет. "
        "Это раздел про внешний стиль и контакт с миром."
    )
    return await ask_gpt(prompt, limit=1200)


async def interpret_compatibility(data: dict) -> str:
    prompt = (
        "Раздел: ❤️ Совместимость. Ответ 900–1200 символов, не больше 1200.\n\n"
        f"Первый человек: {data.get('person_1')}\n"
        f"Второй человек: {data.get('person_2')}\n\n"
        "Раскрой: общая динамика пары, что притягивает, эмоциональная совместимость, быт, зоны риска, как укрепить связь. "
        "Не обещай брак, расставание или гарантию будущего."
    )
    return await ask_gpt(prompt, limit=1200)


async def interpret_month_forecast(data: dict) -> str:
    prompt = (
        "Раздел: 🔮 Прогноз на месяц. Ответ 700–1000 символов, не больше 1200.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Солнечный знак: {data.get('sign')}\n\n"
        "Раскрой: главная тема месяца, отношения, работа, деньги, энергия, совет месяца. "
        "Пиши как прогноз, а не как описание характера."
    )
    return await ask_gpt(prompt, limit=1200)
