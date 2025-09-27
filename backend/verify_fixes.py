"""
Simple verification of key fixes in main.py
"""
import re

def verify_fixes():
    """Verify that the key fixes have been applied"""
    
    print("🔍 Verifying AI Guided Interview Fixes in main.py")
    print("=" * 55)
    
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        fixes_verified = []
        
        # Check 1: Proper job title format
        if 'f"AI Guided Interview - {request.companyName}"' in content:
            fixes_verified.append("✅ Job title fix applied - no more TBD")
        else:
            fixes_verified.append("❌ Job title fix not found")
        
        # Check 2: Interview ID in metadata
        if '"interviewId": interview_id' in content:
            fixes_verified.append("✅ Interview ID included in metadata")
        else:
            fixes_verified.append("❌ Interview ID metadata fix not found")
        
        # Check 3: Enhanced error handling
        if 'print(f"⚠️  WARNING: Vapi call returned mock response - check configuration")' in content:
            fixes_verified.append("✅ Enhanced Vapi error detection")
        else:
            fixes_verified.append("❌ Vapi error detection not found")
        
        # Check 4: Improved webhook handler
        if 'async def generate_ai_feedback_for_interview' in content:
            fixes_verified.append("✅ Improved feedback generation function")
        else:
            fixes_verified.append("❌ Feedback generation function not found")
        
        # Check 5: Better interview lookup
        if 'print(f"🔍 Looking up interview by metadata ID: {interview_id}")' in content:
            fixes_verified.append("✅ Enhanced interview lookup in webhook")
        else:
            fixes_verified.append("❌ Enhanced interview lookup not found")
        
        # Check 6: Feedback tracking flags
        if '"feedbackGenerated": False' in content and '"transcriptAvailable": False' in content:
            fixes_verified.append("✅ Feedback tracking flags added")
        else:
            fixes_verified.append("❌ Feedback tracking flags not found")
        
        print("\n📋 Fix Verification Results:")
        for fix in fixes_verified:
            print(f"   {fix}")
        
        # Count successful fixes
        success_count = sum(1 for fix in fixes_verified if fix.startswith("✅"))
        total_count = len(fixes_verified)
        
        print(f"\n📊 Summary: {success_count}/{total_count} fixes verified successfully")
        
        if success_count == total_count:
            print("🎉 ALL FIXES HAVE BEEN SUCCESSFULLY APPLIED!")
            print("\nThe three main issues should now be resolved:")
            print("1. ✅ Vapi workflow calling with better error handling")
            print("2. ✅ Proper interview storage (no more TBD)")
            print("3. ✅ Feedback generation on interview completion")
        else:
            print(f"⚠️  {total_count - success_count} fixes may need attention")
        
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ Error reading main.py: {e}")
        return False

if __name__ == "__main__":
    verify_fixes()