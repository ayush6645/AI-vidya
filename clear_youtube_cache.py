"""
Script to delete all cached YouTube video links from Firebase.
This will force the system to fetch fresh videos for all lessons.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.db_service import db_service

async def clear_all_youtube_links():
    """Delete all youtube_link fields from all lessons in Firebase."""
    
    print("🗑️ Starting to clear all cached YouTube links...")
    
    try:
        # We need to get all users first, then their plans
        # Since we don't have a get_all_users method, we'll use a simpler approach:
        # Just clear youtube_link from ALL lessons in the lessons collection
        
        print("\n📚 Clearing all lessons directly from lessons collection...")
        
        # Access Firestore directly
        from backend.app.core.config import db
        
        def _clear_all_lessons():
            lessons_ref = db.collection('lessons')
            lessons = lessons_ref.stream()
            
            count = 0
            cleared = 0
            
            for lesson_doc in lessons:
                count += 1
                lesson_data = lesson_doc.to_dict()
                
                if lesson_data.get('youtube_link'):
                    # Delete the youtube_link field
                    lesson_doc.reference.update({'youtube_link': firestore.DELETE_FIELD})
                    cleared += 1
                    print(f"  ✅ Cleared: {lesson_data.get('topic', 'Unknown')}")
                else:
                    print(f"  ⏭️  No cache: {lesson_data.get('topic', 'Unknown')}")
            
            return count, cleared
        
        total, cleared = await asyncio.to_thread(_clear_all_lessons)
        
        print("\n" + "="*60)
        print(f"✅ COMPLETE!")
        print(f"Total lessons processed: {total}")
        print(f"Cached links cleared: {cleared}")
        print(f"Already empty: {total - cleared}")
        print("="*60)
        print("\n🎉 All done! Fresh videos will be fetched on next visit!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("="*60)
    print("CLEAR ALL CACHED YOUTUBE LINKS")
    print("="*60)
    print("\nThis will delete all cached video links from Firebase.")
    print("Fresh videos will be fetched when you click on lessons.\n")
    
    confirmation = input("Are you sure? (yes/no): ").lower().strip()
    
    if confirmation == "yes":
        asyncio.run(clear_all_youtube_links())
    else:
        print("\n❌ Cancelled. No changes made.")
