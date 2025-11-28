from datetime import datetime
from flask import current_app

from .text_utils import clean_text, format_smart_numbers


def _clamp_copies(copies: int) -> int:
    maximum = int(current_app.config.get("MAX_COPIES", 50))
    return max(1, min(int(copies or 1), maximum))


def generate_pro_product_label(name: str, barcode: str, unit_info: str, copies: int) -> str:
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
        f"^FO150,5^A0N,18,18^FB240,1,0,R,0^FD{timestamp}^FS",
        f"^FO10,25^A0N,24,24^FB380,2,0,C,0^FD{name}^FS",
        "^FO60,85^BY2,2,50^BCN,50,N,N,N",
        f"^FD{barcode}^FS",
        f"^FO10,145^A0N,22,22^FB380,1,0,C,0^FD{barcode}^FS",
        f"^FO0,175^GB{width},65,65^FS",
        f"^FO10,192^A0N,24,24^FR^FB380,1,0,C,0^FD{unit_info}^FS",
        f"^PQ{copies}",
        "^XZ",
    ]
    return "".join(zpl)


def generate_list_label(title: str, qr_data: str, copies: int) -> str:
    copies = _clamp_copies(copies)
    width = current_app.config.get("LABEL_WIDTH", 400)

    title = clean_text(title)
    qr_data = clean_text(qr_data)
    line1 = title[:20]
    line2 = title[20:40]

    zpl = [
        "^XA",
        "^CI28",
        f"^PW{width}",
        "^LL240",
        f"^FO15,20^A0N,32,32^FD{line1}^FS",
        f"^FO15,60^A0N,28,28^FD{line2}^FS" if line2 else "",
        "^FO240,30^BQN,2,5",
        f"^FDLA,{qr_data}^FS",
        f"^FO230,190^A0N,18,18^FD{qr_data[:15]}^FS",
        f"^PQ{copies}",
        "^XZ",
    ]
    return "".join(part for part in zpl if part)
