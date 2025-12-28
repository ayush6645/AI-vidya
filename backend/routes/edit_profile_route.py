# backend/routes/profile_route.py

from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from backend import db

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/edit-profile')
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))
    
    user_doc = db.collection('users').document(session['user_id']).get()
    if not user_doc.exists:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('login.login'))
    
    return render_template('edit_profile.html', user=user_doc.to_dict())

@profile_bp.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    try:
        user_ref = db.collection('users').document(session['user_id'])
        user_ref.update({
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'phone_number': request.form.get('phone_number')
        })
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating profile: {e}', 'error')
    
    return redirect(url_for('profile.edit_profile'))

@profile_bp.route('/profile/delete-all-plans', methods=['POST'])
def delete_all_plans():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        # This is a more robust way to delete all associated data
        # Note: For very large datasets, this should be a background job
        plans_query = db.collection('plans').where('userId', '==', user_id).stream()
        plan_ids = [plan.id for plan in plans_query]

        if not plan_ids:
            return jsonify({'status': 'success', 'message': 'No plans to delete.'})

        # Find all modules related to these plans
        modules_query = db.collection('modules').where('planId', 'in', plan_ids).stream()
        module_ids = [module.id for module in modules_query]

        # Find all lessons related to these modules
        if module_ids:
            lessons_query = db.collection('lessons').where('moduleId', 'in', module_ids).stream()
            for lesson in lessons_query:
                lesson.reference.delete()

        # Delete modules and plans
        for module_id in module_ids:
            db.collection('modules').document(module_id).delete()
        for plan_id in plan_ids:
            db.collection('plans').document(plan_id).delete()
            
        return jsonify({'status': 'success', 'message': 'All plans and associated data have been deleted.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@profile_bp.route('/profile/delete-account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        # First, delete all plans associated with the user
        delete_all_plans() 
        # Then, delete the user document itself
        db.collection('users').document(user_id).delete()
        
        session.clear() # Log the user out
        return jsonify({'status': 'success', 'message': 'Account deleted successfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500