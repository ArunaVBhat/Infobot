from flask import Flask, render_template
from app.infobot import infobot_bp
from app.DocBot import docbot_bp
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    # Register Blueprints
    app.register_blueprint(infobot_bp, url_prefix='/infobot')
    app.register_blueprint(docbot_bp, url_prefix='/docbot')

    # ✅ Define routes inside create_app()
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/contact')
    def contact():
        return render_template('contact.html')

    @app.route('/DocBot')
    def DocBot():
        return render_template('DocBot.html')

    @app.route("/visitor-chat")
    def visitor_chat():
        return render_template("visitor_chat.html")

    @app.route("/staff-chat")
    def staff_chat():
        return render_template("staff_chat.html")

    return app
