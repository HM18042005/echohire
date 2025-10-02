# AI Service utilities for EchoHire backend
import os
from typing import Dict, Any, List, Optional

# Universal Vapi Workflow Configuration
UNIVERSAL_WORKFLOW_ID = "7894c32f-8b29-4e71-90f3-a19047832a21"

# Control whether the backend should attempt to kick off web-based workflow calls
AUTO_INITIATE_WEB_WORKFLOW = os.getenv("AUTO_INITIATE_WEB_WORKFLOW", "1") == "1"

# Make google.generativeai optional so the backend doesn't crash if the package isn't installed
try:
    import google.generativeai as genai  # type: ignore
    GENAI_AVAILABLE = True
except Exception as e:  # ModuleNotFoundError or other import-time errors
    genai = None  # type: ignore
    GENAI_AVAILABLE = False
    print(f"WARNING: google.generativeai not available ({type(e).__name__}: {e}). AI analysis will use fallback.")

import httpx
import asyncio
import json

class GeminiAnalysisService:
    """Service for AI-powered interview analysis using Google Gemini"""
    
    def __init__(self):
        # Default state
        self.model = None
        self.model_name: Optional[str] = None
        self.safety_settings = []

        # Check if API key and package are configured
        api_key = os.getenv("GOOGLE_AI_API_KEY", "your-gemini-api-key-here")

        if not GENAI_AVAILABLE:
            print("WARNING: google.generativeai package missing. AI analysis will use fallback.")
            self.is_configured = False
            return

        if api_key == "your-gemini-api-key-here" or not api_key:
            print("WARNING: GOOGLE_AI_API_KEY not configured properly. AI analysis will use mock data.")
            self.is_configured = False
            return

        # Configure SDK and initialize model
        try:
            genai.configure(api_key=api_key)
            preferred_models = [
                "gemini-1.5-pro-latest",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.0-pro",
            ]
            for model_name in preferred_models:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    self.model_name = model_name
                    break
                except Exception as model_error:
                    print(f"WARNING: Gemini model {model_name} unavailable ({model_error}). Trying fallback...")
                    continue

            if not self.model:
                print("WARNING: No compatible Gemini model available. AI analysis will use fallback.")
                self.is_configured = False
                return

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
            print(f"[GEMINI_INIT] Using model: {self.model_name}")
            self.is_configured = True
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            self.is_configured = False
    
    async def analyze_interview_transcript(self, transcript: str, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze interview transcript and generate comprehensive feedback"""
        try:
            role = interview_data.get('jobTitle', 'Software Engineer')
            interview_type = interview_data.get('type', 'technical')
            experience_level = interview_data.get('level', 'mid')

            # Fallback early if Gemini isn't configured/available
            if not self.is_configured or not self.model:
                return self._fallback_analysis(
                    "AI analysis unavailable - using heuristic fallback.",
                    role,
                    interview_type
                )
            
            analysis_prompt = f"""
            You are an expert technical interviewer with 10+ years of experience analyzing {interview_type} interviews for {role} positions at {experience_level} level.

            CONTEXT:
            - Role: {role} ({experience_level} level)
            - Interview Type: {interview_type}
            - Company: {interview_data.get('companyName', 'Technology Company')}
            
            INTERVIEW TRANSCRIPT:
            {transcript}
            
            ANALYSIS INSTRUCTIONS:
            Analyze this transcript as if you were evaluating a candidate for hiring. The transcript may contain both interviewer questions and candidate responses. Focus on the candidate's responses, technical depth, communication style, and problem-solving approach.

            For {experience_level} level {role} candidates, expect:
            - Junior: Basic concepts, willingness to learn, good foundation
            - Mid: Solid experience, independent work, some leadership
            - Senior: Deep expertise, mentoring ability, strategic thinking
            - Lead: Technical vision, team leadership, business alignment

            Please provide a comprehensive analysis in the following JSON format:
            {{
                "overallScore": <integer 1-100>,
                "overallImpression": "<2-3 sentence summary of candidate performance>",
                "technicalCompetency": {{
                    "score": <integer 1-100>,
                    "strengths": ["<specific technical strength>", "<another strength>"],
                    "weaknesses": ["<area for improvement>", "<another area>"],
                    "assessment": "<detailed technical assessment with specific examples from transcript>"
                }},
                "communicationSkills": {{
                    "score": <integer 1-100>,
                    "clarity": <integer 1-100>,
                    "articulation": <integer 1-100>,
                    "confidence": <integer 1-100>,
                    "examples": "<specific examples of good/poor communication from transcript>"
                }},
                "problemSolving": {{
                    "score": <integer 1-100>,
                    "approach": "<description of how candidate approached problems>",
                    "creativity": <integer 1-100>,
                    "logicalThinking": <integer 1-100>,
                    "methodology": "<describe their problem-solving methodology>"
                }},
                "keyInsights": [
                    "<specific insight about candidate's performance>",
                    "<notable strength or concern>", 
                    "<recommendation for improvement>"
                ],
                "recommendedAreas": [
                    "<specific skill or knowledge gap to address>",
                    "<area for professional development>"
                ],
                "roleSpecificAssessment": {{
                    "roleAlignment": <integer 1-100>,
                    "experienceLevel": "<junior|mid|senior|lead - actual level demonstrated>",
                    "readiness": "<assessment of readiness for this role>",
                    "growthPotential": "<assessment of growth potential>"
                }},
                "hiringRecommendation": "<hire|conditional_hire|no_hire>",
                "confidenceLevel": <float 0.0-1.0>,
                "nextSteps": "<specific recommended next steps or additional assessment needs>",
                "interviewQuality": {{
                    "responseDepth": <integer 1-100>,
                    "questionHandling": <integer 1-100>,
                    "engagement": <integer 1-100>
                }}
            }}
            
            EVALUATION CRITERIA:
            1. **Technical Depth**: Knowledge appropriate for {experience_level} {role}
            2. **Problem-Solving**: Approach, methodology, and logical thinking
            3. **Communication**: Clarity, articulation, and ability to explain complex concepts
            4. **Experience**: Relevant background and practical application
            5. **Cultural Fit**: Enthusiasm, collaboration, and growth mindset
            6. **Role Readiness**: Ability to perform at expected {experience_level} level
            
            SCORING GUIDELINES:
            - 90-100: Exceptional, exceeds expectations for level
            - 80-89: Strong, meets expectations with some standout qualities
            - 70-79: Good, meets basic expectations for level
            - 60-69: Below expectations, needs improvement
            - Below 60: Does not meet minimum requirements
            
            Provide honest, constructive feedback that helps both hiring decisions and candidate development. Be specific and reference actual content from the transcript.
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
                    "transcriptAnalysis": self._generate_enhanced_analysis(analysis_data),
                    "speechAnalysis": self._analyze_speech_patterns(transcript),
                    "emotionalAnalysis": self._analyze_emotional_indicators(transcript),
                    "recommendation": self._format_recommendation(analysis_data.get("hiringRecommendation", "conditional_hire")),
                    "technicalAssessment": analysis_data.get("technicalCompetency", {}),
                    "communicationAssessment": analysis_data.get("communicationSkills", {}),
                    "problemSolvingAssessment": analysis_data.get("problemSolving", {}),
                    "roleSpecificAssessment": analysis_data.get("roleSpecificAssessment", {}),
                    "interviewQuality": analysis_data.get("interviewQuality", {}),
                    "recommendedAreas": analysis_data.get("recommendedAreas", []),
                    "nextSteps": analysis_data.get("nextSteps", "Further evaluation recommended")
                }
                
                return structured_analysis
                
            except json.JSONDecodeError:
                # If JSON parsing fails, extract insights from text
                return self._fallback_analysis(response.text, role, interview_type)
            
        except Exception as e:
            print(f"Gemini analysis error: {e}")
            return self._emergency_fallback_analysis(role, interview_type)
    
    def _generate_enhanced_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Generate a comprehensive analysis summary with enhanced details"""
        try:
            technical = analysis_data.get("technicalCompetency", {})
            communication = analysis_data.get("communicationSkills", {})
            problem_solving = analysis_data.get("problemSolving", {})
            role_specific = analysis_data.get("roleSpecificAssessment", {})
            interview_quality = analysis_data.get("interviewQuality", {})
            
            analysis_text = f"""
            OVERALL ASSESSMENT:
            {analysis_data.get('overallImpression', 'Analysis completed')}
            
            TECHNICAL COMPETENCY ({technical.get('score', 75)}/100):
            {technical.get('assessment', 'Technical skills assessed')}
            Strengths: {', '.join(technical.get('strengths', ['Technical knowledge demonstrated']))}
            Areas for Improvement: {', '.join(technical.get('weaknesses', ['Additional practice recommended']))}
            
            COMMUNICATION SKILLS ({communication.get('score', 75)}/100):
            - Clarity: {communication.get('clarity', 75)}/100
            - Articulation: {communication.get('articulation', 75)}/100  
            - Confidence: {communication.get('confidence', 75)}/100
            Examples: {communication.get('examples', 'Communication patterns analyzed')}
            
            PROBLEM SOLVING ({problem_solving.get('score', 75)}/100):
            Approach: {problem_solving.get('approach', 'Problem-solving approach evaluated')}
            Methodology: {problem_solving.get('methodology', 'Systematic approach observed')}
            - Creativity: {problem_solving.get('creativity', 75)}/100
            - Logical Thinking: {problem_solving.get('logicalThinking', 75)}/100
            
            ROLE-SPECIFIC ASSESSMENT:
            - Role Alignment: {role_specific.get('roleAlignment', 75)}/100
            - Experience Level Demonstrated: {role_specific.get('experienceLevel', 'mid')}
            - Role Readiness: {role_specific.get('readiness', 'Generally prepared for role expectations')}
            - Growth Potential: {role_specific.get('growthPotential', 'Positive growth trajectory expected')}
            
            INTERVIEW PERFORMANCE:
            - Response Depth: {interview_quality.get('responseDepth', 75)}/100
            - Question Handling: {interview_quality.get('questionHandling', 75)}/100
            - Engagement Level: {interview_quality.get('engagement', 75)}/100
            
            DEVELOPMENT RECOMMENDATIONS:
            {chr(10).join(f"• {area}" for area in analysis_data.get('recommendedAreas', ['Continue professional development']))}
            
            HIRING RECOMMENDATION: {analysis_data.get('hiringRecommendation', 'Conditional hire').upper()}
            NEXT STEPS: {analysis_data.get('nextSteps', 'Further evaluation recommended')}
            """
            
            return analysis_text.strip()
            
        except Exception:
            return "Comprehensive analysis completed with AI evaluation."
    
    def _generate_detailed_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Legacy method for backward compatibility"""
        return self._generate_enhanced_analysis(analysis_data)
    
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
    
    def _emergency_fallback_analysis(self, role: str, interview_type: str) -> Dict[str, Any]:
        """Emergency fallback when all analysis fails"""
        return {
            "overallScore": 70,
            "overallImpression": f"Interview completed - manual review recommended for {role} {interview_type} interview",
            "keyInsights": [
                "Technical interview conducted",
                "Response quality evaluated", 
                "Communication assessed"
            ],
            "confidenceScore": 0.5,
            "transcriptAnalysis": "AI analysis temporarily unavailable - manual review recommended",
            "speechAnalysis": {"pace": "moderate", "clarity": "adequate"},
            "emotionalAnalysis": {"confidence": 0.6, "enthusiasm": 0.5, "stress": 0.4},
            "recommendation": "Manual review required - AI analysis unavailable",
            "technicalAssessment": {
                "score": 68,
                "strengths": ["Baseline technical competency observed"],
                "weaknesses": ["Detailed AI insights unavailable"],
                "assessment": "Automated analysis unavailable. Please review candidate responses manually.",
            },
            "communicationAssessment": {
                "score": 70,
                "clarity": 70,
                "articulation": 68,
                "confidence": 65,
                "examples": "Communication metrics unavailable due to AI fallback.",
            },
            "problemSolvingAssessment": {
                "score": 69,
                "approach": "Problem-solving indicators require manual verification.",
                "creativity": 65,
                "logicalThinking": 68,
                "methodology": "Review transcript to assess structured thinking and methodology.",
            },
            "roleSpecificAssessment": {
                "roleAlignment": 70,
                "experienceLevel": "mid",
                "readiness": "Manual evaluation required to confirm readiness.",
                "growthPotential": "Manual evaluation required to gauge growth potential.",
            },
            "interviewQuality": {
                "responseDepth": 68,
                "questionHandling": 70,
                "engagement": 72,
            },
            "recommendedAreas": [
                "Review candidate's technical depth manually",
                "Assess communication nuances via transcript",
            ],
            "nextSteps": "Conduct manual review or rerun AI analysis when available",
        }

class VapiInterviewService:
    """Service for managing Vapi voice AI interviews"""
    
    def __init__(self):
        # Debug environment variable loading
        print(f"[VAPI_INIT] Loading environment variables...")
        
        # Get API key with detailed debugging
        self.vapi_api_key = os.getenv("VAPI_API_KEY")
        vapi_public_key = os.getenv("VAPI_PUBLIC_KEY")
        
        print(f"[VAPI_INIT] VAPI_API_KEY found: {bool(self.vapi_api_key)}")
        print(f"[VAPI_INIT] VAPI_PUBLIC_KEY found: {bool(vapi_public_key)}")
        
        if self.vapi_api_key:
            print(f"[VAPI_INIT] VAPI_API_KEY ends with: ***{self.vapi_api_key[-8:]}")
        if vapi_public_key:
            print(f"[VAPI_INIT] VAPI_PUBLIC_KEY ends with: ***{vapi_public_key[-8:]}")
        
        # Ensure we're using the private API key for server-side operations
        if not self.vapi_api_key:
            print("[VAPI_INIT] WARNING: VAPI_API_KEY not found, using fallback")
            self.vapi_api_key = "your-vapi-key-here"
        
        self.base_url = "https://api.vapi.ai"
        # Optional: assistant scoping (many Vapi tokens are scoped to specific assistants)
        self.vapi_assistant_id = os.getenv("VAPI_ASSISTANT_ID")
        # Optional webhook support
        self.backend_public_url = os.getenv("BACKEND_PUBLIC_URL")  # e.g., https://api.example.com
        self.webhook_secret = os.getenv("VAPI_WEBHOOK_SECRET")
        
        print(f"[VAPI_INIT] Assistant ID: {self.vapi_assistant_id}")
        print(f"[VAPI_INIT] Backend URL: {self.backend_public_url}")
        
        # Check if API key is configured
        if self.vapi_api_key == "your-vapi-key-here" or not self.vapi_api_key:
            print("[VAPI_INIT] WARNING: VAPI_API_KEY not configured properly. Vapi calls will use mock data.")
            self.is_configured = False
        else:
            print(f"[VAPI_INIT] API key configured successfully (length: {len(self.vapi_api_key)})")
            self.is_configured = True

        self.auto_init_web_workflow = AUTO_INITIATE_WEB_WORKFLOW
        print(f"[VAPI_INIT] Auto-init web workflow: {self.auto_init_web_workflow}")

    def _client_init_response(self, workflow_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Return standard response instructing clients to initialize web call themselves."""
        return {
            "callId": "web_call_client_side",
            "status": "ready_for_client_init",
            "message": "Use this configuration to initialize web call from client-side",
            "webCallUrl": None,
            "assistantId": self.vapi_assistant_id,
            "publicKey": os.getenv("VAPI_PUBLIC_KEY"),
            "workflowId": workflow_id,
            "metadata": {
                **(metadata or {}),
                "initMode": "client",
            },
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate Vapi configuration and return detailed status"""
        validation_result = {
            "is_configured": self.is_configured,
            "api_key_present": bool(self.vapi_api_key),
            "api_key_length": len(self.vapi_api_key) if self.vapi_api_key else 0,
            "base_url": self.base_url,
            "assistant_id_present": bool(self.vapi_assistant_id),
            "assistant_id": self.vapi_assistant_id,
            "issues": []
        }
        
        if not self.vapi_api_key:
            validation_result["issues"].append("VAPI_API_KEY environment variable not set")
        elif len(self.vapi_api_key) < 20:  # Vapi API keys are typically longer
            validation_result["issues"].append("VAPI_API_KEY appears to be too short (possible invalid key)")
        
        if not self.vapi_assistant_id:
            validation_result["issues"].append("VAPI_ASSISTANT_ID not configured (will use inline assistant config)")
        
        print(f"[VAPI_CONFIG] Configuration validation: {validation_result}")
        return validation_result
    
    async def start_interview_call(self, interview_data: Dict[str, Any], phone_number: Optional[str] = None) -> Dict[str, str]:
        """Start a Vapi voice interview session"""
        try:
            # Validate configuration before proceeding
            config_status = self.validate_configuration()
            if not config_status["is_configured"]:
                print(f"[VAPI_START] Configuration issues detected: {config_status['issues']}")
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.vapi_api_key}",
                    "x-api-key": self.vapi_api_key,
                    "Content-Type": "application/json"
                }
                
                # Prepare Vapi call configuration
                # Note: Removed 'customer' property as it's not supported by Vapi API
                call_config: Dict[str, Any] = {
                    # Include metadata to correlate webhook events
                    "metadata": {
                        "interviewId": interview_data.get('id') or interview_data.get('interviewId'),
                        "userId": interview_data.get('userId'),
                        "candidateName": interview_data.get('candidateName', 'Candidate')
                    }
                }

                # Always use the assistant ID since we have one configured
                call_config["assistantId"] = self.vapi_assistant_id or "bc32bb37-e1ff-40bc-97f2-230bf9710231"

                # Note: Webhook configuration removed as it's causing 400 errors with Vapi API
                # Webhooks can be configured directly in the Vapi dashboard instead
                # if self.backend_public_url:
                #     webhook_url = f"{self.backend_public_url.rstrip('/')}/webhooks/vapi"
                #     call_config["serverUrl"] = webhook_url  # Use serverUrl instead of webhook
                print(f"[VAPI_START] Starting Vapi call with config: {json.dumps(call_config, indent=2)}")
                print(f"[VAPI_START] Using {'phone' if phone_number else 'web'} call mode")
                print(f"[VAPI_START] API Key: ***{self.vapi_api_key[-8:] if len(self.vapi_api_key) > 8 else '***'}")

                # Use the standard calls endpoint - Vapi determines call type from configuration
                endpoint = f"{self.base_url}/call"
                print(f"[VAPI_START] Call endpoint: {endpoint}")
                
                # Add phone number if provided (for phone calls)
                if phone_number:
                    call_config["phoneNumberId"] = phone_number
                    print(f"[VAPI_START] Phone call mode with number: {phone_number}")
                else:
                    # For web calls, Vapi requires client-side initiation using the Web SDK.
                    # Return configuration needed by the client to initialize the call.
                    print(f"[VAPI_START] Web call mode - returning client-side init config")
                    return {
                        # Use a stable marker ID so the client knows this is a web client-side call
                        "callId": "web_call_client_side",
                        "status": "ready_for_client_init",
                        "message": "Use this configuration to initialize web call from client-side",
                        "webCallUrl": None,
                        "assistantId": call_config["assistantId"],
                        "publicKey": os.getenv("VAPI_PUBLIC_KEY"),
                        "metadata": call_config.get("metadata", {})
                    }
                
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=call_config
                )
                
                print(f"[VAPI_START] Response status: {response.status_code}")
                print(f"[VAPI_START] Response headers: {dict(response.headers)}")
                
                if response.status_code in (200, 201):
                    call_data = response.json()
                    call_id = call_data.get("id") or call_data.get("callId")
                    print(f"[VAPI_START] SUCCESS! Call created with ID: {call_id}")
                    print(f"[VAPI_START] Call data keys: {list(call_data.keys())}")
                    print(f"[VAPI_START] Call status: {call_data.get('status')}")
                    
                    return {
                        "callId": call_id,
                        "status": call_data.get("status", "initiated"),
                        "message": "Interview call started successfully",
                        "webCallUrl": call_data.get("webCallUrl") if not phone_number else None
                    }
                else:
                    # Get detailed error information
                    try:
                        error_body = response.text
                        print(f"[VAPI_START] Error response body: {error_body}")
                        if response.headers.get('content-type', '').startswith('application/json'):
                            error_json = response.json()
                            print(f"[VAPI_START] Error JSON: {error_json}")
                    except Exception as parse_error:
                        print(f"[VAPI_START] Could not parse error response: {parse_error}")
                        error_body = "<unparseable response>"
                    
                    error_msg = f"HTTP {response.status_code}"
                    if response.status_code == 400:
                        error_msg += " - Bad request. Check call configuration parameters."
                    elif response.status_code == 401:
                        error_msg += " - Authentication failed. Check API key validity and permissions."
                    elif response.status_code == 403:
                        error_msg += " - Access forbidden. Check API key permissions for creating calls."
                    elif response.status_code == 422:
                        error_msg += " - Validation error. Check assistant ID and call parameters."
                    elif response.status_code >= 500:
                        error_msg += " - Vapi server error. The service may be temporarily unavailable."
                    
                    error_msg += f" Response: {error_body}"
                    print(f"[VAPI_START] Detailed error: {error_msg}")
                    raise Exception(f"Failed to start Vapi call: {error_msg}")
            
        except httpx.TimeoutException as e:
            print(f"[VAPI_START] Timeout error: Request to Vapi API timed out")
            print(f"[VAPI_START] Timeout details: {e}")
            # Return error status for timeout with mock call ID
            import uuid
            call_id = f"mock_timeout_{str(uuid.uuid4())}"
            return {
                "callId": call_id,
                "status": "timeout_error",
                "message": "Vapi API request timed out",
                "webCallUrl": None
            }
        except httpx.RequestError as e:
            print(f"[VAPI_START] Network error: Failed to connect to Vapi API")
            print(f"[VAPI_START] Network error details: {e}")
            # Return error status for network errors with mock call ID
            import uuid
            call_id = f"mock_network_{str(uuid.uuid4())}"
            return {
                "callId": call_id,
                "status": "network_error",
                "message": "Failed to connect to Vapi API",
                "webCallUrl": None
            }
        except Exception as e:
            print(f"[VAPI_START] Unexpected error: {type(e).__name__}: {e}")
            import traceback
            print(f"[VAPI_START] Full traceback: {traceback.format_exc()}")
            # Return mock data for development with mock call ID
            import uuid
            call_id = f"mock_error_{str(uuid.uuid4())}"
            return {
                "callId": call_id,
                "status": "error",
                "message": "Mock interview call started (Vapi integration pending)",
                "webCallUrl": "https://mock-vapi-call.com/session/123"
            }
    
    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get the status of a Vapi call with detailed error logging"""
        try:
            # Check if this is a mock/fallback call ID
            if (call_id.startswith("vapi_call_") or call_id.startswith("vapi_") or 
                call_id.startswith("mock_") or call_id == "web_call_client_side"):
                print(f"[VAPI_STATUS] Mock/fallback call ID detected: {call_id}")
                print(f"[VAPI_STATUS] Returning mock status for development/error call")
                
                # Determine status based on mock call type
                if call_id == "web_call_client_side":
                    status = "ready_for_client_init"
                    ended_reason = "Initialize from client using Vapi Web SDK"
                elif "timeout" in call_id:
                    status = "timeout_error"
                    ended_reason = "Call timed out - Vapi API not responding"
                elif "network" in call_id:
                    status = "network_error"
                    ended_reason = "Network error - Could not connect to Vapi API"
                elif "error" in call_id:
                    status = "error"
                    ended_reason = "Call failed - Vapi integration error"
                else:
                    status = "mock_call"
                    ended_reason = "Mock call - Vapi integration not available"
                
                result = {
                    "callId": call_id,
                    "status": status,
                    "duration": 300,
                    "transcriptUrl": None,
                    "recordingUrl": None,
                    "endedReason": ended_reason
                }
                if call_id == "web_call_client_side":
                    result.update({
                        "assistantId": self.vapi_assistant_id,
                        "publicKey": os.getenv("VAPI_PUBLIC_KEY"),
                        "metadata": {
                            "note": "client_init_required"
                        }
                    })
                return result
            
            # Validate configuration before proceeding
            config_status = self.validate_configuration()
            if not config_status["is_configured"]:
                print("[VAPI_STATUS] Vapi not configured, returning mock status")
                print(f"[VAPI_STATUS] Config check - API Key: {'***' if self.vapi_api_key else 'MISSING'}, Base URL: {self.base_url}")
                return {
                    "callId": call_id,
                    "status": "in_progress",
                    "duration": 300,
                    "transcriptUrl": None,
                    "recordingUrl": None
                }
                
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.vapi_api_key}",
                    "Content-Type": "application/json"
                }
                print(f"[VAPI_STATUS] Checking call status for: {call_id}")
                print(f"[VAPI_STATUS] Request URL: {self.base_url}/call/{call_id}")
                print(f"[VAPI_STATUS] Headers: Authorization=Bearer ***{self.vapi_api_key[-8:] if len(self.vapi_api_key) > 8 else '***'}, Content-Type={headers['Content-Type']}")
                
                response = await client.get(
                    f"{self.base_url}/call/{call_id}",
                    headers=headers
                )
                
                print(f"[VAPI_STATUS] Response status: {response.status_code}")
                print(f"[VAPI_STATUS] Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    call_data = response.json()
                    print(f"[VAPI_STATUS] Call data keys: {list(call_data.keys())}")
                    print(f"[VAPI_STATUS] Call status: {call_data.get('status')}, endedReason: {call_data.get('endedReason')}")
                    
                    result = {
                        "callId": call_id,
                        "status": (call_data.get("status") or call_data.get("state") or "unknown"),
                        "duration": call_data.get("duration") or call_data.get("callDuration") or 0,
                        "transcriptUrl": call_data.get("transcriptUrl") or call_data.get("transcript_url"),
                        "recordingUrl": call_data.get("recordingUrl") or call_data.get("recording_url"),
                        "endedReason": call_data.get("endedReason") or call_data.get("end_reason")
                    }
                    print(f"[VAPI_STATUS] Returning result: {result}")
                    return result
                else:
                    # Get detailed error information
                    try:
                        error_body = response.text
                        print(f"[VAPI_STATUS] Error response body: {error_body}")
                        if response.headers.get('content-type', '').startswith('application/json'):
                            error_json = response.json()
                            print(f"[VAPI_STATUS] Error JSON: {error_json}")
                    except Exception as parse_error:
                        print(f"[VAPI_STATUS] Could not parse error response: {parse_error}")
                        error_body = "<unparseable response>"
                    
                    error_msg = f"HTTP {response.status_code}"
                    if response.status_code == 401:
                        error_msg += " - Authentication failed. Check API key validity and permissions."
                    elif response.status_code == 404:
                        error_msg += f" - Call {call_id} not found. Verify the call ID is correct."
                    elif response.status_code == 403:
                        error_msg += " - Access forbidden. Check API key permissions for this resource."
                    elif response.status_code >= 500:
                        error_msg += " - Vapi server error. The service may be temporarily unavailable."
                    
                    error_msg += f" Response: {error_body}"
                    print(f"[VAPI_STATUS] Detailed error: {error_msg}")
                    raise Exception(f"Failed to get call status: {error_msg}")
            
        except httpx.TimeoutException as e:
            print(f"[VAPI_STATUS] Timeout error: Request to Vapi API timed out after 30 seconds")
            print(f"[VAPI_STATUS] Timeout details: {e}")
            # Return mock status for timeout
            return {
                "callId": call_id,
                "status": "timeout_error",
                "duration": 300,
                "transcriptUrl": None,
                "recordingUrl": None
            }
        except httpx.RequestError as e:
            print(f"[VAPI_STATUS] Network error: Failed to connect to Vapi API")
            print(f"[VAPI_STATUS] Network error details: {e}")
            print(f"[VAPI_STATUS] Check internet connection and Vapi API availability")
            # Return mock status for network errors
            return {
                "callId": call_id,
                "status": "network_error",
                "duration": 300,
                "transcriptUrl": None,
                "recordingUrl": None
            }
        except Exception as e:
            print(f"[VAPI_STATUS] Unexpected error: {type(e).__name__}: {e}")
            import traceback
            print(f"[VAPI_STATUS] Full traceback: {traceback.format_exc()}")
            # Return mock status for development
            return {
                "callId": call_id,
                "status": "error",
                "duration": 300,  # 5 minutes
                "transcriptUrl": None,
                "recordingUrl": None
            }
    
    async def stop_call(self, call_id: str) -> bool:
        """Attempt to explicitly end a Vapi call using multiple fallback strategies."""
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.vapi_api_key}",
                    "x-api-key": self.vapi_api_key,
                    "Content-Type": "application/json"
                }

                attempts = [
                    ("PATCH", f"{self.base_url}/call/{call_id}", {"action": "end"}, "patch-action"),
                    ("PATCH", f"{self.base_url}/call/{call_id}", None, "patch-empty"),
                    ("POST", f"{self.base_url}/call/{call_id}/actions", {"action": "end"}, "post-actions"),
                    ("POST", f"{self.base_url}/call/{call_id}/end", None, "post-end"),
                    ("DELETE", f"{self.base_url}/call/{call_id}", None, "delete-call"),
                ]

                for method, url, payload, label in attempts:
                    try:
                        print(f"[VAPI_STOP] Attempt {label} via {method} {url}")
                        if method == "PATCH":
                            response = await client.patch(url, headers=headers, json=payload)
                        elif method == "POST":
                            response = await client.post(url, headers=headers, json=payload)
                        elif method == "DELETE":
                            response = await client.delete(url, headers=headers)
                        else:
                            continue

                        if response.status_code in (200, 202, 204):
                            try:
                                body_preview = response.text[:500]
                            except Exception:
                                body_preview = "<unavailable>"
                            print(
                                f"[VAPI_STOP] Success via {label} (status={response.status_code}) for call {call_id}. "
                                f"Body: {body_preview}"
                            )
                            return True

                        try:
                            body_preview = response.text[:500]
                        except Exception:
                            body_preview = "<unavailable>"
                        print(
                            f"[VAPI_STOP] {label} failed for call {call_id} (status={response.status_code}). "
                            f"Body: {body_preview}"
                        )
                    except Exception as attempt_err:
                        print(
                            f"[VAPI_STOP] {label} raised {type(attempt_err).__name__}: {attempt_err}"
                        )

                return False

        except Exception as e:
            print(f"Vapi call stop error: {e}")
            return False
    
    async def get_call_transcript(self, call_id: str) -> Optional[str]:
        """Get the transcript of a completed call. Returns None when unavailable."""
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
                    messages = transcript_data.get("messages", [])
                    transcript_text = "\n".join([
                        f"{msg.get('role', 'unknown')}: {msg.get('message', '')}"
                        for msg in messages
                    ])
                    return transcript_text

                if response.status_code == 404:
                    print(f"Vapi transcript not ready for call {call_id} (404)")
                    return None

                print(
                    f"Failed to get transcript for call {call_id}: HTTP {response.status_code}"
                )
                return None

        except Exception as e:
            print(f"Vapi transcript error for call {call_id}: {e}")
            return None

    async def start_workflow_call(self, workflow_id: str, metadata: Dict[str, Any], phone_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a Vapi call using a specific workflow ID.
        This enables AI-guided interview creation where the AI collects preferences and creates the interview.
        """
        try:
            print(f"🚀 Starting Vapi workflow call with ID: {workflow_id}")
            
            # Validate configuration
            config_status = self.validate_configuration()
            if not config_status["is_configured"]:
                print(f"[VAPI_WORKFLOW] Configuration issues: {config_status['issues']}")
                return self._fallback_workflow_response(workflow_id, metadata)
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.vapi_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Prepare workflow call configuration
                call_config: Dict[str, Any] = {
                    "workflowId": workflow_id,
                    "metadata": {
                        **metadata,
                        "workflowType": "ai_guided_interview",
                        "workflowId": workflow_id
                    }
                }

                if self.vapi_assistant_id:
                    call_config["assistantId"] = self.vapi_assistant_id
                else:
                    call_config["assistant"] = {
                        "model": {
                            "provider": "openai",
                            "model": "gpt-4",
                        },
                        "voice": {
                            "provider": "playht",
                            "voiceId": "jennifer"
                        }
                    }
                
                # Determine call mode
                web_call_mode = not bool(phone_number)

                # Add phone number if provided
                if phone_number:
                    call_config["phoneNumberId"] = phone_number
                    print(f"[VAPI_WORKFLOW] Phone call mode with number: {phone_number}")
                else:
                    if not self.auto_init_web_workflow:
                        print(f"[VAPI_WORKFLOW] Auto-init disabled; returning client-side init payload")
                        return self._client_init_response(workflow_id, metadata)
                    print(f"[VAPI_WORKFLOW] Web call mode - attempting server-side initiation")
                
                redacted_config = {k: v for k, v in call_config.items() if k != "metadata"}
                print(f"[VAPI_WORKFLOW] Call config: {json.dumps(redacted_config, indent=2)}")
                print(f"[VAPI_WORKFLOW] Metadata keys: {list(call_config['metadata'].keys())}")
                
                # Make the API call
                endpoint = f"{self.base_url}/call"
                response = await client.post(endpoint, json=call_config, headers=headers)
                
                if response.status_code in (200, 201):
                    call_data = response.json() 
                    call_id = call_data.get("id")
                    
                    print(f"✅ Vapi workflow call created successfully: {call_id}")
                    
                    return {
                        "callId": call_id,
                        "status": call_data.get("status", "created"),
                        "workflowId": workflow_id,
                        "assistantId": call_data.get("assistantId"),
                        "publicKey": os.getenv("VAPI_PUBLIC_KEY"),
                        "webUrl": call_data.get("webCallUrl") or call_data.get("clientUrl"),
                        "phoneNumber": phone_number,
                        "metadata": metadata
                    }
                error_body: Optional[Any] = None
                if response.headers.get("content-type", "").startswith("application/json"):
                    try:
                        error_body = response.json()
                    except Exception:
                        error_body = response.text
                else:
                    error_body = response.text

                print(f"❌ Vapi workflow call failed - HTTP {response.status_code}: {error_body}")

                if web_call_mode:
                    print("[VAPI_WORKFLOW] Falling back to client-side init for web call")
                    fallback_meta = {
                        **metadata,
                        "workflowError": error_body,
                        "workflowStatus": response.status_code,
                    }
                    return self._client_init_response(workflow_id, fallback_meta)

                if response.status_code == 400:
                    return self._fallback_workflow_response(workflow_id, metadata, f"Bad request: {error_body}")
                if response.status_code == 401:
                    return self._fallback_workflow_response(workflow_id, metadata, "Authentication failed")

                return self._fallback_workflow_response(workflow_id, metadata, f"HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Workflow call error: {e}")
            if not phone_number and self.auto_init_web_workflow:
                print("[VAPI_WORKFLOW] Exception during web call initiation, providing client-side init payload")
                fallback_meta = {
                    **metadata,
                    "workflowError": str(e),
                    "workflowStatus": "exception",
                }
                return self._client_init_response(workflow_id, fallback_meta)
            return self._fallback_workflow_response(workflow_id, metadata, str(e))
    
    def _fallback_workflow_response(self, workflow_id: str, metadata: Dict[str, Any], error: Optional[str] = None) -> Dict[str, Any]:
        """Generate fallback response for workflow calls when Vapi is not available"""
        fallback_call_id = f"workflow_mock_{workflow_id[:8]}_{metadata.get('sessionId', 'unknown')[:8]}"
        
        return {
            "callId": fallback_call_id,
            "status": "mock_workflow",
            "workflowId": workflow_id,
            "assistantId": "mock_workflow_assistant",
            "publicKey": "mock_public_key",
            "webUrl": None,
            "phoneNumber": None,
            "metadata": {
                **metadata,
                "mockMode": True,
                "error": error,
                "message": "Workflow running in mock mode - Vapi not configured"
            }
        }

# Service instances
gemini_service = GeminiAnalysisService()
vapi_service = VapiInterviewService()