from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(app.config.get("PORT", 5000)))
