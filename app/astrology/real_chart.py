from datetime import datetime
from zoneinfo import ZoneInfo

import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]

PLANETS = {
    "Солнце": swe.SUN,
    "Луна": swe.MOON,
    "Меркурий": swe.MERCURY,
    "Венера": swe.VENUS,
    "Марс": swe.MARS,
    "Юпитер": swe.JUPITER,
    "Сатурн": swe.SATURN,
}


def sign_name(degree: float) -> str:
    return SIGNS[int(degree // 30) % 12]


def degree_in_sign(degree: float) -> float:
    return degree % 30


def geocode_city(city: str):
    geolocator = Nominatim(user_agent="astronum_bot")
    location = geolocator.geocode(city, timeout=10)
    if not location:
        raise ValueError("Город не найден")
    return location.latitude, location.longitude, location.address


def get_timezone(lat: float, lon: float) -> str:
    tf = TimezoneFinder()
    tz = tf.timezone_at(lat=lat, lng=lon)
    if not tz:
        raise ValueError("Не удалось определить часовой пояс")
    return tz


def parse_birth_datetime(date_text: str, time_text: str):
    return datetime.strptime(f"{date_text.strip()} {time_text.strip()}", "%d.%m.%Y %H:%M")


def calculate_real_chart(date_text: str, time_text: str, city: str) -> dict:
    lat, lon, address = geocode_city(city)
    tz_name = get_timezone(lat, lon)

    local_dt = parse_birth_datetime(date_text, time_text).replace(tzinfo=ZoneInfo(tz_name))
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    jd = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    )

    planets = []

    for name, planet_id in PLANETS.items():
        pos, _ = swe.calc_ut(jd, planet_id)
        lon_deg = pos[0]
        planets.append({
            "name": name,
            "longitude": round(lon_deg, 2),
            "sign": sign_name(lon_deg),
            "degree": round(degree_in_sign(lon_deg), 2),
        })

    houses, ascmc = swe.houses(jd, lat, lon)
    asc = ascmc[0]
    mc = ascmc[1]

    return {
        "birth_date": date_text,
        "birth_time": time_text,
        "birth_city": city,
        "resolved_address": address,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "timezone": tz_name,
        "planets": planets,
        "ascendant": {
            "longitude": round(asc, 2),
            "sign": sign_name(asc),
            "degree": round(degree_in_sign(asc), 2),
        },
        "mc": {
            "longitude": round(mc, 2),
            "sign": sign_name(mc),
            "degree": round(degree_in_sign(mc), 2),
        }
    }


def format_chart_for_prompt(chart: dict) -> str:
    lines = [
        f"Дата рождения: {chart['birth_date']}",
        f"Время рождения: {chart['birth_time']}",
        f"Город: {chart['birth_city']}",
        f"Координаты: {chart['latitude']}, {chart['longitude']}",
        f"Часовой пояс: {chart['timezone']}",
        "",
        "Планеты:",
    ]

    for p in chart["planets"]:
        lines.append(f"- {p['name']}: {p['degree']}° {p['sign']}")

    lines += [
        "",
        f"ASC: {chart['ascendant']['degree']}° {chart['ascendant']['sign']}",
        f"MC: {chart['mc']['degree']}° {chart['mc']['sign']}",
    ]

    return "\n".join(lines)
