#!/usr/bin/env python3
"""
Configuration Check Utility for EchoHire Vapi Integration
=========================================================

This script helps diagnose configuration issues with the Vapi integration.
Run this to check if all required environment variables are set correctly.
"""

import os
import asyncio
import httpx
from typing import Dict, List

def check_environment_variables() -> Dict[str, bool]:
    """Check if required environment variables are set."""
    required_vars = {
        "VAPI_API_KEY": os.getenv("VAPI_API_KEY"),
        "GOOGLE_AI_API_KEY": os.getenv("GOOGLE_AI_API_KEY"),
        "FIREBASE_CREDENTIALS": os.getenv("FIREBASE_CREDENTIALS"),
    }
    
    optional_vars = {
        "VAPI_ASSISTANT_ID": os.getenv("VAPI_ASSISTANT_ID"),
        "BACKEND_PUBLIC_URL": os.getenv("BACKEND_PUBLIC_URL"),
        "VAPI_WEBHOOK_SECRET": os.getenv("VAPI_WEBHOOK_SECRET"),
        "PORT": os.getenv("PORT", "8000"),
    }
    
    print("🔍 Environment Variables Check")
    print("=" * 50)
    
    issues = []
    
    for var_name, value in required_vars.items():
        status = "✅" if value and value != "your-vapi-key-here" and value != "your-gemini-api-key-here" else "❌"
        print(f"{status} {var_name}: {'SET' if value and value not in ['your-vapi-key-here', 'your-gemini-api-key-here'] else 'NOT SET'}")
        if not value or value in ['your-vapi-key-here', 'your-gemini-api-key-here']:
            issues.append(f"Missing required environment variable: {var_name}")
    
    print("\n📋 Optional Variables:")
    for var_name, value in optional_vars.items():
        status = "ℹ️" if value else "⚪"
        print(f"{status} {var_name}: {value or 'NOT SET'}")
    
    return {"required": required_vars, "optional": optional_vars, "issues": issues}

async def test_vapi_connection() -> Dict[str, any]:
    """Test connection to Vapi API."""
    print("\n🔗 Vapi API Connection Test")
    print("=" * 50)
    
    vapi_key = os.getenv("VAPI_API_KEY")
    if not vapi_key or vapi_key == "your-vapi-key-here":
        print("❌ Cannot test Vapi - API key not configured")
        return {"success": False, "error": "No API key"}
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {vapi_key}",
                "Content-Type": "application/json"
            }
            
            # Test a simple API call - get account info or similar
            response = await client.get(
                "https://api.vapi.ai/call",  # List calls endpoint
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Vapi API connection successful")
                return {"success": True, "status_code": response.status_code}
            elif response.status_code == 401:
                print("❌ Vapi API authentication failed - check your API key")
                return {"success": False, "error": "Authentication failed", "status_code": 401}
            else:
                print(f"⚠️ Vapi API returned status {response.status_code}")
                return {"success": False, "status_code": response.status_code, "response": response.text}
                
    except httpx.TimeoutException:
        print("❌ Vapi API connection timeout")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ Vapi API connection error: {e}")
        return {"success": False, "error": str(e)}

async def test_gemini_connection() -> Dict[str, any]:
    """Test connection to Google Gemini API."""
    print("\n🧠 Gemini AI Connection Test")
    print("=" * 50)
    
    gemini_key = os.getenv("GOOGLE_AI_API_KEY")
    if not gemini_key or gemini_key == "your-gemini-api-key-here":
        print("❌ Cannot test Gemini - API key not configured")
        return {"success": False, "error": "No API key"}
    
    try:
        # Try importing and configuring Gemini
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say 'Hello' if you're working correctly")
        
        if response and response.text:
            print("✅ Gemini AI connection successful")
            print(f"   Response: {response.text.strip()}")
            return {"success": True, "response": response.text}
        else:
            print("❌ Gemini AI returned empty response")
            return {"success": False, "error": "Empty response"}
            
    except ImportError:
        print("❌ google-generativeai package not installed")
        return {"success": False, "error": "Package not installed"}
    except Exception as e:
        print(f"❌ Gemini AI connection error: {e}")
        return {"success": False, "error": str(e)}

def generate_debug_report(env_check: Dict, vapi_test: Dict, gemini_test: Dict):
    """Generate a debug report."""
    print("\n📋 DEBUG REPORT")
    print("=" * 50)
    
    if env_check["issues"]:
        print("❌ Configuration Issues Found:")
        for issue in env_check["issues"]:
            print(f"   - {issue}")
    else:
        print("✅ All required environment variables are configured")
    
    print(f"\n🔗 Vapi API: {'✅ Working' if vapi_test.get('success') else '❌ Issues'}")
    if not vapi_test.get('success'):
        print(f"   Error: {vapi_test.get('error', 'Unknown')}")
    
    print(f"🧠 Gemini AI: {'✅ Working' if gemini_test.get('success') else '❌ Issues'}")
    if not gemini_test.get('success'):
        print(f"   Error: {gemini_test.get('error', 'Unknown')}")
    
    print("\n💡 Next Steps:")
    if env_check["issues"]:
        print("   1. Set the missing environment variables")
        print("   2. Restart your application")
    if not vapi_test.get('success'):
        print("   3. Verify your Vapi API key in the dashboard")
        print("   4. Check if your Vapi account has sufficient credits")
    if not gemini_test.get('success'):
        print("   5. Verify your Google AI API key")
        print("   6. Ensure Gemini API is enabled in Google Cloud Console")

async def main():
    """Run all configuration checks."""
    print("🔧 EchoHire Configuration Checker")
    print("=" * 50)
    
    # Check environment variables
    env_check = check_environment_variables()
    
    # Test API connections
    vapi_test = await test_vapi_connection()
    gemini_test = await test_gemini_connection()
    
    # Generate report
    generate_debug_report(env_check, vapi_test, gemini_test)

if __name__ == "__main__":
    asyncio.run(main())