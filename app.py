from app import app

from app.controllers import app_controller, api_controller
from app.utils.config import get_port

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=get_port())
