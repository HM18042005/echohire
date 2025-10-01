"""
Vapi AI Workflows for Conversational Interview Setup and Execution
================================================================

This module contains the InterviewSetupAssistant class that handles the complete
conversational flow for setting up and conducting mock interviews using Vapi AI.

The flow includes:
1. Greeting and preference gathering (Job Role, Interview Type, Experience Level)
2. Dynamic question generation using Gemini API
3. Seamless transition to interview coaching
4. Interactive feedback after each answer
5. Comprehensive conclusion and summary
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import os

# Optional AI imports - graceful fallback if not available
try:
    import google.generativeai as genai  # type: ignore
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False
from datetime import datetime


class InterviewPhase(Enum):
    """Enum representing different phases of the interview process"""
    GREETING = "greeting"
    COLLECTING_JOB_ROLE = "collecting_job_role"
    COLLECTING_INTERVIEW_TYPE = "collecting_interview_type"
    COLLECTING_EXPERIENCE_LEVEL = "collecting_experience_level"
    GENERATING_QUESTIONS = "generating_questions"
    INTERVIEW_STARTING = "interview_starting"
    ASKING_QUESTION = "asking_question"
    LISTENING_FOR_ANSWER = "listening_for_answer"
    PROVIDING_FEEDBACK = "providing_feedback"
    INTERVIEW_COMPLETE = "interview_complete"


@dataclass
class UserPreferences:
    """Data class to store user interview preferences"""
    job_role: Optional[str] = None
    interview_type: Optional[str] = None
    experience_level: Optional[str] = None


@dataclass
class InterviewQuestion:
    """Data class representing an interview question"""
    id: int
    question: str
    category: str
    difficulty: str


@dataclass
class InterviewSession:
    """Data class to track the complete interview session"""
    session_id: str
    user_preferences: UserPreferences
    questions: List[InterviewQuestion]
    current_question_index: int = 0
    phase: InterviewPhase = InterviewPhase.GREETING
    answers: List[str] = None
    feedback: List[str] = None
    
    def __post_init__(self):
        if self.answers is None:
            self.answers = []
        if self.feedback is None:
            self.feedback = []


class InterviewSetupAssistant:
    """
    Main class for handling the conversational interview setup and execution flow.
    
    This assistant manages the entire conversation from initial greeting through
    question generation to interview completion with feedback.
    """
    
    def __init__(self, gemini_api_key: str):
        """
        Initialize the InterviewSetupAssistant.
        
        Args:
            gemini_api_key (str): API key for Google Gemini AI
        """
        self.gemini_api_key = gemini_api_key
        self.model = None
        self.model_name: Optional[str] = None

        if GENAI_AVAILABLE and gemini_api_key and gemini_api_key != "your-gemini-api-key-here":
            try:
                genai.configure(api_key=gemini_api_key)
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
                        print(f"[WORKFLOW_GEMINI] Using model: {model_name}")
                        break
                    except Exception as model_error:
                        print(f"[WORKFLOW_GEMINI] Model {model_name} unavailable ({model_error}). Trying next...")
                        continue
            except Exception as configure_err:
                print(f"[WORKFLOW_GEMINI] Gemini init failed: {configure_err}")

        if self.model is None:
            print("[WORKFLOW_GEMINI] Gemini model unavailable. Workflow assistant will use fallback responses.")
        self.sessions: Dict[str, InterviewSession] = {}
    
    def create_session(self, session_id: str) -> InterviewSession:
        """
        Create a new interview session.
        
        Args:
            session_id (str): Unique identifier for the session
            
        Returns:
            InterviewSession: The created session object
        """
        session = InterviewSession(
            session_id=session_id,
            user_preferences=UserPreferences(),
            questions=[],
            phase=InterviewPhase.GREETING
        )
        self.sessions[session_id] = session
        return session
    
    def get_system_prompt(self, phase: InterviewPhase, context: Dict[str, Any] = None) -> str:
        """
        Generate system prompts based on the current interview phase.
        
        Args:
            phase (InterviewPhase): Current phase of the interview
            context (Dict[str, Any]): Additional context information
            
        Returns:
            str: The appropriate system prompt
        """
        if context is None:
            context = {}
            
        prompts = {
            InterviewPhase.GREETING: """
You are an AI Interview Coach for EchoHire. You are friendly, professional, and encouraging. 

Your task is to conduct a conversational interview setup and then perform a mock interview.

Start by greeting the user warmly and explaining that you'll ask them three quick questions to personalize their interview experience. Be conversational and natural.

Then ask for their Job Role first. Wait for their response before proceeding.

Keep your responses concise but warm. Speak as if you're having a natural conversation.
""",

            InterviewPhase.COLLECTING_JOB_ROLE: """
You are collecting the user's job role. Listen carefully to their response and acknowledge it positively.

Then ask about their Interview Type. Explain the options clearly:
- Technical (coding, system design, technical skills)
- Behavioral (situational questions, soft skills, culture fit)  
- Mixed (combination of technical and behavioral)

Wait for their response before proceeding.
""",

            InterviewPhase.COLLECTING_INTERVIEW_TYPE: """
You are collecting the interview type preference. Acknowledge their choice positively.

Now ask about their Experience Level:
- Entry Level (0-2 years of experience)
- Mid Level (3-5 years of experience)  
- Senior Level (6+ years of experience)

Wait for their response before proceeding.
""",

            InterviewPhase.COLLECTING_EXPERIENCE_LEVEL: """
You are collecting the experience level. Acknowledge their choice and thank them for providing all the information.

Tell them you're now generating a personalized interview specifically for their profile. Mention their job role and level to show you're personalizing it.

Be encouraging and set expectations that you'll be starting the mock interview shortly.
""",

            InterviewPhase.GENERATING_QUESTIONS: """
You are in the process of generating questions. Inform the user that you're creating their personalized interview questions and that this will take just a moment.

Be encouraging and build anticipation for the upcoming interview.
""",

            InterviewPhase.INTERVIEW_STARTING: """
You are about to start the mock interview. Welcome the user to their personalized interview session.

Explain briefly:
- You'll ask them {total_questions} questions
- After each answer, you'll provide constructive feedback
- They should answer as if this were a real interview
- Take their time and be thoughtful

Then announce you're starting with the first question and ask it clearly.

The first question is: "{current_question}"

Be encouraging and professional.
""",

            InterviewPhase.ASKING_QUESTION: """
You are asking an interview question. Present the question clearly and encourage the candidate to take their time.

Current question: "{current_question}"

Be supportive and remind them to answer as thoroughly as they'd like.
""",

            InterviewPhase.PROVIDING_FEEDBACK: """
You are providing feedback on the user's answer. Be constructive, specific, and encouraging.

The question was: "{question}"
Their answer was: "{answer}"

Provide feedback that:
- Acknowledges what they did well
- Offers specific suggestions for improvement
- Is encouraging and supportive
- Relates to real interview scenarios

Keep feedback concise but valuable. Then transition to the next question if there are more, or to the conclusion if this was the final question.
""",

            InterviewPhase.INTERVIEW_COMPLETE: """
You are concluding the interview. Congratulate the user on completing their mock interview.

Provide a brief overall summary highlighting:
- Their overall performance
- Key strengths demonstrated
- Areas for improvement
- Encouragement for their job search

Thank them for using EchoHire and wish them success in their interviews.

End the call on a positive, encouraging note.
"""
        }
        
        prompt = prompts.get(phase, "You are a helpful AI assistant.")
        
        # Format the prompt with context if provided
        if context:
            try:
                prompt = prompt.format(**context)
            except KeyError:
                # If formatting fails, use the prompt as-is
                pass
                
        return prompt
    
    async def generate_interview_questions(self, preferences: UserPreferences) -> List[InterviewQuestion]:
        """
        Generate personalized interview questions using Gemini API.
        
        Args:
            preferences (UserPreferences): User's interview preferences
            
        Returns:
            List[InterviewQuestion]: Generated interview questions
        """
        prompt = f"""
Generate exactly 5 interview questions for the following profile:

Job Role: {preferences.job_role}
Interview Type: {preferences.interview_type}
Experience Level: {preferences.experience_level}

Requirements:
1. Questions should be appropriate for the {preferences.experience_level} level
2. Questions should match the {preferences.interview_type} interview type
3. Questions should be relevant to the {preferences.job_role} role
4. Include a mix of difficulty levels
5. Make questions realistic and commonly asked

For each question, provide:
- The question text
- A category (e.g., "Technical Skills", "Problem Solving", "Behavioral", "Experience")
- A difficulty level ("Easy", "Medium", "Hard")

Format your response as a JSON array with this structure:
[
  {{
    "question": "Tell me about yourself and your background in {preferences.job_role}.",
    "category": "General",
    "difficulty": "Easy"
  }},
  ...
]

Make sure the JSON is valid and contains exactly 5 questions.
"""

        try:
            if not self.model:
                # Fallback when AI is not available
                return self._get_fallback_questions(preferences)
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            questions_text = response.text.strip()
            
            # Clean up the response to extract JSON
            if "```json" in questions_text:
                questions_text = questions_text.split("```json")[1].split("```")[0].strip()
            elif "```" in questions_text:
                questions_text = questions_text.split("```")[1].strip()
            
            questions_data = json.loads(questions_text)
            
            # Convert to InterviewQuestion objects
            questions = []
            for i, q_data in enumerate(questions_data):
                question = InterviewQuestion(
                    id=i + 1,
                    question=q_data["question"],
                    category=q_data["category"],
                    difficulty=q_data["difficulty"]
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            # Fallback questions if API fails
            print(f"Error generating questions: {e}")
            return self._get_fallback_questions(preferences)
    
    def _get_fallback_questions(self, preferences: UserPreferences) -> List[InterviewQuestion]:
        """
        Provide fallback questions if the API fails.
        
        Args:
            preferences (UserPreferences): User's interview preferences
            
        Returns:
            List[InterviewQuestion]: Fallback interview questions
        """
        fallback_questions = [
            InterviewQuestion(1, f"Tell me about yourself and your background in {preferences.job_role}.", "General", "Easy"),
            InterviewQuestion(2, f"What interests you most about working as a {preferences.job_role}?", "Motivation", "Easy"),
            InterviewQuestion(3, "Describe a challenging project you've worked on and how you overcame obstacles.", "Problem Solving", "Medium"),
            InterviewQuestion(4, "Where do you see yourself in your career in the next 3-5 years?", "Career Goals", "Medium"),
            InterviewQuestion(5, f"What do you think are the most important skills for a {preferences.job_role}?", "Technical Knowledge", "Medium")
        ]
        
        return fallback_questions
    
    async def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        Process user input and manage the conversation flow.
        
        Args:
            session_id (str): Session identifier
            user_input (str): User's spoken input
            
        Returns:
            Dict[str, Any]: Response containing the AI's reply and session state
        """
        session = self.sessions.get(session_id)
        if not session:
            session = self.create_session(session_id)
        
        response = await self._handle_phase_logic(session, user_input)
        
        return {
            "session_id": session_id,
            "phase": session.phase.value,
            "ai_response": response,
            "session_state": {
                "job_role": session.user_preferences.job_role,
                "interview_type": session.user_preferences.interview_type,
                "experience_level": session.user_preferences.experience_level,
                "current_question": session.current_question_index + 1 if session.questions else 0,
                "total_questions": len(session.questions)
            }
        }
    
    async def _handle_phase_logic(self, session: InterviewSession, user_input: str) -> str:
        """
        Handle the logic for each phase of the conversation.
        
        Args:
            session (InterviewSession): Current session
            user_input (str): User's input
            
        Returns:
            str: AI response for the current phase
        """
        if session.phase == InterviewPhase.GREETING:
            session.phase = InterviewPhase.COLLECTING_JOB_ROLE
            return """Hello! Welcome to EchoHire's AI Interview Coach. I'm excited to help you practice for your upcoming interviews!

I'll start by asking you three quick questions to personalize your interview experience, and then we'll dive into a mock interview with real-time feedback.

Let's begin! What job role are you interviewing for? For example, Software Engineer, Product Manager, Data Scientist, etc."""

        elif session.phase == InterviewPhase.COLLECTING_JOB_ROLE:
            session.user_preferences.job_role = user_input.strip()
            session.phase = InterviewPhase.COLLECTING_INTERVIEW_TYPE
            return f"""Perfect! A {session.user_preferences.job_role} role - that's exciting!

Now, what type of interview would you like to practice? I can help you with:

• Technical interviews - focusing on coding, system design, and technical skills
• Behavioral interviews - situational questions, soft skills, and culture fit
• Mixed interviews - a combination of both technical and behavioral questions

Which type would you prefer?"""

        elif session.phase == InterviewPhase.COLLECTING_INTERVIEW_TYPE:
            session.user_preferences.interview_type = user_input.strip()
            session.phase = InterviewPhase.COLLECTING_EXPERIENCE_LEVEL
            return f"""Great choice! {session.user_preferences.interview_type} interviews are really valuable to practice.

One last question - what's your experience level?

• Entry Level - 0 to 2 years of experience
• Mid Level - 3 to 5 years of experience  
• Senior Level - 6 or more years of experience

This helps me tailor the questions to the right difficulty level for you."""

        elif session.phase == InterviewPhase.COLLECTING_EXPERIENCE_LEVEL:
            session.user_preferences.experience_level = user_input.strip()
            session.phase = InterviewPhase.GENERATING_QUESTIONS
            
            # Generate questions asynchronously
            session.questions = await self.generate_interview_questions(session.user_preferences)
            session.phase = InterviewPhase.INTERVIEW_STARTING
            
            return f"""Perfect! Thank you for that information.

I'm now generating a personalized {session.user_preferences.interview_type} interview specifically designed for a {session.user_preferences.experience_level} {session.user_preferences.job_role}. This will just take a moment...

Excellent! I've created 5 tailored questions for you. 

Welcome to your personalized mock interview! Here's how this will work:
• I'll ask you 5 questions, one at a time
• Take your time to answer each question thoughtfully
• After each answer, I'll provide constructive feedback
• Answer as if this were a real interview - be detailed and specific

Ready? Let's begin with your first question:

{session.questions[0].question}

Take your time and answer as thoroughly as you'd like!"""

        elif session.phase == InterviewPhase.INTERVIEW_STARTING:
            # User answered the first question
            session.answers.append(user_input)
            session.phase = InterviewPhase.PROVIDING_FEEDBACK
            
            feedback = await self._generate_feedback(
                session.questions[session.current_question_index].question,
                user_input,
                session.user_preferences
            )
            session.feedback.append(feedback)
            
            session.current_question_index += 1
            
            if session.current_question_index < len(session.questions):
                session.phase = InterviewPhase.ASKING_QUESTION
                return f"""{feedback}

Great! Let's move on to question {session.current_question_index + 1}:

{session.questions[session.current_question_index].question}"""
            else:
                session.phase = InterviewPhase.INTERVIEW_COMPLETE
                return f"""{feedback}

🎉 Congratulations! You've completed your mock interview!

## Overall Performance Summary

You've successfully answered all 5 questions for the {session.user_preferences.job_role} position. Here's my overall assessment:

**Strengths:** You demonstrated good communication skills and showed relevant experience for a {session.user_preferences.experience_level} level candidate.

**Areas for Improvement:** Continue practicing articulating your thoughts clearly and providing specific examples from your experience.

**Next Steps:** Keep practicing with different types of questions, and remember to prepare specific examples that showcase your skills and achievements.

Thank you for using EchoHire's AI Interview Coach! I hope this practice session has helped boost your confidence. Best of luck with your real interviews - you've got this! 🚀"""

        elif session.phase == InterviewPhase.ASKING_QUESTION:
            # User answered a subsequent question
            session.answers.append(user_input)
            
            feedback = await self._generate_feedback(
                session.questions[session.current_question_index].question,
                user_input,
                session.user_preferences
            )
            session.feedback.append(feedback)
            
            session.current_question_index += 1
            
            if session.current_question_index < len(session.questions):
                return f"""{feedback}

Excellent! Let's continue with question {session.current_question_index + 1}:

{session.questions[session.current_question_index].question}"""
            else:
                session.phase = InterviewPhase.INTERVIEW_COMPLETE
                return f"""{feedback}

🎉 Fantastic! You've completed your mock interview!

## Overall Performance Summary

You've successfully answered all 5 questions for the {session.user_preferences.job_role} position. Here's my overall assessment:

**Strengths:** You showed strong communication skills and provided relevant examples throughout the interview.

**Areas for Improvement:** Keep practicing structuring your answers and providing concrete examples with measurable results.

**Key Takeaway:** You're well-prepared for {session.user_preferences.experience_level} level interviews. Continue building on the strengths you've demonstrated today.

Thank you for practicing with EchoHire! This experience should help you feel more confident in your real interviews. Wishing you all the best in your job search! 🌟"""

        else:
            return "Thank you for using EchoHire's AI Interview Coach! Good luck with your interviews!"
    
    async def _generate_feedback(self, question: str, answer: str, preferences: UserPreferences) -> str:
        """
        Generate constructive feedback for a user's answer.
        
        Args:
            question (str): The interview question
            answer (str): User's answer
            preferences (UserPreferences): User's interview preferences
            
        Returns:
            str: Constructive feedback
        """
        prompt = f"""
Provide constructive interview feedback for this {preferences.experience_level} {preferences.job_role} candidate.

Question: {question}
Answer: {answer}

Provide feedback that:
1. Acknowledges what they did well (be specific)
2. Offers 1-2 concrete suggestions for improvement
3. Is encouraging and supportive
4. Is appropriate for their experience level
5. Keeps the feedback concise (2-3 sentences max)

Focus on practical advice they can use in real interviews.
"""

        try:
            if not self.model:
                # Fallback feedback when AI is not available
                return f"Good answer! You provided relevant information. To strengthen your response, consider adding more specific examples or metrics to demonstrate your impact. Keep up the great work!"
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text.strip()
        except Exception as e:
            # Fallback feedback
            return f"Good answer! You provided relevant information. To strengthen your response, consider adding more specific examples or metrics to demonstrate your impact. Keep up the great work!"
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of the interview session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Dict[str, Any]: Session summary
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "preferences": {
                "job_role": session.user_preferences.job_role,
                "interview_type": session.user_preferences.interview_type,
                "experience_level": session.user_preferences.experience_level
            },
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "category": q.category,
                    "difficulty": q.difficulty
                } for q in session.questions
            ],
            "answers": session.answers,
            "feedback": session.feedback,
            "phase": session.phase.value,
            "completed": session.phase == InterviewPhase.INTERVIEW_COMPLETE
        }


# Example usage and helper functions
def create_vapi_assistant_config(gemini_api_key: str) -> Dict[str, Any]:
    """
    Create a Vapi assistant configuration for the interview setup workflow.
    
    Args:
        gemini_api_key (str): Gemini API key
        
    Returns:
        Dict[str, Any]: Vapi assistant configuration
    """
    assistant = InterviewSetupAssistant(gemini_api_key)
    
    return {
        "model": {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "paula",  # Professional, friendly voice
        },
        "firstMessage": "Hello! Welcome to EchoHire's AI Interview Coach. I'm excited to help you practice for your upcoming interviews! I'll start by asking you three quick questions to personalize your interview experience, and then we'll dive into a mock interview with real-time feedback. Let's begin! What job role are you interviewing for?",
        "systemPrompt": assistant.get_system_prompt(InterviewPhase.GREETING),
        "recordingEnabled": True,
        "endCallMessage": "Thank you for using EchoHire! Good luck with your interviews!",
        "maxDurationSeconds": 1800,  # 30 minutes max
    }


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def test_workflow():
        """Test the interview workflow"""
        assistant = InterviewSetupAssistant(os.getenv("GEMINI_API_KEY", "test-key"))
        
        # Simulate conversation flow
        session_id = "test-session-123"
        
        # Test the complete flow
        responses = [
            await assistant.process_user_input(session_id, ""),  # Initial greeting
            await assistant.process_user_input(session_id, "Software Engineer"),  # Job role
            await assistant.process_user_input(session_id, "Technical"),  # Interview type
            await assistant.process_user_input(session_id, "Mid Level"),  # Experience level
            await assistant.process_user_input(session_id, "I have 4 years of experience..."),  # First answer
        ]
        
        for i, response in enumerate(responses):
            print(f"Response {i + 1}:")
            print(response["ai_response"])
            print("-" * 50)
    
    # Uncomment to test
    # asyncio.run(test_workflow())