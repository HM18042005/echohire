# FastAPI backend with Firebase authentication and profile management
from datetime import datetime
from typing import Optional, List
import firebase_admin
from firebase_admin import credentials, firestore, auth
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field, field_validator
import os

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
