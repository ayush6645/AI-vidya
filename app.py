'''
from flask import Flask, render_template
from backend.db.db_config import mysql  # Import from your config
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='Web_App', template_folder='Web_App')

# Set a secret key for session management
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-default-secret-key-123!')

# MySQL Configuration - MUST come before initialization
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'aividya')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_PORT'] = 3306  # Explicit port for XAMPP
app.config['MYSQL_UNIX_SOCKET'] = None  # Important for XAMPP

# Initialize MySQL with the app - CRITICAL STEP
mysql.init_app(app)

# Import blueprints AFTER mysql is initialized
from backend.routes.login_route import login_bp
from backend.routes.register_route import register_bp
from backend.routes.start_plan_route import start_plan_bp

app.register_blueprint(login_bp)
app.register_blueprint(register_bp)
app.register_blueprint(start_plan_bp)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
'''

# D:\AI_Edu_Bot_Project\app.py

from backend import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False)