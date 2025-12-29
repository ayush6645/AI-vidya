from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from backend import db
from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import firestore
import requests
import os
import re

# --- Imports for Data Science & New Features ---
# --- Imports for Data Science & New Features ---
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

from youtube_transcript_api import YouTubeTranscriptApi
# import spacy
import random

# --- Load the NLP models once when the server starts ---
print("Loading NLP models...")
# video_search_model = SentenceTransformer('all-MiniLM-L6-v2')
video_search_model = None # Placeholder
# quiz_model = spacy.load("en_core_web_md")
quiz_model = None # Placeholder
print("NLP models loaded.")

my_courses_bp = Blueprint('my_courses', __name__)

# ----------------------------- HELPER FUNCTIONS -----------------------------

def get_semantically_best_video(lesson: dict) -> str:
    """Finds the most semantically relevant YouTube video for a given lesson."""
    YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
    if not YOUTUBE_API_KEY:
        return ""

    search_query = f"{lesson.get('topic', '')} tutorial"
    lesson_text = f"{lesson.get('topic', '')}: {lesson.get('description', '')}"

    try:
        search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={search_query}&type=video&maxResults=5&key={YOUTUBE_API_KEY}"
        response = requests.get(search_url)
        response.raise_for_status()
        search_results = response.json().get('items', [])
        if not search_results:
            return ""

        # Use the first result as default since semantic search is disabled on deployment
        best_video_id = search_results[0]['id']['videoId']
        
        # --- Semantic logic disabled for deployment compatibility ---
        # if video_search_model:
        #     lesson_embedding = video_search_model.encode([lesson_text])
        #     video_texts = [f"{item['snippet']['title']}: {item['snippet']['description']}" for item in search_results]
        #     video_embeddings = video_search_model.encode(video_texts)
        #     similarities = cosine_similarity(lesson_embedding, video_embeddings)[0]
        #     best_match_index = similarities.argmax()
        #     best_video_id = search_results[best_match_index]['id']['videoId']
        
        # Return an embeddable URL

        return f"https://www.youtube.com/embed/{best_video_id}"

    except Exception as e:
        print(f"Semantic video search error: {e}")
        return ""


def get_transcript_for_lesson(lesson_id: str) -> str:
    """Fetches the transcript for a lesson's YouTube video."""
    lesson_doc = db.collection('lessons').document(lesson_id).get()
    if not lesson_doc.exists:
        return ""
    
    video_url = lesson_doc.to_dict().get('youtube_link', '')
    if video_url and 'embed' in video_url:
        video_id = video_url.split('/embed/')[-1]
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([item['text'] for item in transcript_list])
        except Exception as e:
            print(f"Could not get transcript for video {video_id}: {e}")
            return None # Return None to indicate a fetch error
    return ""
"""
def generate_quiz_with_nlp(text: str, num_questions: int = 5) -> dict:
    if not quiz_model:
        return {"quiz": []}
        
    doc = quiz_model(text)
    
    candidate_sents = [sent for sent in doc.sents if 10 < len(sent.text.split()) < 50 and sent.ents]
    num_questions = min(num_questions, len(candidate_sents))
    if num_questions == 0:
        return {"quiz": []}

    selected_sents = random.sample(candidate_sents, num_questions)
    quiz = []
    for sent in selected_sents:
        answer_entity = random.choice(sent.ents)
        answer = answer_entity.text
        question = sent.text.replace(answer, "_______")
        
        distractors = [ent.text for ent in doc.ents if ent.label_ == answer_entity.label_ and ent.text != answer]
        if len(distractors) < 3:
            answer_token = quiz_model(answer)[0]
            if answer_token.has_vector:
                similar_words = [token.text for token in doc if token.is_noun and token.has_vector and token.similarity(answer_token) > 0.6]
                distractors.extend(similar_words)
        
        final_distractors = list(set(distractors))
        if answer in final_distractors:
            final_distractors.remove(answer)
        
        options = random.sample(final_distractors, min(3, len(final_distractors))) + [answer]
        random.shuffle(options)
        
        quiz.append({"question": question, "options": options, "answer": answer})
        
    return {"quiz": quiz}
"""
# ----------------------------- PAGE ROUTES -----------------------------

@my_courses_bp.route('/api/my-courses')
def list_my_courses():
    if 'user_id' not in session: return redirect(url_for('login.login'))
    
    try:
        user_id = session['user_id']
        plans_ref = db.collection('plans').where(filter=FieldFilter('userId', '==', user_id)).order_by('creation_date', direction=firestore.Query.DESCENDING).stream()
        user_plans = [plan.to_dict() | {'id': plan.id} for plan in plans_ref]
        return render_template('my_courses_list.html', plans=user_plans)
    except Exception as e:
        print(f"My Courses List Error: {e}")
        return redirect(url_for('dashboard.show_dashboard'))

@my_courses_bp.route('/api/my-courses/<string:plan_id>')
def course_details(plan_id):
    """Endpoint to display course details with progress tracking"""
    if 'user_id' not in session:
        return redirect(url_for('login.login'))
    
    try:
        # Get plan document and verify ownership
        plan_ref = db.collection('plans').document(plan_id)
        plan_doc = plan_ref.get()
        if not plan_doc.exists or plan_doc.to_dict().get('userId') != session['user_id']:
            return redirect(url_for('my_courses.list_my_courses'))
        
        plan_data = plan_doc.to_dict()
        
        # Initialize progress tracking variables
        total_lessons = 0
        completed_lessons = 0
        
        # Get all modules for this plan
        modules_ref = db.collection('modules').where(
            filter=FieldFilter('planId', '==', plan_id)
        ).order_by('module_number').stream()
        
        modules_with_lessons = []
        all_lessons_flat = []
        
        for module in modules_ref:
            module_data = module.to_dict()
            module_data['module_number'] = module_data.get('module_number', '') or 'N/A'
            
            # Get all lessons for this module
            lessons_ref = db.collection('lessons').where(
                filter=FieldFilter('moduleId', '==', module.id)
            ).order_by('day_of_plan').stream()
            
            module_lessons = []
            for lesson in lessons_ref:
                lesson_data = lesson.to_dict()
                lesson_data['id'] = lesson.id
                
                # Track completion status
                is_completed = lesson_data.get('is_completed', False)
                if is_completed:
                    completed_lessons += 1
                total_lessons += 1
                
                module_lessons.append(lesson_data)
                all_lessons_flat.append(lesson_data)
            
            module_data['lessons'] = module_lessons
            modules_with_lessons.append(module_data)
        
        # Calculate progress percentage
        progress = 0
        if total_lessons > 0:
            progress = round((completed_lessons / total_lessons) * 100)
        
        # Update plan progress if different from stored value
        if plan_data.get('progress', 0) != progress:
            plan_ref.update({
                'progress': progress,
                'last_updated': firestore.SERVER_TIMESTAMP
            })
            plan_data['progress'] = progress
        
        # Get all notes for this plan
        notes_ref = db.collection('notes').where(
            filter=FieldFilter('planId', '==', plan_id)
        ).order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        
        user_notes = []
        for note in notes_ref:
            note_data = note.to_dict()
            note_data['id'] = note.id
            
            # Add lesson topic to note for display
            for lesson in all_lessons_flat:
                if lesson['id'] == note_data.get('lessonId'):
                    note_data['topic'] = lesson['topic']
                    break
            
            user_notes.append(note_data)
        
        return render_template(
            'my_course.html',
            plan=plan_data,
            modules=modules_with_lessons,
            lessons=all_lessons_flat,
            notes=user_notes,
            plan_id=plan_id
        )
        
    except Exception as e:
        print(f"Course Detail Error: {e}")
        flash('An error occurred while loading the course details', 'error')
        return redirect(url_for('my_courses.list_my_courses'))

# Add this new route to my_courses_route.py

@my_courses_bp.route('/plans/<string:plan_id>/delete', methods=['POST'])
def delete_plan(plan_id):
    """API endpoint to delete a specific plan and all its related data."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        plan_ref = db.collection('plans').document(plan_id)
        plan_doc = plan_ref.get()

        # Security check: Make sure the plan belongs to the logged-in user
        if not plan_doc.exists or plan_doc.to_dict().get('userId') != user_id:
            return jsonify({'status': 'error', 'message': 'Plan not found or permission denied.'}), 404

        # Find and delete all associated modules and lessons
        modules_query = db.collection('modules').where(filter=FieldFilter('planId', '==', plan_id)).stream()
        module_ids = [module.id for module in modules_query]

        if module_ids:
            lessons_query = db.collection('lessons').where(filter=FieldFilter('moduleId', 'in', module_ids)).stream()
            for lesson in lessons_query:
                lesson.reference.delete()
        
        for module_id in module_ids:
            db.collection('modules').document(module_id).delete()
        
        # Find and delete all associated notes
        notes_query = db.collection('notes').where(filter=FieldFilter('planId', '==', plan_id)).stream()
        for note in notes_query:
            note.reference.delete()

        # Finally, delete the plan itself
        plan_ref.delete()
        
        return jsonify({'status': 'success', 'message': 'Plan deleted successfully.'})
    except Exception as e:
        print(f"Delete Plan Error: {e}")
        return jsonify({'status': 'error', 'message': 'An error occurred while deleting the plan.'}), 500
    
# ----------------------------- API ROUTES -----------------------------
@my_courses_bp.route('/get-video-for-lesson/<string:lesson_id>', methods=['POST'])
def get_video_for_lesson(lesson_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        lesson_ref = db.collection('lessons').document(lesson_id)
        lesson_doc = lesson_ref.get()
        
        # Create document if it doesn't exist
        if not lesson_doc.exists:
            lesson_ref.set({
                'created_at': firestore.SERVER_TIMESTAMP,
                'status': 'Pending',
                'youtube_link': ''  # Initialize empty link
            })
            return jsonify({
                'status': 'error',
                'message': 'New lesson document created. Please try again.'
            }), 404

        lesson_data = lesson_doc.to_dict()
        
        # Return existing link if valid
        if lesson_data.get('youtube_link'):
            return jsonify({
                'status': 'success',
                'video_url': lesson_data['youtube_link'],
                'from_cache': True
            })

        # Find and save new video
        video_url = get_semantically_best_video(lesson_data)
        if not video_url:
            return jsonify({
                'status': 'error',
                'message': 'No suitable video found'
            }), 404

        # Update document with merge=True to preserve other fields
        lesson_ref.set({
            'youtube_link': video_url,
            'last_updated': firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        return jsonify({
            'status': 'success',
            'video_url': video_url,
            'from_cache': False
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@my_courses_bp.route('/lessons/<string:lesson_id>/completion', methods=['POST'])
def update_lesson_completion(lesson_id):
    """API endpoint to update lesson completion status and track overall progress"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        is_completed = data.get('is_completed', False)
        plan_id = data.get('plan_id')
        
        if not plan_id:
            return jsonify({'status': 'error', 'message': 'Plan ID is required'}), 400

        # Update the lesson completion status
        lesson_ref = db.collection('lessons').document(lesson_id)
        lesson_ref.update({
            'is_completed': is_completed,
            'last_updated': firestore.SERVER_TIMESTAMP
        })

        # Recalculate overall progress for the plan
        modules_query = db.collection('modules').where(filter=FieldFilter('planId', '==', plan_id)).stream()
        total_lessons = 0
        completed_lessons = 0
        
        for module in modules_query:
            lessons_query = db.collection('lessons').where(filter=FieldFilter('moduleId', '==', module.id)).stream()
            for lesson in lessons_query:
                total_lessons += 1
                if lesson.to_dict().get('is_completed', False):
                    completed_lessons += 1

        progress = 0
        if total_lessons > 0:
            progress = round((completed_lessons / total_lessons) * 100)

        # Update the plan's progress
        plan_ref = db.collection('plans').document(plan_id)
        plan_ref.update({
            'progress': progress,
            'last_updated': firestore.SERVER_TIMESTAMP
        })

        return jsonify({
            'status': 'success',
            'message': 'Lesson status updated',
            'progress': progress
        })

    except Exception as e:
        print(f"Error updating lesson completion: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    


@my_courses_bp.route('/lessons/<string:lesson_id>/ensure-video', methods=['POST'])
def ensure_video_link(lesson_id):
    """Endpoint to verify and fix missing video links"""
    try:
        lesson_ref = db.collection('lessons').document(lesson_id)
        lesson_data = lesson_ref.get().to_dict()
        
        if not lesson_data:
            return jsonify({'status': 'error', 'message': 'Lesson not found'}), 404

        # If link exists and is valid
        if lesson_data.get('youtube_link'):
            return jsonify({
                'status': 'success',
                'action': 'existing_link',
                'video_url': lesson_data['youtube_link']
            })

        # Generate and save new link
        video_url = get_semantically_best_video(lesson_data)
        if not video_url:
            return jsonify({
                'status': 'error',
                'message': 'No suitable video found'
            }), 404

        lesson_ref.set({'youtube_link': video_url}, merge=True)
        return jsonify({
            'status': 'success',
            'action': 'new_link_generated',
            'video_url': video_url
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@my_courses_bp.route('/lessons/<string:lesson_id>', methods=['GET'])
def get_lesson(lesson_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        lesson_doc = db.collection('lessons').document(lesson_id).get()
        if not lesson_doc.exists:
            return jsonify({'status': 'error', 'message': 'Lesson not found'}), 404
        
        lesson_data = lesson_doc.to_dict()
        return jsonify({
            'status': 'success',
            'lesson': {
                'id': lesson_id,
                'topic': lesson_data.get('topic'),
                'description': lesson_data.get('description'),
                'youtube_link': lesson_data.get('youtube_link'),
                'status': lesson_data.get('status', 'Not Started')
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

# backend/routes/my_courses_route.py
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
@my_courses_bp.route('/lesson/<string:lesson_id>/transcript', methods=['POST'])
def get_transcript(lesson_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    try:
        lesson_doc = db.collection('lessons').document(lesson_id).get()
        if not lesson_doc.exists:
            return jsonify({'status': 'error', 'message': 'Lesson not found'}), 404

        lesson_data = lesson_doc.to_dict()
        video_url = lesson_data.get('youtube_link', '')

        if 'embed/' not in video_url:
            return jsonify({'status': 'error', 'message': 'Invalid YouTube URL for this lesson.'}), 400

        video_id = video_url.split('embed/')[-1]

        # This line will now be handled by the specific exceptions below
        transcript_items = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = "\n".join([item['text'] for item in transcript_items])

        return jsonify({
            'status': 'success',
            'transcript': transcript_text,
            'video_url': video_url
        })

    # --- RE-WRITE THE ENTIRE EXCEPTION BLOCK LIKE THIS ---
    except (TranscriptsDisabled, NoTranscriptFound):
        # This is the expected error when a video has no captions.
        return jsonify({
            'status': 'error',
            'message': 'No transcript is available for this video. The owner may have disabled captions.'
        }), 404 # 404 Not Found is a suitable HTTP status
    except Exception as e:
        # This will catch any other unexpected errors (network issues, etc.)
        print(f"An unexpected error occurred while fetching transcript: {e}")
        return jsonify({'status': 'error', 'message': 'A server error occurred while trying to fetch the transcript.'}), 500


from google import genai

# ... (all your existing imports) ...
import json
def generate_llm_summary(video_title: str, video_description: str) -> str:
    # This function remains the same as before
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        return "Summary generation is currently disabled by the administrator."

    # New Client Initialization
    client = genai.Client(api_key=GOOGLE_API_KEY)
    model_id = 'gemini-2.5-flash-lite'
    
    prompt = f"""
    You are an expert content analyst. Based on the following video title and description, generate a concise, single-paragraph summary of about 100-150 words.
    The summary should be easy for a student to understand and capture the key learning points.

    **Video Title:** {video_title}
    **Video Description:** {video_description}

    **Generated Summary:**
    """
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"LLM Summary Generation Failed: {e}")
        return "The AI summary could not be generated at this time. Please try again later."
    
# In my_courses_route.py

# --- NEW All-in-One Function ---
def generate_summary_and_quiz_from_lesson(title: str, description: str) -> dict:
    """
    Uses the Gemini API to generate a detailed summary and a conceptual quiz
    in a single call, returning them in a structured JSON object.
    """
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        return {"summary": "Content generation is disabled by the administrator.", "quiz": []}

    genai.configure(api_key=GOOGLE_API_KEY)
    client = genai.Client(api_key=GOOGLE_API_KEY)
    model_id = 'gemini-2.5-flash-lite'

    # A more sophisticated prompt for a combined task
    prompt = f"""
    You are an expert instructor and content creator. Perform the following two tasks based on the provided lesson topic and description. Your response MUST be ONLY the raw JSON object, without any markdown formatting.

    **Lesson Topic:** {title}
    **Lesson Description:** {description}

    **Task 1: Write a Summary**
    Generate a detailed, informative summary of the lesson topic. The summary should be at least 4-5 paragraphs long and cover the key concepts, definitions, and importance of the topic. Write it as a piece of educational text. DO NOT mention "this video" or "the lesson".

    **Task 2: Create a Quiz**
    Based on the summary you just generated, create a 3-question multiple-choice quiz. The questions should test conceptual understanding, not just be "fill-in-the-blank".

    **JSON Output Format:**
    Return a single JSON object with two keys: "summary" (a string) and "quiz" (a list of objects), like this:
    {{"summary": "Your detailed summary here...", "quiz": [{{"question": "...", "options": ["...", "...", "..."], "answer": "..."}}]}}
    """
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        
        # Use regex to find and parse the JSON object
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            json_string = json_match.group(0)
            data = json.loads(json_string)
            return data
        else:
            print("Generation Failed: No valid JSON object found in the LLM response.")
            return {"summary": "Failed to generate content in the correct format.", "quiz": []}

    except Exception as e:
        print(f"Content Generation Failed: {e}")
        return {"summary": "An error occurred while generating content.", "quiz": []}

# In my_courses_route.py

# --- REPLACE the existing route with this simplified version ---
@my_courses_bp.route('/lesson/<string:lesson_id>/generate-summary', methods=['POST'])
def get_lesson_summary_and_quiz(lesson_id):
    """API endpoint to generate a lesson summary and quiz."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    try:
        # 1. Fetch lesson details
        lesson_doc = db.collection('lessons').document(lesson_id).get()
        lesson_data = lesson_doc.to_dict() if lesson_doc.exists else {}
        title = lesson_data.get('topic', '')
        description = lesson_data.get('description', '')

        if not title:
            return jsonify({'status': 'error', 'message': 'Lesson title is missing.'}), 400

        # 2. Call the new all-in-one function
        generated_content = generate_summary_and_quiz_from_lesson(title, description)

        # 3. Return the combined data
        return jsonify({
            'status': 'success',
            'summary': generated_content.get('summary'),
            'quiz': generated_content.get('quiz')
        })

    except Exception as e:
        print(f"Summary/Quiz route error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
       
@my_courses_bp.route('/lessons/<string:lesson_id>/status', methods=['POST'])
def update_lesson_status(lesson_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        new_status = request.get_json().get('status')
        db.collection('lessons').document(lesson_id).update({'status': new_status})
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# In backend/routes/my_courses_route.py
@my_courses_bp.route('/lessons/<string:lesson_id>/notes', methods=['GET'])
def get_notes_for_lesson(lesson_id):
    """API endpoint to fetch all notes for a specific lesson."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        # Query Firestore for notes linked to this lesson AND this user
        notes_ref = db.collection('notes').where(filter=FieldFilter('lessonId', '==', lesson_id)).where(filter=FieldFilter('userId', '==', session['user_id'])).stream()
        
        # Create a list of notes from the query results
        notes = [note.to_dict() | {'id': note.id} for note in notes_ref]
        
        return jsonify({'status': 'success', 'notes': notes})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@my_courses_bp.route('/my-courses/<string:plan_id>/add-note', methods=['POST'])
def add_note(plan_id):
    """API endpoint for saving a new note."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # --- Server-side validation ---
        title = data.get('title', '').strip()
        body = data.get('body', '').strip()
        lesson_id = data.get('lessonId')

        if not all([title, body, lesson_id]):
            return jsonify({'status': 'error', 'message': 'Title, body, and a linked lesson are required.'}), 400
        # --- End of validation ---

        note_data = {
            "userId": session['user_id'],
            "planId": plan_id,
            "lessonId": lesson_id,
            "title": title,
            "body": body,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        # Add the new note to the 'notes' collection
        update_time, note_ref = db.collection('notes').add(note_data)
        
        return jsonify({'status': 'success', 'message': 'Note saved!', 'noteId': note_ref.id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- ADD THESE TWO NEW ROUTES TO THE END OF my_courses_route.py ---

@my_courses_bp.route('/my-courses')
def api_list_my_courses():
    if 'user_id' not in session: return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    try:
        user_id = session['user_id']
        plans_ref = db.collection('plans').where('userId', '==', user_id).order_by('creation_date', direction='DESCENDING').stream()
        user_plans = []
        for plan in plans_ref:
            plan_data = plan.to_dict()
            plan_data['id'] = plan.id
            if 'creation_date' in plan_data and hasattr(plan_data['creation_date'], 'isoformat'):
                plan_data['creation_date'] = plan_data['creation_date'].isoformat()
            user_plans.append(plan_data)
        return jsonify({'status': 'success', 'plans': user_plans})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
# This route is now also needed for the API
@my_courses_bp.route('/my-courses/<string:plan_id>')
def api_course_details(plan_id):
    if 'user_id' not in session: return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    try:
        plan_doc = db.collection('plans').document(plan_id).get()
        if not plan_doc.exists or plan_doc.to_dict().get('userId') != session['user_id']:
            return jsonify({'status': 'error', 'message': 'Plan not found or permission denied'}), 404
        
        plan_data = plan_doc.to_dict()
        plan_data['id'] = plan_doc.id

        modules_ref = db.collection('modules').where('planId', '==', plan_id).order_by('module_number').stream()
        
        modules_with_lessons = []
        total_lessons_count = 0
        completed_lessons_count = 0

        for module in modules_ref:
            module_data = module.to_dict()
            module_data['id'] = module.id
            lessons_ref = db.collection('lessons').where('moduleId', '==', module.id).order_by('day_of_plan').stream()
            
            lessons_list = []
            for lesson in lessons_ref:
                lesson_data = lesson.to_dict()
                lesson_data['id'] = lesson.id
                lessons_list.append(lesson_data)
                total_lessons_count += 1
                if lesson_data.get('is_completed', False):
                    completed_lessons_count += 1

            module_data['lessons'] = lessons_list
            modules_with_lessons.append(module_data)
        
        progress = round((completed_lessons_count / total_lessons_count) * 100) if total_lessons_count > 0 else 0
        plan_data['progress'] = progress

        return jsonify({
            'status': 'success',
            'plan': plan_data,
            'modules': modules_with_lessons
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@my_courses_bp.route('/quizzes')
def show_quizzes_page():
    """
    Route to display the main quizzes page for the web app OR
    return JSON data for the mobile app, based on the request type.
    """
    if 'user_id' not in session:
        # If the request is from the app, return a JSON error
        if 'application/json' in request.headers.get('Accept', ''):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        # Otherwise, redirect the web browser to the login page
        return redirect(url_for('login.login'))

    user_id = session['user_id']

    try:
        # --- Part 1: Gather Data for Stats and History ---
        attempts_ref = db.collection('quiz_attempts').where(
            filter=FieldFilter('userId', '==', user_id)
        ).order_by('submitted_at', direction=firestore.Query.DESCENDING).stream()

        history = []
        total_score_sum = 0
        highest_score = 0
        
        all_lessons = {doc.id: doc.to_dict() for doc in db.collection('lessons').stream()}

        for attempt in attempts_ref:
            attempt_data = attempt.to_dict()
            lesson_id = attempt_data.get('lessonId')
            lesson_info = all_lessons.get(lesson_id, {})

            score_percent = round((attempt_data.get('score', 0) / attempt_data.get('total', 1)) * 100)

            # Convert Firestore Timestamp -> datetime -> string
            submitted_at = attempt_data.get('submitted_at')
            if submitted_at and hasattr(submitted_at, "to_datetime"):
                submitted_at = submitted_at.to_datetime()
            date_str = submitted_at.strftime('%B %d, %Y') if submitted_at else "N/A"

            history.append({
                "topic": lesson_info.get('topic', 'Unknown Topic'),
                "date": date_str,
                "score": f"{score_percent}% ({attempt_data.get('score')}/{attempt_data.get('total')})",
                "lessonId": lesson_id,
                "planId": attempt_data.get('planId')
            })
            
            total_score_sum += score_percent
            if score_percent > highest_score:
                highest_score = score_percent

        total_taken = len(history)
        stats = {
            'total_taken': total_taken,
            'average_score': round(total_score_sum / total_taken) if total_taken > 0 else 0,
            'highest_score': highest_score,
            'last_attempt': history[0]['topic'] if history else "N/A"
        }

        # This is used by the web template
        available_quizzes = list({item['topic']: item for item in history}.values())[:4]

        # --- Part 2: Gather Data for Leaderboard ---
        all_users = {doc.id: doc.to_dict() for doc in db.collection('users').stream()}
        user_scores = {}

        all_attempts = db.collection('quiz_attempts').stream()
        for attempt in all_attempts:
            data = attempt.to_dict()
            uid = data.get('userId')
            score = data.get('score', 0)
            user_scores[uid] = user_scores.get(uid, 0) + score
            
        sorted_users = sorted(user_scores.items(), key=lambda item: item[1], reverse=True)
        
        leaderboard = []
        for i, (uid, total_score) in enumerate(sorted_users[:5]):
            user_info = all_users.get(uid, {})
            leaderboard.append({
                'rank': i + 1,
                'name': user_info.get('username', 'Anonymous User'),
                'score': total_score
            })
        
        # --- Part 3: Return Correct Format Based on Request ---
        data_to_send = {
            'stats': stats, 
            'quiz_history': history, 
            'leaderboard': leaderboard,
            'available_quizzes': available_quizzes
        }

        # Debug log
        if 'application/json' in request.headers.get('Accept', ''):
            print("--- Sending this JSON to Flutter: ---", {'status': 'success', **data_to_send})

        if 'application/json' in request.headers.get('Accept', ''):
            return jsonify({
                'status': 'success',
                **data_to_send
            })
        else:
            return render_template('quizzes.html', **data_to_send)

    except Exception as e:
        print(f"Quizzes page error: {e}")
        if 'application/json' in request.headers.get('Accept', ''):
            return jsonify({'status': 'error', 'message': 'Could not load quiz data.'}), 500
        else:
            flash('An error occurred while loading the quiz data.', 'error')
            return redirect(url_for('dashboard.show_dashboard'))


@my_courses_bp.route('/lesson/<string:lesson_id>/submit-quiz', methods=['POST'])
def submit_quiz_score(lesson_id):
    """API endpoint to save a user's quiz score."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        score = data.get('score')
        total = data.get('total')
        plan_id = data.get('planId')

        if score is None or total is None or not plan_id:
            return jsonify({'status': 'error', 'message': 'Missing required data.'}), 400
        
        # Save to the new 'quiz_attempts' collection
        db.collection('quiz_attempts').add({
            'userId': session['user_id'],
            'lessonId': lesson_id,
            'planId': plan_id,
            'score': score,
            'total': total,
            'submitted_at': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({'status': 'success', 'message': 'Score saved!'})
    except Exception as e:
        print(f"Error saving quiz score: {e}")
        return jsonify({'status': 'error', 'message': 'Server error.'}), 500