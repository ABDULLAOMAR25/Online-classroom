from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Database Configuration ---
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///classes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class ClassSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    is_live = db.Column(db.Boolean, default=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False)

# --- Routes ---
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        user = User.query.filter_by(username=username, password=password, role=role).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session.get('role')
    if role == 'student':
        return render_template('dashboard_student.html')
    elif role == 'teacher':
        return render_template('dashboard_teacher.html')
    elif role == 'admin':
        return render_template('dashboard_admin.html')
    else:
        return "Unknown role"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/create-session', methods=['GET', 'POST'])
def create_session():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return "Unauthorized", 403
    if request.method == 'POST':
        class_name = request.form['class_name']
        session_obj = ClassSession(class_name=class_name)
        db.session.add(session_obj)
        db.session.commit()
        return redirect(url_for('sessions'))
    return render_template('create_session.html')

@app.route('/sessions')
def sessions():
    all_sessions = ClassSession.query.all()
    return render_template('sessions.html', sessions=all_sessions)

@app.route('/start-session/<int:session_id>')
def start_session(session_id):
    session_obj = ClassSession.query.get_or_404(session_id)
    session_obj.is_live = True
    session_obj.start_time = datetime.now()
    db.session.commit()
    return redirect(url_for('sessions'))

@app.route('/end-session/<int:session_id>')
def end_session(session_id):
    session_obj = ClassSession.query.get_or_404(session_id)
    session_obj.is_live = False
    session_obj.end_time = datetime.now()
    db.session.commit()
    return redirect(url_for('sessions'))

@app.route('/join-session/<int:session_id>')
def join_session(session_id):
    session_obj = ClassSession.query.get_or_404(session_id)
    if session_obj.is_live:
        return render_template('join_session.html', session=session_obj)
    else:
        return "This session is not live right now."

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
