from gstroy_server import create_app

app = create_app()

if __name__ == "__main__":
    port = app.config.get("SERVER_PORT", 8001)
    print(f"Стартирам GStroy PRO Server на порт {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
