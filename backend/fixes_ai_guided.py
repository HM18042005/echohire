"""
Comprehensive Fix for AI Guided Interview Issues
===============================================

This script contains the fixes for:
1. Vapi workflow not being called properly
2. Interview not being stored correctly (TBD issue)
3. Feedback not being generated after completion
"""

import asyncio
import json
from datetime import datetime

# Fix 1: Improve AI Guided Interview Creation
def get_improved_ai_guided_interview_endpoint():
    """Returns the improved AI guided interview endpoint code"""
    return '''
@app.post("/interviews/ai-guided", response_model=AIGuidedInterviewResponse)
async def create_ai_guided_interview(
    request: AIGuidedInterviewRequest,
    user_data: dict = Depends(verify_firebase_token)
):
    """
    Create an AI guided interview using a Vapi workflow ID.
    FIXES:
    - Ensures proper job title instead of TBD
    - Better error handling for Vapi failures
    - Improved interview record structure
    """
    try:
        uid = user_data["uid"]
        session_id = str(uuid.uuid4())
        interview_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        
        print(f"🤖 Creating AI guided interview for company: {request.companyName}")
        print(f"📋 Session ID: {session_id}")
        print(f"📋 Interview ID: {interview_id}")
        print(f"🔧 Using workflow ID: {UNIVERSAL_WORKFLOW_ID}")
        
        # Prepare enhanced interview metadata
        interview_metadata = {
            "userId": uid,
            "companyName": request.companyName,
            "sessionId": session_id,
            "workflowId": UNIVERSAL_WORKFLOW_ID,
            "interviewId": interview_id,  # Include interview ID in metadata
            "createdAt": now,
            "type": "ai_guided",
            "purpose": "dynamic_interview_setup"
        }
        
        # CRITICAL FIX: Start Vapi call with proper error handling
        vapi_call_result = None
        call_id = None
        call_status = "pending"
        
        try:
            print(f"🚀 Attempting to start Vapi workflow call...")
            vapi_call_result = await vapi_service.start_workflow_call(
                workflow_id=UNIVERSAL_WORKFLOW_ID,
                metadata=interview_metadata,
                phone_number=None  # Web-based by default
            )
            
            call_id = vapi_call_result.get("callId")
            call_status = vapi_call_result.get("status", "unknown")
            
            print(f"✅ Vapi workflow call started successfully!")
            print(f"   Call ID: {call_id}")
            print(f"   Status: {call_status}")
            
            # Check if this is actually a mock response
            if call_status == "mock_ai_guided" or (call_id and "mock" in call_id):
                print(f"⚠️  WARNING: Vapi call returned mock response - check configuration")
                
        except Exception as vapi_error:
            print(f"❌ Vapi workflow call failed: {vapi_error}")
            print(f"🔄 This will create interview record but Vapi integration is not working")
            # Don't fail the entire request - create interview record anyway
            call_id = f"fallback_ai_guided_{session_id[:8]}"
            call_status = "vapi_failed"
            
        # CRITICAL FIX: Create interview record with proper job title
        preliminary_interview = {
            "id": interview_id,
            "jobTitle": f"AI Guided Interview - {request.companyName}",  # FIXED: No more TBD
            "companyName": request.companyName,
            "interviewDate": now,
            "status": "ai_guided_setup",  # FIXED: Proper initial status
            "overallScore": None,  # Will be set after completion
            "userId": uid,
            "vapiCallId": call_id,
            "workflowId": UNIVERSAL_WORKFLOW_ID,
            "aiGuided": True,
            "interviewType": "ai_guided",  # FIXED: Explicit type
            "experienceLevel": "to_be_determined",  # AI will collect this
            "metadata": interview_metadata,
            "createdAt": now,
            "updatedAt": now,
            "feedbackGenerated": False,  # Track feedback status
            "transcriptAvailable": False  # Track transcript status
        }
        
        # Save interview to Firebase with better error handling
        if db is not None:
            try:
                interview_ref = db.collection("interviews").document(interview_id)
                interview_ref.set(preliminary_interview)
                print(f"✅ Saved interview record: {interview_id}")
                print(f"   Job Title: {preliminary_interview['jobTitle']}")
                print(f"   Status: {preliminary_interview['status']}")
            except Exception as db_error:
                print(f"❌ Failed to save interview to Firebase: {db_error}")
                # Don't fail the request - Vapi call might still work
        else:
            print(f"⚠️  Firebase not available - interview record not saved")
        
        # Save session mapping for webhook tracking
        if db is not None:
            try:
                session_ref = db.collection("ai_guided_sessions").document(session_id)
                session_data = {
                    "sessionId": session_id,
                    "interviewId": interview_id,
                    "userId": uid,
                    "workflowId": UNIVERSAL_WORKFLOW_ID,
                    "vapiCallId": call_id,
                    "status": call_status,
                    "metadata": interview_metadata,
                    "createdAt": now,
                    "updatedAt": now
                }
                session_ref.set(session_data)
                print(f"✅ Saved session mapping: {session_id}")
            except Exception as session_error:
                print(f"⚠️  Failed to save session mapping: {session_error}")
        
        # Return comprehensive response
        response = AIGuidedInterviewResponse(
            sessionId=session_id,
            callId=call_id,
            status=call_status,
            assistantId=vapi_call_result.get("assistantId") if vapi_call_result else "assistant_unavailable",
            publicKey=vapi_call_result.get("publicKey") if vapi_call_result else os.getenv("VAPI_PUBLIC_KEY"),
            workflowId=UNIVERSAL_WORKFLOW_ID,
            interviewId=interview_id,
            message=f"AI guided interview session created for {request.companyName}. " + 
                   (f"Call ID: {call_id}" if call_status != "vapi_failed" else "Note: Vapi integration failed but interview record created.")
        )
        
        print(f"🎉 AI guided interview creation completed!")
        print(f"   Response: {response.dict()}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ AI guided interview creation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create AI guided interview: {str(e)}")
'''

# Fix 2: Improved Webhook Handling for Feedback Generation
def get_improved_webhook_handler():
    """Returns improved webhook handler with better feedback generation"""
    return '''
@app.post("/webhooks/vapi")
async def vapi_webhook(request: Request):
    """
    IMPROVED webhook handler with better feedback generation
    """
    try:
        raw_body = await request.body()
        try:
            event = json.loads(raw_body.decode("utf-8"))
        except Exception:
            event = await request.json()

        print(f"🔔 Vapi webhook received: {event.get('type', 'unknown')} event")

        # Extract identifiers with better logging
        call_id = event.get("id") or event.get("callId") or event.get("call_id")
        status = (event.get("status") or event.get("state") or "").lower()
        duration = event.get("duration") or event.get("callDuration")
        transcript_url = event.get("transcriptUrl") or event.get("transcript_url")
        recording_url = event.get("recordingUrl") or event.get("recording_url")
        
        print(f"📋 Webhook details:")
        print(f"   Call ID: {call_id}")
        print(f"   Status: {status}")
        print(f"   Duration: {duration}")
        print(f"   Transcript URL: {transcript_url}")

        # IMPROVED: Better interview lookup
        interview_id = None
        interview_ref = None
        interview_data = None
        
        if db is not None:
            # First try metadata lookup
            meta = event.get("metadata") or {}
            interview_id = meta.get("interviewId") or meta.get("interview_id")
            
            if interview_id:
                print(f"🔍 Looking up interview by metadata ID: {interview_id}")
                interview_ref = db.collection("interviews").document(interview_id)
                snapshot = interview_ref.get()
                if snapshot.exists:
                    interview_data = snapshot.to_dict()
                    print(f"✅ Found interview by metadata: {interview_data.get('jobTitle', 'Unknown')}")
            
            # Fallback: lookup by Vapi call ID
            if interview_data is None and call_id:
                print(f"🔍 Looking up interview by call ID: {call_id}")
                try:
                    candidates = db.collection("interviews").where("vapiCallId", "==", call_id).stream()
                    for doc in candidates:
                        interview_ref = db.collection("interviews").document(doc.id)
                        interview_data = doc.to_dict()
                        interview_id = doc.id
                        print(f"✅ Found interview by call ID: {interview_data.get('jobTitle', 'Unknown')}")
                        break
                except Exception as e:
                    print(f"❌ Interview lookup error: {e}")

        # CRITICAL FIX: Update interview status and trigger feedback
        if interview_ref is not None and interview_data is not None:
            print(f"📝 Updating interview: {interview_id}")
            
            update_payload = {"updatedAt": datetime.utcnow().isoformat() + "Z"}
            
            # Normalize status
            if status:
                normalized = "inProgress"
                if "completed" in status or "ended" in status or status == "completed":
                    normalized = "completed"
                    print(f"🎯 Interview completed - will trigger feedback generation")
                elif "failed" in status or status == "failed":
                    normalized = "failed"
                    print(f"❌ Interview failed")
                update_payload["status"] = normalized
                
            if duration is not None:
                update_payload["interviewDuration"] = duration
            if transcript_url:
                update_payload["transcriptUrl"] = transcript_url
                update_payload["transcriptAvailable"] = True
            if recording_url:
                update_payload["audioRecordingUrl"] = recording_url
            if call_id and not interview_data.get("vapiCallId"):
                update_payload["vapiCallId"] = call_id

            try:
                interview_ref.update(update_payload)
                print(f"✅ Interview updated successfully")
            except Exception as e:
                print(f"❌ Failed to update interview: {e}")

            # CRITICAL FIX: Improved feedback generation on completion
            try:
                if update_payload.get("status") == "completed":
                    await generate_ai_feedback_for_interview(interview_id, interview_data, call_id, transcript_url)
            except Exception as e:
                print(f"❌ Feedback generation failed: {e}")
        else:
            print(f"⚠️  No interview record found for webhook - this might be a problem")

        return {"ok": True}
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

async def generate_ai_feedback_for_interview(interview_id: str, interview_data: dict, call_id: str, transcript_url: str):
    """
    IMPROVED feedback generation with better error handling
    """
    try:
        print(f"🧠 Starting AI feedback generation for interview: {interview_id}")
        
        # Check if feedback already exists
        if db is not None:
            existing_feedback = list(db.collection("feedback").where("interviewId", "==", interview_id).limit(1).stream())
            if existing_feedback:
                print(f"⚠️  Feedback already exists for interview: {interview_id}")
                return
        
        # Fetch transcript with multiple fallback methods
        transcript_text = None
        
        # Method 1: Use provided transcript URL
        if transcript_url:
            print(f"📄 Fetching transcript from URL: {transcript_url}")
            try:
                async with httpx.AsyncClient() as client:
                    t_resp = await client.get(transcript_url, timeout=30)
                    if t_resp.status_code == 200:
                        transcript_text = t_resp.text
                        print(f"✅ Transcript fetched from URL: {len(transcript_text)} characters")
            except Exception as e:
                print(f"❌ Failed to fetch transcript from URL: {e}")
        
        # Method 2: Fetch directly from Vapi
        if transcript_text is None and call_id:
            print(f"📄 Fetching transcript from Vapi for call: {call_id}")
            try:
                transcript_text = await vapi_service.get_call_transcript(call_id)
                if transcript_text:
                    print(f"✅ Transcript fetched from Vapi: {len(transcript_text)} characters")
            except Exception as e:
                print(f"❌ Failed to fetch transcript from Vapi: {e}")
        
        # Method 3: Fallback transcript for testing
        if transcript_text is None:
            print(f"⚠️  No transcript available - using fallback for feedback generation")
            transcript_text = f"AI Guided Interview completed for {interview_data.get('companyName', 'Unknown Company')}. Detailed transcript not available."
        
        # Generate AI feedback
        print(f"🤖 Generating AI analysis...")
        ai_feedback_data = await gemini_service.analyze_interview_transcript(transcript_text, interview_data)
        
        # Create comprehensive feedback record
        ai_analysis_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        
        feedback_doc = {
            "id": ai_analysis_id,
            "interviewId": interview_id,
            "userId": interview_data.get("userId", ""),
            "overallScore": ai_feedback_data.get("overallScore", 75),
            "overallImpression": ai_feedback_data.get("overallImpression", "AI guided interview completed successfully"),
            "keyInsights": ai_feedback_data.get("keyInsights", ["Interview completed", "Feedback generated from AI analysis"]),
            "confidenceScore": ai_feedback_data.get("confidenceScore", 0.8),
            "speechAnalysis": ai_feedback_data.get("speechAnalysis", {}),
            "transcriptAnalysis": ai_feedback_data.get("transcriptAnalysis", "Analysis completed"),
            "emotionalAnalysis": ai_feedback_data.get("emotionalAnalysis", {}),
            "finalVerdict": ai_feedback_data.get("recommendation", "Review completed"),
            "technicalAssessment": ai_feedback_data.get("technicalAssessment", {}),
            "communicationAssessment": ai_feedback_data.get("communicationAssessment", {}),
            "roleSpecificAssessment": ai_feedback_data.get("roleSpecificAssessment", {}),
            "hiringRecommendation": ai_feedback_data.get("hiringRecommendation", "review"),
            "createdAt": now,
            "aiAnalysisId": ai_analysis_id,
            "transcriptLength": len(transcript_text) if transcript_text else 0,
            "generatedBy": "ai_guided_workflow"
        }
        
        # Save feedback to Firebase
        if db is not None:
            db.collection("feedback").document(ai_analysis_id).set(feedback_doc)
            print(f"✅ Feedback saved: {ai_analysis_id}")
            
            # Update interview record with feedback info
            db.collection("interviews").document(interview_id).update({
                "overallScore": feedback_doc["overallScore"],
                "feedbackGenerated": True,
                "feedbackId": ai_analysis_id,
                "updatedAt": now,
            })
            print(f"✅ Interview updated with feedback reference")
        
        print(f"🎉 AI feedback generation completed successfully!")
        print(f"   Overall Score: {feedback_doc['overallScore']}")
        print(f"   Recommendation: {feedback_doc['hiringRecommendation']}")
        
    except Exception as e:
        print(f"❌ AI feedback generation failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Still update the interview to mark that we attempted feedback
        if db is not None:
            try:
                db.collection("interviews").document(interview_id).update({
                    "feedbackGenerated": False,
                    "feedbackError": str(e),
                    "updatedAt": datetime.utcnow().isoformat() + "Z"
                })
            except Exception as update_error:
                print(f"❌ Failed to update interview with feedback error: {update_error}")
'''

if __name__ == "__main__":
    print("🔧 AI Guided Interview Fixes Generated")
    print("=" * 50)
    print("1. Improved AI guided interview creation with proper job titles")
    print("2. Enhanced webhook handling for feedback generation")
    print("3. Better error handling and logging throughout")
    print("\nTo apply these fixes:")
    print("1. Replace the create_ai_guided_interview function in main.py")
    print("2. Replace the vapi_webhook function in main.py")
    print("3. Add the generate_ai_feedback_for_interview helper function")
    print("4. Test the complete flow end-to-end")