#!/usr/bin/env python3
"""
Environment Variable Validation Script for EchoHire Backend
Run this script to validate your environment configuration before deployment.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_required_env_vars():
    """Check if all required environment variables are set"""
    
    required_vars = {
        'GOOGLE_AI_API_KEY': {
            'description': 'Google AI (Gemini) API key for interview analysis',
            'min_length': 30,
            'required': True
        },
        'VAPI_API_KEY': {
            'description': 'Vapi AI API key for voice interviews',
            'min_length': 20,
            'required': True
        },
        'FIREBASE_PROJECT_ID': {
            'description': 'Firebase project ID',
            'min_length': 5,
            'required': True
        },
        'VAPI_ASSISTANT_ID': {
            'description': 'Vapi Assistant ID (if key is scoped)',
            'min_length': 10,
            'required': False
        },
        'BACKEND_PUBLIC_URL': {
            'description': 'Public URL of your deployed backend',
            'min_length': 10,
            'required': False
        },
        'VAPI_WEBHOOK_SECRET': {
            'description': 'Webhook secret for Vapi integration',
            'min_length': 16,
            'required': False
        }
    }
    
    firebase_creds = {
        'FIREBASE_SERVICE_ACCOUNT_JSON': {
            'description': 'Firebase service account JSON',
            'required': False
        },
        'FIREBASE_SERVICE_ACCOUNT_JSON_BASE64': {
            'description': 'Base64 encoded Firebase service account JSON',
            'required': False
        }
    }
    
    print("🔍 EchoHire Environment Variable Validation")
    print("=" * 50)
    
    missing_required = []
    warnings = []
    success_count = 0
    
    # Check main environment variables
    for var_name, config in required_vars.items():
        value = os.getenv(var_name)
        
        if not value:
            if config['required']:
                missing_required.append(f"❌ {var_name}: MISSING (Required)")
                print(f"❌ {var_name}: MISSING")
                print(f"   📝 {config['description']}")
            else:
                warnings.append(f"⚠️  {var_name}: Not set (Optional)")
                print(f"⚠️  {var_name}: Not set (Optional)")
                print(f"   📝 {config['description']}")
        elif len(value) < config['min_length']:
            warnings.append(f"⚠️  {var_name}: Too short (possible invalid key)")
            print(f"⚠️  {var_name}: Set but appears too short")
            print(f"   📝 Length: {len(value)} (expected min: {config['min_length']})")
        else:
            success_count += 1
            masked_value = f"***{value[-6:]}" if len(value) > 6 else "***"
            print(f"✅ {var_name}: {masked_value}")
    
    # Check Firebase credentials (at least one should be set)
    firebase_cred_set = False
    for var_name, config in firebase_creds.items():
        value = os.getenv(var_name)
        if value:
            firebase_cred_set = True
            print(f"✅ {var_name}: Set ({len(value)} characters)")
            break
    
    if not firebase_cred_set:
        warnings.append("⚠️  Firebase credentials: No service account JSON found")
        print("⚠️  Firebase credentials: No service account JSON found")
        print("   📝 Set either FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_JSON_BASE64")
    
    # Check production settings
    print("\n🚀 Production Settings:")
    debug = os.getenv('DEBUG', 'True')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    host = os.getenv('HOST', '0.0.0.0')
    port = os.getenv('PORT', '8000')
    
    print(f"   DEBUG: {debug}")
    print(f"   LOG_LEVEL: {log_level}")
    print(f"   HOST: {host}")
    print(f"   PORT: {port}")
    
    if debug.lower() == 'true':
        warnings.append("⚠️  DEBUG is set to True (consider setting to False for production)")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    if missing_required:
        print("❌ REQUIRED VARIABLES MISSING:")
        for item in missing_required:
            print(f"   {item}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
    
    print(f"\n✅ Successfully configured: {success_count} variables")
    print(f"⚠️  Warnings: {len(warnings)}")
    print(f"❌ Missing required: {len(missing_required)}")
    
    if missing_required:
        print("\n🚨 DEPLOYMENT NOT READY")
        print("Please set the missing required environment variables before deploying.")
        return False
    elif warnings:
        print("\n⚠️  DEPLOYMENT READY WITH WARNINGS")
        print("Consider addressing the warnings above for optimal configuration.")
        return True
    else:
        print("\n🎉 DEPLOYMENT READY!")
        print("All required environment variables are properly configured.")
        return True

def main():
    """Main function"""
    print("Starting environment validation...\n")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ Found .env file")
    else:
        print("⚠️  No .env file found (using system environment variables)")
    
    print()
    
    # Run validation
    is_ready = check_required_env_vars()
    
    # Exit with appropriate code
    sys.exit(0 if is_ready else 1)

if __name__ == "__main__":
    main()