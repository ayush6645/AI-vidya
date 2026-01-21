import asyncio
from typing import Any, Dict, List, Optional
from backend.app.core import config
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud import firestore

class DBService:
    """
    Async wrapper for Firebase Firestore operations.
    Since firebase-admin is synchronous, we run these in a thread pool.
    """

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not config.db:
            config.init_firebase()
        if not config.db: return None
        def _get():
            doc = config.db.collection('users').document(user_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
        return await asyncio.to_thread(_get)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if not config.db:
            config.init_firebase()
        if not config.db: return None
        def _get():
            query = config.db.collection('users').where(filter=FieldFilter('email', '==', email)).limit(1).stream()
            docs = list(query)
            if docs:
                data = docs[0].to_dict()
                data['id'] = docs[0].id
                return data
            return None
        return await asyncio.to_thread(_get)

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        if not config.db:
            config.init_firebase()
        if not config.db: return None
        def _get():
            query = config.db.collection('users').where(filter=FieldFilter('username', '==', username)).limit(1).stream()
            docs = list(query)
            if docs:
                data = docs[0].to_dict()
                data['id'] = docs[0].id
                return data
            return None
        return await asyncio.to_thread(_get)
        
    async def create_user(self, email: str, data: Dict[str, Any]):
        # Firestore Auto-ID is better for new users than using email as key if we want consistency, 
        # but original code likely used email or auto-id.
        # The argument name `user_id` in original code in line 40 was ambiguous.
        # In calling code (auth.py): await db_service.create_user(email, user_data)
        # So it was using email as document ID. 
        if not config.db:
            config.init_firebase()
        if not config.db: raise Exception("Status: Database not connected")
        
        # We need to query by email first to check existence? Auth controller does that.
        # But wait, using email as Doc ID is risky if email changes (unlikely here but still).
        # Standard practice: Auto ID, store email as field.
        # However, looking at `get_user` (line 16), it expects `user_id`.
        # In `auth.py`: `access_token = security.create_access_token(user['id'])`
        # If we use email as ID, then user['id'] is email.
        # If we used auto-ID, user['id'] is UUID.
        
        # Let's see `get_user_by_email` implementation in line 23.
        # It queries `where('email', '==', email)`. This implies Email is a FIELD, not necessarily the ID.
        # IF email was ID, we would just do db.collection('users').document(email).get().
        
        # So, we should CREATE with a new ID (Auto) or use the logic from before.
        # In Phase 1 code (Flask), register route did:
        # db.collection('users').add(user_data) (which generates ID)
        # OR
        # db.collection('users').document(username).set(user_data) ?
        
        # Current implementation of `create_user` in Step 493 status:
        # async def create_user(self, user_id: str, data: Dict[str, Any]):
        #    await asyncio.to_thread(db.collection('users').document(user_id).set, data)
        
        # And called in `auth.py`: await db_service.create_user(email, user_data)
        # So it uses EMAIL as the Document ID.
        
        # BUT `get_user_by_username` returns `docs[0].to_dict()` which DOES NOT include the ID unless we add it.
        # In Step 493 line 37: `return docs[0].to_dict() if docs else None`
        # THIS IS THE BUG. `user` object in `auth.py` needs `user['id']`.
        # line 26 in `get_user_by_email` ADDS `data['id'] = docs[0].id`.
        # line 37 in `get_user_by_username` DOES NOT.
        
        # So when we login by username, `user['id']` is missing (or fails KeyAccess if strictly typed, but here it's dict).
        # Then `security.create_access_token(user['id'])` throws KeyError.
        # This causes the 500 error.
        
        if not config.db:
            config.init_firebase()
        if not config.db: raise Exception("Status: Database not connected")
        await asyncio.to_thread(config.db.collection('users').document(email).set, data)

    async def update_user(self, user_id: str, data: Dict[str, Any]):
        if not config.db:
            config.init_firebase()
        if not config.db: return
        await asyncio.to_thread(config.db.collection('users').document(user_id).update, data)

    async def delete_user(self, user_id: str):
         if not config.db: return
         await asyncio.to_thread(config.db.collection('users').document(user_id).delete)

    async def get_user_plans(self, user_id: str) -> List[Dict[str, Any]]:
        if not config.db:
            config.init_firebase()
        if not config.db: return []
        def _query():
            plans_ref = config.db.collection('plans').where(filter=FieldFilter('userId', '==', user_id)).order_by('creation_date', direction='DESCENDING').stream()
            return [p.to_dict() | {'id': p.id} for p in plans_ref]
        return await asyncio.to_thread(_query)
        
    async def create_plan(self, plan_data: Dict[str, Any]) -> str:
        if not config.db:
            config.init_firebase()
        if not config.db: raise Exception("Database Error")
        def _create():
            update_time, ref = config.db.collection('plans').add(plan_data)
            return ref.id
        return await asyncio.to_thread(_create)

    async def create_module(self, module_data: Dict[str, Any]) -> str:
        if not config.db:
            config.init_firebase()
        if not config.db: raise Exception("Database Error")
        def _create():
            update_time, ref = config.db.collection('modules').add(module_data)
            return ref.id
        return await asyncio.to_thread(_create)

    async def create_lesson(self, lesson_data: Dict[str, Any]):
         if not config.db:
             config.init_firebase()
         if not config.db: return
         await asyncio.to_thread(config.db.collection('lessons').add, lesson_data)

    async def get_plan_details(self, plan_id: str) -> Optional[Dict[str, Any]]:
        if not config.db:
            config.init_firebase()
        if not config.db: return None
        def _get():
            doc = config.db.collection('plans').document(plan_id).get()
            if doc.exists:
                return doc.to_dict() | {'id': doc.id}
            return None
        return await asyncio.to_thread(_get)

    async def delete_plan_full(self, plan_id: str, user_id: str):
        """Transaction-like deletion of plan and sub-collections"""
        if not config.db:
            config.init_firebase()
        if not config.db: return

        def _delete_logic():
            # Verify owner
            plan_ref = config.db.collection('plans').document(plan_id)
            plan_doc = plan_ref.get()
            if not plan_doc.exists or plan_doc.to_dict().get('userId') != user_id:
                raise ValueError("Unauthorized or Plan not found")

            # Get modules
            modules = list(config.db.collection('modules').where(filter=FieldFilter('planId', '==', plan_id)).stream())
            module_ids = [m.id for m in modules]

            # Delete lessons
            if module_ids:
                lessons = config.db.collection('lessons').where(filter=FieldFilter('moduleId', 'in', module_ids)).stream()
                for l in lessons: l.reference.delete()
            
            # Delete modules
            for m in modules: m.reference.delete()

            # Delete notes
            notes = config.db.collection('notes').where(filter=FieldFilter('planId', '==', plan_id)).stream()
            for n in notes: n.reference.delete()

            # Delete plan
            plan_ref.delete()

        await asyncio.to_thread(_delete_logic)

    async def get_modules_by_plan(self, plan_id: str) -> List[Dict[str, Any]]:
        def _get():
             return [m.to_dict() | {'id': m.id} for m in config.db.collection('modules').where(filter=FieldFilter('planId', '==', plan_id)).order_by('module_number').stream()]
        return await asyncio.to_thread(_get)

    async def get_lessons_by_module(self, module_id: str) -> List[Dict[str, Any]]:
        def _get():
             return [l.to_dict() | {'id': l.id} for l in config.db.collection('lessons').where(filter=FieldFilter('moduleId', '==', module_id)).order_by('day_of_plan').stream()]
        return await asyncio.to_thread(_get)
    
    async def get_lesson(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        if not config.db:
            config.init_firebase()
        if not config.db: return None
        def _get():
            doc = config.db.collection('lessons').document(lesson_id).get()
            return doc.to_dict() | {'id': doc.id} if doc.exists else None
        return await asyncio.to_thread(_get)

    async def update_lesson(self, lesson_id: str, data: Dict[str, Any]):
        await asyncio.to_thread(config.db.collection('lessons').document(lesson_id).update, data)

    async def add_note(self, note_data: Dict[str, Any]) -> str:
        def _add():
            _, ref = config.db.collection('notes').add(note_data)
            return ref.id
        return await asyncio.to_thread(_add)

    async def get_notes(self, user_id: str, lesson_id: Optional[str] = None) -> List[Dict[str, Any]]:
        def _get():
            query = config.db.collection('notes').where(filter=FieldFilter('userId', '==', user_id))
            if lesson_id:
                query = query.where(filter=FieldFilter('lessonId', '==', lesson_id))
            return [n.to_dict() | {'id': n.id} for n in query.stream()]
        return await asyncio.to_thread(_get)

    async def get_completed_lessons_count(self, user_id: str) -> int:
        if not config.db:
            config.init_firebase()
        if not config.db: return 0
        def _count():
            # Join is hard in Firestore. We need to find all plans for user, then all modules, then all lessons?
            # Or simpler: if we store userId on lessons (denormalization), it's easy.
            # But currently lessons only have moduleId.
            # Modules have planId. Plans have userId.
            
            # Alternative: User has a 'completed_lessons' collection or array? No.
            
            # Fetch all plans for user
            plans = config.db.collection('plans').where(filter=FieldFilter('userId', '==', user_id)).stream()
            plan_ids = [p.id for p in plans]
            
            if not plan_ids: return 0
            
            # Fetch all modules for these plans
            # Firestore 'in' query supports up to 10/30 items. If user has many plans, this breaks.
            # Batching needed. 
            
            # For "Complete Potential", let's do it properly even if slow for now (it's a demo).
            # Better: Fetch all lessons where 'completed' == True, then filter in memory? 
            # No, that's scanning ALL lessons in DB. Bad.
            
            # Let's iterate plans.
            count = 0
            for pid in plan_ids:
                modules = config.db.collection('modules').where(filter=FieldFilter('planId', '==', pid)).stream()
                mod_ids = [m.id for m in modules]
                if not mod_ids: continue
                
                # Check lessons for these modules
                # Batch mod_ids in chunks of 10 for 'in' query
                for i in range(0, len(mod_ids), 10):
                    chunk = mod_ids[i:i+10]
                    lessons = config.db.collection('lessons').where(filter=FieldFilter('moduleId', 'in', chunk)).where(filter=FieldFilter('completed', '==', True)).count().get()
                    count += lessons[0][0].value
            return count

        return await asyncio.to_thread(_count)

    async def add_quiz_result(self, result_data: Dict[str, Any]) -> str:
        if not config.db:
            config.init_firebase()
        if not config.db: return ""
        def _add():
            _, ref = config.db.collection('quiz_results').add(result_data)
            return ref.id
        return await asyncio.to_thread(_add)

    async def get_quiz_history(self, user_id: str) -> List[Dict[str, Any]]:
        if not config.db:
            config.init_firebase()
        if not config.db: return []
        def _get():
            # NOTE: Removed server-side order_by to avoid needing a composite index
            query = config.db.collection('quiz_results').where(filter=FieldFilter('userId', '==', user_id))
            results = [q.to_dict() | {'id': q.id} for q in query.stream()]
            # Client-side sort by date descending
            results.sort(key=lambda x: x.get('date', ''), reverse=True)
            return results
        return await asyncio.to_thread(_get)

    async def get_quiz_average(self, user_id: str) -> str:
        if not config.db:
            config.init_firebase()
        if not config.db: return "N/A"
        def _avg():
            query = config.db.collection('quiz_results').where(filter=FieldFilter('userId', '==', user_id)).stream()
            scores = []
            for q in query:
                d = q.to_dict()
                if d.get('total') and d.get('total') > 0:
                    scores.append((d.get('score', 0) / d.get('total', 1)) * 100)
            
            if not scores: return "N/A"
            avg = sum(scores) / len(scores)
            return f"{avg:.0f}%"
        return await asyncio.to_thread(_avg)

    async def get_leaderboard(self) -> List[Dict[str, Any]]:
        if not config.db:
            config.init_firebase()
        if not config.db: return []
        def _get():
            # Fetch users (limit 20 to avoid loading too many, sort in memory)
            # We don't use order_by here to ensure we get users even if they lack 'total_points'
            query = config.db.collection('users').limit(20).stream()
            users = [u.to_dict() | {'id': u.id} for u in query]
            # Sort by total_points descending, default to 0
            users.sort(key=lambda x: x.get('total_points', 0), reverse=True)
            return users[:10]
        return await asyncio.to_thread(_get)

    async def update_user_score(self, user_id: str, points: int):
        if not config.db:
            config.init_firebase()
        if not config.db: return
        def _update():
            # Atomic increment? Firestore supports FieldValue.increment
            doc_ref = config.db.collection('users').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                doc_ref.update({"total_points": firestore.Increment(points)})
            else:
                pass
        await asyncio.to_thread(_update)

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        if not config.db:
            config.init_firebase()
        if not config.db: return {"streak": 0, "level": 1, "total_quizzes": 0}
        def _calc():
            # 1. Get Quiz Count for Level Calculation
            quizzes = config.db.collection('quiz_results').where(filter=FieldFilter('userId', '==', user_id)).count().get()
            total_quizzes = quizzes[0][0].value
            
            # Level Logic:
            # L1->L2 requires 5 quizzes. Step is 5 until L10.
            # After L10, step increases by 2? Or step becomes 7?
            # User: "increase the number with 2 quizzes"
            # Interpretation: Step size = 5 + ((Level - 10) * 2) ?? No, that's complex.
            # Simple interpretation:
            # - If quizzes < 50: Level = 1 + (quizzes // 5)
            # - If quizzes >= 50:
            #     base_level = 10
            #     remaining = quizzes - 45  (Wait, 10 * 5 = 50. So 0-4=L1... 45-49=L10).
            #     Actually: 50th quiz triggers L11?
            #     Let's use a loop for precision after 50.
            
            level = 1
            if total_quizzes < 45: # 0-44 quizzes (Maps to Levels 1-9)
                 level = 1 + (total_quizzes // 5)
            else:
                # Level 10 achieved at 45 quizzes?
                # Let's say L1 = 0, L2 = 5, L3 = 10 ... L10 = 45.
                # After L10 (45 quizzes), next level L11 needs +7 (5+2) quizzes? => 52
                # L12 needs +9 (7+2) quizzes? => 61
                
                # Let's just implement fixed step of 7 after L10 for simplicity unless dynamic is strictly needed.
                # "increase the number with 2 quizzes... to increase the level" implies dynamic step.
                
                current_q = 45
                current_lvl = 10
                step = 7 # 5 + 2
                
                while total_quizzes >= (current_q + step):
                    current_q += step
                    current_lvl += 1
                    step += 2 # Increase step by 2 each time
                
                # If total_quizzes is between current_q and current_q + step, we are at current_lvl
                if total_quizzes >= 45: 
                     # Re-eval simplistic logic:
                     # If total_quizzes=45, we are L10. Next req 45+7=52.
                     # If total=50, 50 < 52, so L10.
                     pass 
                
                # Let's refine the loop
                remaining = total_quizzes - 45
                lvl_inc = 0
                step = 7
                while remaining >= step:
                    remaining -= step
                    lvl_inc += 1
                    step += 2
                
                level = 10 + lvl_inc

            # 2. Calculate Streak
            # We need a 'last_activity_date' on user or infer from quiz/lesson dates.
            # Inferring is expensive (fetching all dates).
            # Let's check 'users' collection for 'streak' and 'last_active'.
            # If not present, default to 0.
            user_doc = config.db.collection('users').document(user_id).get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            
            streak = user_data.get('streak', 0)
            
            return {
                "streak": streak,
                "level": level,
                "total_quizzes": total_quizzes,
                "xp": user_data.get('total_points', 0)
            }
        return await asyncio.to_thread(_calc)

db_service = DBService()
