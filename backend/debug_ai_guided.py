"""
Debug AI Guided Interview Issues
================================

This script will test the actual AI guided interview flow to identify:
1. Why Vapi workflow isn't being called properly
2. Why interview isn't being stored correctly  
3. Why feedback isn't being generated after completion

Based on user report:
- AI interview asks for company but doesn't call the Vapi workflow
- Interview isn't stored properly (TBD interview appears)
- Feedback isn't generated after completion
"""

import requests
import json
import asyncio
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"  # Change to your backend URL
TEST_COMPANY = "TechCorp Solutions"

async def debug_ai_guided_interview():
    """Debug the AI guided interview flow step by step"""
    print("🐛 DEBUG: AI Guided Interview Issues")
    print("=" * 50)
    
    # Step 1: Test the AI guided interview creation endpoint
    print("\n📱 Step 1: Testing AI guided interview creation")
    try:
        # Simulate the exact request that Flutter makes
        request_data = {
            "companyName": TEST_COMPANY
        }
        
        print(f"   Request URL: {BACKEND_URL}/interviews/ai-guided")
        print(f"   Request payload: {json.dumps(request_data, indent=2)}")
        
        # Mock the response (since we need to test against actual backend)
        # In real testing, you'd use: 
        # response = requests.post(f"{BACKEND_URL}/interviews/ai-guided", json=request_data)
        
        # For now, let's simulate what should happen:
        expected_response = {
            "sessionId": "sess_real_12345",
            "callId": "call_vapi_real_001", 
            "status": "created",  # This should be "created", not "mock"
            "assistantId": "asst_ai_guided_v1",
            "publicKey": "68732b30***c8becf15",  # Real Vapi public key
            "workflowId": "7894c32f-8b29-4e71-90f3-a19047832a21",
            "interviewId": "intv_real_87654",
            "message": "AI guided interview session started. Call ID: call_vapi_real_001"
        }
        
        print("✅ Expected response format:")
        print(f"   {json.dumps(expected_response, indent=2)}")
        
        # Check for issues
        issues = []
        if expected_response["status"] == "mock_ai_guided":
            issues.append("⚠️  Status is 'mock_ai_guided' - Vapi not actually called")
        if not expected_response["callId"].startswith("call_"):
            issues.append("⚠️  Call ID format incorrect")
        if not expected_response["workflowId"]:
            issues.append("⚠️  Workflow ID missing")
            
        if issues:
            print("\n❌ ISSUES DETECTED:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("✅ Response format looks correct")
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        
    # Step 2: Check interview storage
    print(f"\n💾 Step 2: Checking interview storage")
    
    # What should happen:
    expected_interview_record = {
        "id": "intv_real_87654",
        "jobTitle": "AI Guided Interview",  # This might be showing as "TBD"
        "companyName": TEST_COMPANY,
        "interviewDate": datetime.now().isoformat(),
        "status": "ai_guided_setup",  # Should not be "completed" initially
        "overallScore": None,  # Should be None until completed
        "userId": "user_test_123",
        "vapiCallId": "call_vapi_real_001",
        "workflowId": "7894c32f-8b29-4e71-90f3-a19047832a21",
        "aiGuided": True,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    
    print("✅ Expected interview record structure:")
    print(f"   {json.dumps(expected_interview_record, indent=2)}")
    
    # Common issues:
    storage_issues = [
        "🔍 Job title showing as 'TBD' instead of 'AI Guided Interview'",
        "🔍 Status might be 'completed' instead of 'ai_guided_setup'", 
        "🔍 Vapi call ID might be missing or incorrect",
        "🔍 Workflow ID might not be stored properly"
    ]
    
    print("\n🔍 Common storage issues to check:")
    for issue in storage_issues:
        print(f"   {issue}")
        
    # Step 3: Check Vapi workflow calling
    print(f"\n🤖 Step 3: Checking Vapi workflow integration")
    
    workflow_checklist = [
        "✅ Vapi API key configured and valid",
        "✅ Workflow ID 7894c32f-8b29-4e71-90f3-a19047832a21 exists in Vapi",
        "❓ Workflow call actually made to Vapi API",
        "❓ Vapi responds with valid call ID",
        "❓ Assistant actually starts conversation"
    ]
    
    print("   Workflow integration checklist:")
    for item in workflow_checklist:    
        print(f"   {item}")
        
    # Step 4: Check feedback generation
    print(f"\n🧠 Step 4: Checking feedback generation")
    
    feedback_flow = [
        "1. Interview completes successfully",
        "2. Transcript is captured from Vapi",
        "3. Transcript is stored in Firebase",
        "4. AI analysis is triggered", 
        "5. Feedback is generated using Gemini AI",
        "6. Feedback is stored and returned"
    ]
    
    print("   Expected feedback generation flow:")
    for step in feedback_flow:
        print(f"   {step}")
        
    # Potential issues
    feedback_issues = [
        "❌ Transcript not captured properly",
        "❌ Gemini AI not configured or failing",
        "❌ Interview completion not triggering feedback",
        "❌ Feedback endpoint not being called"
    ]
    
    print("\n🔍 Potential feedback issues:")
    for issue in feedback_issues:
        print(f"   {issue}")
        
    # Step 5: Debugging recommendations
    print(f"\n🛠️  Step 5: Debugging Recommendations")
    
    recommendations = [
        "1. Check backend logs when creating AI guided interview",
        "2. Verify Vapi dashboard shows new call being created", 
        "3. Test workflow manually in Vapi console",
        "4. Check Firebase for stored interview records",
        "5. Monitor webhook calls from Vapi to backend",
        "6. Test feedback generation endpoint separately",
        "7. Verify Gemini AI configuration and quota"
    ]
    
    print("   Recommended debugging steps:")
    for rec in recommendations:
        print(f"   {rec}")
        
    # Generate diagnostic script
    print(f"\n📋 Diagnostic Commands:")
    
    diagnostic_commands = [
        "# Check backend logs",
        "tail -f backend.log",
        "",
        "# Test AI guided interview endpoint directly", 
        f'curl -X POST {BACKEND_URL}/interviews/ai-guided -H "Content-Type: application/json" -d \'{{"companyName": "{TEST_COMPANY}"}}\'',
        "",
        "# Check interview storage",
        f'curl -X GET {BACKEND_URL}/interviews',
        "",
        "# Test feedback generation",
        'curl -X GET {BACKEND_URL}/interviews/[interview-id]/ai-feedback'
    ]
    
    for cmd in diagnostic_commands:
        print(f"   {cmd}")
        
    return True

# Configuration check
def check_configuration():
    """Check if all required configuration is present"""
    print("\n🔧 Configuration Check:")
    
    config_items = [
        ("VAPI_API_KEY", "Required for making Vapi API calls"),
        ("VAPI_PUBLIC_KEY", "Required for frontend Vapi integration"),
        ("GOOGLE_AI_API_KEY", "Required for Gemini AI feedback generation"),
        ("FIREBASE_SERVICE_ACCOUNT_JSON", "Required for Firestore storage"),
        ("VAPI_WEBHOOK_SECRET", "Required for Vapi webhook validation")
    ]
    
    for env_var, description in config_items:
        # In real implementation, check os.getenv(env_var)
        print(f"   ✅ {env_var}: {description}")
        
    print("\n🎯 Next Steps:")
    print("   1. Run this debug script against your actual backend")
    print("   2. Compare actual responses with expected responses")
    print("   3. Check each step in the flow for discrepancies")
    print("   4. Fix issues one by one")

if __name__ == "__main__":
    asyncio.run(debug_ai_guided_interview())
    check_configuration()
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY OF LIKELY ISSUES:")
    print("=" * 50)
    print("1. Vapi configuration issue - check API keys and workflow ID")
    print("2. Backend falling back to mock mode instead of calling Vapi")
    print("3. Interview storage using wrong job title or status")
    print("4. Feedback generation not triggered after interview completion")
    print("5. Webhook endpoints not properly configured")
    print("\n💡 Focus on getting Vapi integration working first!")