# GStroy Internal Print Server

### Purpose
Modular Flask service that exposes Zebra-compatible label printing and printer health endpoints. The runtime sanitizes inputs, generates ZPL, and streams it directly to TCP port `9100` without intermediate files.

### Project layout
- `app.py`: executable entry point (`create_app` factory is invoked, sets up logging/printouts).
- `gstroy_server/config.py`: centralized configuration values (ports, timeouts, label dimensions).
- `gstroy_server/middleware.py`: reusable CORS hook so every response is browser-friendly.
- `gstroy_server/blueprints/`: Flask blueprints that keep routing separate from services.
  - `core.py`: health metadata endpoint.
  - `printers.py`: printer status plus the two label-printing actions.
- `gstroy_server/services/`: reusable helpers.
  - `label.py`: ZPL builders for product and list labels.
  - `printer.py`: raw TCP/timeout handling.
  - `text_utils.py` + `validators.py`: shared sanitizers and IP checks.

### Requirements & install
1. Create/activate a virtualenv:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

### Run locally
1. Optionally set `LABEL_SERVER_PORT` (defaults to `8001`):
   ```powershell
   $env:LABEL_SERVER_PORT = "8001"
   ```
2. Start the server:
   ```powershell
   python app.py
   ```

### API reference
All endpoints live under `/` or `/printers`. Responses are JSON with `Content-Type: application/json`.

#### `GET /`
Returns metadata for health checks.

#### `GET /printers/<ip>/status`
- Checks TCP `9100` reachability for the requested IPv4 printer.
- Success response (HTTP 200):
  ```json
  { "ip": "192.168.1.100", "online": true, "checked_at": "15:23:10" }
  ```
- Invalid IP yields HTTP 400 with `error`.

#### `POST /printers/<ip>/print-product-label`
- JSON payload:
  ```json
  {
    "name": "Widget Model X",
    "barcode": "123456789012",
    "quantity": 12,
    "copies": 2
  }
  ```
- Generates the product label ZPL and pushes it to the printer.
- Response:
  ```json
  { "success": true, "message": "Pro Product Label Sent" }
  ```

#### `POST /printers/<ip>/print-list-label`
- JSON payload:
  ```json
  {
    "name": "Picking List 1056",
    "qr_data": "https://erp.example.com/orders/1056",
    "copies": 1
  }
  ```
- Streams a list label containing a QR block.
- Same success/error schema above.

### Label/service internals
- `generate_pro_product_label` clamps copies, sanitizes text, renders a Code128 barcode, prints a timestamp and quantity line, and frames the layout at configured width/height.
- `generate_list_label` includes a header plus structured QR data trimmed to 15 characters for the human-friendly footer. Empty segments are skipped before joining.
- `check_printer_online` and `send_zpl_to_socket` reuse the config-driven timeouts and raise clear errors when the socket operations fail.

### Observability & security
- Logs rotate under `logs/gstroy-server.log` with 5 MB chunks and five backups (use `GSTROY_LOG_DIR`, `GSTROY_LOG_FILE`, `GSTROY_LOG_MAX_BYTES`, `GSTROY_LOG_BACKUP_COUNT` to override). Every request, print job, and exception is recorded at INFO/ERROR so you have an audit trail for deployments.
- `gstroy_server.middleware.register_cors` now also records every incoming HTTP request and its response duration to the console/log file so you can watch activity live and later audit the logs.
- CORS headers are already managed by `gstroy_server.middleware.register_cors`, and every POST endpoint enforces JSON payloads before moving on to label generation.
- Harden deployments by running the Flask app behind TLS/ACL-enforced frontends (reverse proxy or VPN), pinning network access to your printer VLAN, and keeping `debug=False`.

### Next steps
1. Containerize (`Dockerfile`) and map `LABEL_SERVER_PORT` as needed.
2. Add automated tests around label generation (pure string outputs) and mocked socket behavior.
3. Consider exposing OpenAPI docs or Postman collections so clients know the request schema in advance.
