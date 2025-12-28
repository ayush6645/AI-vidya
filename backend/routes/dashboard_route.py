from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from backend import db
from google.cloud.firestore_v1.base_query import FieldFilter

dashboard_bp = Blueprint('dashboard', __name__)

# This is your existing route for the web page, you can keep it.
@dashboard_bp.route('/dashboard')
def show_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))
    
    # ... (your existing web logic here) ...
    # For simplicity, we'll just show a basic render
    return render_template('dashboard.html', name=session.get('name'))


# --- NEW API ROUTE FOR FLUTTER APP ---
@dashboard_bp.route('/api/dashboard-data')
def get_dashboard_data():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        
        # 1. Fetch user's name
        name = session.get('name', 'User')

        # 2. Get total plan count
        plans_query = db.collection('plans').where(filter=FieldFilter('userId', '==', user_id))
        plan_count = len(list(plans_query.stream()))

        # 3. Get total count of completed topics
        # Note: Your original code had a potential issue with 'userId' on lessons, assuming it should be linked via plans/modules.
        # This is a simplified query. For a real app, you would query lessons based on the user's plans.
        completed_topics_count = 0 # Placeholder until lesson schema is confirmed to have userId
        
        # 4. Find the most recently created plan for the "Continue Learning" button
        last_plan_id = None
        latest_plan_query = db.collection('plans').where(filter=FieldFilter('userId', '==', user_id)).order_by('creation_date', direction='DESCENDING').limit(1)
        last_plan_docs = list(latest_plan_query.stream())
        if last_plan_docs:
            last_plan_id = last_plan_docs[0].id

        # 5. Package all data into a JSON response
        return jsonify({
            'status': 'success',
            'data': {
                'name': name,
                'plan_count': plan_count,
                'completed_topics_count': completed_topics_count,
                'last_plan_id': last_plan_id,
                # Placeholder data from your HTML, can be made dynamic later
                'xp_points': 1250,
                'day_streak': 7,
                'level': 3
            }
        }), 200

    except Exception as e:
        print(f"API Dashboard Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500