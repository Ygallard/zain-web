import os

from app import app

from app.controllers import app_controller, api_controller

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
