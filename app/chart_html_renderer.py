import math
import base64
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from app.astrology.real_chart import calculate_real_chart

BASE = Path("/opt/bots/astrology_bot")
OUT = BASE / "data/generated_charts/test_natal_card_html.png"

chart = calculate_real_chart("29.05.1995", "12:30", "Москва")

def deg_text(item):
    return f"{item['degree']:.1f}° {item['sign']}"

sun = next(p for p in chart["planets"] if p["name"] == "Солнце")
moon = next(p for p in chart["planets"] if p["name"] == "Луна")

env = Environment(loader=FileSystemLoader(BASE / "app/templates"))
template = env.get_template("natal_card.html")

# Вырезаем круг из существующей полной карты
from PIL import Image
src = BASE / "data/generated_charts/test_circle.png"
wheel = BASE / "data/generated_charts/wheel_crop.png"
if src.exists():
    im = Image.open(src).convert("RGBA")
    crop = im.crop((70, 120, 900, 950))
    crop.save(wheel)

html = template.render(
    chart=chart,
    sun=sun,
    moon=moon,
    asc=chart["ascendant"],
    mc=chart["mc"],
    deg_text=deg_text,
    wheel_uri='data:image/png;base64,' + base64.b64encode(wheel.read_bytes()).decode('ascii'),
)

html_path = BASE / "data/generated_charts/test_natal_card.html"
html_path.write_text(html, encoding="utf-8")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1536, "height": 1024}, device_scale_factor=1)
    page.set_content(html, wait_until="networkidle")
    page.screenshot(path=str(OUT), full_page=True)
    browser.close()

print(OUT)
