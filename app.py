from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "super_secret_vibecode_key_2025"

# Papkalar
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# JSON fayllar
COURSES_FILE = os.path.join(DATA_DIR, "courses.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")

def load_json(file_path, default={}):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

courses = load_json(COURSES_FILE, {})
users = load_json(USERS_FILE, {})
chats = load_json(CHATS_FILE, {})

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username, role):
        self.id = username
        self.role = role

@login_manager.user_loader
def load_user(username):
    if username in users:
        return User(username, users[username]["role"])
    return None

# === ROUTES ===
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == "teacher":
            return redirect(url_for('teacher'))
        else:
            return redirect(url_for('student'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username]['password'], password):
            user = User(username, users[username]['role'])
            login_user(user)
            return redirect(url_for('index'))
        flash('Noto‘g‘ri login yoki parol')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        if username in users:
            flash('Bu login band!')
        else:
            users[username] = {
                "password": generate_password_hash(password),
                "role": role,
                "created": datetime.now().isoformat()
            }
            save_json(USERS_FILE, users)
            flash('Muvaffaqiyatli ro‘yxatdan o‘tdingiz!')
            return redirect(url_for('login'))
    return render_template('login.html', register=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/student')
@login_required
def student():
    if current_user.role != "student":
        return redirect(url_for('index'))
    return render_template('student.html', courses=courses, username=current_user.id)

@app.route('/teacher')
@login_required
def teacher():
    if current_user.role != "teacher":
        return redirect(url_for('index'))
    return render_template('teacher.html', courses=courses, username=current_user.id)

@app.route('/upload', methods=['POST'])
@login_required
def upload_material():
    if current_user.role != "teacher":
        return jsonify({"error": "Faqat ustoz yuklay oladi"}), 403
    
    course = request.form['course']
    title = request.form['title']
    type_ = request.form['type']
    
    file = request.files['file']
    if not file:
        return jsonify({"error": "Fayl tanlanmadi"}), 400
    
    filename = str(uuid.uuid4()) + "_" + file.filename
    file_path = os.path.join(UPLOAD_DIR, filename)
    file.save(file_path)
    
    if course not in courses:
        courses[course] = {"videos": [], "teacher": current_user.id}
    
    material = {
        "title": title,
        "type": type_,
        "file": filename,
        "likes": 0,
        "added": datetime.now().isoformat()
    }
    if type_ == "video" and 'image' in request.files:
        img = request.files['image']
        if img.filename:
            imgname = "thumb_" + str(uuid.uuid4()) + "_" + img.filename
            img.save(os.path.join(UPLOAD_DIR, imgname))
            material["image"] = imgname
    
    courses[course]["videos"].append(material)
    save_json(COURSES_FILE, courses)
    return jsonify({"success": True})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route('/like/<course>/<int:idx>')
@login_required
def like(course, idx):
    if course in courses and idx < len(courses[course]["videos"]):
        courses[course]["videos"][idx]["likes"] += 1
        save_json(COURSES_FILE, courses)
    return redirect(url_for('student'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
