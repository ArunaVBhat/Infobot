from flask import Blueprint

infobot_bp = Blueprint('infobot', __name__)

from app.infobot import routes