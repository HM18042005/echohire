# FastAPI backend with Firebase authentication and profile management
# Updated: 2025-09-24 19:07 - Firebase service account key regenerated for security
# Deployment timestamp: 2025-09-24 19:07:53
from datetime import datetime
from typing import Optional, List, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore, auth
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field, field_validator
import os
import uuid
import asyncio
import json
from dotenv import load_dotenv
import hmac
import hashlib

# Load environment variables from .env file
load_dotenv()

# AI Integration imports
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import httpx
from ai_services import gemini_service, vapi_service
from vapi_workflows import InterviewSetupAssistant

# Helper to stop Vapi call
async def stop_vapi_call(call_id: str) -> bool:
    """Stop a Vapi call via the VapiInterviewService; returns True on success."""
    try:
        return await vapi_service.stop_call(call_id)
    except Exception as e:
        print(f"stop_vapi_call error: {e}")
        return False

# Initialize Firebase Admin SDK
try:
    import json, base64

    # 1) Prefer environment variables in production
    firebase_creds = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON') or os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON_BASE64')
    used_env_name = 'FIREBASE_SERVICE_ACCOUNT_JSON' if os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON') else (
        'FIREBASE_SERVICE_ACCOUNT_JSON_BASE64' if os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON_BASE64') else None
    )
    if firebase_creds:
        raw = firebase_creds.strip()
        try:
            # Try plain JSON first
            service_account_info = json.loads(raw)
            source_hint = f"env:{used_env_name} (json)"
        except json.JSONDecodeError:
            # If not JSON, try base64-decoded JSON
            decoded = base64.b64decode(raw).decode('utf-8')
            service_account_info = json.loads(decoded)
            source_hint = f"env:{used_env_name} (base64)"
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
        key_id = service_account_info.get('private_key_id', '<unknown>')
        email = service_account_info.get('client_email', '<unknown>')
        print(f"✅ Firebase initialized with env credentials [{source_hint}] (key_id={key_id}, client_email={email})")
        db = firestore.client()
    # 2) Allow local file ONLY if explicitly enabled
    elif os.getenv("ALLOW_FIREBASE_FILE", "0") == "1" and os.path.exists("firebase-service-account.json"):
        if not firebase_admin._apps:
            cred = credentials.Certificate("firebase-service-account.json")
            firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized with service account file (ALLOW_FIREBASE_FILE=1)")
        db = firestore.client()
    else:
        print("⚠️ No Firebase env credentials set and local file not allowed. Trying Application Default Credentials...")
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

# Temporary debug endpoint for environment variables (remove in production)
@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variable configuration"""
    import os
    
    vapi_api_key = os.getenv("VAPI_API_KEY")
    vapi_public_key = os.getenv("VAPI_PUBLIC_KEY")
    
    return {
        "vapi_api_key_present": bool(vapi_api_key),
        "vapi_api_key_length": len(vapi_api_key) if vapi_api_key else 0,
        "vapi_api_key_ends_with": vapi_api_key[-8:] if vapi_api_key else None,
        "vapi_public_key_present": bool(vapi_public_key),
        "vapi_public_key_length": len(vapi_public_key) if vapi_public_key else 0,
        "vapi_public_key_ends_with": vapi_public_key[-8:] if vapi_public_key else None,
        "vapi_assistant_id": os.getenv("VAPI_ASSISTANT_ID"),
        "backend_public_url": os.getenv("BACKEND_PUBLIC_URL"),
        "expected_api_key_ending": "9fc458b3",
        "expected_public_key_ending": "c8becf15",
        "keys_correctly_configured": (
            vapi_api_key and vapi_api_key.endswith("9fc458b3") and
            vapi_public_key and vapi_public_key.endswith("c8becf15")
        )
    }

# Environment toggles
AUTO_GENERATE_AI_FEEDBACK = os.getenv("AUTO_GENERATE_AI_FEEDBACK", "0") == "1"
VAPI_WEBHOOK_SECRET = os.getenv("VAPI_WEBHOOK_SECRET", "")

# Interview setup workflow assistant (Gemini-powered)
workflow_assistant = InterviewSetupAssistant(os.getenv("GOOGLE_AI_API_KEY", ""))

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
    webCallUrl: Optional[str] = None

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

# Interview Setup Workflow Endpoints
class WorkflowMessage(BaseModel):
    text: str = Field(..., min_length=1)

class WorkflowFinalizeIn(BaseModel):
    companyName: Optional[str] = None
    interviewDate: Optional[str] = None  # ISO datetime string
    autoStart: bool = True

@app.post("/workflow/start")
async def workflow_start(user_data: dict = Depends(verify_firebase_token)):
    try:
        session_id = str(uuid.uuid4())
        # Kick off with initial greeting by sending empty input
        init = await workflow_assistant.process_user_input(session_id, "")
        return {
            "sessionId": session_id,
            "ai_response": init.get("ai_response"),
            "session_state": init.get("session_state"),
        }
    except Exception as e:
        print(f"Workflow start error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start workflow")

@app.post("/workflow/{session_id}/message")
async def workflow_message(session_id: str, payload: WorkflowMessage, user_data: dict = Depends(verify_firebase_token)):
    try:
        resp = await workflow_assistant.process_user_input(session_id, payload.text)
        return resp
    except Exception as e:
        print(f"Workflow message error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

@app.get("/workflow/{session_id}/summary")
async def workflow_summary(session_id: str, user_data: dict = Depends(verify_firebase_token)):
    try:
        summary = workflow_assistant.get_session_summary(session_id)
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        return summary
    except HTTPException:
        raise
    except Exception as e:
        print(f"Workflow summary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch summary")

@app.post("/workflow/{session_id}/finalize")
async def workflow_finalize(session_id: str, payload: WorkflowFinalizeIn, user_data: dict = Depends(verify_firebase_token)):
    """
    Create an interview from collected preferences and optionally start the Vapi AI assistant.
    Returns the interview record and (if autoStart) the Vapi start response.
    """
    try:
        uid = user_data["uid"]
        summary = workflow_assistant.get_session_summary(session_id)
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])

        prefs = summary.get("preferences", {})
        questions = summary.get("questions", [])

        # Build interview record
        interview_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        interview_doc = {
            "id": interview_id,
            "jobTitle": prefs.get("job_role") or "Interview",
            "companyName": payload.companyName,
            "interviewDate": payload.interviewDate or now,
            "status": "scheduled" if not payload.autoStart else "inProgress",
            "overallScore": None,
            "userId": uid,
            "createdAt": now,
            "updatedAt": now,
            # Extra fields captured by the workflow
            "type": (prefs.get("interview_type") or "").lower(),
            "level": (prefs.get("experience_level") or "").lower(),
            "questions": questions,
        }

        if db is not None:
            db.collection("interviews").document(interview_id).set(interview_doc)

        start_resp = None
        if payload.autoStart:
            # Start Vapi AI interview immediately
            try:
                start_resp = await vapi_service.start_interview_call({
                    **interview_doc,
                    "candidateName": user_data.get("name", "Candidate"),
                })
                # Persist Vapi metadata
                updates = {
                    "aiSessionId": str(uuid.uuid4()),
                    "vapiCallId": start_resp.get("callId"),
                    "webCallUrl": start_resp.get("webCallUrl"),
                    "status": "inProgress",
                    "updatedAt": datetime.utcnow().isoformat() + "Z",
                }
                interview_doc.update(updates)
                if db is not None:
                    db.collection("interviews").document(interview_id).update(updates)
            except Exception as e:
                print(f"Finalize autoStart error: {e}")
                # Keep interview scheduled if start failed
                interview_doc["status"] = "scheduled"
                if db is not None:
                    db.collection("interviews").document(interview_id).update({
                        "status": "scheduled",
                        "updatedAt": datetime.utcnow().isoformat() + "Z",
                    })

        return {
            "interview": interview_doc,
            "start": start_resp,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Workflow finalize error: {e}")
        raise HTTPException(status_code=500, detail="Failed to finalize workflow")

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
    """
    Returns the current user's interviews. If Firestore is unavailable or slow,
    uses a fast mock fallback to avoid client timeouts.
    """
    try:
        uid = user_data["uid"]

        # Optional kill-switch to bypass Firestore (e.g., on misconfigured prod)
        if os.getenv("DISABLE_FIRESTORE", "0") == "1":
            print("⚠️ Firestore disabled by env var; returning mock data")
            return _mock_interviews(uid)

        if db is None:
            print("🔄 Returning mock interview data - Firebase not available")
            return _mock_interviews(uid)

        # Wrap Firestore call in a short timeout to prevent hanging requests
        loop = asyncio.get_running_loop()

        def _fetch_from_firestore_sync(user_id: str) -> List[InterviewOut]:
            # Synchronous Firestore fetch executed in a thread
            interviews_ref = db.collection("interviews").where("userId", "==", user_id)
            interviews = interviews_ref.stream()
            items: List[InterviewOut] = []
            for interview in interviews:
                interview_data = interview.to_dict()
                items.append(InterviewOut(**interview_data))
            # Sort by interview date in Python instead of Firestore
            items.sort(key=lambda x: x.interviewDate, reverse=True)
            return items

        try:
            # If Firestore is slow/unreachable, fall back quickly
            interview_list = await asyncio.wait_for(
                loop.run_in_executor(None, _fetch_from_firestore_sync, uid),
                timeout=8.0,
            )
            return interview_list
        except asyncio.TimeoutError:
            print("⏱️ Firestore fetch timed out; returning mock data")
            return _mock_interviews(uid)
        except Exception as e:
            print(f"Interviews fetch error (Firestore): {e}")
            return _mock_interviews(uid)
    except Exception as e:
        print(f"Interviews fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch interviews")

def _mock_interviews(uid: str) -> List["InterviewOut"]:
    now = datetime.utcnow().isoformat() + "Z"
    return [
        InterviewOut(
            id="mock-interview-1",
            jobTitle="Flutter Developer",
            companyName="Tech Corp",
            interviewDate=now,
            status="completed",
            overallScore=85,
            userId=uid,
            createdAt=now,
            updatedAt=now,
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
            updatedAt=now,
        ),
    ]

@app.get("/health/vapi")
async def health_vapi():
    """Report Vapi configuration status."""
    try:
        return {"configured": getattr(vapi_service, "is_configured", False)}
    except Exception as e:
        return {"configured": False, "error": str(e)}

@app.get("/health/db")
async def health_db():
    """Lightweight Firestore connectivity check with timeout."""
    try:
        if db is None:
            return {"ok": False, "db": "unavailable"}

        loop = asyncio.get_running_loop()

        def _check_sync() -> bool:
            # Minimal check: try to list at most one document from a known collection
            try:
                next(db.collection("interviews").limit(1).stream(), None)
                return True
            except Exception:
                return False

        ok = await asyncio.wait_for(loop.run_in_executor(None, _check_sync), timeout=5.0)
        return {"ok": ok}
    except asyncio.TimeoutError:
        return {"ok": False, "timeout": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

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
        
        # Start Vapi interview call
        vapi_response = await vapi_service.start_interview_call(
            interview_data, 
            request.candidatePhoneNumber
        )
        
        # Check if we got a valid call ID
        call_id = vapi_response.get("callId")
        if not call_id:
            raise HTTPException(status_code=500, detail="Failed to initialize Vapi call - no call ID returned")
        
        # Update interview with AI session info
        now = datetime.utcnow().isoformat()
        interview_ref.update({
            "aiSessionId": ai_session_id,
            "vapiCallId": call_id,
            "webCallUrl": vapi_response.get("webCallUrl"),
            "status": "inProgress",
            "updatedAt": now
        })
        
        return AIInterviewStartResponse(
            aiSessionId=ai_session_id,
            vapiCallId=call_id,
            status="in_progress",
            message=vapi_response.get("message", "AI interview session started successfully"),
            webCallUrl=vapi_response.get("webCallUrl")
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

            # Normalize and persist status/artifacts when available
            status_val = vapi_status.get("status", interview_data.get("status", "pending"))
            duration_val = vapi_status.get("duration", interview_data.get("interviewDuration"))
            transcript_url = vapi_status.get("transcriptUrl", interview_data.get("transcriptUrl"))
            recording_url = vapi_status.get("recordingUrl", interview_data.get("audioRecordingUrl"))

            # Persist completion to Firestore when Vapi indicates the call ended/completed
            try:
                normalized = str(status_val).lower()
                is_completed = (
                    normalized == "completed" or
                    normalized == "ended" or
                    "completed" in normalized or
                    "ended" in normalized
                )
                update_payload = {"updatedAt": datetime.utcnow().isoformat() + "Z"}
                if duration_val is not None:
                    update_payload["interviewDuration"] = duration_val
                if transcript_url:
                    update_payload["transcriptUrl"] = transcript_url
                if recording_url:
                    update_payload["audioRecordingUrl"] = recording_url
                # Only flip to completed once
                if is_completed and interview_data.get("status") != "completed":
                    update_payload["status"] = "completed"
                if len(update_payload) > 1:  # more than just updatedAt
                    interview_ref.update(update_payload)
            except Exception as persist_err:
                print(f"Warning: failed to persist AI status for {interview_id}: {persist_err}")

            return AIInterviewStatusResponse(
                aiSessionId=ai_session_id,
                status=status_val,
                duration=duration_val,
                transcriptUrl=transcript_url,
                audioRecordingUrl=recording_url
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

            # Persist feedback to Firestore
            try:
                now = datetime.utcnow().isoformat() + "Z"
                feedback_doc = {
                    "id": ai_analysis_id,
                    "interviewId": interview_id,
                    "userId": uid,
                    "overallScore": ai_feedback_data.get("overallScore", 75),
                    "overallImpression": ai_feedback_data.get("overallImpression", "Analysis completed"),
                    "keyInsights": ai_feedback_data.get("keyInsights", []),
                    "confidenceScore": ai_feedback_data.get("confidenceScore", 0.8),
                    "speechAnalysis": ai_feedback_data.get("speechAnalysis", {}),
                    "transcriptAnalysis": ai_feedback_data.get("transcriptAnalysis", ""),
                    "emotionalAnalysis": ai_feedback_data.get("emotionalAnalysis", {}),
                    "finalVerdict": ai_feedback_data.get("recommendation", "Review recommended"),
                    "createdAt": now,
                    "aiAnalysisId": ai_analysis_id,
                }
                db.collection("feedback").document(ai_analysis_id).set(feedback_doc)
                # Update interview summary fields
                db.collection("interviews").document(interview_id).update({
                    "overallScore": feedback_doc["overallScore"],
                    "updatedAt": now,
                })
            except Exception as save_err:
                print(f"Warning: failed to save AI feedback: {save_err}")

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
        
        # Attempt to stop Vapi call if present
        vapi_call_id = interview_data.get("vapiCallId")
        if vapi_call_id:
            try:
                await stop_vapi_call(vapi_call_id)
            except Exception as stop_err:
                # Log and continue; stopping the call shouldn't block user flow
                print(f"Warning: Failed to stop Vapi call {vapi_call_id}: {stop_err}")
        
        return {"message": "AI interview stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"AI interview stop error: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop AI interview")

# Webhook endpoint to receive Vapi call events
@app.post("/webhooks/vapi")
async def vapi_webhook(request: Request):
    try:
        raw_body = await request.body()
        try:
            event = json.loads(raw_body.decode("utf-8"))
        except Exception:
            event = await request.json()

        # Optional signature verification if provider sends one
        provided_sig = request.headers.get("X-Signature") or request.headers.get("X-Vapi-Signature")
        if VAPI_WEBHOOK_SECRET and provided_sig:
            try:
                computed = hmac.new(VAPI_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(computed, provided_sig):
                    return {"ok": False, "error": "invalid signature"}
            except Exception as e:
                print(f"Webhook signature verification error: {e}")
                # Continue but mark unverified

        # Extract identifiers
        call_id = event.get("id") or event.get("callId") or event.get("call_id")
        status = (event.get("status") or event.get("state") or "").lower()
        duration = event.get("duration") or event.get("callDuration")
        transcript_url = event.get("transcriptUrl") or event.get("transcript_url")
        recording_url = event.get("recordingUrl") or event.get("recording_url")

        # Determine interview id either from metadata or by lookup
        interview_id = None
        meta = event.get("metadata") or {}
        interview_id = meta.get("interviewId") or meta.get("interview_id")

        interview_ref = None
        interview_data = None
        if db is not None:
            if interview_id:
                interview_ref = db.collection("interviews").document(interview_id)
                snapshot = interview_ref.get()
                if snapshot.exists:
                    interview_data = snapshot.to_dict()
            # If not found via metadata, try to find by vapiCallId
            if interview_data is None and call_id:
                try:
                    candidates = db.collection("interviews").where("vapiCallId", "==", call_id).stream()
                    for doc in candidates:
                        interview_ref = db.collection("interviews").document(doc.id)
                        interview_data = doc.to_dict()
                        interview_id = doc.id
                        break
                except Exception as e:
                    print(f"Vapi webhook lookup error: {e}")

        # Persist updates if we have a document reference
        if interview_ref is not None:
            update_payload = {"updatedAt": datetime.utcnow().isoformat() + "Z"}
            if status:
                # normalize into our domain status
                normalized = "inProgress"
                if "completed" in status or "ended" in status or status == "completed":
                    normalized = "completed"
                elif "failed" in status or status == "failed":
                    normalized = "failed"
                update_payload["status"] = normalized
            if duration is not None:
                update_payload["interviewDuration"] = duration
            if transcript_url:
                update_payload["transcriptUrl"] = transcript_url
            if recording_url:
                update_payload["audioRecordingUrl"] = recording_url
            if call_id and not interview_data.get("vapiCallId"):
                update_payload["vapiCallId"] = call_id
            try:
                interview_ref.update(update_payload)
            except Exception as e:
                print(f"Failed to update interview from webhook: {e}")

            # Optionally auto-generate AI feedback on completion
            try:
                if AUTO_GENERATE_AI_FEEDBACK and update_payload.get("status") == "completed":
                    # Avoid duplicate work if feedback already exists
                    feedback_query = db.collection("feedback").where("interviewId", "==", interview_id).limit(1).stream()
                    if not list(feedback_query):
                        # Fetch transcript (prefer firestore transcriptUrl, else from vapi)
                        transcript_text = None
                        turl = update_payload.get("transcriptUrl") or interview_data.get("transcriptUrl")
                        if turl:
                            try:
                                async with httpx.AsyncClient() as client:
                                    t_resp = await client.get(turl, timeout=20)
                                    if t_resp.status_code == 200:
                                        transcript_text = t_resp.text
                            except Exception:
                                pass
                        if transcript_text is None and call_id:
                            try:
                                transcript_text = await vapi_service.get_call_transcript(call_id)
                            except Exception:
                                transcript_text = ""
                        ai_analysis_id = str(uuid.uuid4())
                        ai_feedback_data = await gemini_service.analyze_interview_transcript(transcript_text or "", interview_data or {})
                        now = datetime.utcnow().isoformat() + "Z"
                        feedback_doc = {
                            "id": ai_analysis_id,
                            "interviewId": interview_id,
                            "userId": interview_data.get("userId") if interview_data else "",
                            "overallScore": ai_feedback_data.get("overallScore", 75),
                            "overallImpression": ai_feedback_data.get("overallImpression", "Analysis completed"),
                            "keyInsights": ai_feedback_data.get("keyInsights", []),
                            "confidenceScore": ai_feedback_data.get("confidenceScore", 0.8),
                            "speechAnalysis": ai_feedback_data.get("speechAnalysis", {}),
                            "transcriptAnalysis": ai_feedback_data.get("transcriptAnalysis", ""),
                            "emotionalAnalysis": ai_feedback_data.get("emotionalAnalysis", {}),
                            "finalVerdict": ai_feedback_data.get("recommendation", "Review recommended"),
                            "createdAt": now,
                            "aiAnalysisId": ai_analysis_id,
                        }
                        db.collection("feedback").document(ai_analysis_id).set(feedback_doc)
                        db.collection("interviews").document(interview_id).update({
                            "overallScore": feedback_doc["overallScore"],
                            "updatedAt": now,
                        })
            except Exception as e:
                print(f"Auto feedback generation failed: {e}")

        return {"ok": True}
    except Exception as e:
        print(f"Webhook processing error: {e}")
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    import os
    # Use PORT environment variable for Render deployment, fallback to 8000 for local dev
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
