from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Student Table
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    batch = db.Column(db.String(10), nullable=False)
    usn = db.Column(db.String(15), unique=True, nullable=False)  # Password
    email = db.Column(db.String(100), unique=True, nullable=False)  # Username
    branch = db.Column(db.String(50), nullable=False)
    pass_out_year = db.Column(db.String(4), nullable=False)

# Staff Table
class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unique_id = db.Column(db.String(20), unique=True, nullable=False)  # Password
    email = db.Column(db.String(100), unique=True, nullable=False)  # Username
