import socket

from flask import current_app

from .validators import validate_ip


def check_printer_online(ip: str) -> bool:
    ip = validate_ip(ip)
    port = current_app.config.get("PRINTER_PORT", 9100)
    timeout = current_app.config.get("PING_TIMEOUT", 0.5)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((ip, port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False


def send_zpl_to_socket(ip: str, zpl_code: str) -> None:
    ip = validate_ip(ip)
    if not zpl_code:
        raise ValueError("ZPL payload is empty")

    port = current_app.config.get("PRINTER_PORT", 9100)
    connect_timeout = current_app.config.get("PRINT_CONNECT_TIMEOUT", 2.0)
    write_timeout = current_app.config.get("PRINT_WRITE_TIMEOUT", 3.0)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(connect_timeout)
        try:
            sock.connect((ip, port))
            sock.settimeout(write_timeout)
            sock.sendall(zpl_code.encode("utf-8"))
        except Exception as exc:
            raise OSError(f"?? ???? ?? ?? ???????? ?????? ??? {ip}: {exc}")
