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
    "Доступные разделы: Натальная карта, Солнечный знак, Лунный знак, Асцендент, Совместимость, Карьера и деньги, Прогноз на месяц. "
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
        "Раздел: ⭐ Натальная карта. Это главный премиальный раздел. Ответ 1900–2300 символов, не больше.\\n\\n"
        "Используй только реальные астрологические данные ниже. Не выдумывай положения планет, знаки, дома, ASC, MC и аспекты.\\n"
        "Обязательно учитывай не только знак планеты, но и дом, в котором она стоит.\\n"
        "Аспекты трактуй как внутренние связки между планетами, а не просто перечисляй их.\\n\\n"
        f"{chart_text}\\n\\n"
        "Структура ответа:\\n"
        "<b>Ключ карты</b> — Солнце, Луна, ASC: темперамент, способ проявления и базовая энергия.\\n"
        "<b>Внутренний мир</b> — Луна, Венера и связанные аспекты: чувства, близость, потребности.\\n"
        "<b>Мышление и решения</b> — Меркурий: знак, дом и аспектные связи.\\n"
        "<b>Действие и амбиции</b> — Марс, MC и 10 дом: энергия, работа, реализация.\\n"
        "<b>Рост и задачи</b> — Юпитер и Сатурн: где расширение, где дисциплина и уроки.\\n"
        "<b>Главные напряжения и таланты</b> — 2–3 самых важных аспекта карты простыми словами.\\n"
        "<b>Совет</b> — конкретная рекомендация по карте без мистического фатализма.\\n\\n"
        "Пиши персонально, конкретно, без длинных вступлений. Не обещай судьбу, брак, богатство или гарантированные события."
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


async def interpret_career_money(data: dict) -> str:
    prompt = (
        "Раздел: 💼 Карьера и деньги. Ответ 800–1000 символов, не больше 1200.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Солнечный знак: {data.get('sign')}\n\n"
        "Раскрой: рабочий стиль, сильные профессиональные качества, 2–3 подходящие сферы, денежное поведение, риски, один практичный шаг. "
        "Не давай инвестиционных советов и финансовых гарантий."
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
