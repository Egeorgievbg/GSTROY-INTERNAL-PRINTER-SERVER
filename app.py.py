#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import socket
import ipaddress
import time
from typing import Dict, Any, Optional
from flask import Flask, jsonify, request, abort

# ============================================================
# ⚙️ НАСТРОЙКИ НА СЪРВЪРА
# ============================================================

# Порт на самия Python сървър
SERVER_PORT = int(os.environ.get("LABEL_SERVER_PORT", "8001"))

# Порт на Zebra принтерите (стандартен)
PRINTER_PORT = 9100

# Тайминг настройки (в секунди)
# Важно: Ping timeout е кратък, за да не бави интерфейса на ERP-то
PING_TIMEOUT = 0.5      
PRINT_CONNECT_TIMEOUT = 2.0
PRINT_WRITE_TIMEOUT = 3.0

# Лимити за безопасност
MAX_COPIES = 50         # Макс. копия наведнъж
MAX_TEXT_LEN = 50       # Макс. символи за име на продукт

# ============================================================
# 🚀 FLASK APP SETUP
# ============================================================

app = Flask(__name__)

# Глобален CORS (Разрешава достъп от всякакви локални IP-та)
@app.after_request
def add_cors_headers(response):
    response.headers.setdefault("Access-Control-Allow-Origin", "*")
    response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type")
    return response

# ============================================================
# 🛠 ПОМОЩНИ ФУНКЦИИ (HELPERS)
# ============================================================

def validate_ip(ip: str) -> str:
    """
    Проверява дали подаденият стринг е валиден IPv4 адрес.
    Не проверява дали е в 'разрешен списък', за да има гъвкавост.
    """
    try:
        ipaddress.IPv4Address(ip)
        return ip
    except ValueError:
        raise ValueError(f"Невалиден IP формат: {ip}")

def check_printer_online(ip: str) -> bool:
    """
    Бърза проверка дали порт 9100 е отворен.
    """
    ip = validate_ip(ip)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(PING_TIMEOUT)
    try:
        s.connect((ip, PRINTER_PORT))
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
    finally:
        s.close()

def send_zpl_to_socket(ip: str, zpl_code: str):
    """
    Изпраща ZPL кода директно към принтера.
    """
    ip = validate_ip(ip)
    if not zpl_code:
        raise ValueError("Липсва ZPL код.")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(PRINT_CONNECT_TIMEOUT)
    
    try:
        sock.connect((ip, PRINTER_PORT))
        sock.settimeout(PRINT_WRITE_TIMEOUT)
        sock.sendall(zpl_code.encode("utf-8")) 
    except socket.timeout:
        raise TimeoutError(f"Таймаут при връзка с принтер {ip}")
    except OSError as e:
        raise OSError(f"Грешка при комуникация с {ip}: {e}")
    finally:
        sock.close()

# --- Санитизация на данни ---

def clean_text(text: Any) -> str:
    """Чисти забранени символи и ограничава дължината."""
    if not text: 
        return ""
    # Премахваме ZPL контролни символи и нови редове
    s = str(text).replace("^", "").replace("~", "").replace("\n", " ").strip()
    return s[:MAX_TEXT_LEN]

def clean_qty(qty: Any) -> str:
    """Форматира количеството (маха .00 ако е цяло число)."""
    if qty is None: return ""
    try:
        val = float(qty)
        if val.is_integer():
            return str(int(val))
        return f"{val:.2f}"
    except ValueError:
        return ""

# ============================================================
# 🎨 ZPL ГЕНЕРАТОРИ (ДИЗАЙН НА ЕТИКЕТИ)
# ============================================================

def generate_product_label(name, barcode, quantity, copies):
    """
    Генерира ZPL за етикет 50x30mm: Продукт + Баркод + Количество
    """
    copies = min(max(int(copies), 1), MAX_COPIES)
    name = clean_text(name)
    barcode = clean_text(barcode)
    qty_str = clean_qty(quantity)

    # Логика за 2 реда текст на името
    line1 = name[:22]
    line2 = name[22:44]

    zpl = [
        "^XA",
        "^CI28",                # Поддръжка на кирилица (UTF-8)
        "^PW400",               # Ширина
        "^LL240",               # Височина
        
        # Име на продукт (Горе)
        f"^FO15,15^A0N,28,28^FD{line1}^FS",
        f"^FO15,45^A0N,24,24^FD{line2}^FS" if line2 else "",
        
        # Баркод (Средата)
        "^FO20,85^BY2",
        "^BCN,60,Y,N,N",        # Code128
        f"^FD{barcode}^FS",
        
        # Човешки четим текст под баркода
        f"^FO20,155^A0N,20,20^FD{barcode}^FS",
        
        # Количество (Долу вдясно, ако има)
        f"^FO240,190^A0N,24,24^FDQTY: {qty_str}^FS" if qty_str else "",
        
        # Настройки за печат
        f"^PQ{copies}",
        "^XZ"
    ]
    return "".join(zpl)


def generate_list_label(title, qr_data, copies):
    """
    Генерира ZPL за етикет 50x30mm: Име на списък + QR код
    """
    copies = min(max(int(copies), 1), MAX_COPIES)
    title = clean_text(title)
    qr_data = clean_text(qr_data)

    line1 = title[:20]
    line2 = title[20:40]

    zpl = [
        "^XA",
        "^CI28",
        "^PW400",
        "^LL240",
        
        # Заглавие (Ляво)
        f"^FO15,20^A0N,32,32^FD{line1}^FS",
        f"^FO15,60^A0N,28,28^FD{line2}^FS" if line2 else "",
        
        # QR Code (Дясно)
        "^FO240,30",
        "^BQN,2,5",              # QR Code settings
        f"^FDLA,{qr_data}^FS",   # QR Data
        
        # Текст под QR-а (ID)
        f"^FO230,190^A0N,18,18^FD{qr_data[:15]}^FS",
        
        f"^PQ{copies}",
        "^XZ"
    ]
    return "".join(zpl)

# ============================================================
# 🌐 API ENDPOINTS
# ============================================================

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "GStroy Internal Print Server",
        "status": "running",
        "version": "2.0-final"
    })

@app.route("/printers/<ip>/status", methods=["GET"])
def endpoint_status(ip):
    """Връща JSON: { "online": true/false } - използва се за UI индикатора"""
    try:
        is_online = check_printer_online(ip)
        return jsonify({
            "ip": ip,
            "online": is_online,
            "checked_at": time.strftime("%H:%M:%S")
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/printers/<ip>/print-product-label", methods=["POST"])
def endpoint_print_product(ip):
    """Печат на продуктов етикет"""
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400
    
    data = request.json
    try:
        zpl = generate_product_label(
            name=data.get("name", ""),
            barcode=data.get("barcode", ""),
            quantity=data.get("quantity"),
            copies=data.get("copies", 1)
        )
        send_zpl_to_socket(ip, zpl)
        return jsonify({"success": True, "message": "Sent to printer"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/printers/<ip>/print-list-label", methods=["POST"])
def endpoint_print_list(ip):
    """Печат на етикет за списък/палет"""
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400
    
    data = request.json
    try:
        zpl = generate_list_label(
            title=data.get("name", ""),
            qr_data=data.get("qr_data", ""),
            copies=data.get("copies", 1)
        )
        send_zpl_to_socket(ip, zpl)
        return jsonify({"success": True, "message": "Sent to printer"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# 🏁 MAIN
# ============================================================

if __name__ == "__main__":
    print(f"🖨️  GStroy Label Server стартира на порт {SERVER_PORT}...")
    # debug=False за по-добра производителност, host=0.0.0.0 за достъп от мрежата
    app.run(host="0.0.0.0", port=SERVER_PORT, debug=False)