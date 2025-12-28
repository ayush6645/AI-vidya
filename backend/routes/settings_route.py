from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from backend import db
from werkzeug.security import generate_password_hash, check_password_hash

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
def show_settings():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))
    
    try:
        user_doc = db.collection('users').document(session['user_id']).get()
        if not user_doc.exists:
            flash('User not found. Please log in again.', 'error')
            return redirect(url_for('login.login'))
        
        return render_template('settings.html', user=user_doc.to_dict())
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
        return redirect(url_for('dashboard.show_dashboard'))


@settings_bp.route('/settings/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_ref = db.collection('users').document(session['user_id'])
        user_ref.update({
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'username': data.get('username'),
            'phone_number': data.get('phone_number')
        })
        session['name'] = f"{data.get('first_name')} {data.get('last_name')}"
        return jsonify({'status': 'success', 'message': 'Profile updated successfully!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@settings_bp.route('/settings/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        user_ref = db.collection('users').document(session['user_id'])
        user_doc = user_ref.get()
        if not user_doc.exists:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        if not check_password_hash(user_data.get('password_hash'), current_password):
            return jsonify({'status': 'error', 'message': 'Current password does not match.'}), 403

        hashed_password = generate_password_hash(new_password)
        user_ref.update({'password_hash': hashed_password})
        
        return jsonify({'status': 'success', 'message': 'Password changed successfully!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- NEW ROUTE to handle deleting all plans ---
@settings_bp.route('/settings/delete-all-plans', methods=['POST'])
def delete_all_plans():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        
        # Find all plans for the current user
        plans_query = db.collection('plans').where('userId', '==', user_id).stream()
        plan_ids = [plan.id for plan in plans_query]

        if not plan_ids:
            return jsonify({'status': 'success', 'message': 'No plans to delete.'})

        # Find all modules related to these plans
        modules_query = db.collection('modules').where('planId', 'in', plan_ids).stream()
        module_ids = [module.id for module in modules_query]

        # Find all lessons related to these modules and delete them
        if module_ids:
            lessons_query = db.collection('lessons').where('moduleId', 'in', module_ids).stream()
            for lesson in lessons_query:
                lesson.reference.delete()

        # Delete the modules
        for module_id in module_ids:
            db.collection('modules').document(module_id).delete()
            
        # Delete the plans
        for plan_id in plan_ids:
            db.collection('plans').document(plan_id).delete()
            
        return jsonify({'status': 'success', 'message': 'All plans and data have been deleted.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- UPDATED to correctly call the delete_all_plans logic ---
@settings_bp.route('/settings/delete-account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        
        # First, delete all data associated with the user
        delete_all_plans() 
        
        # Then, delete the user document itself
        db.collection('users').document(user_id).delete()
        
        session.clear() # Log the user out
        return jsonify({'status': 'success', 'message': 'Account deleted successfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500