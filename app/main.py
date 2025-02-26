from app import create_app
from app.infobot import infobot_bp  # Ensure correct import

# ✅ Create Flask app using create_app()
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
