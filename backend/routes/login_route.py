from flask import Blueprint, render_template, request, session, url_for, jsonify
from werkzeug.security import check_password_hash
from backend import db
from google.cloud.firestore_v1.base_query import FieldFilter
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
                logger.debug(f"Received JSON data: {data}")
            else:
                data = request.form.to_dict()
                logger.debug(f"Received form data: {data}")
            
            # Extract values with fallbacks
            login_type = data.get('loginType')
            login_value = data.get('login_value', '').strip()
            auth_type = data.get('authType')
            auth_value = data.get('auth_value', '').strip()

            logger.debug(f"Parsed values - login_type: {login_type}, login_value: {login_value}, auth_type: {auth_type}, auth_value: {auth_value}")

            if not all([login_type, login_value, auth_type, auth_value]):
                return jsonify({'status': 'error', 'message': 'Please fill all fields'}), 400

            users_ref = db.collection('users')
            user_query = None

            # Map login types to database fields
            field_map = {
                'loginUsername': 'username',
                'loginEmail': 'email', 
                'loginPhone': 'phone_number'
            }

            db_field = field_map.get(login_type)
            if not db_field:
                return jsonify({'status': 'error', 'message': 'Invalid login type'}), 400

            # Query Firestore for the user
            query = users_ref.where(filter=FieldFilter(db_field, '==', login_value))
            user_docs = list(query.limit(1).stream())
            
            if not user_docs:
                logger.warning(f"User not found with {db_field}: {login_value}")
                return jsonify({'status': 'error', 'message': 'Invalid credentials. Please try again.'}), 401

            user_doc = user_docs[0]
            user_data = user_doc.to_dict()
            
            # Check password
            if not check_password_hash(user_data.get('password_hash', ''), auth_value):
                logger.warning(f"Password mismatch for user: {user_doc.id}")
                return jsonify({'status': 'error', 'message': 'Invalid credentials. Please try again.'}), 401

            # Login successful - set session
            session['user_id'] = user_doc.id
            session['username'] = user_data.get('username')
            session['name'] = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            
            logger.info(f"User {user_doc.id} logged in successfully")
            
            return jsonify({
                'status': 'success', 
                'message': 'Login successful!',
                'user': {
                    'id': user_doc.id,
                    'username': user_data.get('username'),
                    'name': session['name']
                }
            }), 200

        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'message': 'A server error occurred. Please try again later.'}), 500
        
    return render_template('login.html')


@login_bp.route('/logout')
def logout():
    """Logout endpoint to clear session"""
    session.clear()
    return jsonify({'status': 'success', 'message': 'Logged out successfully'}), 200


@login_bp.route('/check-auth')
def check_auth():
    """Endpoint to check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({
            'status': 'success', 
            'authenticated': True,
            'user': {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'name': session.get('name')
            }
        }), 200
    else:
        return jsonify({'status': 'success', 'authenticated': False}), 200