from flask import render_template as page
from app import app


from app.controllers import api_controller

from flask import request, jsonify
from datetime import datetime


@app.route("/")
def index():
    return page("app.html")