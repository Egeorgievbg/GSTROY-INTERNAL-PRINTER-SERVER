from datetime import datetime
from typing import Any, Iterable, Mapping

from flask import current_app

from .text_utils import clean_text, format_smart_numbers


def _clamp_copies(copies: int) -> int:
    maximum = int(current_app.config.get("MAX_COPIES", 50))
    return max(1, min(int(copies or 1), maximum))


def _render_quantity_component(value: Any, unit: Any) -> str:
    value_text = clean_text(value)
    if not value_text:
        return ""
    unit_text = clean_text(unit)
    return f"{value_text} {unit_text}".strip()


def build_unit_info(unit_info: Any, quantity: Any, quantities: Iterable[Mapping[str, Any]] | None) -> str:
    if unit_info:
        return format_smart_numbers(clean_text(unit_info))

    components: list[str] = []
    if quantities:
        for entry in quantities:
            if not isinstance(entry, Mapping):
                continue
            rendered = _render_quantity_component(entry.get("value"), entry.get("unit"))
            if rendered:
                components.append(rendered)

    if components:
        return " / ".join(components)

    if quantity is not None:
        fallback = clean_text(quantity)
        if fallback:
            return format_smart_numbers(fallback)

    return ""


def generate_pro_product_label(name: str, barcode: str, unit_info: str, copies: int) -> str:
    """
    PRODUCT LABEL - SAFETY FIRST VERSION
    - Шрифтовете са намалени леко.
    - Всички елементи са сбутани нагоре.
    - Оставя много място (бяло поле) най-отдолу, за да не реже нищо.
    """
    copies = _clamp_copies(copies)
    width = current_app.config.get("LABEL_WIDTH", 400)
    height = current_app.config.get("LABEL_HEIGHT", 240)

    name = clean_text(name)
    barcode = clean_text(barcode)
    unit_info = format_smart_numbers(clean_text(unit_info))
    timestamp = datetime.now().strftime("%d.%m.%y %H:%M")

    zpl = [
        "^XA",
        "^CI28",
        f"^PW{width}",
        f"^LL{height}",
        
        # --- HEADER ---
        # 1. ДАТА: Горе вдясно.
        f"^FO220,5^A0N,18,18^FB170,1,0,R,0^FD{timestamp}^FS",
        
        # 2. ИМЕ НА ПРОДУКТА:
        # Свалено на Y=25 (под датата).
        # Намален шрифт на 22 (беше 24), за да се събира по-добре.
        f"^FO10,25^A0N,22,22^FB380,2,0,C,0^FD{name}^FS",
        
        # Линия 1: Вдигната на Y=65
        f"^FO10,65^GB380,2,2^FS",

        # --- BODY (BARCODE) ---
        # 3. БАРКОД:
        # Вдигнат на Y=70.
        # Височината е намалена драстично на 40 (беше 55+). Пак ще се чете без проблем.
        "^FO60,70^BY2,2,40^BCN,40,N,N,N",
        f"^FD{barcode}^FS",
        
        # Текст на баркода (цифрите): Вдигнат на Y=115
        f"^FO10,115^A0N,20,20^FB380,1,0,C,0^FD{barcode}^FS",

        # Линия 2: Вдигната на Y=140
        f"^FO10,140^GB380,2,2^FS",

        # --- FOOTER ---
        # 4. КОЛИЧЕСТВО (0 БРОЙ / 0 БРОЙ):
        # Вдигнат на Y=145 (Преди беше 165). Това са 20 точки нагоре (около 3мм).
        # Шрифтът е намален на 24 (беше 28), за да е по-компактен.
        # Това гарантира, че текстът приключва на позиция 170, а етикетът е дълъг 240.
        # Има 70 точки празно място отдолу - НЯМА да се отреже.
        f"^FO10,145^A0N,24,24^FB380,1,0,C,0^FD{unit_info}^FS",
        
        f"^PQ{copies}",
        "^XZ",
    ]
    return "".join(zpl)

def generate_list_label(title: str, qr_data: str, copies: int) -> str:
    """
    LIST LABEL - COMPACT VERSION
    """
    copies = _clamp_copies(copies)
    width = current_app.config.get("LABEL_WIDTH", 400)
    height = current_app.config.get("LABEL_HEIGHT", 240)

    title = clean_text(title)
    qr_data = clean_text(qr_data)
    timestamp = datetime.now().strftime("%d.%m.%y %H:%M")

    zpl = [
        "^XA",
        "^CI28",
        f"^PW{width}",
        f"^LL{height}",

        # Дата: Малка
        f"^FO220,5^A0N,18,18^FB170,1,0,R,0^FD{timestamp}^FS",
        
        # Заглавие: По-компактно (шрифт 24)
        f"^FO10,15^A0N,24,24^FB240,3,0,L,0^FD{title}^FS",
        
        # QR Code: Позиция Y=20
        "^FO260,20^BQN,2,5", 
        f"^FDLA,{qr_data}^FS",
        
        # Линия: Y=155 (синхронизирано с другия етикет)
        f"^FO10,155^GB380,2,2^FS",
        
        # Footer: Y=165 (Много въздух отдолу)
        f"^FO10,165^A0N,26,26^FB380,1,0,C,0^FD{qr_data}^FS",
        
        f"^PQ{copies}",
        "^XZ",
    ]
    return "".join(part for part in zpl if part)