import math
import html
import cairosvg


ZODIAC = [
    ("Овен", "♈", "#FDE2E2"),
    ("Телец", "♉", "#E2F7DF"),
    ("Близнецы", "♊", "#FFF3C4"),
    ("Рак", "♋", "#DFF3FF"),
    ("Лев", "♌", "#FFE0B8"),
    ("Дева", "♍", "#E8F5D6"),
    ("Весы", "♎", "#E8E5FF"),
    ("Скорпион", "♏", "#F4D7F1"),
    ("Стрелец", "♐", "#FFE7C8"),
    ("Козерог", "♑", "#E4EEF8"),
    ("Водолей", "♒", "#DFF7F4"),
    ("Рыбы", "♓", "#E7E2FF"),
]

PLANET_SYMBOLS = {
    "Солнце": "☉",
    "Луна": "☽",
    "Меркурий": "☿",
    "Венера": "♀",
    "Марс": "♂",
    "Юпитер": "♃",
    "Сатурн": "♄",
}

ASPECT_SYMBOLS = {
    "соединение": "☌",
    "секстиль": "✶",
    "квадрат": "□",
    "трин": "△",
    "оппозиция": "☍",
}


def esc(value):
    return html.escape(str(value), quote=True)


def point(cx, cy, degree, radius):
    angle = math.radians(180 - degree)
    return cx + math.cos(angle) * radius, cy - math.sin(angle) * radius


def sector_path(cx, cy, r_outer, r_inner, start_deg, end_deg):
    x1, y1 = point(cx, cy, start_deg, r_outer)
    x2, y2 = point(cx, cy, end_deg, r_outer)
    x3, y3 = point(cx, cy, end_deg, r_inner)
    x4, y4 = point(cx, cy, start_deg, r_inner)
    large = 1 if abs(end_deg - start_deg) > 180 else 0
    return (
        f"M {x1:.2f} {y1:.2f} "
        f"A {r_outer} {r_outer} 0 {large} 0 {x2:.2f} {y2:.2f} "
        f"L {x3:.2f} {y3:.2f} "
        f"A {r_inner} {r_inner} 0 {large} 1 {x4:.2f} {y4:.2f} Z"
    )


def generate_chart_svg(chart: dict, output_png: str):
    W, H = 1800, 1100
    cx, cy = 560, 610
    r_outer = 430
    r_mid = 352
    r_inner = 215
    r_aspect = 165

    planets = chart.get("planets", [])
    houses = chart.get("houses", [])
    aspects = chart.get("aspects", [])
    asc = chart.get("ascendant", {})
    mc = chart.get("mc", {})

    svg = []
    svg.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#FAFCFF"/>
    <stop offset="55%" stop-color="#F4F7FB"/>
    <stop offset="100%" stop-color="#EEF4FA"/>
  </linearGradient>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#64748B" flood-opacity="0.16"/>
  </filter>
  <style>
    .title {{ font-family: DejaVu Sans, Arial, sans-serif; font-size: 44px; font-weight: 800; fill:#182235; }}
    .sub {{ font-family: DejaVu Sans, Arial, sans-serif; font-size: 21px; fill:#64748B; }}
    .label {{ font-family: DejaVu Sans, Arial, sans-serif; font-size: 24px; font-weight: 800; fill:#182235; }}
    .text {{ font-family: DejaVu Sans, Arial, sans-serif; font-size: 20px; fill:#182235; }}
    .small {{ font-family: DejaVu Sans, Arial, sans-serif; font-size: 16px; fill:#64748B; }}
    .tiny {{ font-family: DejaVu Sans, Arial, sans-serif; font-size: 13px; fill:#64748B; }}
    .glyph {{ font-family: DejaVu Sans, Arial, sans-serif; font-size: 34px; font-weight: 800; fill:#182235; }}
    .zodiac {{ font-family: DejaVu Sans, Arial, sans-serif; font-size: 38px; font-weight: 800; fill:#182235; }}
    .water {{ font-family: DejaVu Sans, Arial, sans-serif; font-size: 96px; font-weight: 900; fill:#DCE8F5; opacity:0.42; }}
  </style>
</defs>
<rect width="1800" height="1100" fill="url(#bg)"/>
<circle cx="-100" cy="-80" r="360" fill="none" stroke="#DCE8F5" stroke-width="4"/>
<circle cx="1780" cy="1080" r="420" fill="none" stroke="#DCE8F5" stroke-width="4"/>
<text x="560" y="602" text-anchor="middle" class="water">ASTRONUM</text>
<text x="560" y="650" text-anchor="middle" class="small" opacity="0.35">ТВОЯ КАРТА · ТВОЙ ПУТЬ</text>
<text x="80" y="72" class="title">Натальная карта</text>
<text x="82" y="112" class="sub">премиальный астрологический расчёт</text>
<rect x="80" y="145" rx="22" ry="22" width="660" height="92" fill="#FFFFFF" stroke="#D7E3F1" stroke-width="2" filter="url(#shadow)"/>
<text x="112" y="183" class="text">{esc(chart.get("birth_date",""))} · {esc(chart.get("birth_time",""))} · {esc(chart.get("birth_city",""))}</text>
<text x="112" y="216" class="small">{esc(chart.get("latitude",""))}°, {esc(chart.get("longitude",""))}° · {esc(chart.get("timezone",""))}</text>
''')

    for i, (_, sym, color) in enumerate(ZODIAC):
        start = i * 30
        end = start + 30
        path = sector_path(cx, cy, r_outer, r_mid, start, end)
        svg.append(f'<path d="{path}" fill="{color}" stroke="#D8E2EF" stroke-width="1.4"/>')
        tx, ty = point(cx, cy, start + 15, 392)
        svg.append(f'<text x="{tx:.1f}" y="{ty+13:.1f}" text-anchor="middle" class="zodiac">{sym}</text>')

    for radius, stroke, width in [
        (r_outer, "#7C93B8", 3),
        (r_mid, "#B9C8DE", 2),
        (292, "#D8E2EF", 2),
        (r_inner, "#B9C8DE", 2),
        (95, "#D8E2EF", 2),
    ]:
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{stroke}" stroke-width="{width}"/>')

    for i in range(12):
        deg = i * 30
        x1, y1 = point(cx, cy, deg, r_inner)
        x2, y2 = point(cx, cy, deg, r_outer)
        svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#AFC1D8" stroke-width="2"/>')

    for h in houses:
        x1, y1 = point(cx, cy, h["longitude"], 80)
        x2, y2 = point(cx, cy, h["longitude"], r_outer + 12)
        svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#64748B" stroke-width="1.2" opacity="0.55"/>')
        tx, ty = point(cx, cy, h["longitude"] + 3, r_outer + 32)
        svg.append(f'<text x="{tx:.1f}" y="{ty+4:.1f}" text-anchor="middle" class="tiny">{h["house"]}</text>')

    lon_by_name = {p["name"]: p["longitude"] for p in planets}
    for a in aspects[:10]:
        p1, p2 = a.get("planet1"), a.get("planet2")
        if p1 not in lon_by_name or p2 not in lon_by_name:
            continue
        x1, y1 = point(cx, cy, lon_by_name[p1], r_aspect)
        x2, y2 = point(cx, cy, lon_by_name[p2], r_aspect)
        color = "#EF4444" if a.get("aspect") in ("квадрат", "оппозиция") else "#3B82F6"
        svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="2.2" opacity="0.72"/>')

    buckets = {}
    for p in planets:
        bucket = int(p["longitude"] // 6)
        buckets[bucket] = buckets.get(bucket, 0) + 1
        rr = 260 + buckets[bucket] * 22
        x, y = point(cx, cy, p["longitude"], rr)
        sym = PLANET_SYMBOLS.get(p["name"], p["name"][0])
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="29" fill="#FFFFFF" stroke="#7C93B8" stroke-width="2.2"/>')
        svg.append(f'<text x="{x:.1f}" y="{y+12:.1f}" text-anchor="middle" class="glyph">{sym}</text>')

    for key, label in [("ascendant", "ASC"), ("mc", "MC")]:
        item = chart.get(key, {})
        if item:
            x1, y1 = point(cx, cy, item["longitude"], 75)
            x2, y2 = point(cx, cy, item["longitude"], r_outer + 26)
            tx, ty = point(cx, cy, item["longitude"], r_outer + 62)
            svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#182235" stroke-width="3.4"/>')
            svg.append(f'<rect x="{tx-42:.1f}" y="{ty-18:.1f}" rx="12" ry="12" width="84" height="36" fill="#182235"/>')
            svg.append(f'<text x="{tx:.1f}" y="{ty+6:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial" font-size="16" font-weight="800" fill="#FFFFFF">{label}</text>')

    svg.append('''
<rect x="1030" y="62" rx="36" ry="36" width="685" height="930" fill="#FFFFFF" stroke="#D7E3F1" stroke-width="2" filter="url(#shadow)"/>
<text x="1080" y="128" font-family="DejaVu Sans, Arial" font-size="52" font-weight="900" fill="#182235">ASTRONUM</text>
<text x="1083" y="166" class="small">@astronum_aibot · t.me/astronum_aibot</text>
<line x1="1080" y1="200" x2="1660" y2="200" stroke="#D7E3F1" stroke-width="2"/>
<text x="1080" y="248" class="label">Планеты</text>
''')

    y = 288
    for p in planets:
        sym = PLANET_SYMBOLS.get(p["name"], "")
        svg.append(f'<text x="1080" y="{y}" class="text">{sym}  {esc(p["name"])}</text>')
        svg.append(f'<text x="1310" y="{y}" class="text">{p["degree"]:.2f}°</text>')
        svg.append(f'<text x="1425" y="{y}" class="text">{esc(p["sign"])}</text>')
        if p.get("house"):
            svg.append(f'<text x="1570" y="{y}" class="small">{p["house"]} дом</text>')
        y += 37

    y += 28
    svg.append(f'<text x="1080" y="{y}" class="label">Углы карты</text>')
    y += 42
    for label, item in [("ASC Асцендент", asc), ("MC Мидхевен", mc)]:
        if item:
            svg.append(f'<text x="1080" y="{y}" class="text">{label}</text>')
            svg.append(f'<text x="1310" y="{y}" class="text">{item["degree"]:.2f}°</text>')
            svg.append(f'<text x="1425" y="{y}" class="text">{esc(item["sign"])}</text>')
            y += 37

    y += 30
    svg.append(f'<text x="1080" y="{y}" class="label">Ключевые аспекты</text>')
    y += 38
    for a in aspects[:6]:
        sym = ASPECT_SYMBOLS.get(a.get("aspect"), a.get("aspect"))
        svg.append(f'<text x="1080" y="{y}" class="small">{esc(a["planet1"])} {sym} {esc(a["planet2"])}</text>')
        svg.append(f'<text x="1530" y="{y}" class="small">орб {a["orb"]}°</text>')
        y += 31

    svg.append('''
<rect x="80" y="1000" rx="20" ry="20" width="800" height="64" fill="#182235"/>
<text x="115" y="1042" font-family="DejaVu Sans, Arial" font-size="24" font-weight="900" fill="#FFFFFF">✦ ASTRONUM</text>
<text x="330" y="1041" font-family="DejaVu Sans, Arial" font-size="17" fill="#DDE8F5">натальная карта построена по данным пользователя</text>
</svg>
''')

    svg_text = "".join(svg)
    cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=output_png, output_width=W, output_height=H)
    return output_png
