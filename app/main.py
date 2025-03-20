from app import create_app, db  # Import Flask app & db from __init__.py

app = create_app()  # Initialize the Flask app

if __name__ == '__main__':
    with app.app_context():  # Ensures the app is properly registered with SQLAlchemy
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)  # Start the Flask app
