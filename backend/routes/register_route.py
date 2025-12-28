from flask import Blueprint, request, render_template, url_for, jsonify
from werkzeug.security import generate_password_hash
from backend import db

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
            return jsonify({'status': 'error', 'message': 'Passwords do not match.'}), 400

        try:
            users_ref = db.collection('users')
            email_check = users_ref.where('email', '==', email).limit(1).stream()
            if next(email_check, None):
                return jsonify({'status': 'error', 'message': 'An account with this email already exists.'}), 409

            username_check = users_ref.where('username', '==', username).limit(1).stream()
            if next(username_check, None):
                return jsonify({'status': 'error', 'message': 'This username is already taken.'}), 409
                
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

            # Return a success JSON response
            return jsonify({'status': 'success', 'message': 'Registration successful! You can now log in.'}), 201

        except Exception as e:
            return jsonify({'status': 'error', 'message': f'A server error occurred: {e}'}), 500

    return render_template('register.html')