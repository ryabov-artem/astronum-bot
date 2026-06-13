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

EXTRA_POINTS = {
    "Северный узел": swe.MEAN_NODE,
}

SIGN_SYMBOLS = {
    "Овен": "♈",
    "Телец": "♉",
    "Близнецы": "♊",
    "Рак": "♋",
    "Лев": "♌",
    "Дева": "♍",
    "Весы": "♎",
    "Скорпион": "♏",
    "Стрелец": "♐",
    "Козерог": "♑",
    "Водолей": "♒",
    "Рыбы": "♓",
}

PLANET_SYMBOLS = {
    "Солнце": "☉",
    "Луна": "☽",
    "Меркурий": "☿",
    "Венера": "♀",
    "Марс": "♂",
    "Юпитер": "♃",
    "Сатурн": "♄",
    "Хирон": "⚷",
    "Лилит": "⚸",
    "Северный узел": "☊",
    "Южный узел": "☋",
}

SIGN_ELEMENTS = {
    "Овен": "fire",
    "Лев": "fire",
    "Стрелец": "fire",
    "Телец": "earth",
    "Дева": "earth",
    "Козерог": "earth",
    "Близнецы": "air",
    "Весы": "air",
    "Водолей": "air",
    "Рак": "water",
    "Скорпион": "water",
    "Рыбы": "water",
}

SIGN_MODALITY = {
    "Овен": "cardinal",
    "Рак": "cardinal",
    "Весы": "cardinal",
    "Козерог": "cardinal",
    "Телец": "fixed",
    "Лев": "fixed",
    "Скорпион": "fixed",
    "Водолей": "fixed",
    "Близнецы": "mutable",
    "Дева": "mutable",
    "Стрелец": "mutable",
    "Рыбы": "mutable",
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



def point_data(name: str, longitude: float) -> dict:
    sign = sign_name(longitude)
    return {
        "name": name,
        "symbol": PLANET_SYMBOLS.get(name, ""),
        "longitude": round(longitude % 360, 2),
        "sign": sign,
        "sign_symbol": SIGN_SYMBOLS.get(sign, ""),
        "degree": round(degree_in_sign(longitude), 2),
    }


def calculate_balance(items: list[dict], mapping: dict, keys: list[str]) -> dict:
    counts = {key: 0 for key in keys}

    for item in items:
        key = mapping.get(item.get("sign"))
        if key in counts:
            counts[key] += 1

    total = sum(counts.values()) or 1
    return {key: round(counts[key] * 100 / total) for key in keys}


def find_dominant_sign(items: list[dict]) -> dict:
    counts = {}

    for item in items:
        sign = item.get("sign")
        if sign:
            counts[sign] = counts.get(sign, 0) + 1

    if not counts:
        name = "Не определён"
    else:
        name = max(counts, key=counts.get)

    return {
        "name": name,
        "symbol": SIGN_SYMBOLS.get(name, ""),
    }


def calculate_top_planets(planets: list[dict], limit: int = 3) -> list[dict]:
    weights = {
        "Солнце": 5,
        "Луна": 5,
        "Меркурий": 3,
        "Венера": 3,
        "Марс": 3,
        "Юпитер": 2,
        "Сатурн": 2,
    }

    scored = []

    for planet in planets:
        name = planet.get("name")
        score = weights.get(name, 1)

        house = planet.get("house")
        if house in (1, 4, 7, 10):
            score += 2

        item = dict(planet)
        item["score"] = score
        item["percent"] = round(score * 100 / 30)
        scored.append(item)

    scored.sort(key=lambda x: x.get("score", 0), reverse=True)

    top = scored[:limit]
    max_score = max((item.get("score", 0) for item in top), default=1) or 1

    for item in top:
        item["percent"] = round(item.get("score", 0) * 100 / max_score)

    return top


def find_dominant_planet(planets: list[dict]) -> dict:
    if not planets:
        return {"name": "Не определена", "symbol": ""}

    weights = {
        "Солнце": 5,
        "Луна": 5,
        "Меркурий": 3,
        "Венера": 3,
        "Марс": 3,
        "Юпитер": 2,
        "Сатурн": 2,
    }

    scores = {}

    for planet in planets:
        name = planet.get("name")
        score = weights.get(name, 1)

        house = planet.get("house")
        if house in (1, 4, 7, 10):
            score += 2

        scores[name] = scores.get(name, 0) + score

    name = max(scores, key=scores.get)

    return {
        "name": name,
        "symbol": PLANET_SYMBOLS.get(name, ""),
    }


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
        planets.append(point_data(name, pos[0]))

    extra_points = []
    for name, point_id in EXTRA_POINTS.items():
        pos, _ = swe.calc_ut(jd, point_id)
        extra_points.append(point_data(name, pos[0]))

    north_node = next((p for p in extra_points if p["name"] == "Северный узел"), None)

    if north_node:
        south_lon = (north_node["longitude"] + 180) % 360
        south_node = point_data("Южный узел", south_lon)
    else:
        south_node = None

    visible_planets = planets + extra_points
    if south_node:
        visible_planets.append(south_node)

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

    for planet in visible_planets:
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
        "planets": visible_planets,
        "houses": houses,
        "aspects": calculate_aspects(planets),
        "elements": calculate_balance(planets, SIGN_ELEMENTS, ["fire", "earth", "air", "water"]),
        "modality": calculate_balance(planets, SIGN_MODALITY, ["cardinal", "fixed", "mutable"]),
        "dominant_planet": find_dominant_planet(planets),
        "dominant_sign": find_dominant_sign(planets),
        "top_planets": calculate_top_planets(planets),
        "dominant_planets": calculate_top_planets(planets),
        "points": {
            "north_node": north_node,
            "south_node": south_node,
        },
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

    # Увеличили холст до 750x750, чтобы убрать лишнее пустое пространство
    W, H = 750, 750
    img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
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

    f_tiny = font(14, True)
    f_symbol = font(28, True)  # Увеличили размер планет для лучшей читаемости

    cx, cy = 375, 375  # Новая центральная точка на холсте 750x750
    
    # Пропорционально увеличили все радиусы
    R_outer = 310
    R_zodiac = 265
    R_inner = 160
    R_aspect = 145

    zodiac_symbols = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
    planet_symbols = {
        "Солнце": "☉", "Луна": "☽", "Меркурий": "☿", "Венера": "♀", 
        "Марс": "♂", "Юпитер": "♃", "Сатурн": "♄"
    }

    # Вычисляем сдвиг: ASC должен быть строго слева (180°)
    asc_long = chart.get("ascendant", {}).get("longitude", 0.0)
    
    def xy(deg, r):
        adjusted_deg = (deg - asc_long + 180) % 360
        a = math.radians(adjusted_deg)
        return (cx + math.cos(a) * r, cy - math.sin(a) * r)

    # Отрисовка колец с повышенной толщиной (width) для контраста
    for r, color, width in [
        (R_outer, "#1E293B", 4),  # Сделали темнее и толще
        (R_zodiac, "#7C93B8", 3),
        (215, "#CBD8EA", 2),
        (R_inner, "#7C93B8", 3),
        (60, "#DDE8F5", 2),
    ]:
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=color, width=width)

    # Сектора знаков зодиака
    for i, sym in enumerate(zodiac_symbols):
        deg = i * 30
        x1, y1 = xy(deg, R_inner)
        x2, y2 = xy(deg, R_outer)
        draw.line((x1, y1, x2, y2), fill="#7C93B8", width=3)  # Сделали разделители контрастнее

        tx, ty = xy(deg + 15, 288)
        draw.text((tx, ty), sym, fill="#1E293B", font=font(26, True), anchor="mm")

        # Рисочки градусов внутри секторов
        for d in range(5, 30, 5):
            xx1, yy1 = xy(deg + d, 235)
            xx2, yy2 = xy(deg + d, 245)
            draw.line((xx1, yy1, xx2, yy2), fill="#94A3B8", width=2)

    # Аспекты внутри круга (сделали линии чуть толще — width=3)
    planets = chart.get("planets", [])
    lon_by_name = {pl["name"]: pl["longitude"] for pl in planets}
    for a in chart.get("aspects", [])[:8]:
        p1 = a.get("planet1")
        p2 = a.get("planet2")
        if p1 not in lon_by_name or p2 not in lon_by_name:
            continue
        x1, y1 = xy(lon_by_name[p1], R_aspect)
        x2, y2 = xy(lon_by_name[p2], R_aspect)
        color = "#EF4444" if a.get("aspect") in ("квадрат", "оппозиция") else "#3B82F6"
        draw.line((x1, y1, x2, y2), fill=color, width=3)

    # Планеты на круге
    used = {}
    for pl in planets:
        deg = pl["longitude"]
        bucket = int(deg // 12)
        used[bucket] = used.get(bucket, 0) + 1
        offset = used[bucket] * 20
        px, py = xy(deg, 175 + offset)
        sym = planet_symbols.get(pl["name"], pl["name"][0])
        
        # Белая подложка-кружок под планету с контрастной рамкой
        draw.ellipse((px-18, py-18, px+18, py+18), fill="#FFFFFF", outline="#1E293B", width=2)
        draw.text((px, py + 1), sym, fill="#1E293B", font=f_symbol, anchor="mm")

    # Оси ASC / MC (Главные оси карты, делаем их максимально четкими)
    for key, label in [("ascendant", "ASC"), ("mc", "MC")]:
        item = chart.get(key, {})
        if item:
            deg = item["longitude"]
            x1, y1 = xy(deg, 60)
            x2, y2 = xy(deg, R_outer + 15)
            draw.line((x1, y1, x2, y2), fill="#1E293B", width=3)
            
            tx, ty = xy(deg, R_outer + 28)
            draw.text((tx, ty), label, fill="#1E293B", font=f_tiny, anchor="mm")

    img.save(output_path, "PNG", quality=95)
    return output_path
