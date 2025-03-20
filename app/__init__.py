from flask import Flask, render_template, request, session, redirect, url_for, flash
import os
from flask_sqlalchemy import SQLAlchemy
from app.models import db, Student, Staff  # Import models
from app.infobot import infobot_bp
from app.DocBot import docbot_bp



def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.register_blueprint(infobot_bp, url_prefix='/infobot')
    app.register_blueprint(docbot_bp, url_prefix='/docbot')
    db.init_app(app)  # Initialize SQLAlchemy with the app

    @app.route('/')
    def home():
        return render_template('index.html')  # Ensure index.html exists

    @app.route('/docbot')
    def docbot():
        return render_template('docbot.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            user_type = request.form['user_type']
            name = request.form['name']
            email = request.form['email']

            if user_type == 'student':
                usn = request.form['usn']
                batch = request.form['batch']
                branch = request.form['branch']
                pass_out_year = request.form['pass_out_year']

                existing_student = Student.query.filter((Student.email == email) | (Student.usn == usn)).first()
                if existing_student:
                    flash("Email or USN already registered!", "danger")
                    return redirect(url_for('register'))

                new_student = Student(name=name, batch=batch, usn=usn, email=email, branch=branch, pass_out_year=pass_out_year)
                db.session.add(new_student)

            elif user_type == 'staff':
                unique_id = request.form['unique_id']

                existing_staff = Staff.query.filter((Staff.email == email) | (Staff.unique_id == unique_id)).first()
                if existing_staff:
                    flash("Email or Unique ID already registered!", "danger")
                    return redirect(url_for('register'))

                new_staff = Staff(name=name, unique_id=unique_id, email=email)
                db.session.add(new_staff)

            db.session.commit()
            flash("Registration successful!", "success")
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            usn = request.form['usn']  # USN for students, Unique ID for staff

            # Check Student Table
            student = Student.query.filter_by(email=email, usn=usn).first()
            if student:
                session['user'] = email
                session['user_type'] = 'student'
                flash("Login Successful!", "success")
                return redirect(url_for('staff_chat'))  # ✅ Redirect to Infobot (staff_chat.html)

            # Check Staff Table
            staff = Staff.query.filter_by(email=email, unique_id=usn).first()
            if staff:
                session['user'] = email
                session['user_type'] = 'staff'
                flash("Login Successful!", "success")
                return redirect(url_for('staff_chat'))  # ✅ Redirect to Infobot (staff_chat.html)

            flash("Invalid credentials!", "danger")

        return render_template('login.html')

    @app.route('/dashboard')
    def dashboard():
        if 'user' not in session:
            flash("Please login first!", "warning")
            return redirect(url_for('login'))

        return redirect(url_for('staff_chat'))

    @app.route('/visitor-chat')
    def visitor_chat():
        return render_template('visitor_chat.html')  # Ensure visitor_chat.html exists in templates/

    @app.route('/staff-chat')
    def staff_chat():
        return render_template('staff_chat.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash("Logged out successfully!", "info")
        return redirect(url_for('login'))

    @app.route('/about')
    def about():
        return render_template('about.html')  # ✅ Ensure about.html exists in templates/

    return app
