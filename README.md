# GStroy Internal Print Server

## Overview
This service acts as an internal print hub for Zebra-compatible printers (Bixolon XD5-40d) by exposing a lightweight Flask REST API. It validates incoming requests, sanitizes label data, and forwards generated ZPL directly to TCP port 9100.

## Architecture & Behavior
- **Flask API** exposes three endpoints: health, printer status, and two printing actions.
- **Direct Zebra Connection**: Every interaction happens over a persistent TCP socket to `:9100` without intermediate storage.
- **Runtime Limits**: Copies, text length, and timeouts are hard limits (`MAX_COPIES`, `MAX_TEXT_LEN`, connection/write timeouts) to avoid overloading the printer or the network.
- **Minimal Dependencies**: Only Flask and Python standard library modules are required, ensuring fast startup and easy deployment.

## Requirements
- Python 3.11+ (confirm compatibility if upgrading)
- Dependencies tracked via `requirements.txt` (`Flask>=2.3,<3`)
- Network connectivity to Zebra/Bixolon printers (XD5-40d tested) on TCP port 9100

## Local Setup
1. Create and activate a virtual environment (recommended):
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
2. Install dependencies from requirements:
   ```powershell
   pip install -r requirements.txt
   ```
3. Set runtime port (default `8001`):
   ```powershell
   $env:LABEL_SERVER_PORT = "8001"
   ```
4. Start the server:
   ```powershell
   python printer-server.py
   ```

## Configuration
- `LABEL_SERVER_PORT` (default `8001`): HTTP port for the Flask app.
- Zebra printers are targeted on port `9100`; that socket is hardcoded.
- Static timeouts are defined via `PING_TIMEOUT`, `PRINT_CONNECT_TIMEOUT`, and `PRINT_WRITE_TIMEOUT`; adjust by editing the module if needed.

## API Reference
All endpoints respond with JSON (`Content-Type: application/json`).

### `GET /`
- Returns basic service metadata.
  ```json
  {
    "service": "GStroy Internal Print Server",
    "status": "running",
    "version": "2.0-final"
  }
  ```

### `GET /printers/<ip>/status`
- Parameters: `<ip>` – IPv4 address of the Zebra printer.
- Attempts a TCP connection to port `9100` and reports whether the device is reachable.
  ```json
  { "ip": "192.168.1.100", "online": true, "checked_at": "15:23:10" }
  ```
- Invalid IP values return `400` with an explanatory message.

### `POST /printers/<ip>/print-product-label`
- Payload example:
  ```json
  {
    "name": "Widget Model X",
    "barcode": "123456789012",
    "quantity": 12,
    "copies": 3
  }
  ```
- Behavior: sanitizes text, splits the product name into two lines, renders a Code128 barcode, adds a human-readable quantity, and subject to the `MAX_COPIES` limit.
- Success response:
  ```json
  { "success": true, "message": "Sent to printer" }
  ```
- Errors bubble up as `500` with `error`.

### `POST /printers/<ip>/print-list-label`
- Payload example:
  ```json
  {
    "name": "Picking List 1056",
    "qr_data": "https://erp.example.com/orders/1056",
    "copies": 1
  }
  ```
- Behavior: formats the provided title, generates a QR code via `^BQN`, and prints the label. Copies obey the same `1..MAX_COPIES` clamp.
- Success/error semantics match `print-product-label`.

## Label Generation Details
- `generate_product_label` limits the name to two lines (22 characters each) and prints a Code128 barcode plus quantity text.
- `generate_list_label` prints a header and a QR code, followed by a compact textual identifier (first 15 characters of `qr_data`).
- `clean_text` strips `^`, `~`, and newline characters before truncating to `MAX_TEXT_LEN` (50 characters).
- Quantity formatting leverages `clean_qty`, which emits integer values when possible or two-decimal floats.

## Error Handling & Troubleshooting
- **Timeout from Zebra**: ensure the printer is online and accessible over TCP 9100, and increase `PRINT_CONNECT_TIMEOUT`/`PRINT_WRITE_TIMEOUT` if the network is slow.
- **`ValueError` for IP**: the API returns HTTP `400`; verify that the client submits a valid IPv4 literal.
- **`OSError` on send**: the printer may reject the connection or the socket is closed mid-session; inspect Zebra logs and network appliances.
- **Monitoring**: capture `stdout`/`stderr` from Flask when running under a service supervisor to track request flow and failures.

## Deployment & Maintenance Notes
- Run under a process manager (`gunicorn`, `waitress`, or `systemd`) and expose `LABEL_SERVER_PORT` as needed.
- Consider adding structured logging with rotation for production observability.
- A Dockerfile can wrap the app, exposing port `8001` and passing `LABEL_SERVER_PORT` through environment variables.

## Security Considerations
- Keep `debug=False`; never deploy Flask’s debugger in production.
- Restrict network access via ACLs or place the service behind a reverse proxy like `nginx`.
- The current sanitization is simple; introduce stricter validation (whitelist of allowed characters) if untrusted clients are expected.

## Suggested Next Steps
1. Add mocked socket integration tests to ensure ZPL generation remains stable.
2. Expand the `docs/` directory with printer settings, QR specifications, and architecture diagrams.
3. Introduce OpenAPI/Swagger documentation to simplify onboarding for API consumers.
