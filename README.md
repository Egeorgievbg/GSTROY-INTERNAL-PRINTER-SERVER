# GStroy Internal Print Server

## Quick Start
1. Create a venv and activate it:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. (Optional) set the HTTP port:
   ```powershell
   $env:LABEL_SERVER_PORT = "8001"
   ```
4. Run the server:
   ```powershell
   python app.py
   ```
   In production you can use `gunicorn -w 4 app:app` with env vars mapped.

## Project structure
- `app.py`: entry point that calls `gstroy_server.create_app()` and keeps `debug=False`.
- `gstroy_server/__init__.py`: application factory that loads configuration, registers middleware, and mounts blueprints.
- `gstroy_server/config.py`: central constants for HTTP/Zebra ports, timeouts, and label dimensions.
- `gstroy_server/logging_setup.py`: configures a rotating file handler (`logs/gstroy-server.log`, 5 MB, 5 backups) plus a console handler and silences low-level werkzeug noise.
- `gstroy_server/middleware.py`: adds CORS headers and logs every request/response with method, path, remote IP, status, and latency.
- `gstroy_server/blueprints/core.py`: exposes `GET /` for health/version information.
- `gstroy_server/blueprints/printers.py`: handles `/printers` endpoints (status, print product label, print list label) and routes logs through `gstroy.printers`.
- `gstroy_server/services/`: helper modules
  - `label.py`: ZPL generators for product and list labels, enforcing copy limits and sanitizing text.
  - `printer.py`: opens TCP sockets with configurable timeouts and raises `OSError` on failure.
  - `text_utils.py`: `clean_text` removes `^`, `~`, and newlines; `format_smart_numbers` normalizes floats (`2.500` → `2.5`).
  - `validators.py`: IPv4 validation logic.

## Configuration overrides
| Variable | Purpose | Default |
|----------|---------|---------|
| `LABEL_SERVER_PORT` | Flask HTTP port | `8001` |
| `PRINTER_PORT` | Zebra TCP port | `9100` |
| `GSTROY_LOG_DIR` | Directory for logs | `logs` |
| `GSTROY_LOG_FILE` | Log file name | `gstroy-server.log` |
| `GSTROY_LOG_MAX_BYTES` | Max log size (bytes) | `5242880` (5 MB) |
| `GSTROY_LOG_BACKUP_COUNT` | Number of rotations | `5` |
| `LABEL_WIDTH` / `LABEL_HEIGHT` | Label canvas | `400` x `240` |

## API reference
### `GET /`
Returns service metadata and version.
```json
{ "service": "GStroy Print Server PRO", "status": "running", "version": "3.1-pro-date-fix" }
```

### `GET /printers/<ip>/status`
Attempts a TCP connection to port 9100 and reports reachability.
- Example: `GET /printers/192.168.1.120/status`
- Success response:
  ```json
  { "ip": "192.168.1.120", "online": true, "checked_at": "14:23:05" }
  ```
- Invalid IP returns HTTP 400 with `{ "error": "Invalid IPv4 address: ..." }`.

### `POST /printers/<ip>/print-product-label`
#### Sample payload
```json
{
  "name": "GStroy Widget Ultra",
  "barcode": "123456789012",
  "quantities": [
    { "value": 12, "unit": "m3" },
    { "value": 12, "unit": "pcs" }
  ],
  "copies": 2
}
```
- `name`: sanitized via `text_utils.clean_text` and split into two lines.
- `barcode`: printed as Code128 and human-readable text.
- `unit_info`: optional full string that is sanitized and printed if supplied.
- `quantities`: optional array of objects (`value`, `unit`); each entry becomes `value unit` and entries are joined with ` / ` (so `12 m3 / 12 pcs` prints correctly).
- `quantity`: fallback when neither `unit_info` nor `quantities` contain data.
- `copies`: clamped between 1 and `MAX_COPIES` (50 default).

Success response:
```json
{ "success": true, "message": "Pro Product Label Sent" }
```
Failure (invalid IP, socket timeout, etc.) returns HTTP 500 with `error`.

### `POST /printers/<ip>/print-list-label`
#### Sample payload
```json
{
  "name": "Picking List 1056",
  "qr_data": "https://erp.example.com/orders/1056",
  "copies": 1
}
```
- `name`: left-aligned string with wrapping, never collides with the QR block.
- `qr_data`: sanitized string that feeds both the QR code and the footer text (15-character preview).
- `copies`: obeys the same clamping rules as above.

Success response:
```json
{ "success": true, "message": "List Label Sent" }
```

## Logging and observability
- `gstroy_server/logging_setup.py` rotates logs and keeps werkzeug at WARNING so the files remain readable.
- `gstroy_server/middleware.py` logs request start/end, duration, status, and origin IP; logs go to both `logs/gstroy-server.log` and the console.
- `gstroy_server/blueprints/printers.py` logs status checks, print attempts, and exceptions through the `gstroy.printers` logger.

## Security and reliability
1. `debug=False` for production; run behind a reverse proxy (Gunicorn/Waitress) with TLS.
2. Strict socket timeouts (`PING_TIMEOUT`, `PRINT_CONNECT_TIMEOUT`, `PRINT_WRITE_TIMEOUT`) prevent hanging printers.
3. POST endpoints require JSON (`request.get_json(silent=True)` ensures errors are caught before processing).
4. CORS allows only `Content-Type`, `GET`, `POST`, `OPTIONS` via the shared middleware.
5. Limit network exposure with firewalls or private VLANs, and use TLS/ACLs on the front door.

## Next steps
- Containerize via Docker and map the `LABEL_SERVER_PORT` + `GSTROY_LOG_DIR` volumes.
- Add unit tests for label generation and a mocked socket for `printer.send_zpl_to_socket`.
- Forward `logs/gstroy-server.log` to Fluentd/Elastic/Datadog if you need long-term observability.
