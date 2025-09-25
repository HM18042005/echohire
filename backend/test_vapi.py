#!/usr/bin/env python3
"""
Test Vapi Integration
Run this to test if Vapi API calls are working correctly
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from ai_services import vapi_service

async def test_vapi_integration():
    """Test Vapi integration with proper error handling"""
    
    print("🧪 Testing Vapi Integration")
    print("=" * 50)
    
    # Test configuration validation
    print("\n1. Configuration Validation:")
    config_status = vapi_service.validate_configuration()
    print(f"   Configuration OK: {config_status['is_configured']}")
    
    if not config_status['is_configured']:
        print("❌ Configuration issues found:")
        for issue in config_status['issues']:
            print(f"   - {issue}")
        return False
    
    # Test call creation
    print("\n2. Testing Call Creation:")
    try:
        mock_interview_data = {
            "id": "test-interview-123",
            "userId": "test-user-456",
            "candidateName": "Test Candidate",
            "type": "technical",
            "jobTitle": "Software Engineer"
        }
        
        print("   Creating test Vapi call...")
        vapi_response = await vapi_service.start_interview_call(mock_interview_data)
        
        print(f"   Response: {json.dumps(vapi_response, indent=2)}")
        
        if vapi_response.get("callId"):
            call_id = vapi_response["callId"]
            print(f"   ✅ Call created successfully: {call_id}")
            
            # Test call status check
            print(f"\n3. Testing Call Status Check:")
            print(f"   Checking status for call: {call_id}")
            
            status_response = await vapi_service.get_call_status(call_id)
            print(f"   Status response: {json.dumps(status_response, indent=2)}")
            
            if status_response.get("status"):
                print(f"   ✅ Status check successful: {status_response['status']}")
                return True
            else:
                print("   ❌ Status check failed")
                return False
        else:
            print("   ❌ Call creation failed - no call ID returned")
            return False
    
    except Exception as e:
        print(f"   ❌ Test failed with error: {e}")
        return False

async def main():
    success = await test_vapi_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Vapi integration test PASSED!")
        print("Your Vapi configuration is working correctly.")
    else:
        print("❌ Vapi integration test FAILED!")
        print("Please check your API key and configuration.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())