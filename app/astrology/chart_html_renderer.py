import base64
import os
from jinja2 import Template
from playwright.sync_api import sync_playwright

def deg_to_text(item_dict):
    """Вспомогательная функция для форматирования градусов в шаблоне"""
    if not item_dict or "degree" not in item_dict:
        return "0.0°"
    return f"{item_dict.get('degree', 0.0):.2f}° {item_dict.get('sign', '')}"

def build_natal_card_image(chart_data, wheel_png_path, output_final_png):
    # 1. Читаем PNG колеса и переводим в Base64
    with open(wheel_png_path, "rb") as img_f:
        wheel_base64 = base64.b64encode(img_f.read()).decode("utf-8")

    # 2. Путь к шаблону natal_card.html
    template_path = os.path.join(os.path.dirname(__file__), "templates", "natal_card.html")
    # Если папки templates нет, укажи прямой абсолютный путь к natal_card.html
    if not os.path.exists(template_path):
        template_path = "/opt/bots/astrology_bot/app/templates/natal_card.html" # поменяй если лежит в другом месте

    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()

    # 3. Готовим контекст для Jinja2 на основе структуры из real_chart.py
    # Ищем Солнце и Луну в списке планет для "Большой тройки"
    sun_data = next((p for p in chart_data["planets"] if p["name"] == "Солнце"), {"sign": "Неизвестно", "degree": 0.0})
    moon_data = next((p for p in chart_data["planets"] if p["name"] == "Луна"), {"sign": "Неизвестно", "degree": 0.0})

    context = {
        "chart": chart_data,
        "asc": chart_data["ascendant"],
        "mc": chart_data["mc"],
        "sun": sun_data,
        "moon": moon_data,
        "wheel_base64": wheel_base64,
        "deg_text": deg_to_text
    }

    # Рендерим HTML
    template = Template(template_html)
    final_html = template.render(**context)

    # 4. Рендерим через Playwright в итоговый файл
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = browser.new_page()
        page.set_viewport_size({"width": 1536, "height": 1024})
        page.set_content(final_html)
        
        # Ожидаем загрузки красивых шрифтов Google Fonts
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=output_final_png, full_page=True)
        browser.close()

    return output_final_png
