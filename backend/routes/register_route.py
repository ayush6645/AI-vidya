from flask import Blueprint, request, render_template, url_for, jsonify, flash
from werkzeug.security import generate_password_hash
from backend import db
from google.cloud.firestore_v1.base_query import FieldFilter

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        # ... get all other form fields ...
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        try:
            users_ref = db.collection('users')
            email_check = users_ref.where(filter=FieldFilter('email', '==', email)).limit(1).stream()
            if next(email_check, None):
                flash('An account with this email already exists.', 'error')
                return render_template('register.html')

            username_check = users_ref.where(filter=FieldFilter('username', '==', username)).limit(1).stream()
            if next(username_check, None):
                flash('This username is already taken.', 'error')
                return render_template('register.html')
                
            hashed_password = generate_password_hash(password)
            
            new_user_data = {
                'first_name': first_name,
                'last_name': request.form.get('last_name', '').strip(),
                'date_of_birth': request.form.get('date_of_birth', '').strip(),
                'education': request.form.get('education', '').strip(),
                'email': email,
                'phone_number': request.form.get('phone_number', '').strip(),
                'username': username,
                'password_hash': hashed_password
            }
            
            users_ref.document(email).set(new_user_data)

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login.login'))

        except Exception as e:
            flash(f'A server error occurred: {e}', 'error')
            return render_template('register.html')

    return render_template('register.html')