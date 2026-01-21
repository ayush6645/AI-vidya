# AI-Vidya Educational Quality Standards
## Content Quality Control System

---

## 🎯 Overview

This document outlines the **strict educational quality standards** implemented in AI-Vidya's LLM service to ensure high-quality learning experiences.

---

## 📋 Implementation Locations

### 1. **Plan Generation** (`llm_service.py::generate_plan`)
Ensures AI-generated learning roadmaps follow professional educational standards.

### 2. **Video Ranking** (`llm_service.py::rank_video_candidates`)
Implements strict filtering to select only legitimate educational content.

### 3. **Search Optimization** (`llm_service.py::generate_youtube_search_query`)
Uses educational intent keywords for better video discovery.

---

## 🏗️ Roadmap Generation Rules

### Module Structure
- ✅ Clear, logical MODULES representing major learning phases
- ✅ Professional course-style naming
- ❌ Avoid vague or broad titles

### Lesson Design (Sub-Modules)
- ✅ Each lesson = ONE teachable concept
- ✅ Specific, actionable topics
- ✅ Smooth progression (basic → advanced)
- ❌ No broad or vague lesson titles

### Pacing & Density
- **HIGH investment (>2 hrs/day)**: In-depth topics, practical exercises
- **LOW investment (<1 hr/day)**: High-yield essential concepts only
- **ACCELERATED**: Rapid progression for short timelines

### Educational Quality
- ✅ Designed for serious study (not browsing)
- ✅ Clear learning objectives in descriptions
- ❌ No filler content or "motivational" days

### Video Search Optimization
**YouTube keywords MUST include educational intent terms**:
- ✅ "tutorial", "explained", "lecture", "step by step", "full course"
- ❌ Never use raw topic keywords alone

**Examples**:
```
❌ Bad:  "Binary Search"
✅ Good: "Binary Search algorithm explained step by step tutorial"

❌ Bad:  "React Hooks"
✅ Good: "React Hooks tutorial for beginners complete guide"
```

---

## 🎥 Video Selection Standards

### ❌ VIDEO EXCLUSION RULES (HARD FAIL)

**Reject IMMEDIATELY if video**:
- Is a YouTube Short
- Is music, song, remix, entertainment, or motivation
- Is shorter than 8 minutes
- Mentions topic but does NOT teach it
- Is clickbait or trend-based
- Has vague titles without educational intent

### ✅ VIDEO INCLUSION RULES (REQUIRED)

**Accept ONLY if video**:
- Clearly explains the exact lesson topic
- Includes examples, demonstrations, or walkthroughs
- Uses educational intent terms:
  - "tutorial", "explained", "lecture", "full course"
  - "step by step", "guide", "introduction", "deep dive"
- PRIMARY purpose is to TEACH (not entertain)

### 🔍 SEMANTIC VALIDATION (CRITICAL)

Before accepting ANY video, AI confirms:
1. ✅ Title + Description STRONGLY align with lesson topic
2. ✅ PRIMARY purpose is to TEACH this specific concept
3. ❌ No partial or indirect matches allowed

**Rule**: If validation fails → REJECT the video

---

## 🏆 Quality Hierarchy

### Tier 1 (BEST)
**Established Educators**:
- CrashCourse
- FreeCodeCamp
- Traversy Media

**Academic Channels**:
- MIT OpenCourseWare
- Stanford Online
- Khan Academy

**Expert Creators**:
- 3Blue1Brown
- Veritasium
- Fireship

### Tier 2 (GOOD)
- Professional tutorials matching exact topic
- Clear teaching structure
- Good production quality

### Tier 3 (ACCEPTABLE)
- Accurate content but lower production value
- MUST still match ALL inclusion rules

---

## 📊 Selection Priority

When multiple videos qualify:
1. **Quality**: Tier 1 > Tier 2 > Tier 3
2. **Comprehensiveness**: Prefer longer, in-depth tutorials
3. **Recency**: Prefer newer content (if quality is equal)

---

## 🎓 Core Philosophy

### User Intent
> **Users want to STUDY seriously, not browse**

### Quality Over Quantity
- Prioritize ACCURACY and EDUCATIONAL VALUE
- Better to have NO video than a poor-quality video

### When In Doubt
> **→ REJECT THE VIDEO**

---

## 🔄 Implementation Details

### Plan Generation Flow
```
User Input (Topic, Difficulty, Timeline, Time Investment)
    ↓
Enhanced Prompt with Quality Standards
    ↓
Groq LLM (Primary) / Gemini (Fallback)
    ↓
Structured JSON Roadmap
    ↓
Professional Modules + Specific Lessons + Optimized Search Terms
```

### Video Selection Flow
```
YouTube Search (with educational intent keywords)
    ↓
Fetch Top Candidates
    ↓
LLM Ranking with Strict Filters
    ↓
Exclusion Rules Applied
    ↓
Semantic Validation
    ↓
Quality Hierarchy Sorting
    ↓
Best Educational Video Selected (or None)
```

---

## ✅ Quality Assurance Checklist

### For Each Generated Plan:
- [ ] Every module has a professional name
- [ ] Every lesson teaches ONE specific concept
- [ ] Descriptions include clear learning objectives
- [ ] YouTube keywords include educational intent terms
- [ ] Pacing matches user's time investment
- [ ] No filler or motivational content

### For Each Video Selection:
- [ ] Video is 8+ minutes long
- [ ] Primary purpose is to TEACH
- [ ] Title/description strongly align with topic
- [ ] No entertainment/music/clickbait content
- [ ] Educational intent terms present
- [ ] Meets at least Tier 3 quality standards

---

## 🚀 Impact

### Before Implementation
- ❌ Generic lesson titles
- ❌ Vague YouTube searches
- ❌ Mixed quality videos (music, shorts, clickbait)
- ❌ Poor educational alignment

### After Implementation
- ✅ Professional, specific lesson plans
- ✅ Optimized educational searches
- ✅ Strictly curated educational content
- ✅ Strong topic-video alignment
- ✅ Quality-tiered selection system

---

## 📈 Future Enhancements

1. **Video Duration Filtering**: Add minimum duration check in YouTube API
2. **Channel Whitelist**: Pre-approved educational channels
3. **User Feedback Loop**: Learn from user ratings
4. **A/B Testing**: Compare strict vs. relaxed filtering
5. **ML-Based Ranking**: Train model on successful video selections

---

**Version**: 2.0  
**Last Updated**: January 21, 2026  
**Status**: ✅ Fully Implemented
