# FastAPI backend with Firebase authentication and profile management
from datetime import datetime
from typing import Optional, List, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore, auth
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field, field_validator
import os
import uuid
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AI Integration imports
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import httpx
from ai_services import gemini_service, vapi_service

# Initialize Firebase Admin SDK
try:
    # First, try to use the service account file (most reliable for development)
    if os.path.exists("firebase-service-account.json"):
        if not firebase_admin._apps:
            cred = credentials.Certificate("firebase-service-account.json")
            firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized with service account file")
        db = firestore.client()
    else:
        print("⚠️  Service account file not found, trying Application Default Credentials...")
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        print("✅ Firebase initialized with Application Default Credentials")
        db = firestore.client()
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")
    print("🔄 Running in offline mode with mock data...")
    db = None

# Initialize Google Gemini AI
genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY", "your-gemini-api-key-here"))

app = FastAPI(title="EchoHire API", version="1.0.0")

# Pydantic Models
class ProfileIn(BaseModel):
    displayName: Optional[str] = Field(None, max_length=80)
    headline: Optional[str] = Field(None, max_length=140)
    skills: Optional[List[str]] = Field(None, max_items=50)
    location: Optional[str] = Field(None, max_length=100)

    @field_validator('displayName')
    @classmethod
    def validate_display_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 80:
                raise ValueError('Display name must be 80 characters or less')
        return v

    @field_validator('headline')
    @classmethod
    def validate_headline(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 140:
                raise ValueError('Headline must be 140 characters or less')
        return v

    @field_validator('skills')
    @classmethod
    def validate_skills(cls, v):
        if v is not None:
            if len(v) > 50:
                raise ValueError('Maximum 50 skills allowed')
            for skill in v:
                if len(skill.strip()) > 40:
                    raise ValueError('Each skill must be 40 characters or less')
        return [skill.strip() for skill in v] if v else None

class ProfileOut(BaseModel):
    uid: str
    email: str
    displayName: Optional[str]
    headline: Optional[str]
    skills: List[str]
    location: Optional[str]
    createdAt: str
    updatedAt: str

# Interview Models
class InterviewIn(BaseModel):
    jobTitle: str = Field(..., max_length=200)
    companyName: Optional[str] = Field(None, max_length=200)
    interviewDate: str  # ISO format date
    status: str = Field(default="pending")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['pending', 'completed', 'scheduled', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v

class InterviewOut(BaseModel):
    id: str
    jobTitle: str
    companyName: Optional[str]
    interviewDate: str
    status: str
    overallScore: Optional[int]
    userId: str
    createdAt: str
    updatedAt: str

# Feedback Models
class EvaluationCriteriaModel(BaseModel):
    title: str
    score: int
    maxScore: int
    feedback: str
    isPassed: bool

class FeedbackIn(BaseModel):
    interviewId: str
    overallScore: int = Field(..., ge=0, le=100)
    overallImpression: str
    breakdown: List[EvaluationCriteriaModel]
    finalVerdict: str
    recommendation: str = Field(default="notRecommended")

    @field_validator('recommendation')
    @classmethod
    def validate_recommendation(cls, v):
        valid_recommendations = ['recommended', 'notRecommended', 'conditionallyRecommended']
        if v not in valid_recommendations:
            raise ValueError(f'Recommendation must be one of: {valid_recommendations}')
        return v

class FeedbackOut(BaseModel):
    id: str
    interviewId: str
    userId: str
    overallScore: int
    overallImpression: str
    breakdown: List[EvaluationCriteriaModel]
    finalVerdict: str
    recommendation: str
    createdAt: str

# AI Interview Generation Models
class InterviewQuestionModel(BaseModel):
    question: str
    category: str
    difficulty: str

class InterviewRequest(BaseModel):
    role: str = Field(..., max_length=200)
    type: str = Field(..., max_length=50)
    level: str = Field(..., max_length=50)
    userId: str

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ['technical', 'behavioral', 'system-design', 'coding']
        if v not in valid_types:
            raise ValueError(f'Type must be one of: {valid_types}')
        return v

    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        valid_levels = ['junior', 'mid', 'senior', 'lead']
        if v not in valid_levels:
            raise ValueError(f'Level must be one of: {valid_levels}')
        return v

class InterviewSessionOut(BaseModel):
    id: str
    userId: str
    role: str
    type: str
    level: str
    questions: List[InterviewQuestionModel]
    createdAt: str

# AI-specific Models
class AIInterviewStartRequest(BaseModel):
    interviewId: str
    candidatePhoneNumber: Optional[str] = None
    vapiSettings: Optional[Dict[str, Any]] = None

class AIInterviewStartResponse(BaseModel):
    aiSessionId: str
    vapiCallId: str
    status: str
    message: str

class AIInterviewStatusResponse(BaseModel):
    aiSessionId: str
    status: str  # "pending", "in_progress", "completed", "failed"
    duration: Optional[int] = None
    transcriptUrl: Optional[str] = None
    audioRecordingUrl: Optional[str] = None

class AIFeedbackResponse(BaseModel):
    interviewId: str
    aiAnalysisId: str
    overallScore: int
    overallImpression: str
    keyInsights: List[str]
    confidenceScore: float
    speechAnalysis: Dict[str, Any]
    transcriptAnalysis: str
    emotionalAnalysis: Dict[str, float]
    recommendation: str

# Firebase token verification dependency
async def verify_firebase_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.split(" ")[1]
    try:
        if db is None:
            # Firebase not properly initialized - use development mode
            print("🔄 Firebase not initialized - using development mode")
            return {
                "uid": "dev-user-123",
                "email": "dev@example.com",
                "name": "Development User"
            }
        
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Token verification error: {e}")
        
        # In development, allow requests with a mock user when Firebase fails
        if os.getenv("DEBUG", "False").lower() == "true":
            print("🔄 Using development mode due to Firebase auth error")
            return {
                "uid": "dev-user-123", 
                "email": "dev@example.com",
                "name": "Development User"
            }
        
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Endpoints
@app.get("/health")
async def health_check():
    return {"ok": True}

# AI Interview Generation Endpoint
@app.post("/api/generate-interview", response_model=InterviewSessionOut)
async def generate_interview(
    request: InterviewRequest,
    user_data: dict = Depends(verify_firebase_token)
):
    """
    Generate an AI-powered interview session with questions based on role, type, and level.
    For now, this returns mock data until AI integration is complete.
    """
    try:
        # Verify user owns this request
        if request.userId != user_data["uid"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Generate interview session ID
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        # Mock questions based on type and level (replace with AI generation later)
        questions = _generate_mock_questions(request.type, request.level, request.role)

        # Create interview session
        interview_session = {
            "id": session_id,
            "userId": request.userId,
            "role": request.role,
            "type": request.type,
            "level": request.level,
            "questions": [q.dict() for q in questions],
            "createdAt": now
        }

        # Save to Firebase
        session_ref = db.collection("interview_sessions").document(session_id)
        session_ref.set(interview_session)

        return InterviewSessionOut(**interview_session)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Interview generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate interview")

def _generate_mock_questions(interview_type: str, level: str, role: str) -> List[InterviewQuestionModel]:
    """
    Generate mock questions based on interview parameters.
    This will be replaced with AI generation (Gemini/Vapi) in the future.
    """
    base_questions = {
        "technical": {
            "junior": [
                InterviewQuestionModel(
                    question=f"Explain the basic concepts of object-oriented programming in the context of {role}.",
                    category="fundamentals",
                    difficulty="easy"
                ),
                InterviewQuestionModel(
                    question="What is the difference between a stack and a queue? Provide examples.",
                    category="data structures",
                    difficulty="easy"
                ),
                InterviewQuestionModel(
                    question=f"How would you debug a simple application as a {role}?",
                    category="problem solving",
                    difficulty="easy"
                ),
                InterviewQuestionModel(
                    question="Explain the concept of Big O notation with examples.",
                    category="algorithms",
                    difficulty="medium"
                ),
                InterviewQuestionModel(
                    question=f"What are the key responsibilities of a {role} in a development team?",
                    category="role specific",
                    difficulty="easy"
                )
            ],
            "mid": [
                InterviewQuestionModel(
                    question=f"Design a scalable architecture for a {role} application with 10,000 daily users.",
                    category="system design",
                    difficulty="medium"
                ),
                InterviewQuestionModel(
                    question="Explain the CAP theorem and its implications in distributed systems.",
                    category="distributed systems",
                    difficulty="medium"
                ),
                InterviewQuestionModel(
                    question="How would you optimize database queries for better performance?",
                    category="databases",
                    difficulty="medium"
                ),
                InterviewQuestionModel(
                    question=f"Describe your approach to code review and mentoring junior {role}s.",
                    category="leadership",
                    difficulty="medium"
                ),
                InterviewQuestionModel(
                    question="Implement a thread-safe singleton pattern and explain potential issues.",
                    category="concurrency",
                    difficulty="medium"
                )
            ],
            "senior": [
                InterviewQuestionModel(
                    question=f"Design a microservices architecture for a large-scale {role} platform.",
                    category="system design",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question="How would you handle data consistency in a distributed system?",
                    category="distributed systems",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question=f"Describe your strategy for technical debt management in a {role} team.",
                    category="technical leadership",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question="Design a caching strategy for a high-traffic application.",
                    category="performance",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question=f"How do you stay current with technology trends relevant to {role}?",
                    category="continuous learning",
                    difficulty="medium"
                )
            ],
            "lead": [
                InterviewQuestionModel(
                    question=f"How would you scale a {role} team from 5 to 50 engineers?",
                    category="leadership",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question="Design a disaster recovery plan for a critical production system.",
                    category="system design",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question=f"Describe your approach to setting technical vision for a {role} organization.",
                    category="strategic thinking",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question="How do you balance technical excellence with business requirements?",
                    category="business alignment",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question=f"What metrics would you use to measure success in a {role} team?",
                    category="metrics",
                    difficulty="medium"
                )
            ]
        },
        "behavioral": {
            "junior": [
                InterviewQuestionModel(
                    question="Tell me about a time when you had to learn a new technology quickly.",
                    category="adaptability",
                    difficulty="easy"
                ),
                InterviewQuestionModel(
                    question="Describe a challenging problem you solved and your approach.",
                    category="problem solving",
                    difficulty="easy"
                ),
                InterviewQuestionModel(
                    question="How do you handle feedback and criticism?",
                    category="growth mindset",
                    difficulty="easy"
                ),
                InterviewQuestionModel(
                    question="Tell me about a time you worked effectively in a team.",
                    category="teamwork",
                    difficulty="easy"
                ),
                InterviewQuestionModel(
                    question=f"Why are you interested in working as a {role}?",
                    category="motivation",
                    difficulty="easy"
                )
            ],
            "mid": [
                InterviewQuestionModel(
                    question="Describe a time when you had to make a difficult technical decision.",
                    category="decision making",
                    difficulty="medium"
                ),
                InterviewQuestionModel(
                    question="Tell me about a project that didn't go as planned. How did you handle it?",
                    category="resilience",
                    difficulty="medium"
                ),
                InterviewQuestionModel(
                    question="How do you prioritize competing demands on your time?",
                    category="time management",
                    difficulty="medium"
                ),
                InterviewQuestionModel(
                    question="Describe a time when you had to influence others without authority.",
                    category="influence",
                    difficulty="medium"
                ),
                InterviewQuestionModel(
                    question=f"How do you approach mentoring junior {role}s?",
                    category="mentorship",
                    difficulty="medium"
                )
            ],
            "senior": [
                InterviewQuestionModel(
                    question="Tell me about a time you led a significant technical change.",
                    category="change management",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question="Describe how you've handled a conflict within your team.",
                    category="conflict resolution",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question="How do you ensure your team delivers high-quality work under pressure?",
                    category="quality management",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question=f"Tell me about a time you had to make a strategic decision for your {role} team.",
                    category="strategic thinking",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question="How do you balance innovation with reliability?",
                    category="risk management",
                    difficulty="medium"
                )
            ],
            "lead": [
                InterviewQuestionModel(
                    question=f"Describe your vision for the future of {role} in your organization.",
                    category="vision",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question="How do you develop and retain top technical talent?",
                    category="talent management",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question="Tell me about a time you had to make an unpopular but necessary decision.",
                    category="tough decisions",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question="How do you measure and improve team performance?",
                    category="performance management",
                    difficulty="hard"
                ),
                InterviewQuestionModel(
                    question=f"What's the biggest challenge facing {role}s today?",
                    category="industry insight",
                    difficulty="medium"
                )
            ]
        }
    }

    # Get questions for the specific type and level
    questions = base_questions.get(interview_type, {}).get(level, [])
    
    # If no specific questions found, return generic ones
    if not questions:
        questions = [
            InterviewQuestionModel(
                question=f"Tell me about your experience as a {role}.",
                category="experience",
                difficulty="easy"
            ),
            InterviewQuestionModel(
                question=f"What interests you most about this {role} position?",
                category="motivation",
                difficulty="easy"
            ),
            InterviewQuestionModel(
                question=f"How do you stay updated with {role} best practices?",
                category="continuous learning",
                difficulty="easy"
            )
        ]
    
    return questions

@app.get("/me", response_model=ProfileOut)
async def get_profile(user_data: dict = Depends(verify_firebase_token)):
    try:
        uid = user_data["uid"]
        email = user_data.get("email", "dev@example.com")

        if db is None:
            # Return mock profile when Firebase is not available
            print("🔄 Returning mock profile data - Firebase not available")
            now = datetime.utcnow().isoformat() + "Z"
            mock_profile = ProfileOut(
                uid=uid,
                email=email,
                displayName="Development User",
                headline="Flutter Developer | EchoHire Tester",
                skills=["Flutter", "Dart", "Firebase", "FastAPI"],
                location="Development Environment",
                createdAt=now,
                updatedAt=now
            )
            return mock_profile

        # Try to get existing profile
        profile_ref = db.collection("profiles").document(uid)
        profile_doc = profile_ref.get()

        if profile_doc.exists:
            profile_data = profile_doc.to_dict()
            return ProfileOut(**profile_data)

        # Create new profile with defaults
        now = datetime.utcnow().isoformat() + "Z"
        new_profile = {
            "uid": uid,
            "email": email,
            "displayName": None,
            "headline": None,
            "skills": [],
            "location": None,
            "createdAt": now,
            "updatedAt": now
        }

        profile_ref.set(new_profile)
        return ProfileOut(**new_profile)
    except Exception as e:
        print(f"Profile get error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")

@app.put("/me", response_model=ProfileOut)
async def update_profile(
    profile_data: ProfileIn,
    user_data: dict = Depends(verify_firebase_token)
):
    try:
        uid = user_data["uid"]
        email = user_data["email"]

        # Get current profile
        profile_ref = db.collection("profiles").document(uid)
        profile_doc = profile_ref.get()

        if not profile_doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")

        current_profile = profile_doc.to_dict()

        # Prepare update data
        update_data = {}
        if profile_data.displayName is not None:
            update_data["displayName"] = profile_data.displayName.strip()
        if profile_data.headline is not None:
            update_data["headline"] = profile_data.headline.strip()
        if profile_data.skills is not None:
            update_data["skills"] = [skill.strip() for skill in profile_data.skills]
        if profile_data.location is not None:
            update_data["location"] = profile_data.location.strip()

        update_data["updatedAt"] = datetime.utcnow().isoformat() + "Z"

        # Update profile
        profile_ref.set(update_data, merge=True)

        # Get updated profile
        updated_doc = profile_ref.get()
        updated_profile = updated_doc.to_dict()

        return ProfileOut(**updated_profile)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

# Interview Endpoints
@app.post("/interviews", response_model=InterviewOut)
async def create_interview(
    interview_data: InterviewIn,
    user_data: dict = Depends(verify_firebase_token)
):
    try:
        uid = user_data["uid"]
        interview_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        new_interview = {
            "id": interview_id,
            "jobTitle": interview_data.jobTitle,
            "companyName": interview_data.companyName,
            "interviewDate": interview_data.interviewDate,
            "status": interview_data.status,
            "overallScore": None,
            "userId": uid,
            "createdAt": now,
            "updatedAt": now
        }

        if db is None:
            # In offline mode, just return the created interview without saving to Firebase
            print("🔄 Creating interview in offline mode - Firebase not available")
        else:
            # Save to Firebase
            interview_ref = db.collection("interviews").document(interview_id)
            interview_ref.set(new_interview)

        return InterviewOut(**new_interview)
    except Exception as e:
        print(f"Interview creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create interview")

@app.get("/interviews", response_model=List[InterviewOut])
async def get_user_interviews(user_data: dict = Depends(verify_firebase_token)):
    try:
        uid = user_data["uid"]
        
        if db is None:
            # Return mock data when Firebase is not available
            print("🔄 Returning mock interview data - Firebase not available")
            now = datetime.utcnow().isoformat() + "Z"
            mock_interviews = [
                InterviewOut(
                    id="mock-interview-1",
                    jobTitle="Flutter Developer",
                    companyName="Tech Corp",
                    interviewDate=now,
                    status="completed",
                    overallScore=85,
                    userId=uid,
                    createdAt=now,
                    updatedAt=now
                ),
                InterviewOut(
                    id="mock-interview-2", 
                    jobTitle="Senior Frontend Developer",
                    companyName="StartupXYZ",
                    interviewDate=now,
                    status="pending",
                    overallScore=None,
                    userId=uid,
                    createdAt=now,
                    updatedAt=now
                )
            ]
            return mock_interviews
        
        # Get user's interviews from Firebase (simplified query to avoid index requirement)
        interviews_ref = db.collection("interviews").where("userId", "==", uid)
        interviews = interviews_ref.stream()

        interview_list = []
        for interview in interviews:
            interview_data = interview.to_dict()
            interview_list.append(InterviewOut(**interview_data))

        # Sort by interview date in Python instead of Firestore
        interview_list.sort(key=lambda x: x.interviewDate, reverse=True)

        return interview_list
    except Exception as e:
        print(f"Interviews fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch interviews")

@app.get("/interviews/{interview_id}", response_model=InterviewOut)
async def get_interview(
    interview_id: str,
    user_data: dict = Depends(verify_firebase_token)
):
    try:
        uid = user_data["uid"]
        
        # Get specific interview
        interview_ref = db.collection("interviews").document(interview_id)
        interview_doc = interview_ref.get()

        if not interview_doc.exists:
            raise HTTPException(status_code=404, detail="Interview not found")

        interview_data = interview_doc.to_dict()
        
        # Check if user owns this interview
        if interview_data.get("userId") != uid:
            raise HTTPException(status_code=403, detail="Access denied")

        return InterviewOut(**interview_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Interview fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch interview")

# Interview Sessions Endpoints
@app.get("/api/interviews/{user_id}", response_model=List[InterviewSessionOut])
async def get_user_interview_sessions(
    user_id: str,
    user_data: dict = Depends(verify_firebase_token)
):
    """
    Get all interview sessions for a specific user.
    This endpoint is used by the Flutter app's ApiService.
    """
    try:
        # Verify user can access this data
        if user_id != user_data["uid"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if db is None:
            # Return mock interview sessions when Firebase is not available
            print("🔄 Returning mock interview sessions - Firebase not available")
            now = datetime.utcnow().isoformat() + "Z"
            mock_sessions = [
                InterviewSessionOut(
                    id="mock-session-1",
                    userId=user_id,
                    role="Flutter Developer",
                    type="technical",
                    level="mid",
                    questions=[
                        InterviewQuestionModel(
                            question="Explain the difference between StatefulWidget and StatelessWidget",
                            category="Flutter Fundamentals",
                            difficulty="medium"
                        ),
                        InterviewQuestionModel(
                            question="How do you handle state management in Flutter?",
                            category="State Management", 
                            difficulty="medium"
                        )
                    ],
                    createdAt=now
                ),
                InterviewSessionOut(
                    id="mock-session-2",
                    userId=user_id,
                    role="Mobile Developer",
                    type="behavioral",
                    level="senior",
                    questions=[
                        InterviewQuestionModel(
                            question="Tell me about a challenging project you worked on",
                            category="Experience",
                            difficulty="easy"
                        ),
                        InterviewQuestionModel(
                            question="How do you handle tight deadlines?",
                            category="Time Management",
                            difficulty="medium"
                        )
                    ],
                    createdAt=now
                )
            ]
            return mock_sessions
        
        # Get user's interview sessions from Firebase
        sessions_ref = db.collection("interview_sessions").where("userId", "==", user_id)
        sessions = sessions_ref.stream()

        session_list = []
        for session in sessions:
            session_data = session.to_dict()
            session_list.append(InterviewSessionOut(**session_data))

        # Sort by creation date (newest first)
        session_list.sort(key=lambda x: x.createdAt, reverse=True)

        return session_list
    except HTTPException:
        raise
    except Exception as e:
        print(f"Interview sessions fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch interview sessions")

# Feedback Endpoints
@app.post("/interviews/{interview_id}/feedback", response_model=FeedbackOut)
async def create_feedback(
    interview_id: str,
    feedback_data: FeedbackIn,
    user_data: dict = Depends(verify_firebase_token)
):
    try:
        uid = user_data["uid"]
        feedback_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        # Verify interview exists and belongs to user
        interview_ref = db.collection("interviews").document(interview_id)
        interview_doc = interview_ref.get()
        
        if not interview_doc.exists:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        interview_data = interview_doc.to_dict()
        if interview_data.get("userId") != uid:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create feedback
        new_feedback = {
            "id": feedback_id,
            "interviewId": interview_id,
            "userId": uid,
            "overallScore": feedback_data.overallScore,
            "overallImpression": feedback_data.overallImpression,
            "breakdown": [item.dict() for item in feedback_data.breakdown],
            "finalVerdict": feedback_data.finalVerdict,
            "recommendation": feedback_data.recommendation,
            "createdAt": now
        }

        # Save feedback to Firebase
        feedback_ref = db.collection("feedback").document(feedback_id)
        feedback_ref.set(new_feedback)

        # Update interview with overall score and status
        interview_ref.update({
            "overallScore": feedback_data.overallScore,
            "status": "completed",
            "updatedAt": now
        })

        return FeedbackOut(**new_feedback)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Feedback creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create feedback")

@app.get("/interviews/{interview_id}/feedback", response_model=FeedbackOut)
async def get_feedback(
    interview_id: str,
    user_data: dict = Depends(verify_firebase_token)
):
    try:
        uid = user_data["uid"]
        
        # Get feedback for specific interview
        feedback_ref = db.collection("feedback").where("interviewId", "==", interview_id).where("userId", "==", uid)
        feedback_docs = feedback_ref.stream()

        feedback_list = list(feedback_docs)
        if not feedback_list:
            raise HTTPException(status_code=404, detail="Feedback not found")

        feedback_data = feedback_list[0].to_dict()
        return FeedbackOut(**feedback_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Feedback fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch feedback")

# AI Interview Endpoints

@app.post("/interviews/{interview_id}/start-ai", response_model=AIInterviewStartResponse)
async def start_ai_interview(
    interview_id: str,
    request: AIInterviewStartRequest,
    user_data: dict = Depends(verify_firebase_token)
):
    """Start an AI-conducted interview session with Vapi integration"""
    try:
        uid = user_data["uid"]
        
        # Verify interview exists and belongs to user
        interview_ref = db.collection("interviews").document(interview_id)
        interview_doc = interview_ref.get()
        
        if not interview_doc.exists:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        interview_data = interview_doc.to_dict()
        if interview_data.get("userId") != uid:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Generate AI session ID
        ai_session_id = str(uuid.uuid4())
        vapi_call_id = f"vapi_{ai_session_id}"
        
        # Start Vapi interview call
        vapi_response = await vapi_service.start_interview_call(
            interview_data, 
            request.candidatePhoneNumber
        )
        
        # Update interview with AI session info
        now = datetime.utcnow().isoformat()
        interview_ref.update({
            "aiSessionId": ai_session_id,
            "vapiCallId": vapi_response.get("callId", vapi_call_id),
            "status": "inProgress",
            "updatedAt": now
        })
        
        return AIInterviewStartResponse(
            aiSessionId=ai_session_id,
            vapiCallId=vapi_response.get("callId", vapi_call_id),
            status="in_progress",
            message=vapi_response.get("message", "AI interview session started successfully")
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"AI interview start error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start AI interview")

@app.get("/interviews/{interview_id}/ai-status", response_model=AIInterviewStatusResponse)
async def get_ai_interview_status(
    interview_id: str,
    user_data: dict = Depends(verify_firebase_token)
):
    """Get the current status of an AI interview session"""
    try:
        uid = user_data["uid"]
        
        # Get interview data
        interview_ref = db.collection("interviews").document(interview_id)
        interview_doc = interview_ref.get()
        
        if not interview_doc.exists:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        interview_data = interview_doc.to_dict()
        if interview_data.get("userId") != uid:
            raise HTTPException(status_code=403, detail="Access denied")
        
        ai_session_id = interview_data.get("aiSessionId")
        if not ai_session_id:
            raise HTTPException(status_code=404, detail="No AI session found for this interview")
        
        # Check Vapi call status
        vapi_call_id = interview_data.get("vapiCallId")
        if vapi_call_id:
            vapi_status = await vapi_service.get_call_status(vapi_call_id)
            
            return AIInterviewStatusResponse(
                aiSessionId=ai_session_id,
                status=vapi_status.get("status", interview_data.get("status", "pending")),
                duration=vapi_status.get("duration", interview_data.get("interviewDuration")),
                transcriptUrl=vapi_status.get("transcriptUrl", interview_data.get("transcriptUrl")),
                audioRecordingUrl=vapi_status.get("recordingUrl", interview_data.get("audioRecordingUrl"))
            )
        else:
            return AIInterviewStatusResponse(
                aiSessionId=ai_session_id,
                status=interview_data.get("status", "pending"),
                duration=interview_data.get("interviewDuration"),
                transcriptUrl=interview_data.get("transcriptUrl"),
                audioRecordingUrl=interview_data.get("audioRecordingUrl")
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"AI status check error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI interview status")

@app.get("/interviews/{interview_id}/ai-feedback", response_model=AIFeedbackResponse)
async def get_ai_feedback(
    interview_id: str,
    user_data: dict = Depends(verify_firebase_token)
):
    """Get AI-generated feedback for a completed interview"""
    try:
        uid = user_data["uid"]
        
        # Get interview data
        interview_ref = db.collection("interviews").document(interview_id)
        interview_doc = interview_ref.get()
        
        if not interview_doc.exists:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        interview_data = interview_doc.to_dict()
        if interview_data.get("userId") != uid:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if interview is completed
        if interview_data.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Interview not completed yet")
        
        # Get existing feedback or generate new AI feedback
        feedback_ref = db.collection("feedback").where("interviewId", "==", interview_id).where("userId", "==", uid)
        feedback_docs = list(feedback_ref.stream())
        
        if feedback_docs:
            # Return existing AI feedback
            feedback_data = feedback_docs[0].to_dict()
            return AIFeedbackResponse(
                interviewId=interview_id,
                aiAnalysisId=feedback_data.get("aiAnalysisId", ""),
                overallScore=feedback_data.get("overallScore", 0),
                overallImpression=feedback_data.get("overallImpression", ""),
                keyInsights=feedback_data.get("keyInsights", []),
                confidenceScore=feedback_data.get("confidenceScore", 0.0),
                speechAnalysis=feedback_data.get("speechAnalysis", {}),
                transcriptAnalysis=feedback_data.get("transcriptAnalysis", ""),
                emotionalAnalysis=feedback_data.get("emotionalAnalysis", {}),
                recommendation=feedback_data.get("finalVerdict", "")
            )
        else:
            # Generate new AI feedback using Gemini
            ai_analysis_id = str(uuid.uuid4())
            
            # Get interview transcript from Vapi
            vapi_call_id = interview_data.get("vapiCallId")
            if vapi_call_id:
                transcript = await vapi_service.get_call_transcript(vapi_call_id)
            else:
                transcript = "Mock interview transcript for analysis"
            
            # Analyze with Gemini AI
            ai_feedback_data = await gemini_service.analyze_interview_transcript(transcript, interview_data)
            
            # Structure the response
            return AIFeedbackResponse(
                interviewId=interview_id,
                aiAnalysisId=ai_analysis_id,
                overallScore=ai_feedback_data.get("overallScore", 75),
                overallImpression=ai_feedback_data.get("overallImpression", "Analysis completed"),
                keyInsights=ai_feedback_data.get("keyInsights", []),
                confidenceScore=ai_feedback_data.get("confidenceScore", 0.8),
                speechAnalysis=ai_feedback_data.get("speechAnalysis", {}),
                transcriptAnalysis=ai_feedback_data.get("transcriptAnalysis", ""),
                emotionalAnalysis=ai_feedback_data.get("emotionalAnalysis", {}),
                recommendation=ai_feedback_data.get("recommendation", "Review recommended")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"AI feedback error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI feedback")

@app.post("/interviews/{interview_id}/stop-ai")
async def stop_ai_interview(
    interview_id: str,
    user_data: dict = Depends(verify_firebase_token)
):
    """Stop an ongoing AI interview session"""
    try:
        uid = user_data["uid"]
        
        # Get interview data
        interview_ref = db.collection("interviews").document(interview_id)
        interview_doc = interview_ref.get()
        
        if not interview_doc.exists:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        interview_data = interview_doc.to_dict()
        if interview_data.get("userId") != uid:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update interview status
        now = datetime.utcnow().isoformat()
        interview_ref.update({
            "status": "cancelled",
            "updatedAt": now
        })
        
        # TODO: Stop Vapi call
        # await stop_vapi_call(interview_data.get("vapiCallId"))
        
        return {"message": "AI interview stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"AI interview stop error: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop AI interview")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
