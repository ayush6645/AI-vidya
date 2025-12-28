# D:\AI_Edu_Bot_Project\backend\__init__.py

from flask import Flask, render_template, session, redirect, url_for
from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, firestore

# --- Firebase Initialization ---
load_dotenv()
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Import Blueprints ---
from .routes.register_route import register_bp
from .routes.login_route import login_bp
from .routes.start_plan_route import start_plan_bp
from .routes.dashboard_route import dashboard_bp
from .routes.edit_profile_route import profile_bp
from .routes.settings_route import settings_bp
from .routes.logout_route import logout_bp
from .routes.my_courses_route import my_courses_bp

# --- Create Flask App ---
app = Flask(
    __name__,
    static_folder='../Web_App',
    template_folder='../Web_App'
)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'aividya-super-secret-key-default')

# --- Register Blueprints ---

# Web Page Blueprints (No Prefix)
app.register_blueprint(register_bp)
app.register_blueprint(login_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(logout_bp)

# API Blueprints for Flutter (All under /api prefix for consistency)
app.register_blueprint(start_plan_bp, url_prefix='/api')
app.register_blueprint(my_courses_bp, url_prefix='/api')
app.register_blueprint(settings_bp, url_prefix='/api')
app.register_blueprint(profile_bp, url_prefix='/api') # Now consistent with other API routes

# --- Core Route ---
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.show_dashboard'))
    return render_template('index.html')