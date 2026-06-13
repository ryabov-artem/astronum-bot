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

ASPECTS = [
    ("соединение", 0, 8),
    ("секстиль", 60, 5),
    ("квадрат", 90, 6),
    ("трин", 120, 6),
    ("оппозиция", 180, 8),
]


def sign_name(degree: float) -> str:
    return SIGNS[int(degree // 30) % 12]


def degree_in_sign(degree: float) -> float:
    return degree % 30


def angular_distance(a: float, b: float) -> float:
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


def calculate_aspects(planets: list[dict]) -> list[dict]:
    result = []

    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1 = planets[i]
            p2 = planets[j]
            distance = angular_distance(p1["longitude"], p2["longitude"])

            for aspect_name, exact_angle, orb in ASPECTS:
                delta = abs(distance - exact_angle)

                if delta <= orb:
                    result.append({
                        "planet1": p1["name"],
                        "planet2": p2["name"],
                        "aspect": aspect_name,
                        "orb": round(delta, 2),
                    })
                    break

    result.sort(key=lambda x: x["orb"])
    return result[:8]


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


def house_for_longitude(longitude: float, houses: list[dict]) -> int:
    lon = longitude % 360

    for i in range(12):
        start = houses[i]["longitude"]
        end = houses[(i + 1) % 12]["longitude"]

        if start <= end:
            if start <= lon < end:
                return houses[i]["house"]
        else:
            if lon >= start or lon < end:
                return houses[i]["house"]

    return 12


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

    cusps, ascmc = swe.houses(jd, lat, lon)
    houses = []
    for i in range(12):
        cusp_lon = float(cusps[i]) % 360
        houses.append({
            "house": i + 1,
            "longitude": round(cusp_lon, 2),
            "sign": sign_name(cusp_lon),
            "degree": round(degree_in_sign(cusp_lon), 2),
        })

    for planet in planets:
        planet["house"] = house_for_longitude(planet["longitude"], houses)

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
        "houses": houses,
        "aspects": calculate_aspects(planets),
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
        house_text = f", {p.get('house')} дом" if p.get("house") else ""
        lines.append(f"- {p['name']}: {p['degree']}° {p['sign']}{house_text}")

    lines += [
        "",
        f"ASC: {chart['ascendant']['degree']}° {chart['ascendant']['sign']}",
        f"MC: {chart['mc']['degree']}° {chart['mc']['sign']}",
        "",
        "Дома:",
    ]

    for h in chart.get("houses", []):
        lines.append(f"- {h['house']} дом: {h['degree']}° {h['sign']}")

    lines += [
        "",
        "Аспекты:",
    ]

    for a in chart.get("aspects", []):
        lines.append(f"- {a['planet1']} {a['aspect']} {a['planet2']} орб {a['orb']}°")

    return "\n".join(lines)

def generate_chart_png(chart: dict, output_path: str):
    import math
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1600, 1000
    img = Image.new("RGB", (W, H), "#F8FBFF")
    draw = ImageDraw.Draw(img)

    def font(size, bold=False):
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]
        for path in paths:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    f_title = font(42, True)
    f_subtitle = font(22)
    f_label = font(24, True)
    f_text = font(22)
    f_small = font(17)
    f_tiny = font(14)
    f_logo = font(52, True)
    f_symbol = font(30, True)

    # soft background
    for y in range(H):
        ratio = y / H
        r = int(247 - ratio * 6)
        g = int(242 - ratio * 10)
        b = int(234 - ratio * 18)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # decorative circles
    draw.ellipse((-220, -250, 480, 450), outline="#DCE7F3", width=3)
    draw.ellipse((1180, 680, 1780, 1280), outline="#DCE7F3", width=3)

    # watermark
    draw.text((470, 500), "ASTRONUM", fill="#EEF4FB", font=font(96, True), anchor="mm")
    draw.text((470, 570), "ТВОЯ КАРТА · ТВОЙ ПУТЬ", fill="#EEF4FB", font=font(22, True), anchor="mm")

    # headers
    draw.text((70, 55), "Натальная карта", fill="#182235", font=f_title)
    draw.text((72, 110), "персональный астрологический расчёт", fill="#64748B", font=f_subtitle)

    birth_line = f"{chart.get('birth_date', '')} · {chart.get('birth_time', '')} · {chart.get('birth_city', '')}"
    draw.rounded_rectangle((70, 150, 590, 230), radius=24, fill="#FFFFFF", outline="#D6E2F0", width=2)
    draw.text((100, 172), birth_line[:48], fill="#182235", font=f_text)
    draw.text((100, 202), f"{chart.get('latitude', '')}°, {chart.get('longitude', '')}°", fill="#64748B", font=f_small)

    # wheel geometry
    cx, cy = 485, 565
    R_outer = 365
    R_zodiac = 315
    R_inner = 178
    R_aspect = 135

    zodiac_symbols = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
    planet_symbols = {
        "Солнце": "☉",
        "Луна": "☽",
        "Меркурий": "☿",
        "Венера": "♀",
        "Марс": "♂",
        "Юпитер": "♃",
        "Сатурн": "♄",
    }
    aspect_symbols = {
        "соединение": "☌",
        "секстиль": "✶",
        "квадрат": "□",
        "трин": "△",
        "оппозиция": "☍",
    }

    def xy(deg, r):
        # astrology wheel: 0 Aries at left, clockwise
        a = math.radians(180 - deg)
        return (cx + math.cos(a) * r, cy - math.sin(a) * r)

    # wheel rings
    for r, color, width in [
        (R_outer, "#7C93B8", 4),
        (R_zodiac, "#B9C8DE", 2),
        (245, "#DDE8F5", 2),
        (R_inner, "#B9C8DE", 2),
        (70, "#DDE8F5", 2),
    ]:
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=color, width=width)

    # zodiac sectors
    for i, sym in enumerate(zodiac_symbols):
        deg = i * 30
        x1, y1 = xy(deg, R_inner)
        x2, y2 = xy(deg, R_outer)
        draw.line((x1, y1, x2, y2), fill="#CBD8EA", width=2)

        tx, ty = xy(deg + 15, 315)
        draw.text((tx, ty), sym, fill="#1E293B", font=font(34, True), anchor="mm")

        for d in range(5, 30, 5):
            xx1, yy1 = xy(deg + d, 276)
            xx2, yy2 = xy(deg + d, 292)
            draw.line((xx1, yy1, xx2, yy2), fill="#E2EAF5", width=1)

    # aspects
    planets = chart.get("planets", [])
    lon_by_name = {pl["name"]: pl["longitude"] for pl in planets}
    for a in chart.get("aspects", [])[:9]:
        p1 = a.get("planet1")
        p2 = a.get("planet2")
        if p1 not in lon_by_name or p2 not in lon_by_name:
            continue
        x1, y1 = xy(lon_by_name[p1], R_aspect)
        x2, y2 = xy(lon_by_name[p2], R_aspect)
        color = "#EF4444" if a.get("aspect") in ("квадрат", "оппозиция") else "#3B82F6"
        draw.line((x1, y1, x2, y2), fill=color, width=2)

    # planets on wheel
    used = {}
    for pl in planets:
        deg = pl["longitude"]
        bucket = int(deg // 6)
        used[bucket] = used.get(bucket, 0) + 1
        offset = used[bucket] * 18
        px, py = xy(deg, 215 + offset)
        sym = planet_symbols.get(pl["name"], pl["name"][0])
        draw.ellipse((px-25, py-25, px+25, py+25), fill="#FFFFFF", outline="#7C93B8", width=2)
        draw.text((px, py-1), sym, fill="#182235", font=f_symbol, anchor="mm")

    # ASC / MC
    for key, label in [("ascendant", "ASC"), ("mc", "MC")]:
        item = chart.get(key, {})
        if item:
            x1, y1 = xy(item["longitude"], 60)
            x2, y2 = xy(item["longitude"], R_outer + 18)
            draw.line((x1, y1, x2, y2), fill="#182235", width=3)
            tx, ty = xy(item["longitude"], R_outer + 45)
            draw.rounded_rectangle((tx-35, ty-16, tx+35, ty+16), radius=10, fill="#182235")
            draw.text((tx, ty-1), label, fill="#FFFFFF", font=f_tiny, anchor="mm")

    # right cards
    panel_x = 930
    draw.rounded_rectangle((875, 55, 1535, 940), radius=34, fill="#FFFFFF", outline="#D6E2F0", width=2)

    draw.text((930, 95), "ASTRONUM", fill="#182235", font=f_logo)
    draw.text((932, 150), "@astronum_aibot · t.me/astronum_aibot", fill="#64748B", font=f_small)
    draw.line((930, 188, 1490, 188), fill="#D6E2F0", width=2)

    y = 220
    draw.text((930, y), "Планеты", fill="#182235", font=f_label)
    y += 42
    for pl in planets:
        sym = planet_symbols.get(pl["name"], "")
        draw.text((930, y), f"{sym}  {pl['name']}", fill="#182235", font=f_text)
        draw.text((1160, y), f"{pl['degree']:.2f}°", fill="#64748B", font=f_text)
        draw.text((1275, y), pl["sign"], fill="#182235", font=f_text)
        y += 36

    y += 20
    draw.text((930, y), "Углы карты", fill="#182235", font=f_label)
    y += 42
    asc = chart.get("ascendant", {})
    mc = chart.get("mc", {})
    if asc:
        draw.text((930, y), "ASC Асцендент", fill="#182235", font=f_text)
        draw.text((1160, y), f"{asc['degree']:.2f}°", fill="#64748B", font=f_text)
        draw.text((1275, y), asc["sign"], fill="#182235", font=f_text)
        y += 36
    if mc:
        draw.text((930, y), "MC Мидхевен", fill="#182235", font=f_text)
        draw.text((1160, y), f"{mc['degree']:.2f}°", fill="#64748B", font=f_text)
        draw.text((1275, y), mc["sign"], fill="#182235", font=f_text)
        y += 50

    draw.text((930, y), "Ключевые аспекты", fill="#182235", font=f_label)
    y += 42
    for a in chart.get("aspects", [])[:6]:
        sym = aspect_symbols.get(a.get("aspect"), a.get("aspect"))
        draw.text((930, y), f"{a['planet1']} {sym} {a['planet2']}", fill="#182235", font=f_small)
        draw.text((1335, y), f"орб {a['orb']}°", fill="#64748B", font=f_small)
        y += 30

    # footer
    draw.rounded_rectangle((70, 910, 820, 965), radius=18, fill="#182235")
    draw.text((100, 927), "✦ ASTRONUM", fill="#FFFFFF", font=font(22, True))
    draw.text((300, 930), "Натальная карта построена по данным пользователя", fill="#E8F0FA", font=f_small)

    img.save(output_path, quality=95)
    return output_path

