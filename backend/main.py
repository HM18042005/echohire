# FastAPI backend with Firebase authentication and profile management
# Updated: 2025-09-24 19:07 - Firebase service account key regenerated for security
# Deployment timestamp: 2025-09-24 19:07:53
from datetime import datetime
from typing import Optional, List, Dict, Any
from typing import Optional, List, Dict, Any, Tuple
import firebase_admin
from firebase_admin import credentials, firestore, auth
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import HTMLResponse, JSONResponse
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

# AI Integration imports (optional)
# Do not hard-require google.generativeai here; ai_services handles fallbacks.
import httpx
from ai_services import gemini_service, vapi_service, UNIVERSAL_WORKFLOW_ID
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

# Initialize Google Gemini AI (best-effort; safe if package/env missing)
try:
    import google.generativeai as genai  # type: ignore
    api_key = os.getenv("GOOGLE_AI_API_KEY", "")
    if api_key:
        genai.configure(api_key=api_key)
        print("✅ Google Generative AI SDK configured")
    else:
        print("⚠️ GOOGLE_AI_API_KEY not set; skipping Generative AI SDK configuration")
except Exception as e:
    print(f"⚠️ google.generativeai not available or failed to configure: {e}")

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

# Consolidated AI/Vapi diagnostics (safe to expose in non-prod only)
@app.get("/debug/ai")
async def debug_ai():
    try:
        from ai_services import gemini_service, vapi_service  # local import to avoid circulars in some setups
    except Exception as e:
        return {
            "error": f"failed to import ai_services: {type(e).__name__}: {e}"
        }

    def last8(s: str | None) -> str | None:
        return s[-8:] if s else None

    # Gemini status
    gemini_key = os.getenv("GOOGLE_AI_API_KEY")
    gemini_status = {
        "env_key_present": bool(gemini_key),
        "env_key_len": len(gemini_key) if gemini_key else 0,
        "env_key_ends_with": last8(gemini_key),
        "service_is_configured": bool(getattr(gemini_service, "is_configured", False)),
        "model_ready": bool(getattr(gemini_service, "model", None) is not None),
    }

    # Vapi status
    vapi_api_key = os.getenv("VAPI_API_KEY")
    vapi_public_key = os.getenv("VAPI_PUBLIC_KEY")
    vapi_status = {
        "is_configured": bool(getattr(vapi_service, "is_configured", False)),
        "base_url": getattr(vapi_service, "base_url", None),
        "assistant_id": getattr(vapi_service, "vapi_assistant_id", None),
        "api_key_present": bool(vapi_api_key),
        "api_key_len": len(vapi_api_key) if vapi_api_key else 0,
        "api_key_ends_with": last8(vapi_api_key),
        "public_key_present": bool(vapi_public_key),
        "public_key_len": len(vapi_public_key) if vapi_public_key else 0,
        "public_key_ends_with": last8(vapi_public_key),
        "backend_public_url": os.getenv("BACKEND_PUBLIC_URL"),
    }

    return {
        "gemini": gemini_status,
        "vapi": vapi_status,
        "notes": [
            "Only use this endpoint in development; it reveals configuration presence and lengths but not full secrets.",
            "For web calls, expect start to return ready_for_client_init; client must post real callId back to backend.",
        ],
    }

# Environment toggles
AUTO_GENERATE_AI_FEEDBACK = os.getenv("AUTO_GENERATE_AI_FEEDBACK", "0") == "1"
VAPI_WEBHOOK_SECRET = os.getenv("VAPI_WEBHOOK_SECRET", "")

# Interview setup workflow assistant (Gemini-powered)
workflow_assistant = InterviewSetupAssistant(os.getenv("GOOGLE_AI_API_KEY", ""))

AI_FEEDBACK_SOURCES = {"ai_auto", "ai_on_demand", "legacy_ai"}
MANUAL_FEEDBACK_SOURCE = "manual"


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _map_ai_recommendation(analysis: Dict[str, Any]) -> Tuple[str, str]:
    raw = str(analysis.get("hiringRecommendation", "")).strip().lower()
    narrative = analysis.get("recommendation")
    mapping = {
        "hire": ("recommended", "Strong Hire - Recommended for immediate offer"),
        "strong_hire": ("recommended", "Strong Hire - Recommended for immediate offer"),
        "conditional_hire": ("conditionallyRecommended", "Conditional Hire - Recommend additional assessment"),
        "no_hire": ("notRecommended", "No Hire - Does not meet current requirements"),
        "reject": ("notRecommended", "No Hire - Does not meet current requirements"),
    }
    final_verdict, fallback = mapping.get(raw, ("conditionallyRecommended", "Review Recommended - Additional evaluation suggested"))
    if not narrative or not str(narrative).strip():
        narrative = fallback
    return final_verdict, str(narrative)


def _build_ai_feedback_payload(
    interview_id: str,
    user_id: str,
    analysis: Dict[str, Any],
    transcript_text: str,
    source: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    ai_analysis_id = str(uuid.uuid4())
    timestamp = _now_iso()
    final_verdict, recommendation_text = _map_ai_recommendation(analysis)

    technical_assessment = analysis.get("technicalAssessment", {})
    communication_assessment = analysis.get("communicationAssessment", {})
    problem_solving_assessment = analysis.get("problemSolvingAssessment", {})
    role_specific_assessment = analysis.get("roleSpecificAssessment", {})
    interview_quality = analysis.get("interviewQuality", {})

    feedback_doc = {
        "id": ai_analysis_id,
        "aiAnalysisId": ai_analysis_id,
        "interviewId": interview_id,
        "userId": user_id,
        "source": source,
        "overallScore": analysis.get("overallScore", 75),
        "overallImpression": analysis.get("overallImpression", "Analysis completed"),
        "keyInsights": analysis.get("keyInsights", []),
        "confidenceScore": analysis.get("confidenceScore", 0.75),
        "speechAnalysis": analysis.get("speechAnalysis", {}),
        "transcriptAnalysis": analysis.get("transcriptAnalysis", ""),
        "emotionalAnalysis": analysis.get("emotionalAnalysis", {}),
        "finalVerdict": final_verdict,
        "recommendation": recommendation_text,
        "technicalAssessment": technical_assessment,
        "communicationAssessment": communication_assessment,
        "problemSolvingAssessment": problem_solving_assessment,
        "roleSpecificAssessment": role_specific_assessment,
        "interviewQuality": interview_quality,
        "recommendedAreas": analysis.get("recommendedAreas", []),
        "nextSteps": analysis.get("nextSteps", "Further evaluation recommended"),
        "transcriptPreview": transcript_text[:5000] if transcript_text else None,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }

    response_payload = {
        "interviewId": interview_id,
        "aiAnalysisId": ai_analysis_id,
        "overallScore": feedback_doc["overallScore"],
        "overallImpression": feedback_doc["overallImpression"],
        "keyInsights": feedback_doc["keyInsights"],
        "confidenceScore": feedback_doc["confidenceScore"],
        "speechAnalysis": feedback_doc["speechAnalysis"],
        "transcriptAnalysis": feedback_doc["transcriptAnalysis"],
        "emotionalAnalysis": feedback_doc["emotionalAnalysis"],
        "recommendation": recommendation_text,
        "technicalAssessment": technical_assessment,
        "communicationAssessment": communication_assessment,
        "problemSolvingAssessment": problem_solving_assessment,
        "roleSpecificAssessment": role_specific_assessment,
        "interviewQuality": interview_quality,
        "recommendedAreas": feedback_doc["recommendedAreas"],
        "nextSteps": feedback_doc["nextSteps"],
        "source": source,
    }

    return feedback_doc, response_payload


def _select_latest_ai_feedback(docs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for data in docs:
        source = data.get("source")
        if source in AI_FEEDBACK_SOURCES or (not source and data.get("aiAnalysisId")):
            if not source:
                data["source"] = "legacy_ai"
            candidates.append(data)
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.get("createdAt", ""), reverse=True)
    return candidates[0]


def _feedback_doc_to_response(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "interviewId": data.get("interviewId"),
        "aiAnalysisId": data.get("aiAnalysisId") or data.get("id"),
        "overallScore": data.get("overallScore", 75),
        "overallImpression": data.get("overallImpression", "Analysis completed"),
        "keyInsights": data.get("keyInsights", []),
        "confidenceScore": data.get("confidenceScore", 0.75),
        "speechAnalysis": data.get("speechAnalysis", {}),
        "transcriptAnalysis": data.get("transcriptAnalysis", data.get("transcriptPreview", "")),
        "emotionalAnalysis": data.get("emotionalAnalysis", {}),
        "recommendation": data.get("recommendation", "Review Recommended"),
        "technicalAssessment": data.get("technicalAssessment", {}),
        "communicationAssessment": data.get("communicationAssessment", {}),
        "problemSolvingAssessment": data.get("problemSolvingAssessment", {}),
        "roleSpecificAssessment": data.get("roleSpecificAssessment", {}),
        "interviewQuality": data.get("interviewQuality", {}),
        "recommendedAreas": data.get("recommendedAreas", []),
        "nextSteps": data.get("nextSteps", "Further evaluation recommended"),
        "source": data.get("source"),
    }


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
    id: Optional[str] = None
    interviewId: str
    userId: str
    overallScore: int
    overallImpression: str
    breakdown: List[EvaluationCriteriaModel]
    finalVerdict: str
    recommendation: str
    createdAt: str
    updatedAt: Optional[str] = None
    source: Optional[str] = None

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
    # Optional fields for client-side web call initialization
    assistantId: Optional[str] = None
    publicKey: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AIInterviewStatusResponse(BaseModel):
    aiSessionId: str
    status: str  # "pending", "in_progress", "completed", "failed", "ready_for_client_init"
    duration: Optional[int] = None
    transcriptUrl: Optional[str] = None
    audioRecordingUrl: Optional[str] = None
    # Optional fields for client-side init during status phase
    assistantId: Optional[str] = None
    publicKey: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class UpdateVapiCallIdRequest(BaseModel):
    callId: str
    assistantId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

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
    # Enhanced fields from improved analysis
    technicalAssessment: Optional[Dict[str, Any]] = None
    communicationAssessment: Optional[Dict[str, Any]] = None
    problemSolvingAssessment: Optional[Dict[str, Any]] = None
    roleSpecificAssessment: Optional[Dict[str, Any]] = None
    interviewQuality: Optional[Dict[str, Any]] = None
    recommendedAreas: Optional[List[str]] = None
    nextSteps: Optional[str] = None
    source: Optional[str] = None

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

# Client-facing Vapi WebView page to enable a proper HTTPS origin in WebView
@app.get("/client/vapi-web", response_class=HTMLResponse)
async def vapi_web_page(publicKey: str, assistantId: str, metadata: str = "{}", interviewId: Optional[str] = None):
        """Serve a minimal Vapi Web SDK page over HTTPS to avoid null-origin/CORS issues in Android WebView.

        Query params expected on the URL:
        - publicKey: Vapi public key
        - assistantId: Vapi assistant ID to start the call
        - metadata: URL-encoded JSON string (optional)
        - interviewId: optional (for logging only)
        """
        # Basic guardrails (no secrets here beyond public key)
        try:
                _ = json.loads(metadata) if metadata else {}
        except Exception:
                metadata = "{}"

        html = """<!DOCTYPE html>
<html>
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>EchoHire • AI Interview</title>
        <style>
            html, body { margin:0; padding:0; height:100%; background:#0b1021; color:#fff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,Cantarell,'Open Sans','Helvetica Neue',sans-serif; transition: background-color 0.3s ease; }
            #app { display:flex; align-items:center; justify-content:center; height:100%; flex-direction:column; gap:20px; text-align:center; padding:20px; }
            .badge { padding:8px 14px; border-radius:999px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); }
            button { padding:12px 22px; background:#3b82f6; color:#fff; border:none; border-radius:12px; font-size:16px; cursor:pointer; }
            .status-indicator { position: fixed; top: 20px; right: 20px; padding: 10px 15px; border-radius: 8px; background: rgba(0,0,0,0.8); color: white; font-size: 14px; z-index: 1000; }
            .audio-level { position: fixed; top: 20px; left: 20px; width: 100px; height: 20px; background: rgba(0,0,0,0.3); border-radius: 10px; overflow: hidden; }
            .audio-level-bar { height: 100%; background: #4ade80; width: 0%; transition: width 0.1s ease; }
            button:disabled { background:#666; }
            .hidden { display:none; }
        </style>
    </head>
    <body>
        <div class="audio-level">
            <div class="audio-level-bar" id="audioBar"></div>
        </div>
        <div class="status-indicator" id="statusIndicator">Initializing...</div>
        
        <div id=\"app\">
            <div style=\"font-size:18px; opacity:.9\">🎤 EchoHire • AI Interview</div>
            <div id=\"status\" class=\"badge\">Preparing interview…</div>
            <button id=\"endBtn\" class=\"hidden\" disabled>End Interview</button>
            <div style="margin-top: 20px; font-size: 14px; opacity: 0.7; max-width: 400px;">
                💡 Make sure your microphone is enabled. You'll see visual cues when the AI is listening or speaking.
            </div>
            <div style="margin-top: 10px; font-size: 12px; opacity: 0.5; max-width: 400px;">
                🔧 Troubleshooting: If you can't hear audio, check device volume and ensure no other apps are using the microphone.
            </div>
        </div>
        <script>
            (async function() {
                const statusEl = document.getElementById('status');
                const endBtn = document.getElementById('endBtn');
                const statusIndicator = document.getElementById('statusIndicator');
                const audioBar = document.getElementById('audioBar');
                
                function updateStatus(msg, showBtn=false) {
                    statusEl.textContent = msg;
                    statusIndicator.textContent = msg;
                    if (showBtn) { endBtn.style.display='inline-block'; endBtn.disabled=false; }
                    try { if (typeof statusUpdate !== 'undefined' && statusUpdate.postMessage) statusUpdate.postMessage(msg); } catch(_){}
                }
                
                function updateAudioLevel(level) {
                    const percentage = Math.min(100, Math.max(0, level * 100));
                    audioBar.style.width = percentage + '%';
                }
                
                // Check microphone permissions
                async function checkMicrophonePermission() {
                    try {
                        updateStatus('🎤 Checking microphone access...');
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        stream.getTracks().forEach(track => track.stop()); // Clean up
                        updateStatus('✅ Microphone access granted');
                        return true;
                    } catch (error) {
                        updateStatus('❌ Microphone access required. Please enable microphone permissions.');
                        return false;
                    }
                }

                // Global error hooks
                window.onerror = function(message, source, lineno, colno, error) {
                    try {
                        const payload = { type:'window.onerror', message, source, lineno, colno, error: error && { name:error.name, message:error.message, stack:error.stack } };
                        if (typeof statusUpdate !== 'undefined' && statusUpdate.postMessage) statusUpdate.postMessage('[VapiWebView] GlobalError: ' + JSON.stringify(payload));
                    } catch(_){}
                };
                window.addEventListener('unhandledrejection', function(ev) {
                    try {
                        const r = ev && (ev.reason || ev.detail || ev.message || ev);
                        if (typeof statusUpdate !== 'undefined' && statusUpdate.postMessage) statusUpdate.postMessage('[VapiWebView] UnhandledRejection: ' + (typeof r === 'object' ? JSON.stringify(r) : String(r)));
                    } catch(_){}
                });

                try {
                    // Check microphone permission first
                    const hasMicAccess = await checkMicrophonePermission();
                    if (!hasMicAccess) {
                        updateStatus('🚫 Cannot start interview without microphone access');
                        return;
                    }
                    
                    const qs = new URLSearchParams(window.location.search);
                    const publicKey = qs.get('publicKey') || '';
                    const assistantId = qs.get('assistantId') || '';
                    const interviewId = qs.get('interviewId') || '';
                    let metadata = {};
                    try { metadata = JSON.parse(decodeURIComponent(qs.get('metadata') || '%7B%7D')); } catch(_e) { metadata = {}; }
                    let client = null;

                    updateStatus('UA: ' + navigator.userAgent);
                    updateStatus('Loading Vapi SDK (ESM)…');

                    // ESM-first loader to avoid UMD/CommonJS issues
                    let Mod = null;
                    const esmCandidates = [
                        'https://esm.sh/@vapi-ai/web@latest?bundle',
                        'https://esm.sh/@vapi-ai/web@latest',
                        'https://cdn.jsdelivr.net/npm/@vapi-ai/web@latest/+esm',
                        'https://unpkg.com/@vapi-ai/web@latest?module'
                    ];
                    for (let i=0; !Mod && i<esmCandidates.length; i++) {
                        const url = esmCandidates[i];
                        try { updateStatus('Importing ESM from: ' + url); Mod = await import(url); } catch(e) { /* try next */ }
                    }
                                if (!Mod) throw new Error('Failed to import Vapi ESM');
                                try {
                                    const keys = Object.keys(Mod || {});
                                    updateStatus('Vapi ESM loaded. typeof(Mod)=' + (typeof Mod) + ', keys=' + (keys.length ? keys.join(',') : '<none>'));
                                } catch(_) {}

                                // Robust constructor detection across ESM variants
                                let VapiCtor = null;
                                
                                // Try each possible location for the constructor
                                const constructorCandidates = [
                                    function() { return Mod; },                           // module itself is the ctor
                                    function() { return Mod && Mod.default; },            // default export is ctor
                                    function() { return Mod && Mod.default && Mod.default.default; }, // double-default pattern
                                    function() { return Mod && Mod.default && Mod.default.Vapi; },  // nested under default
                                    function() { return Mod && Mod.Vapi; },               // named export Vapi
                                    function() { return Mod && Mod.WebVapi; },            // try another plausible name
                                    function() { return Mod && Mod.Client; },             // maybe called Client
                                    function() { return Mod && Mod.default && Mod.default.Client; }, // Client under default
                                ];
                                
                                for (let i = 0; i < constructorCandidates.length && !VapiCtor; i++) {
                                    try {
                                        const candidate = constructorCandidates[i]();
                                        if (typeof candidate === 'function') {
                                            updateStatus('Found constructor via candidate ' + i + ' (' + (candidate.name || 'anonymous') + ')');
                                            VapiCtor = candidate;
                                            break;
                                        }
                                    } catch (e) {
                                        // Ignore and try next candidate
                                    }
                                }
                                
                                // If still not found, try to look for anything that might be a class constructor
                                if (!VapiCtor && Mod) {
                                    try {
                                        const allKeys = [...Object.keys(Mod), ...(Mod.default ? Object.keys(Mod.default) : [])];
                                        updateStatus('Examining all available keys: ' + allKeys.join(', '));
                                        
                                        // First try default export itself as constructor
                                        if (Mod.default && typeof Mod.default === 'function') {
                                            updateStatus('Testing default export as constructor');
                                            try {
                                                const testInstance = new Mod.default(publicKey);
                                                if (testInstance) {
                                                    updateStatus('Default export IS the constructor!');
                                                    VapiCtor = Mod.default;
                                                }
                                            } catch (e) {
                                                updateStatus('Default export not a valid constructor: ' + e.message);
                                            }
                                        }
                                        
                                        // If default didn't work, try other keys
                                        if (!VapiCtor) {
                                            for (const key of allKeys) {
                                                const val = Mod[key] || (Mod.default && Mod.default[key]);
                                                if (typeof val === 'function' && (/Vapi|Client/i.test(key) || val.prototype)) {
                                                    updateStatus('Found potential constructor: ' + key);
                                                    VapiCtor = val;
                                                    break;
                                                }
                                            }
                                        }
                                    } catch (e) {
                                        updateStatus('Error examining keys: ' + e.message);
                                    }
                                }
                                            // If no constructor found, try factory patterns from ESM first
                            if (typeof VapiCtor !== 'function') {
                                updateStatus('No constructor found, trying ESM factory patterns...');
                                
                                // Try common factory function names
                                const factoryCandidates = [
                                    () => Mod && Mod.createClient,
                                    () => Mod && Mod.default && Mod.default.createClient,
                                    () => Mod && Mod.create,
                                    () => Mod && Mod.default && Mod.default.create,
                                    () => Mod && Mod.Vapi && Mod.Vapi.createClient,
                                    () => Mod && Mod.default && Mod.default.Vapi && Mod.default.Vapi.createClient,
                                ];
                                
                                let factory = null;
                                for (let i = 0; i < factoryCandidates.length && !factory; i++) {
                                    try {
                                        const candidate = factoryCandidates[i]();
                                        if (typeof candidate === 'function') {
                                            updateStatus('Found ESM factory via candidate ' + i);
                                            factory = candidate;
                                            break;
                                        }
                                    } catch (e) {
                                        // Ignore and try next
                                    }
                                }
                                
                                if (factory) {
                                    try {
                                        updateStatus('Trying ESM factory with publicKey...');
                                        client = factory({ publicKey });
                                        if (client) {
                                            updateStatus('ESM factory success! ✓');
                                        }
                                    } catch (e) {
                                        updateStatus('ESM factory failed: ' + e.message);
                                    }
                                }
                            }
                            
                            if (!client && typeof VapiCtor !== 'function') {
                                const shape = (function() { try { return JSON.stringify(Mod); } catch(_) { return String(Mod); } })();
                                updateStatus('ESM lacked constructor. typeof(Mod)='+ (typeof Mod) + ' shape=' + shape + ' → Trying UMD dist fallback…');
                                
                                // Set up exports object to avoid "exports is not defined" error
                                if (typeof window.exports === 'undefined') {
                                    window.exports = {};
                                }
                                
                                // UMD fallback: try to load a working UMD build synchronously
                                const loadScriptSync = function(src) {
                                    return new Promise(function(resolve, reject) { 
                                        const s = document.createElement('script'); 
                                        s.src = src; 
                                        s.async = true; 
                                        s.crossOrigin = 'anonymous'; 
                                        s.onload = function() { resolve(); };
                                        s.onerror = function(e) { reject(e); };
                                        document.head.appendChild(s); 
                                    });
                                };
                                
                                const umdCandidates = [
                                    'https://cdn.jsdelivr.net/npm/@vapi-ai/web@latest/dist/vapi.js',
                                    'https://fastly.jsdelivr.net/npm/@vapi-ai/web@latest/dist/vapi.js',
                                    'https://unpkg.com/@vapi-ai/web@latest/dist/vapi.js',
                                ];
                                
                                // Load UMD scripts sequentially
                                let umdLoadPromise = Promise.resolve();
                                if (!window.__vapiUmdLoading) {
                                    window.__vapiUmdLoading = true;
                                    for (let i = 0; i < umdCandidates.length && !window.Vapi && !window.vapi && i < 1; i++) {
                                        const url = umdCandidates[i];
                                        umdLoadPromise = umdLoadPromise.then(function() {
                                            // Clear any previous failed attempts
                                            const existingScripts = document.querySelectorAll('script[src*="@vapi-ai/web"]');
                                            existingScripts.forEach(function(script) {
                                                if (script.src !== url) script.remove();
                                            });
                                            
                                            updateStatus('Loading UMD from: ' + url); 
                                            return loadScriptSync(url);
                                        }).catch(function(e) { 
                                            updateStatus('UMD failed: ' + e.message);
                                        });
                                    }
                                    umdLoadPromise.finally(function() {
                                        window.__vapiUmdLoading = false;
                                    });
                                }
                                await umdLoadPromise;
                                                            // Try common UMD globals
                                                            if (window.Vapi) {
                                                                updateStatus('Found window.Vapi after UMD');
                                                                VapiCtor = (typeof window.Vapi === 'function') ? window.Vapi : (window.Vapi.default || window.Vapi.Vapi);
                                                            } else if (window.vapi) {
                                                                updateStatus('Found window.vapi after UMD');
                                                                const gv = window.vapi;
                                                                VapiCtor = (typeof gv === 'function') ? gv : (gv.default || gv.Vapi);
                                                            }
                                                            // Factory fallback from globals
                                                            if (typeof VapiCtor !== 'function') {
                                                                const tryFactories = [
                                                                    (window.Vapi && window.Vapi.createClient),
                                                                    (window.Vapi && window.Vapi.default && window.Vapi.default.createClient),
                                                                    (window.vapi && window.vapi.createClient),
                                                                    (window.vapi && window.vapi.default && window.vapi.default.createClient),
                                                                ].filter(Boolean);
                                                                let factory = null;
                                                                if (tryFactories.length) {
                                                                    factory = tryFactories[0];
                                                                    updateStatus('Using global factory createClient(..)');
                                                                    try { client = factory({ publicKey }); } catch(_) {}
                                                                }
                                                                if (!client) {
                                                                    // Last resort: scan window for any object exposing createClient
                                                                    try {
                                                                        const names = Object.getOwnPropertyNames(window).slice(0, 5000);
                                                                        let found = null;
                                                                        for (const key of names) {
                                                                            const val = window[key];
                                                                            if (val && typeof val.createClient === 'function') { found = val.createClient; break; }
                                                                            if (val && val.default && typeof val.default.createClient === 'function') { found = val.default.createClient; break; }
                                                                            if (!found && typeof val === 'function' && /Vapi/i.test(key)) { VapiCtor = val; }
                                                                        }
                                                                        if (found && !client) {
                                                                            updateStatus('Found createClient on window.' + (names.find(k => window[k] && (window[k].createClient || (window[k].default && window[k].default.createClient))) || 'unknown'));
                                                                            try { client = found({ publicKey }); } catch(_) {}
                                                                        }
                                                                    } catch(_) {}
                                                                }
                                                                if (!client && typeof VapiCtor !== 'function') {
                                                                    throw new Error('Vapi constructor not found after UMD fallback');
                                                                }
                                                            }
                                            }

                                // Only create client if we haven't already done so via factory
                                if (!client) {
                                    updateStatus('Creating Vapi client…');
                                    try {
                                        client = new VapiCtor(publicKey);
                                    } catch (e1) {
                                        try { 
                                            client = new VapiCtor({ publicKey }); 
                                        } catch (e2) {
                                            // Some builds may expose constructor under a property as well (rare)
                                            try {
                                                const alt = (VapiCtor && VapiCtor.default) || (VapiCtor && VapiCtor.Vapi);
                                                if (typeof alt === 'function') {
                                                    try { client = new alt(publicKey); } catch(_) { client = new alt({ publicKey }); }
                                                }
                                            } catch(_) {}
                                        }
                                        // Factory fallback: some builds might expose a createClient function
                                        if (!client) {
                                            try {
                                                const factory = (Mod && Mod.createClient) || (Mod && Mod.default && Mod.default.createClient);
                                                if (typeof factory === 'function') {
                                                    updateStatus('Using factory createClient(..)');
                                                    client = factory({ publicKey });
                                                }
                                            } catch(_) {}
                                        }
                                        if (!client) {
                                            updateStatus('Fatal: Cannot create Vapi client - no constructor or factory worked');
                                            throw new Error('Unable to create Vapi client after trying all methods');
                                        }
                                    }
                                }
                                try { if (client) updateStatus('Vapi client created ✓'); } catch(_) {}

                    const logError = function(label, e) {
                        try {
                            const msg = (e && e.message) ? e.message : (typeof e === 'object' ? JSON.stringify(e) : String(e));
                            updateStatus(label + ': ' + msg, true);
                            if (typeof statusUpdate !== 'undefined' && statusUpdate.postMessage) {
                                const details = { label, name: e && e.name, message: e && e.message, stack: e && e.stack, code: e && (e.code || e.error || e.type) };
                                statusUpdate.postMessage('[VapiWebView] Error: ' + JSON.stringify(details));
                            }
                        } catch(_e){}
                    };
                    client.on('error', function(e) { logError('Error', e); });
                    try { client.on('call-failed', function(e) { logError('Call failed', e); }); } catch(_e){}
                    try { client.on('daily-error', function(e) { logError('Daily error', e); }); } catch(_e){}

                    // CallId discovery
                    const tryExtractId = function(obj) {
                        if (!obj) return null; const keys=['id','callId','call_id','uuid','roomId','roomName'];
                        for (const k of keys) { if (obj && typeof obj[k]==='string' && obj[k]) return obj[k]; }
                        if (obj.call) { for (const k of keys) { if (obj.call && typeof obj.call[k]==='string' && obj.call[k]) return obj.call[k]; } }
                        if (obj.data) { for (const k of keys) { if (obj.data && typeof obj.data[k]==='string' && obj.data[k]) return obj.data[k]; } }
                        return null;
                    };
                    let sentCallId=false; const maybeSendCallId = function(src,payload) {
                        if (sentCallId) return; const cid = tryExtractId(payload) || tryExtractId(client) || tryExtractId((client && client.call)||null);
                        if (cid && typeof vapiCallId !== 'undefined' && vapiCallId.postMessage) {
                            try { vapiCallId.postMessage(JSON.stringify({ callId: cid, assistantId, metadata })); sentCallId=true; updateStatus('Call ID captured from '+src+': '+cid, true); } catch(_e){}
                        }
                    };

                    // Debug: Test audio capabilities
                    try {
                        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        updateStatus('🔊 Audio context state: ' + audioContext.state);
                        if (audioContext.state === 'suspended') {
                            await audioContext.resume();
                            updateStatus('🔊 Audio context resumed');
                        }
                    } catch (e) {
                        updateStatus('⚠️ Audio context issue: ' + e.message);
                    }

                    updateStatus('Starting interview…');
                    let call=null; try { call = await client.start(assistantId); } catch(e) { logError('Start failed', e); throw e; }
                    try { updateStatus('Start returned: ' + JSON.stringify(call)); } catch(_e){}
                    const immediateId = tryExtractId(call);
                    updateStatus('Interview started (ID: ' + (immediateId || 'unknown') + ')', true);
                    maybeSendCallId('start()', call);

                    // Enhanced event handling with audio feedback
                    client.on('call-start', function(evt) { 
                        updateStatus('🎤 Interview Started - You can speak now!', true); 
                        document.body.style.backgroundColor = '#e8f5e8';
                        try { updateStatus('call-start evt: ' + JSON.stringify(evt)); } catch(_e){} 
                        maybeSendCallId('call-start', evt); 
                    });
                    
                    client.on('speech-start', function() { 
                        updateStatus('🎙️ Listening... (I can hear you speaking)', true); 
                        document.body.style.backgroundColor = '#fff3cd';
                    });
                    
                    client.on('speech-end', function() { 
                        updateStatus('⏳ Processing your response...', true); 
                        document.body.style.backgroundColor = '#d1ecf1';
                    });
                    
                    client.on('assistant-speaking-started', function() { 
                        updateStatus('🤖 AI is speaking - Listen carefully!', true); 
                        document.body.style.backgroundColor = '#f8d7da';
                    });
                    
                    client.on('assistant-speaking-ended', function() { 
                        updateStatus('✅ Your turn to speak!', true); 
                        document.body.style.backgroundColor = '#e8f5e8';
                    });
                    
                    client.on('call-end', function() { 
                        updateStatus('✅ Interview completed successfully!'); 
                        document.body.style.backgroundColor = '#d4edda';
                        if (typeof callEnded !== 'undefined' && callEnded.postMessage) callEnded.postMessage('done'); 
                    });
                    
                    // Audio and microphone status events
                    client.on('volume-level', function(level) {
                        updateAudioLevel(level);
                        if (level > 0.1) {
                            statusIndicator.textContent = '🔊 Speaking... (' + Math.round(level * 100) + '%)';
                        }
                    });
                    
                    client.on('error', function(e) { 
                        logError('Error', e); 
                        document.body.style.backgroundColor = '#f8d7da';
                    });

                    endBtn.onclick = function() {
                        endBtn.disabled = true; 
                        updateStatus('Ending…'); 
                        client.stop().then(function() {
                            updateStatus('Call stopped, completing interview...'); 
                            // Wait for Vapi's system to mark the call as ended
                            setTimeout(function() {
                                updateStatus('Interview completed.'); 
                                if (typeof callEnded !== 'undefined' && callEnded.postMessage) {
                                    callEnded.postMessage('ended');
                                }
                            }, 3000); // Wait 3 seconds for Vapi to update call status
                        }).catch(function(e) { 
                            logError('Failed to end', e); 
                            updateStatus('Error stopping call, completing anyway...'); 
                            // Still complete the interview even if there was an error
                            setTimeout(function() {
                                if (typeof callEnded !== 'undefined' && callEnded.postMessage) {
                                    callEnded.postMessage('ended');
                                }
                            }, 1000);
                            endBtn.disabled = false; 
                        });
                    };
                } catch(e) { updateStatus('Fatal: ' + (e && e.message ? e.message : e), true); }
            })();
        </script>
    </body>
</html>"""
        return HTMLResponse(content=html, media_type="text/html; charset=utf-8")

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
        now = _now_iso()
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
                    "updatedAt": _now_iso(),
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
                        "updatedAt": _now_iso(),
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
        now = _now_iso()

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
            now = _now_iso()
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
        now = _now_iso()
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
        update_data["updatedAt"] = _now_iso()

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
        now = _now_iso()

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

# AI Guided Interview Creation with Vapi Workflow
class AIGuidedInterviewRequest(BaseModel):
    # workflowId is now universal and automatically used - no longer required in request
    candidateName: Optional[str] = Field(None, description="Optional candidate name")
    jobTitle: Optional[str] = Field(None, description="Optional job title if pre-known")
    companyName: Optional[str] = Field(None, description="Optional company name")
    interviewType: Optional[str] = Field("technical", description="Interview type")
    experienceLevel: Optional[str] = Field("mid", description="Experience level")
    phone: Optional[str] = Field(None, description="Phone number for phone-based interviews")

class AIGuidedInterviewResponse(BaseModel):
    sessionId: str
    callId: str
    status: str
    assistantId: Optional[str] = None
    publicKey: Optional[str] = None
    workflowId: str
    interviewId: Optional[str] = None
    message: str
    
@app.post("/interviews/ai-guided", response_model=AIGuidedInterviewResponse)
async def create_ai_guided_interview(
    request: AIGuidedInterviewRequest,
    user_data: dict = Depends(verify_firebase_token)
):
    """
    Create an AI guided interview using a Vapi workflow ID.
    This starts a conversational AI that will gather interview preferences,
    create questions, and conduct the interview.
    """
    try:
        uid = user_data["uid"]
        session_id = str(uuid.uuid4())
        now = _now_iso()
        
        print(f"🤖 Starting AI guided interview with universal workflow ID: {UNIVERSAL_WORKFLOW_ID}")
        
        # Prepare interview metadata
        interview_metadata = {
            "userId": uid,
            "candidateName": request.candidateName or "Candidate",
            "jobTitle": request.jobTitle,
            "companyName": request.companyName,
            "interviewType": request.interviewType,
            "experienceLevel": request.experienceLevel,
            "sessionId": session_id,
            "workflowId": UNIVERSAL_WORKFLOW_ID,
            "createdAt": now
        }
        
        # Start Vapi call with workflow
        try:
            vapi_call_result = await vapi_service.start_workflow_call(
                workflow_id=UNIVERSAL_WORKFLOW_ID,
                metadata=interview_metadata,
                phone_number=request.phone
            )
            
            call_id = vapi_call_result.get("callId")
            call_status = vapi_call_result.get("status", "unknown")
            
            print(f"✅ Vapi workflow call started: {call_id} (status: {call_status})")
            
            # Create a preliminary interview record
            interview_id = str(uuid.uuid4())
            preliminary_interview = {
                "id": interview_id,
                "jobTitle": request.jobTitle or "TBD - AI Guided",
                "companyName": request.companyName or "TBD - AI Guided", 
                "interviewDate": now,
                "status": "ai_guided_setup",
                "overallScore": None,
                "userId": uid,
                "vapiCallId": call_id,
                "workflowId": UNIVERSAL_WORKFLOW_ID,
                "aiGuided": True,
                "metadata": interview_metadata,
                "createdAt": now,
                "updatedAt": now
            }
            
            # Save preliminary interview to Firebase
            if db is not None:
                interview_ref = db.collection("interviews").document(interview_id)
                interview_ref.set(preliminary_interview)
                print(f"📝 Saved preliminary AI guided interview: {interview_id}")
            
            # Save session mapping for workflow tracking
            if db is not None:
                session_ref = db.collection("ai_guided_sessions").document(session_id)
                session_ref.set({
                    "sessionId": session_id,
                    "interviewId": interview_id,
                    "userId": uid,
                    "workflowId": UNIVERSAL_WORKFLOW_ID,
                    "vapiCallId": call_id,
                    "status": call_status,
                    "metadata": interview_metadata,
                    "createdAt": now,
                    "updatedAt": now
                })
            
            return AIGuidedInterviewResponse(
                sessionId=session_id,
                callId=call_id,
                status=call_status,
                assistantId=vapi_call_result.get("assistantId"),
                publicKey=vapi_call_result.get("publicKey"),
                workflowId=UNIVERSAL_WORKFLOW_ID,
                interviewId=interview_id,
                message=f"AI guided interview session started. Call ID: {call_id}"
            )
            
        except Exception as vapi_error:
            print(f"❌ Vapi workflow call failed: {vapi_error}")
            # Return fallback response for mock/development mode
            fallback_call_id = f"ai_guided_mock_{session_id[:8]}"
            
            return AIGuidedInterviewResponse(
                sessionId=session_id,
                callId=fallback_call_id,
                status="mock_ai_guided",
                assistantId="mock_assistant",
                publicKey="mock_public_key",
                workflowId=UNIVERSAL_WORKFLOW_ID,
                interviewId=None,
                message=f"AI guided interview in mock mode (Vapi not configured). Session: {session_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"AI guided interview creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create AI guided interview")

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
    now = _now_iso()
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
            now = _now_iso()
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
        now = _now_iso()

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
            "createdAt": now,
            "updatedAt": now,
            "source": MANUAL_FEEDBACK_SOURCE,
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
        now = _now_iso()
        interview_ref.update({
            "aiSessionId": ai_session_id,
            "vapiCallId": call_id,
            "webCallUrl": vapi_response.get("webCallUrl"),
            "status": "inProgress",
            "updatedAt": now
        })
        
        # Determine status and include client-side init data when applicable
        resp_status = vapi_response.get("status", "in_progress")
        public_key = vapi_response.get("publicKey") or os.getenv("VAPI_PUBLIC_KEY")
        assistant_id = vapi_response.get("assistantId") or os.getenv("VAPI_ASSISTANT_ID")
        metadata = vapi_response.get("metadata") or {
            "interviewId": interview_id,
            "userId": uid,
        }

        return AIInterviewStartResponse(
            aiSessionId=ai_session_id,
            vapiCallId=call_id,
            status=resp_status,
            message=vapi_response.get("message", "AI interview session started successfully"),
            webCallUrl=vapi_response.get("webCallUrl"),
            assistantId=assistant_id,
            publicKey=public_key,
            metadata=metadata,
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
                update_payload = {"updatedAt": _now_iso()}
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
                audioRecordingUrl=recording_url,
                assistantId=vapi_status.get("assistantId"),
                publicKey=vapi_status.get("publicKey"),
                metadata=vapi_status.get("metadata"),
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

@app.post("/interviews/{interview_id}/complete-ai")
async def complete_ai_interview(
    interview_id: str,
    user_data: dict = Depends(verify_firebase_token)
):
    """Manually mark an AI interview as completed when the client ends the call"""
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
        
        # Update interview status to completed
        now = _now_iso()
        update_payload = {
            "status": "completed",
            "updatedAt": now
        }
        
        # If we have a vapi call ID, try to get final status/transcript
        vapi_call_id = interview_data.get("vapiCallId")
        transcript_text = None
        
        if vapi_call_id:
            try:
                # First try to get status with transcript URL
                vapi_status = await vapi_service.get_call_status(vapi_call_id)
                if vapi_status.get("duration"):
                    update_payload["interviewDuration"] = vapi_status.get("duration")
                if vapi_status.get("transcriptUrl"):
                    update_payload["transcriptUrl"] = vapi_status.get("transcriptUrl")
                if vapi_status.get("recordingUrl"):
                    update_payload["audioRecordingUrl"] = vapi_status.get("recordingUrl")
                
                # Also try to get transcript directly via API
                try:
                    transcript_text = await vapi_service.get_call_transcript(vapi_call_id)
                    if transcript_text and transcript_text.strip():
                        # Store transcript directly in Firebase
                        transcript_doc = {
                            'interviewId': interview_id,
                            'userId': uid,
                            'transcript': transcript_text,
                            'createdAt': now,
                            'updatedAt': now,
                        }
                        db.collection('transcripts').document(interview_id).set(transcript_doc, merge=True)
                        print(f"✅ Transcript saved directly to Firebase for interview {interview_id}")
                    
                except Exception as transcript_err:
                    print(f"Warning: Could not fetch transcript directly: {transcript_err}")
                    
            except Exception as e:
                print(f"Warning: Could not get final Vapi status during completion: {e}")
        
        interview_ref.update(update_payload)
        
        return {
            "message": "Interview marked as completed",
            "status": "completed",
            "updatedAt": now,
            "transcriptGenerated": transcript_text is not None and transcript_text.strip() != ""
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Complete AI interview error: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete AI interview")

@app.get("/interviews/{interview_id}/transcript")
async def get_interview_transcript(
    interview_id: str,
    user_data: dict = Depends(verify_firebase_token)
):
    """Get the transcript for an interview"""
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
        
        # First try to get from stored transcripts
        transcript_ref = db.collection("transcripts").document(interview_id)
        transcript_doc = transcript_ref.get()
        
        if transcript_doc.exists:
            transcript_data = transcript_doc.to_dict()
            return {
                "interviewId": interview_id,
                "transcript": transcript_data.get("transcript", ""),
                "createdAt": transcript_data.get("createdAt"),
                "source": "stored"
            }
        
        # If not stored, try to fetch from Vapi
        vapi_call_id = interview_data.get("vapiCallId")
        if vapi_call_id:
            try:
                transcript_text = await vapi_service.get_call_transcript(vapi_call_id)
                if transcript_text and transcript_text.strip():
                    # Store it for future use
                    now = _now_iso()
                    transcript_doc = {
                        'interviewId': interview_id,
                        'userId': uid,
                        'transcript': transcript_text,
                        'createdAt': now,
                        'updatedAt': now,
                    }
                    db.collection('transcripts').document(interview_id).set(transcript_doc)
                    
                    return {
                        "interviewId": interview_id,
                        "transcript": transcript_text,
                        "createdAt": now,
                        "source": "vapi_api"
                    }
            except Exception as e:
                print(f"Error fetching transcript from Vapi: {e}")
        
        # Return not found if no transcript available
        raise HTTPException(status_code=404, detail="Transcript not available")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get transcript error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get transcript")

@app.get("/interviews/{interview_id}/ai-feedback", response_model=AIFeedbackResponse)
async def get_ai_feedback(
    interview_id: str,
    user_data: dict = Depends(verify_firebase_token),
    force: bool = False,
):
    """Get AI-generated feedback for a completed interview"""
    try:
        uid = user_data.get("uid")

        if db is None:
            transcript_text = "Mock interview transcript for analysis"
            analysis = await gemini_service.analyze_interview_transcript(transcript_text, {
                "jobTitle": "Interview",
                "type": "technical",
                "level": "mid",
            })
            _, response_payload = _build_ai_feedback_payload(
                interview_id,
                uid,
                analysis,
                transcript_text,
                "ai_on_demand",
            )
            return AIFeedbackResponse(**response_payload)

        interview_ref = db.collection("interviews").document(interview_id)
        interview_doc = interview_ref.get()
        if not interview_doc.exists:
            raise HTTPException(status_code=404, detail="Interview not found")

        interview_data = interview_doc.to_dict()
        if interview_data.get("userId") != uid:
            raise HTTPException(status_code=403, detail="Access denied")

        if interview_data.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Interview not completed yet")

        feedback_query = db.collection("feedback").where("interviewId", "==", interview_id).where("userId", "==", uid)
        feedback_docs = [doc.to_dict() for doc in feedback_query.stream()]
        existing_ai = _select_latest_ai_feedback(feedback_docs)
        if existing_ai:
            return AIFeedbackResponse(**_feedback_doc_to_response(existing_ai))

        transcript_text = ""
        transcript_snapshot = db.collection("transcripts").document(interview_id).get()
        if transcript_snapshot.exists:
            transcript_text = transcript_snapshot.to_dict().get("transcript", "") or ""

        vapi_call_id = interview_data.get("vapiCallId")
        if not transcript_text and vapi_call_id:
            try:
                transcript_text = await vapi_service.get_call_transcript(vapi_call_id) or ""
            except Exception as transcript_err:
                print(f"Transcript fetch error for {interview_id}: {transcript_err}")

        if not transcript_text.strip():
            if not force:
                return JSONResponse(
                    status_code=202,
                    content={
                        "status": "pending_transcript",
                        "message": "Transcript not yet available for AI analysis",
                        "interviewId": interview_id,
                    },
                )
            transcript_text = "Transcript not available. Proceeding with limited analysis."

        analysis = await gemini_service.analyze_interview_transcript(transcript_text, interview_data)
        feedback_doc, response_payload = _build_ai_feedback_payload(
            interview_id,
            uid,
            analysis,
            transcript_text,
            "ai_on_demand",
        )

        try:
            db.collection("feedback").document(feedback_doc["id"]).set(feedback_doc)
            interview_ref.update({
                "overallScore": feedback_doc["overallScore"],
                "updatedAt": feedback_doc["updatedAt"],
            })
        except Exception as save_err:
            print(f"Warning: failed to persist AI feedback for {interview_id}: {save_err}")

        return AIFeedbackResponse(**response_payload)

    except HTTPException:
        raise
    except Exception as e:
        print(f"AI feedback error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI feedback")

@app.post("/interviews/{interview_id}/vapi-call-id")
async def update_vapi_call_id(
    interview_id: str,
    payload: UpdateVapiCallIdRequest,
    user_data: dict = Depends(verify_firebase_token)
):
    """Record the real Vapi callId initiated from the client Web SDK.
    This enables status polling without relying on webhooks."""
    try:
        uid = user_data["uid"]

        interview_ref = db.collection("interviews").document(interview_id)
        interview_doc = interview_ref.get()

        if not interview_doc.exists:
            raise HTTPException(status_code=404, detail="Interview not found")

        interview_data = interview_doc.to_dict()
        if interview_data.get("userId") != uid:
            raise HTTPException(status_code=403, detail="Access denied")

        now = _now_iso()
        update_payload: Dict[str, Any] = {
            "vapiCallId": payload.callId,
            "updatedAt": now,
            # If the call started, ensure interview is marked in progress
            "status": "inProgress",
        }
        if payload.assistantId:
            update_payload["vapiAssistantId"] = payload.assistantId
        if payload.metadata is not None:
            update_payload["vapiClientInitMeta"] = payload.metadata

        interview_ref.update(update_payload)

        return {"ok": True, "vapiCallId": payload.callId}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update vapi call id error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Vapi call id")
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
        now = _now_iso()
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
            update_payload = {"updatedAt": _now_iso()}
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
                if (
                    AUTO_GENERATE_AI_FEEDBACK
                    and update_payload.get("status") == "completed"
                    and interview_data is not None
                ):
                    feedback_docs = [doc.to_dict() for doc in db.collection("feedback").where("interviewId", "==", interview_id).stream()]
                    existing_ai = _select_latest_ai_feedback(feedback_docs)
                    if existing_ai is None:
                        transcript_text = ""
                        transcript_snapshot = db.collection("transcripts").document(interview_id).get()
                        if transcript_snapshot.exists:
                            transcript_text = transcript_snapshot.to_dict().get("transcript", "") or ""

                        if not transcript_text:
                            turl = update_payload.get("transcriptUrl") or interview_data.get("transcriptUrl")
                            if turl:
                                try:
                                    async with httpx.AsyncClient() as client:
                                        t_resp = await client.get(turl, timeout=20)
                                        if t_resp.status_code == 200:
                                            transcript_text = t_resp.text
                                except Exception as download_err:
                                    print(f"Transcript download error: {download_err}")

                        if not transcript_text and call_id:
                            try:
                                transcript_text = await vapi_service.get_call_transcript(call_id) or ""
                            except Exception as transcript_err:
                                print(f"Webhook transcript fetch error: {transcript_err}")

                        if transcript_text:
                            analysis = await gemini_service.analyze_interview_transcript(transcript_text, interview_data)
                            feedback_doc, _response_payload = _build_ai_feedback_payload(
                                interview_id,
                                interview_data.get("userId", ""),
                                analysis,
                                transcript_text,
                                "ai_auto",
                            )
                            db.collection("feedback").document(feedback_doc["id"]).set(feedback_doc)
                            db.collection("interviews").document(interview_id).update({
                                "overallScore": feedback_doc["overallScore"],
                                "updatedAt": feedback_doc["updatedAt"],
                            })
                        else:
                            print(f"Skipping auto AI feedback for {interview_id}: transcript unavailable")
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
