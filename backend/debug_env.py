#!/usr/bin/env python3
"""
Environment Variable Debug Script
Run this on your server to verify which API keys are being loaded
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

def debug_vapi_keys():
    """Debug Vapi API keys to identify which one is being used"""
    
    print("🔍 Vapi API Key Debug Information")
    print("=" * 50)
    
    # Get both keys
    vapi_api_key = os.getenv("VAPI_API_KEY")
    vapi_public_key = os.getenv("VAPI_PUBLIC_KEY")
    
    print(f"VAPI_API_KEY present: {bool(vapi_api_key)}")
    print(f"VAPI_PUBLIC_KEY present: {bool(vapi_public_key)}")
    
    if vapi_api_key:
        print(f"VAPI_API_KEY length: {len(vapi_api_key)}")
        print(f"VAPI_API_KEY starts with: {vapi_api_key[:8]}***")
        print(f"VAPI_API_KEY ends with: ***{vapi_api_key[-8:]}")
    else:
        print("❌ VAPI_API_KEY not found!")
    
    if vapi_public_key:
        print(f"VAPI_PUBLIC_KEY length: {len(vapi_public_key)}")
        print(f"VAPI_PUBLIC_KEY starts with: {vapi_public_key[:8]}***")
        print(f"VAPI_PUBLIC_KEY ends with: ***{vapi_public_key[-8:]}")
    else:
        print("❌ VAPI_PUBLIC_KEY not found!")
    
    # Check other Vapi-related env vars
    print(f"\nOther Vapi environment variables:")
    print(f"VAPI_ASSISTANT_ID: {os.getenv('VAPI_ASSISTANT_ID')}")
    print(f"BACKEND_PUBLIC_URL: {os.getenv('BACKEND_PUBLIC_URL')}")
    print(f"VAPI_WEBHOOK_SECRET: {'***' if os.getenv('VAPI_WEBHOOK_SECRET') else 'Not set'}")
    
    # Identify the correct key to use
    print(f"\n" + "=" * 50)
    print("🎯 Key Usage Guide:")
    print("=" * 50)
    
    if vapi_api_key and vapi_public_key:
        if vapi_api_key.endswith("c8becf15"):
            print("❌ ERROR: VAPI_API_KEY appears to be the PUBLIC key!")
            print("📝 VAPI_API_KEY should be the PRIVATE key for server-side calls")
            print("📝 VAPI_PUBLIC_KEY should be the PUBLIC key for client-side calls")
        elif vapi_public_key.endswith("c8becf15"):
            print("✅ Correct: VAPI_PUBLIC_KEY is the public key")
            print("✅ Correct: VAPI_API_KEY appears to be the private key")
        else:
            print("⚠️  Unable to determine key types from endings")
    
    print(f"\n📋 For server-side API calls (backend), use: VAPI_API_KEY")
    print(f"📋 For client-side calls (frontend), use: VAPI_PUBLIC_KEY")

if __name__ == "__main__":
    debug_vapi_keys()