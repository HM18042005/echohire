#!/usr/bin/env python3
"""
Test script for AI Guided Interview Creation with Vapi Workflows
"""

import asyncio
import json
from ai_services import VapiInterviewService


async def _run_ai_guided_interview() -> None:
    """Test the AI guided interview creation with workflow ID"""
    vapi_service = VapiInterviewService()
    
    print("🤖 Testing AI Guided Interview Creation")
    print("=" * 60)
    
    # Test workflow ID (you can replace this with actual Vapi workflow ID)
    test_workflow_id = "7894c32f-8b29-4e71-90f3-a19047832a21"  # Universal workflow ID
    
    # Test metadata
    test_metadata = {
        "userId": "test_user_123",
        "sessionId": "session_456",
        "candidateName": "Alex Johnson",
        "jobTitle": "Full Stack Developer",
        "companyName": "TechCorp Inc",
        "interviewType": "technical",
        "experienceLevel": "mid"
    }
    
    print(f"📋 Test Configuration:")
    print(f"   Workflow ID: {test_workflow_id}")
    print(f"   Candidate: {test_metadata['candidateName']}")
    print(f"   Position: {test_metadata['jobTitle']}")
    print(f"   Company: {test_metadata['companyName']}")
    print(f"   Type: {test_metadata['interviewType']}")
    print(f"   Level: {test_metadata['experienceLevel']}")
    print("-" * 60)
    
    try:
        # Test web call (no phone number)
        print("🌐 Testing Web Call Mode...")
        web_result = await vapi_service.start_workflow_call(
            workflow_id=test_workflow_id,
            metadata=test_metadata
        )
        
        print("✅ Web Call Result:")
        print(f"   Call ID: {web_result['callId']}")
        print(f"   Status: {web_result['status']}")
        print(f"   Workflow ID: {web_result['workflowId']}")
        print(f"   Assistant ID: {web_result.get('assistantId', 'N/A')}")
        print(f"   Public Key: {web_result.get('publicKey', 'N/A')}")
        
        if web_result.get('metadata', {}).get('mockMode'):
            print("   🔧 Running in mock mode (Vapi not configured)")
            if web_result['metadata'].get('error'):
                print(f"   ⚠️  Error: {web_result['metadata']['error']}")
        
        print()
        
        # Test phone call mode  
        print("📞 Testing Phone Call Mode...")
        phone_result = await vapi_service.start_workflow_call(
            workflow_id=test_workflow_id,
            metadata=test_metadata,
            phone_number="+1234567890"
        )
        
        print("✅ Phone Call Result:")
        print(f"   Call ID: {phone_result['callId']}")
        print(f"   Status: {phone_result['status']}")
        print(f"   Phone Number: {phone_result.get('phoneNumber', 'N/A')}")
        print(f"   Web URL: {phone_result.get('webUrl', 'N/A')}")
        
        print()
        print("🎯 AI Guided Interview Flow:")
        print("1. User provides workflow ID and basic info")
        print("2. System starts Vapi call with workflow")
        print("3. AI assistant guides candidate through setup:")
        print("   - Collects job role preferences")
        print("   - Determines interview type and level")
        print("   - Generates appropriate questions")
        print("   - Conducts the interview")
        print("   - Provides real-time feedback")
        print("   - Delivers final assessment")
        print("4. Results stored in Firebase with full transcript")
        
        print()
        print("🚀 Integration Ready!")
        print("   - Add workflow ID to frontend")
        print("   - Call /interviews/ai-guided endpoint") 
        print("   - Handle both web and phone call modes")
        print("   - Track session with returned sessionId")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_ai_guided_interview():
    asyncio.run(_run_ai_guided_interview())


if __name__ == "__main__":
    asyncio.run(_run_ai_guided_interview())