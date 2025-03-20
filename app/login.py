from flask import Flask, request, render_template, flash, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
from app.models import db, Student, Staff

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.secret_key = 'your_secret_key'
app.permanent_session_lifetime = timedelta(minutes=30)
db.init_app(app)

# CSRF Protection
csrf = CSRFProtect(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check in Student Table
        student = Student.query.filter_by(email=email, usn=password).first()
        if student:
            session['user_id'] = student.id
            session['user_type'] = 'student'
            flash("Login Successful as Student!", "success")
            return redirect(url_for('dashboard'))

        # Check in Staff Table
        staff = Staff.query.filter_by(email=email, unique_id=password).first()
        if staff:
            session['user_id'] = staff.id
            session['user_type'] = 'staff'
            flash("Login Successful as Staff!", "success")
            return redirect(url_for('staff_chat'))

        flash("Invalid credentials, please try again!", "danger")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    if session['user_type'] == 'student':
        return "Welcome Student: " + session['user_type']
    elif session['user_type'] == 'staff':
        return "Welcome Staff: " + session['user_type']

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
