from flask import Blueprint

docbot_bp = Blueprint('docbot', __name__)

from . import routes