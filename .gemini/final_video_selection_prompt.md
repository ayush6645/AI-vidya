# FINAL VIDEO SELECTION PROMPT - ULTRA STRICT FILTERING

Your task is to select ONLY valid educational YouTube videos for serious learning.

Lesson Topic: {topic}
Lesson Description: {description}

Candidate Videos:
{candidates_str}

═══════════════════════════════════════════════════════════
STRICT RULES (NON-NEGOTIABLE)
═══════════════════════════════════════════════════════════

1. VIDEO SELECTION CRITERIA
Accept ONLY if the video:
✅ Is a tutorial or lecture
✅ Clearly teaches the EXACT concept from the lesson
✅ Is suitable for serious, focused learning
✅ Is longer than 8 minutes
✅ Has clear teaching intent in title/description

2. HARD REJECTIONS (IMMEDIATE DISQUALIFICATION)
Reject ANY video that is:
❌ A YouTube Short (< 1 min)
❌ Music, song, remix, entertainment, or pop culture
❌ Shorter than 8 minutes
❌ Not primarily instructional
❌ Selected due to popularity or fame (not educational value)
❌ A live performance, concert, or event
❌ Comedy, satire, or entertainment-focused

3. TITLE & DESCRIPTION VALIDATION
ACCEPT only if title/description contains teaching keywords:
✅ "tutorial", "explained", "lecture", "course", "lesson"
✅ "step by step", "guide", "introduction", "learn", "how to"
✅ "crash course", "masterclass", "training", "workshop"

REJECT if title/description contains:
❌ "official video", "music video", "MV", "lyrics"
❌ "song", "remix", "cover", "live performance"
❌ "reaction", "review", "commentary" (unless educational)
❌ "funny", "comedy", "prank", "challenge"

4. SEMANTIC VALIDATION (CRITICAL)
Before accepting ANY video, ask yourself:
"Is the PRIMARY purpose of this video to TEACH {topic}?"

If the answer is NOT a clear YES → REJECT

5. DOMAIN ENFORCEMENT
Since this is a learning platform:
- Technical/academic topics → ONLY tutorials/lectures allowed
- Entertainment content → STRICTLY FORBIDDEN
- Music/pop culture → AUTOMATIC REJECTION

6. QUALITY HIERARCHY (For Educational Videos ONLY)

Tier 1 (BEST - Established Educators):
- "CrashCourse", "freeCodeCamp", "MIT OpenCourseWare"
- "Khan Academy", "Stanford Online", "Coursera"
- "3Blue1Brown", "Fireship", "Traversy Media"
- "The Coding Train", "Academind", "Net Ninja"

Tier 2 (GOOD - Professional Tutorials):
- Clear teaching structure
- Demonstrates concepts with examples
- Good production quality

Tier 3 (ACCEPTABLE):
- Educational but lower production
- MUST still meet ALL acceptance criteria

═══════════════════════════════════════════════════════════
OUTPUT INSTRUCTIONS
═══════════════════════════════════════════════════════════

Step 1: FILTER OUT all non-educational content
Step 2: VALIDATE remaining videos for teaching intent
Step 3: SELECT the best educational match

Return ONLY the 'videoId' of the best educational video.

If NO video meets the strict educational standards:
Return EXACTLY: "None"

═══════════════════════════════════════════════════════════
EXAMPLES OF REJECTIONS
═══════════════════════════════════════════════════════════

❌ "Artist - Song Name (Official Video)" → REJECT (Music)
❌ "Top 10 [Topic]" → REJECT (Listicle, not tutorial)
❌ "[Topic] in 60 seconds" → REJECT (Too short)
❌ "React to [Topic]" → REJECT (Entertainment)
❌ "[Famous Person] talks about [Topic]" → REJECT (Not instructional)

✅ "[Topic] Tutorial for Beginners" → ACCEPT (Clear teaching intent)
✅ "[Topic] Explained Step by Step" → ACCEPT (Educational)
✅ "Learn [Topic] - Full Course" → ACCEPT (Comprehensive tutorial)

═══════════════════════════════════════════════════════════
FINAL REMINDER
═══════════════════════════════════════════════════════════

This is a LEARNING PLATFORM.
Users want to STUDY seriously, not be entertained.

When in doubt → REJECT the video.
Better to return "None" than recommend bad content.

PRIORITIZE: Educational value, teaching clarity, instructional intent.
REJECT: Entertainment, music, popularity-based selections.
