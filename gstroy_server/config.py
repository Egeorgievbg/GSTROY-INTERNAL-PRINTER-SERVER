import os


class Config:
    SERVER_PORT = int(os.environ.get("LABEL_SERVER_PORT", "8001"))
    PRINTER_PORT = 9100

    PING_TIMEOUT = float(os.environ.get("LABEL_PING_TIMEOUT", "0.5"))
    PRINT_CONNECT_TIMEOUT = float(os.environ.get("PRINT_CONNECT_TIMEOUT", "2.0"))
    PRINT_WRITE_TIMEOUT = float(os.environ.get("PRINT_WRITE_TIMEOUT", "3.0"))

    MAX_COPIES = 50
    LABEL_WIDTH = 400
    LABEL_HEIGHT = 240
