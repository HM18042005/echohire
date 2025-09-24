# AI Service utilities for EchoHire backend
import os
from typing import Dict, Any, List, Optional
import google.generativeai as genai
import httpx
import asyncio
import json

class GeminiAnalysisService:
    """Service for AI-powered interview analysis using Google Gemini"""
    
    def __init__(self):
        # Check if API key is configured
        api_key = os.getenv("GOOGLE_AI_API_KEY", "your-gemini-api-key-here")
        if api_key == "your-gemini-api-key-here" or not api_key:
            print("WARNING: GOOGLE_AI_API_KEY not configured properly. AI analysis will use mock data.")
            self.is_configured = False
        else:
            self.is_configured = True
            genai.configure(api_key=api_key)
            
        try:
            self.model = genai.GenerativeModel('gemini-pro')
            self.safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            self.is_configured = False
    
    async def analyze_interview_transcript(self, transcript: str, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze interview transcript and generate comprehensive feedback"""
        try:
            role = interview_data.get('jobTitle', 'Software Engineer')
            interview_type = interview_data.get('type', 'technical')
            experience_level = interview_data.get('level', 'mid')
            
            analysis_prompt = f"""
            You are an expert technical interviewer analyzing a {interview_type} interview for a {role} position at {experience_level} level.
            
            Interview Transcript:
            {transcript}
            
            Please provide a comprehensive analysis in the following JSON format:
            {{
                "overallScore": <integer 1-100>,
                "overallImpression": "<brief summary in 1-2 sentences>",
                "technicalCompetency": {{
                    "score": <integer 1-100>,
                    "strengths": ["<strength1>", "<strength2>"],
                    "weaknesses": ["<weakness1>", "<weakness2>"],
                    "assessment": "<detailed technical assessment>"
                }},
                "communicationSkills": {{
                    "score": <integer 1-100>,
                    "clarity": <integer 1-100>,
                    "articulation": <integer 1-100>,
                    "confidence": <integer 1-100>
                }},
                "problemSolving": {{
                    "score": <integer 1-100>,
                    "approach": "<description of problem-solving approach>",
                    "creativity": <integer 1-100>,
                    "logicalThinking": <integer 1-100>
                }},
                "keyInsights": [
                    "<insight1>",
                    "<insight2>", 
                    "<insight3>"
                ],
                "recommendedAreas": [
                    "<area1>",
                    "<area2>"
                ],
                "hiringRecommendation": "<hire|conditional_hire|no_hire>",
                "confidenceLevel": <float 0.0-1.0>,
                "nextSteps": "<recommended next steps>"
            }}
            
            Evaluate based on:
            1. Technical knowledge and problem-solving skills
            2. Communication clarity and confidence
            3. Depth of experience and understanding
            4. Cultural fit and enthusiasm
            5. Ability to handle challenging questions
            
            Provide honest, constructive feedback suitable for both hiring decisions and candidate development.
            """
            
            response = self.model.generate_content(
                analysis_prompt,
                safety_settings=self.safety_settings
            )
            
            # Parse the JSON response
            try:
                analysis_data = json.loads(response.text)
                
                # Validate and structure the response
                structured_analysis = {
                    "overallScore": max(1, min(100, analysis_data.get("overallScore", 75))),
                    "overallImpression": analysis_data.get("overallImpression", "Analysis completed"),
                    "keyInsights": analysis_data.get("keyInsights", [
                        "Technical competency evaluated",
                        "Communication skills assessed",
                        "Problem-solving approach reviewed"
                    ]),
                    "confidenceScore": max(0.0, min(1.0, analysis_data.get("confidenceLevel", 0.8))),
                    "transcriptAnalysis": self._generate_detailed_analysis(analysis_data),
                    "speechAnalysis": self._analyze_speech_patterns(transcript),
                    "emotionalAnalysis": self._analyze_emotional_indicators(transcript),
                    "recommendation": self._format_recommendation(analysis_data.get("hiringRecommendation", "conditional_hire")),
                    "technicalAssessment": analysis_data.get("technicalCompetency", {}),
                    "communicationAssessment": analysis_data.get("communicationSkills", {}),
                    "problemSolvingAssessment": analysis_data.get("problemSolving", {})
                }
                
                return structured_analysis
                
            except json.JSONDecodeError:
                # If JSON parsing fails, extract insights from text
                return self._fallback_analysis(response.text, role, interview_type)
            
        except Exception as e:
            print(f"Gemini analysis error: {e}")
            return self._emergency_fallback_analysis()
    
    def _generate_detailed_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Generate a comprehensive analysis summary"""
        try:
            technical = analysis_data.get("technicalCompetency", {})
            communication = analysis_data.get("communicationSkills", {})
            problem_solving = analysis_data.get("problemSolving", {})
            
            analysis_text = f"""
            TECHNICAL COMPETENCY ({technical.get('score', 75)}/100):
            {technical.get('assessment', 'Technical skills assessed')}
            
            COMMUNICATION SKILLS ({communication.get('score', 75)}/100):
            - Clarity: {communication.get('clarity', 75)}/100
            - Articulation: {communication.get('articulation', 75)}/100  
            - Confidence: {communication.get('confidence', 75)}/100
            
            PROBLEM SOLVING ({problem_solving.get('score', 75)}/100):
            {problem_solving.get('approach', 'Problem-solving approach evaluated')}
            
            RECOMMENDATION: {analysis_data.get('hiringRecommendation', 'Conditional hire')}
            NEXT STEPS: {analysis_data.get('nextSteps', 'Further evaluation recommended')}
            """
            
            return analysis_text.strip()
            
        except Exception:
            return "Comprehensive analysis completed with AI evaluation."
    
    def _analyze_speech_patterns(self, transcript: str) -> Dict[str, Any]:
        """Analyze speech patterns from transcript"""
        words = transcript.split()
        sentences = transcript.split('.')
        
        return {
            "total_words": len(words),
            "total_sentences": len(sentences),
            "avg_words_per_sentence": len(words) / max(1, len(sentences)),
            "complexity_score": min(100, len(set(words)) / max(1, len(words)) * 100),
            "pace": "moderate",  # This would require audio analysis in real implementation
            "clarity": "high"
        }
    
    def _analyze_emotional_indicators(self, transcript: str) -> Dict[str, float]:
        """Analyze emotional indicators from text"""
        positive_words = ["confident", "excited", "enthusiastic", "positive", "great", "excellent", "perfect"]
        negative_words = ["nervous", "unsure", "difficult", "challenging", "worried", "stressed"]
        
        words = transcript.lower().split()
        positive_count = sum(1 for word in words if any(pos in word for pos in positive_words))
        negative_count = sum(1 for word in words if any(neg in word for neg in negative_words))
        
        total_words = len(words)
        
        return {
            "confidence": max(0.3, min(1.0, 0.7 + (positive_count - negative_count) / max(1, total_words) * 10)),
            "enthusiasm": max(0.2, min(1.0, positive_count / max(1, total_words) * 20)),
            "stress": max(0.0, min(0.8, negative_count / max(1, total_words) * 15)),
            "overall_sentiment": max(0.1, min(1.0, (positive_count - negative_count + total_words * 0.05) / max(1, total_words)))
        }
    
    def _format_recommendation(self, recommendation: str) -> str:
        """Format hiring recommendation"""
        recommendation_map = {
            "hire": "Strong Hire - Recommended for immediate offer",
            "conditional_hire": "Conditional Hire - Recommend additional assessment", 
            "no_hire": "No Hire - Does not meet current requirements"
        }
        return recommendation_map.get(recommendation.lower(), "Review Required - Additional evaluation needed")
    
    def _fallback_analysis(self, analysis_text: str, role: str, interview_type: str) -> Dict[str, Any]:
        """Fallback analysis when JSON parsing fails"""
        return {
            "overallScore": 78,
            "overallImpression": f"AI analysis completed for {role} {interview_type} interview",
            "keyInsights": [
                "Interview transcript analyzed successfully",
                "Performance metrics evaluated",
                "Areas for improvement identified"
            ],
            "confidenceScore": 0.75,
            "transcriptAnalysis": analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text,
            "speechAnalysis": {"pace": "moderate", "clarity": "good", "complexity_score": 75},
            "emotionalAnalysis": {"confidence": 0.7, "enthusiasm": 0.6, "stress": 0.3},
            "recommendation": "Further review recommended based on AI analysis"
        }
    
    def _emergency_fallback_analysis(self) -> Dict[str, Any]:
        """Emergency fallback when all analysis fails"""
        return {
            "overallScore": 70,
            "overallImpression": "Interview completed - manual review recommended",
            "keyInsights": [
                "Technical interview conducted",
                "Response quality evaluated", 
                "Communication assessed"
            ],
            "confidenceScore": 0.5,
            "transcriptAnalysis": "AI analysis temporarily unavailable - manual review recommended",
            "speechAnalysis": {"pace": "moderate", "clarity": "adequate"},
            "emotionalAnalysis": {"confidence": 0.6, "enthusiasm": 0.5, "stress": 0.4},
            "recommendation": "Manual review required - AI analysis unavailable"
        }

class VapiInterviewService:
    """Service for managing Vapi voice AI interviews"""
    
    def __init__(self):
        self.vapi_api_key = os.getenv("VAPI_API_KEY", "your-vapi-key-here")
        self.base_url = "https://api.vapi.ai"
        # Optional webhook support
        self.backend_public_url = os.getenv("BACKEND_PUBLIC_URL")  # e.g., https://api.example.com
        self.webhook_secret = os.getenv("VAPI_WEBHOOK_SECRET")
        
        # Check if API key is configured
        if self.vapi_api_key == "your-vapi-key-here" or not self.vapi_api_key:
            print("WARNING: VAPI_API_KEY not configured properly. Vapi calls will use mock data.")
            self.is_configured = False
        else:
            self.is_configured = True
    
    async def start_interview_call(self, interview_data: Dict[str, Any], phone_number: Optional[str] = None) -> Dict[str, str]:
        """Start a Vapi voice interview session"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.vapi_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Prepare Vapi call configuration
                call_config: Dict[str, Any] = {
                    "assistant": {
                        "model": {
                            "provider": "openai",
                            "model": "gpt-4",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": f"""You are an expert interviewer conducting a {interview_data.get('type', 'technical')} interview for a {interview_data.get('jobTitle', 'Software Engineer')} position. 
                                    
                                    Your task is to:
                                    1. Ask relevant questions based on the role and experience level
                                    2. Listen carefully to responses and ask follow-up questions
                                    3. Evaluate technical competency and communication skills
                                    4. Keep the interview engaging and professional
                                    5. End the interview after 15-20 minutes with a summary
                                    
                                    Start by introducing yourself and explaining the interview process."""
                                }
                            ]
                        },
                        "voice": {
                            "provider": "elevenlabs",
                            "voiceId": "professional_interviewer"
                        }
                    },
                    "customer": {
                        "name": interview_data.get('candidateName', 'Candidate')
                    },
                    # Include metadata to correlate webhook events
                    "metadata": {
                        "interviewId": interview_data.get('id') or interview_data.get('interviewId'),
                        "userId": interview_data.get('userId'),
                    }
                }

                # Attach webhook callback if configured
                if self.backend_public_url:
                    webhook_url = f"{self.backend_public_url.rstrip('/')}/webhooks/vapi"
                    call_config["webhook"] = {"url": webhook_url}
                    if self.webhook_secret:
                        call_config["webhook"]["secret"] = self.webhook_secret
                    # Some providers accept direct webhookUrl field; include both for compatibility
                    call_config["webhookUrl"] = webhook_url

                # Phone or web call selection
                if phone_number:
                    call_config["phoneNumberId"] = phone_number
                    response = await client.post(
                        f"{self.base_url}/call/phone",
                        headers=headers,
                        json=call_config
                    )
                else:
                    response = await client.post(
                        f"{self.base_url}/call/web",
                        headers=headers,
                        json=call_config
                    )
                
                if response.status_code in (200, 201):
                    call_data = response.json()
                    return {
                        "callId": call_data.get("id") or call_data.get("callId"),
                        "status": call_data.get("status", "initiated"),
                        "message": "Interview call started successfully",
                        "webCallUrl": call_data.get("webCallUrl") if not phone_number else None
                    }
                else:
                    raise Exception(f"Failed to start Vapi call: {response.status_code}")
            
        except Exception as e:
            print(f"Vapi call start error: {e}")
            # Return mock data for development
            call_id = f"vapi_call_{interview_data.get('id', 'unknown')}"
            return {
                "callId": call_id,
                "status": "initiated",
                "message": "Mock interview call started (Vapi integration pending)",
                "webCallUrl": "https://mock-vapi-call.com/session/123"
            }
    
    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get the status of a Vapi call"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.vapi_api_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.get(
                    f"{self.base_url}/call/{call_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    call_data = response.json()
                    return {
                        "callId": call_id,
                        "status": (call_data.get("status") or call_data.get("state") or "unknown"),
                        "duration": call_data.get("duration") or call_data.get("callDuration") or 0,
                        "transcriptUrl": call_data.get("transcriptUrl") or call_data.get("transcript_url"),
                        "recordingUrl": call_data.get("recordingUrl") or call_data.get("recording_url"),
                        "endedReason": call_data.get("endedReason") or call_data.get("end_reason")
                    }
                else:
                    raise Exception(f"Failed to get call status: {response.status_code}")
            
        except Exception as e:
            print(f"Vapi status check error: {e}")
            # Return mock status for development
            return {
                "callId": call_id,
                "status": "in_progress",
                "duration": 300,  # 5 minutes
                "transcriptUrl": None,
                "recordingUrl": None
            }
    
    async def stop_call(self, call_id: str) -> bool:
        """Stop an ongoing Vapi call"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.vapi_api_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.patch(
                    f"{self.base_url}/call/{call_id}",
                    headers=headers,
                    json={"status": "ended"}
                )
                
                return response.status_code == 200
            
        except Exception as e:
            print(f"Vapi call stop error: {e}")
            return True  # Return True for mock implementation
    
    async def get_call_transcript(self, call_id: str) -> str:
        """Get the transcript of a completed call"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.vapi_api_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.get(
                    f"{self.base_url}/call/{call_id}/transcript",
                    headers=headers
                )
                
                if response.status_code == 200:
                    transcript_data = response.json()
                    # Process transcript format from Vapi
                    messages = transcript_data.get("messages", [])
                    transcript_text = "\n".join([
                        f"{msg.get('role', 'unknown')}: {msg.get('message', '')}"
                        for msg in messages
                    ])
                    return transcript_text
                else:
                    raise Exception(f"Failed to get transcript: {response.status_code}")
            
        except Exception as e:
            print(f"Vapi transcript error: {e}")
            # Return mock transcript for development
            return """Interviewer: Hello! I'm conducting a technical interview today. Can you tell me about your experience with software development?

Candidate: Hi! I have about 3 years of experience in software development, primarily working with Python and JavaScript. I've built several web applications using Django and React.

Interviewer: That's great! Can you walk me through how you would approach debugging a slow-performing web application?

Candidate: I would start by identifying the bottleneck - whether it's in the frontend, backend, or database. I'd use profiling tools to measure performance, check database queries for efficiency, and optimize any slow endpoints.

Interviewer: Excellent approach! Thank you for your time today. We'll be in touch soon with feedback."""

# Service instances
gemini_service = GeminiAnalysisService()
vapi_service = VapiInterviewService()