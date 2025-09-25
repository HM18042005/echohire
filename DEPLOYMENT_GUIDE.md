# EchoHire Backend Deployment Guide

## Environment Variables Setup for Production

This guide ensures all API keys and sensitive data are properly managed using environment variables for secure deployment.

### Required Environment Variables

#### 1. Google AI (Gemini) Configuration
```bash
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
```
- Get your API key from: https://makersuite.google.com/app/apikey
- Used for AI-powered interview analysis and feedback generation

#### 2. Vapi AI Configuration
```bash
VAPI_API_KEY=your_vapi_api_key_here
VAPI_ASSISTANT_ID=your_vapi_assistant_id_here  # Optional
BACKEND_PUBLIC_URL=https://your-domain.com
VAPI_WEBHOOK_SECRET=your_strong_webhook_secret_here
AUTO_GENERATE_AI_FEEDBACK=0  # Set to 1 to enable auto-feedback
```
- Get your API key from: https://vapi.ai/dashboard
- `VAPI_ASSISTANT_ID`: Only needed if your API key is scoped to a specific assistant
- `BACKEND_PUBLIC_URL`: Your deployed backend URL for webhook callbacks
- `VAPI_WEBHOOK_SECRET`: Strong secret for webhook verification

#### 3. Firebase Configuration
```bash
FIREBASE_PROJECT_ID=your_firebase_project_id

# Choose ONE of these methods for Firebase credentials:

# Option 1: Direct JSON (not recommended for security)
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# Option 2: Base64 encoded JSON (recommended)
FIREBASE_SERVICE_ACCOUNT_JSON_BASE64=base64_encoded_service_account_json
```

#### 4. Production Settings
```bash
DEBUG=False
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### Deployment Platforms

#### Render.com
1. Go to your Render dashboard
2. Select your service
3. Go to Environment tab
4. Add each environment variable as key-value pairs
5. Redeploy your service

#### Railway
```bash
# Install Railway CLI
railway login
railway environment set GOOGLE_AI_API_KEY your_key_here
railway environment set VAPI_API_KEY your_key_here
# ... set all other variables
railway deploy
```

#### Docker
Create a `.env.production` file and use it with Docker:
```bash
docker run --env-file .env.production your-image
```

#### Heroku
```bash
heroku config:set GOOGLE_AI_API_KEY=your_key_here
heroku config:set VAPI_API_KEY=your_key_here
heroku config:set VAPI_ASSISTANT_ID=your_assistant_id
# ... set all other variables
```

### Security Best Practices

1. **Never commit API keys to version control**
   - The `.env` file is already in `.gitignore`
   - Use placeholder values in `.env.example`

2. **Use strong webhook secrets**
   ```bash
   # Generate a strong webhook secret
   openssl rand -base64 32
   ```

3. **Firebase Service Account Security**
   - For production, use base64 encoded JSON in environment variables
   - To encode your service account JSON:
   ```bash
   base64 -i firebase-service-account.json
   ```

4. **Environment-specific configurations**
   - Set `DEBUG=False` in production
   - Use appropriate `LOG_LEVEL` (INFO or WARNING for production)

### Validation

Your application will automatically validate the configuration on startup and provide detailed logging:

```
[VAPI_CONFIG] Configuration validation: {
  "is_configured": true,
  "api_key_present": true,
  "api_key_length": 36,
  "base_url": "https://api.vapi.ai",
  "assistant_id_present": true,
  "assistant_id": "bc32bb37-...",
  "issues": []
}
```

### Troubleshooting

#### Common Issues:

1. **401 Authentication Errors**
   - Check if `VAPI_API_KEY` is correctly set
   - Verify the API key is valid and has proper permissions
   - Check if key is scoped to the correct assistant

2. **Missing Environment Variables**
   - The enhanced logging will show exactly which variables are missing
   - Check spelling and case sensitivity of variable names

3. **Firebase Connection Issues**
   - Ensure `FIREBASE_PROJECT_ID` matches your project
   - Verify service account JSON is properly encoded
   - Check if Firebase credentials have proper permissions

#### Debug Mode:
Set `DEBUG=True` and `LOG_LEVEL=DEBUG` temporarily to get detailed logging information.

### Testing Your Deployment

1. Check application logs for configuration validation messages
2. Test a simple API endpoint to verify Firebase connection
3. Try creating a Vapi call to test the integration
4. Monitor logs for any authentication or configuration issues

Remember to set `DEBUG=False` and appropriate logging levels for production use.