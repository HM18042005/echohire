# FastAPI backend with Firebase authentication and profile management
from datetime import datetime
from typing import Optional, List
import firebase_admin
from firebase_admin import credentials, firestore, auth
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field, field_validator
import os
import uuid

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

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

# Firebase token verification dependency
async def verify_firebase_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Endpoints
@app.get("/health")
async def health_check():
    return {"ok": True}

@app.get("/me", response_model=ProfileOut)
async def get_profile(user_data: dict = Depends(verify_firebase_token)):
    try:
        uid = user_data["uid"]
        email = user_data["email"]

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
        
        # Get user's interviews from Firebase
        interviews_ref = db.collection("interviews").where("userId", "==", uid).order_by("interviewDate", direction=firestore.Query.DESCENDING)
        interviews = interviews_ref.stream()

        interview_list = []
        for interview in interviews:
            interview_data = interview.to_dict()
            interview_list.append(InterviewOut(**interview_data))

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
