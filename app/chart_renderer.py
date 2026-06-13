from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

from app.astrology.real_chart import calculate_real_chart

OUT = "data/generated_charts/test_natal_card.png"
W, H = 1536, 1024

BG = "#FBF7EF"
INK = "#142033"
GOLD = "#B97A2B"
LINE = "#D7B98A"
BLUE = "#7894BD"

SIGNS = ["Овен","Телец","Близнецы","Рак","Лев","Дева","Весы","Скорпион","Стрелец","Козерог","Водолей","Рыбы"]
SIGN_GLYPHS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
PLANET_GLYPHS = {"Солнце":"☉","Луна":"☽","Меркурий":"☿","Венера":"♀","Марс":"♂","Юпитер":"♃","Сатурн":"♄"}

def font(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)

def pt(cx, cy, deg, r):
    a = math.radians(deg - 90)
    return cx + math.cos(a) * r, cy + math.sin(a) * r

def rounded(draw, box, radius=18, fill=None, outline=LINE, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def deg_text(item, digits=1):
    return f"{item['degree']:.{digits}f}° {item['sign']}"

chart = calculate_real_chart("29.05.1995", "12:30", "Москва")
sun = next(p for p in chart["planets"] if p["name"] == "Солнце")
moon = next(p for p in chart["planets"] if p["name"] == "Луна")

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

f_title = font(72)
f_sub = font(25, True)
f_h = font(25, True)
f = font(21)
f_s = font(18)
f_xs = font(14)
f_big = font(34)
f_value = font(32)

# Заголовок
draw.text((W//2, 32), "АСТРОНУМ", font=f_title, fill=INK, anchor="ma")
draw.text((W//2, 115), "✦ НАТАЛЬНАЯ КАРТА ✦", font=f_sub, fill=GOLD, anchor="ma")

# Верхняя строка данных
rounded(draw, (70, 145, 1040, 225), 16, fill="#FFFDF8")
top = [
    ("ДАТА РОЖДЕНИЯ", chart["birth_date"]),
    ("ВРЕМЯ РОЖДЕНИЯ", chart["birth_time"]),
    ("МЕСТО РОЖДЕНИЯ", chart["birth_city"]),
    ("АСЦЕНДЕНТ", deg_text(chart["ascendant"], 2)),
    ("MC", deg_text(chart["mc"], 2)),
]
for x, (label, value) in zip([165, 350, 545, 765, 950], top):
    draw.text((x, 163), label, font=f_xs, fill=INK, anchor="ma")
    draw.text((x, 195), value, font=f, fill=INK, anchor="ma")

# Круг
cx, cy = 505, 555
r_outer, r_mid, r_inner, r_aspect = 300, 250, 125, 110
colors = ["#F9D5D0","#DDF3D1","#FFF0B8","#D9EFFA","#F9D5A7","#E4F4D2","#E4E1FA","#F3D1EC","#F8D8AA","#DCEAF5","#D8F2EF","#E7DDF8"]

for i in range(12):
    start = i * 30 - 90
    end = start + 30
    draw.pieslice((cx-r_outer, cy-r_outer, cx+r_outer, cy+r_outer), start, end, fill=colors[i], outline=LINE)
    draw.pieslice((cx-r_mid, cy-r_mid, cx+r_mid, cy+r_mid), start, end, fill=BG, outline=LINE)
    tx, ty = pt(cx, cy, i * 30 + 15, r_outer - 34)
    draw.text((tx, ty), SIGN_GLYPHS[i], font=f_big, fill=INK, anchor="mm")

draw.ellipse((cx-r_outer, cy-r_outer, cx+r_outer, cy+r_outer), outline=BLUE, width=3)
draw.ellipse((cx-r_mid, cy-r_mid, cx+r_mid, cy+r_mid), outline="#C7D3E2", width=2)
draw.ellipse((cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner), outline="#C7D3E2", width=2)
draw.ellipse((cx-38, cy-38, cx+38, cy+38), outline="#E6D3B4", width=1)

for i in range(12):
    x1, y1 = pt(cx, cy, i * 30, 35)
    x2, y2 = pt(cx, cy, i * 30, r_outer + 10)
    draw.line((x1, y1, x2, y2), fill="#AAB9CD", width=1)
    tx, ty = pt(cx, cy, i * 30 + 7, r_outer + 20)
    draw.text((tx, ty), str(i + 1), font=f_xs, fill="#637792", anchor="mm")

# ASC / MC
for key, label in [("ascendant", "ASC"), ("mc", "MC")]:
    item = chart[key]
    x1, y1 = pt(cx, cy, item["longitude"], 45)
    x2, y2 = pt(cx, cy, item["longitude"], r_outer + 18)
    draw.line((x1, y1, x2, y2), fill=INK, width=2)
    label_radius = r_outer + 42
    lx, ly = pt(cx, cy, item["longitude"], label_radius)
    rounded(draw, (lx-36, ly-17, lx+36, ly+17), 9, fill=INK, outline=INK)
    draw.text((lx, ly), label, font=f_xs, fill="white", anchor="mm")

# Аспекты
lon = {p["name"]: p["longitude"] for p in chart["planets"]}
for a in chart.get("aspects", [])[:8]:
    if a["planet1"] in lon and a["planet2"] in lon:
        x1, y1 = pt(cx, cy, lon[a["planet1"]], r_aspect)
        x2, y2 = pt(cx, cy, lon[a["planet2"]], r_aspect)
        col = "#E54848" if a["aspect"] in ("квадрат", "оппозиция") else "#3B82F6"
        draw.line((x1, y1, x2, y2), fill=col, width=2)

# Планеты на круге
used = {}
for p in chart["planets"]:
    bucket = int(p["longitude"] // 4)
    used[bucket] = used.get(bucket, 0) + 1
    rr = 165 + used[bucket] * 42
    x, y = pt(cx, cy, p["longitude"], rr)
    draw.ellipse((x-22, y-22, x+22, y+22), fill="#FFFDF8", outline=BLUE, width=2)
    draw.text((x, y+1), PLANET_GLYPHS.get(p["name"], p["name"][0]), font=f_big, fill=INK, anchor="mm")

# Правая панель
rounded(draw, (1070, 145, 1470, 815), 18, fill="#FFFDF8")
draw.text((1110, 185), "ПЛАНЕТЫ", font=f_h, fill=GOLD)
y = 225
for p in chart["planets"]:
    draw.text((1110, y), f"{PLANET_GLYPHS.get(p['name'],'')} {p['name']}", font=f_s, fill=INK)
    draw.text((1260, y), f"{p['degree']:.2f}°", font=f_s, fill=INK)
    draw.text((1360, y), p["sign"], font=f_s, fill=INK)
    y += 34

draw.line((1110, y+12, 1430, y+12), fill=LINE, width=1)
y += 52
draw.text((1110, y), "УГЛЫ КАРТЫ", font=f_h, fill=GOLD)
y += 42
draw.text((1110, y), f"ASC Асцендент     {deg_text(chart['ascendant'], 2)}", font=f_s, fill=INK)
y += 34
draw.text((1110, y), f"MC Мидхевен       {deg_text(chart['mc'], 2)}", font=f_s, fill=INK)

draw.line((1110, y+45, 1430, y+45), fill=LINE, width=1)
y += 85
draw.text((1110, y), "КЛЮЧЕВЫЕ АСПЕКТЫ", font=f_h, fill=GOLD)
y += 40
for a in chart.get("aspects", [])[:5]:
    draw.text((1110, y), f"{a['planet1']} {a['aspect']} {a['planet2']}", font=f_xs, fill=INK)
    draw.text((1430, y), f"орб {a['orb']}°", font=f_xs, fill="#66758E", anchor="ra")
    y += 28

# Большая тройка
rounded(draw, (70, 835, 1470, 960), 18, fill="#FFFDF8")
draw.text((768, 852), "✦ ВАША БОЛЬШАЯ ТРОЙКА ✦", font=f_h, fill=INK, anchor="ma")

draw.text((250, 882), "☉ СОЛНЦЕ", font=f_s, fill=GOLD)
draw.text((250, 922), f"{sun['sign']} {sun['degree']:.1f}°", font=font(44), fill=INK)

draw.line((575, 875, 575, 930), fill=LINE, width=1)
draw.text((680, 882), "☽ ЛУНА", font=f_s, fill=GOLD)
draw.text((680, 922), f"{moon['sign']} {moon['degree']:.1f}°", font=font(44), fill=INK)

draw.line((1005, 875, 1005, 930), fill=LINE, width=1)
draw.text((1110, 882), "↑ АСЦЕНДЕНТ", font=f_s, fill=GOLD)
draw.text((1110, 922), f"{chart['ascendant']['sign']} {chart['ascendant']['degree']:.1f}°", font=font(44), fill=INK)

# Футер
draw.text((W//2, 995), "Познай себя. Используй свои сильные стороны. Создавай своё будущее.  ✦  АСТРОНУМ  ✦  @astronum_aibot", font=f_s, fill=INK, anchor="mm")

Path("data/generated_charts").mkdir(parents=True, exist_ok=True)
img.save(OUT, quality=95)
print(OUT)
