from datetime import datetime

SIGNS = [
    ((1,20),"♒ Водолей"),((2,19),"♓ Рыбы"),((3,21),"♈ Овен"),
    ((4,20),"♉ Телец"),((5,21),"♊ Близнецы"),((6,22),"♋ Рак"),
    ((7,23),"♌ Лев"),((8,23),"♍ Дева"),((9,23),"♎ Весы"),
    ((10,23),"♏ Скорпион"),((11,22),"♐ Стрелец"),((12,22),"♑ Козерог")
]

def parse_birth_date(date_text:str):
    return datetime.strptime(date_text.strip(), "%d.%m.%Y")

def zodiac_sign(date_text:str):
    dt = parse_birth_date(date_text)
    m,d = dt.month, dt.day
    sign = "♑ Козерог"
    for (sm,sd),name in SIGNS:
        if (m,d) >= (sm,sd):
            sign = name
    return {
        "birth_date": date_text,
        "sign": sign
    }
