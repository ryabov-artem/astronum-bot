import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv("/opt/bots/astrology_bot/.env")

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")


async def ask_gpt(prompt: str) -> str:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — эксперт по западной астрологии и психологическим интерпретациям. "
                    "Пиши на русском языке, тепло, понятно и структурно. "
                    "Используй HTML-разметку Telegram: <b>жирный текст</b>. "
                    "Не используй Markdown. Не пиши слишком длинно. "
                    "Астрология — это развлекательный и рефлексивный формат, не медицинский и не юридический совет."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.8
    )
    return response.choices[0].message.content


async def interpret_natal_chart(data: dict) -> str:
    prompt = (
        "Сделай краткий разбор натальной карты в стиле западной астрологии.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Время рождения: {data.get('birth_time')}\n"
        f"Место рождения: {data.get('birth_place')}\n\n"
        "Структура ответа:\n"
        "1. Общий психологический портрет\n"
        "2. Сильные стороны\n"
        "3. Уязвимые места\n"
        "4. Отношения\n"
        "5. Карьера и деньги\n"
        "6. Рекомендация\n"
    )
    return await ask_gpt(prompt)


async def interpret_sun_sign(data: dict) -> str:
    prompt = (
        "Сделай разбор солнечного знака в западной астрологии.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Солнечный знак: {data.get('sign')}\n\n"
        "Раскрой характер, сильные стороны, слабые стороны, отношения и карьерный потенциал."
    )
    return await ask_gpt(prompt)


async def interpret_moon_sign(data: dict) -> str:
    prompt = (
        "Сделай психологический разбор лунного знака в западной астрологии.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Время рождения: {data.get('birth_time')}\n\n"
        "Для MVP точный лунный знак не рассчитывается. Сделай мягкий эмоциональный разбор по дате и времени рождения: "
        "эмоции, близость, стресс, потребности в отношениях."
    )
    return await ask_gpt(prompt)


async def interpret_ascendant(data: dict) -> str:
    prompt = (
        "Сделай разбор асцендента в западной астрологии.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Время рождения: {data.get('birth_time')}\n"
        f"Место рождения: {data.get('birth_place')}\n\n"
        "Для MVP точный асцендент не рассчитывается. Сделай интерпретацию внешнего проявления личности: "
        "первое впечатление, стиль поведения, как человека видят окружающие."
    )
    return await ask_gpt(prompt)


async def interpret_compatibility(data: dict) -> str:
    prompt = (
        "Сделай разбор совместимости в западной астрологии.\n\n"
        f"Первый человек: {data.get('person_1')}\n"
        f"Второй человек: {data.get('person_2')}\n\n"
        "Структура: эмоциональная совместимость, романтика, быт, конфликты, сильные стороны пары, рекомендация."
    )
    return await ask_gpt(prompt)


async def interpret_career_money(data: dict) -> str:
    prompt = (
        "Сделай астрологический разбор карьеры и денег.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Солнечный знак: {data.get('sign')}\n\n"
        "Раскрой: сильные рабочие качества, подходящие сферы, стиль заработка, риски в деньгах, рекомендация."
    )
    return await ask_gpt(prompt)


async def interpret_month_forecast(data: dict) -> str:
    prompt = (
        "Сделай астрологический прогноз на месяц.\n\n"
        f"Дата рождения: {data.get('birth_date')}\n"
        f"Солнечный знак: {data.get('sign')}\n\n"
        "Структура: общий фон месяца, отношения, работа, деньги, энергия, совет месяца."
    )
    return await ask_gpt(prompt)
