from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, render_template
from backend import db
from dotenv import load_dotenv
import os
from google import genai
import requests
import json
from firebase_admin import firestore
import re
from collections import Counter

load_dotenv()
start_plan_bp = Blueprint('start_plan', __name__)

# --- API Key Configuration ---
try:
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    # Initialize the new Client
    client = genai.Client(api_key=GOOGLE_API_KEY)
except (ValueError, TypeError) as e:
    print(f"FATAL ERROR: API keys not configured correctly. {e}")
    client = None
    YOUTUBE_API_KEY = None

# ----------------------------- HELPER FUNCTIONS -----------------------------

def generate_structured_plan_from_gemini(topic: str, difficulty: str, timeline_months: int) -> dict | None:
    if not client:
        print("CRITICAL: Gemini Client is not initialized.")
        return None

    model_id = 'gemini-2.5-flash' 
    
    prompt = f"""
    You are a hyper-detailed, logical curriculum architect for an AI learning platform. Your task is to generate a comprehensive, day-by-day study plan based on user requirements.

    **User Request:**
    - Topic: "{topic}"
    - Skill Level: "{difficulty}"
    - Completion Timeline: "{timeline_months} months"

    **CRITICAL INSTRUCTIONS (MUST be followed exactly):**

    1.  **Strict Duration Calculation:**
        - A "study month" consists of exactly **20 study days** (5 days/week for 4 weeks).
        - The total number of lessons in the plan MUST equal **{timeline_months} months * 20 days/month**.
        - For a **{timeline_months}-month timeline**, you must generate a plan with exactly **{int(timeline_months) * 20} lessons**.

    2.  **Syllabus Pacing and Depth:**
        - You **MUST** adjust the content's depth and breadth to perfectly fit the requested timeline.
        - For a **long timeline** (4+ months), the syllabus must progress from fundamental concepts to advanced topics, and must include dedicated "Project Days" or "Review Weeks".
        - For a **short timeline** (1-2 months), focus only on the core, most essential topics.
        - **Do not** include generic filler days like "Catch-up day". Every day must have a specific, actionable topic.

    3.  **JSON Output Requirements:**
        - Your entire response **MUST** be a single, valid JSON object and nothing else.
        - Do not include any text, explanations, or markdown formatting like ```json before or after the JSON object.
        - The JSON must have keys: "plan_title", and "modules".
        - The "modules" array should be structured logically (e.g., one module per month).
        - Each lesson object must have keys: "day_of_plan", "topic", "description", and "Youtube_keywords".

    **Example Logic:** An 8-month plan for "Data Science" must cover basics like Python and stats in the first months, then progress to Machine Learning algorithms, and dedicate the final months to advanced topics like Deep Learning and a capstone project.

    Now, generate the detailed, day-by-day JSON plan for the user's request.
    """
    try:
        # New API Call
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        # Result text access might differ slightly, usually response.text works
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        raise ValueError("No valid JSON object found in the AI response.")
    except Exception as e:
        print(f"CRITICAL GEMINI ERROR: {str(e)}") # Print explicitly for Azure Logs
        return None

# ----------------------------- MAIN API ROUTES -----------------------------

@start_plan_bp.route('/start-plan', methods=['GET'])
def show_start_plan():
    if 'user_id' not in session:
        return redirect(url_for('login.login'))
    return render_template('start_plan.html', user_id=session['user_id'])

# This route is kept for compatibility with the frontend if it's still being used
@start_plan_bp.route('/get_recommendations', methods=['GET'])
def get_recommendations():
    """
    Generates course recommendations based on the most popular plan titles
    in the Firestore database.
    """
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Authentication required."}), 401
    
    try:
        plans_ref = db.collection('plans').stream()
        all_titles = [plan.to_dict().get('plan_title') for plan in plans_ref if plan.to_dict().get('plan_title')]
        
        if not all_titles:
            return jsonify({"status": "success", "recommendations": []})
            
        title_counts = Counter(all_titles)
        most_common_titles = [title for title, count in title_counts.most_common(5)]
        
        return jsonify({"status": "success", "recommendations": most_common_titles}), 200
        
    except Exception as e:
        print(f"Recommendation Error: {e}")
        return jsonify({"status": "error", "message": "Could not fetch recommendations."}), 500


@start_plan_bp.route('/generate_plan', methods=['POST'])
def generate_plan():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Authentication required."}), 401
    data = request.get_json()
    plan_data = generate_structured_plan_from_gemini(
        data.get("topic"), data.get("difficulty"), int(data.get("timeline"))
    )
    if plan_data:
        return jsonify({ "status": "success", "plan_data": plan_data }), 200
    else:
        return jsonify({"status": "error", "message": "Failed to generate plan from AI."}), 500

@start_plan_bp.route('/save_plan', methods=['POST'])
def save_plan():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Authentication required."}), 401
    data = request.get_json()
    plan_data = data.get('plan_data')
    user_id = data.get('userId')
    try:
        plan_to_save = {
            'userId': user_id,
            'plan_title': plan_data.get('plan_title'),
            'difficulty_level': plan_data.get('difficulty_level'),
            'total_duration_months': plan_data.get('total_duration_months'),
            'creation_date': firestore.SERVER_TIMESTAMP,
            'status': 'active'
        }
        update_time, plan_ref = db.collection('plans').add(plan_to_save)
        plan_id = plan_ref.id

        for module in plan_data.get('modules', []):
            module_to_save = { 'planId': plan_id, 'module_number': module.get('module_number'), 'module_title': module.get('module_title') }
            update_time, module_ref = db.collection('modules').add(module_to_save)
            module_id = module_ref.id

            for lesson in module.get('lessons', []):
                lesson_to_save = { 'moduleId': module_id, **lesson }
                lesson_to_save.pop('Youtube_keywords', None)
                db.collection('lessons').add(lesson_to_save)
        
        return jsonify({"status": "success", "plan_id": plan_id}), 200
    except Exception as e:
        print(f"Firestore Save Error: {e}")
        return jsonify({"status": "error", "message": "A database error occurred."}), 500

# ✨ FIX: Added the correct Python logic to the recommend_plan route.
@start_plan_bp.route('/recommend_plan')
def recommend_plan():
    """
    This feature recommends learning plans based on the most popular
    courses created by other users.
    """
    # Ensure user is logged in
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Authentication required."}), 401
    
    try:
        # Get all documents from the 'plans' collection
        plans_ref = db.collection('plans').stream()
        
        # Create a list of all plan titles, filtering out any that are empty
        all_titles = [plan.to_dict().get('plan_title') for plan in plans_ref if plan.to_dict().get('plan_title')]
        
        # If there are no titles, return an empty list
        if not all_titles:
            return jsonify({"status": "success", "recommendations": []})
            
        # Use Counter to find the 5 most common plan titles
        title_counts = Counter(all_titles)
        most_common_titles = [title for title, count in title_counts.most_common(5)]
        
        # Return the list of recommendations
        return jsonify({"status": "success", "recommendations": most_common_titles}), 200
        
    except Exception as e:
        # Log the error for debugging and return a generic error message
        print(f"Recommendation Logic Error: {e}")
        return jsonify({"status": "error", "message": "An error occurred while fetching recommendations."}), 500
