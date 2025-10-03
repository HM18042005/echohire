#!/usr/bin/env python3
"""
Test script to verify transcript generation functionality
"""

import asyncio
from ai_services import VapiInterviewService


async def _run_transcript_generation() -> None:
    """Test the transcript generation with mock data"""
    vapi_service = VapiInterviewService()
    
    print("Testing transcript generation...")
    print("=" * 50)
    
    # Test with a mock call ID (this should return our enhanced mock transcript)
    test_call_id = "mock_call_123"
    
    try:
        transcript = await vapi_service.get_call_transcript(test_call_id)
        
        if transcript:
            print(f"✅ Transcript generated successfully!")
            print(f"📝 Transcript length: {len(transcript)} characters")
            print(f"🎯 First 200 characters:")
            print("-" * 30)
            print(transcript[:200] + "...")
            print("-" * 30)
            
            # Check if it contains key elements
            has_interviewer = "Interviewer:" in transcript
            has_candidate = "Candidate:" in transcript
            has_technical_content = any(word in transcript.lower() for word in [
                "javascript", "react", "python", "technical", "development", "project"
            ])
            
            print(f"✅ Contains interviewer dialogue: {has_interviewer}")
            print(f"✅ Contains candidate responses: {has_candidate}")
            print(f"✅ Contains technical content: {has_technical_content}")
            
            if has_interviewer and has_candidate and has_technical_content:
                print("\n🎉 Mock transcript generation is working perfectly!")
                print("   This transcript will provide rich content for AI feedback analysis.")
            else:
                print("\n⚠️  Mock transcript may need enhancement for better AI analysis.")
                
        else:
            print("❌ No transcript returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_transcript_generation():
    asyncio.run(_run_transcript_generation())


if __name__ == "__main__":
    asyncio.run(_run_transcript_generation())