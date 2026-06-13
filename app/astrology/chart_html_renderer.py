import base64
import os
from jinja2 import Template
from playwright.sync_api import sync_playwright

def build_natal_card_image(chart_data, wheel_png_path, output_final_png):
    # 1. Читаем PNG колеса и кодируем в Base64
    with open(wheel_png_path, "rb") as img_f:
        wheel_base64 = base64.b64encode(img_f.read()).decode("utf-8")

    # 2. Путь к шаблону natal_card.html
    template_path = "/opt/bots/astrology_bot/app/templates/natal_card.html" # Проверь этот путь!
    
    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()

    # 3. Вытаскиваем Солнце и Луну для блока Большой Тройки
    sun_data = next((p for p in chart_data["planets"] if p["name"] == "Солнце"), {"sign": "Неизвестно", "degree": 0.0})
    moon_data = next((p for p in chart_data["planets"] if p["name"] == "Луна"), {"sign": "Неизвестно", "degree": 0.0})

    points = chart_data.get("points") or {}

    chart_data["north_node"] = points.get("north_node")
    chart_data["south_node"] = points.get("south_node")

    context = {
        "chart": chart_data,
        "asc": chart_data["ascendant"],
        "mc": chart_data["mc"],
        "sun": sun_data,
        "moon": moon_data,
        "north_node": points.get("north_node"),
        "south_node": points.get("south_node"),
        "elements": chart_data.get("elements"),
        "modality": chart_data.get("modality"),
        "dominant_planet": chart_data.get("dominant_planet"),
        "dominant_sign": chart_data.get("dominant_sign"),
        "wheel_base64": wheel_base64
    }

    # Рендерим HTML текст через Jinja2
    template = Template(template_html)
    final_html = template.render(**context)

    # 4. Скриншот через Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = browser.new_page()
        page.set_viewport_size({"width": 1536, "height": 1024})
        page.set_content(final_html)
        
        # Ждем шрифты
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=output_final_png, full_page=True)
        browser.close()

    return output_final_png
