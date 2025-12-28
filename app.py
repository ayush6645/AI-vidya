'''
from flask import Flask, render_template
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='Web_App', template_folder='Web_App')

# Set a secret key for session management
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-default-secret-key-123!')

# MySQL Configuration removed - Using Firebase Firestore


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