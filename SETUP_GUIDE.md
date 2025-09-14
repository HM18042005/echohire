# EchoHire Setup Guide - AI Interview System

## 🚀 Quick Start

### Prerequisites
- **Flutter SDK** (latest stable version)
- **Python 3.8+** with pip
- **Android Studio/VS Code** for development
- **Firebase project** (already configured)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip install fastapi uvicorn firebase-admin google-generativeai httpx python-dotenv
   ```

3. **Configure API Keys:**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` file with your API keys:
     ```bash
     # Get from https://makersuite.google.com/app/apikey
     GOOGLE_AI_API_KEY=your_actual_google_ai_api_key_here
     
     # Get from https://vapi.ai/dashboard
     VAPI_API_KEY=your_actual_vapi_api_key_here
     ```

4. **Start the backend server:**
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to project root:**
   ```bash
   cd ..  # if in backend directory
   ```

2. **Install Flutter dependencies:**
   ```bash
   flutter pub get
   ```

3. **Run the app:**
   ```bash
   flutter run
   ```

## 🎯 API Key Configuration

### Google AI (Gemini) API Key

1. **Visit**: https://makersuite.google.com/app/apikey
2. **Create new API key** or use existing one
3. **Add to .env file**: `GOOGLE_AI_API_KEY=your_key_here`

### Vapi AI API Key

1. **Visit**: https://vapi.ai/dashboard
2. **Sign up/Login** and navigate to API keys
3. **Create new API key**
4. **Add to .env file**: `VAPI_API_KEY=your_key_here`

## 🔧 System Architecture

### Backend Services
- **FastAPI Server**: Running on `localhost:8000`
- **Firebase Firestore**: User and interview data storage
- **Google Gemini AI**: Interview transcript analysis
- **Vapi Voice AI**: Conducting voice interviews

### Frontend Configuration
- **API Base URL**: `http://10.0.2.2:8000` (Android emulator)
- **Flutter Services**: API client, authentication, state management

## 📱 Testing the AI Interview Flow

### Complete Workflow
1. **Create Interview**: Add new interview in the app
2. **Start AI Interview**: Tap "Start AI Interview" button
3. **Voice Recording**: AI conducts voice interview via Vapi
4. **Real-time Status**: Monitor interview progress
5. **AI Analysis**: Gemini analyzes transcript automatically
6. **View Feedback**: Review comprehensive AI-generated feedback

### Mock Mode (No API Keys)
- System gracefully falls back to mock data
- All features remain functional for testing
- Warning messages indicate mock mode operation

## 🛠 Troubleshooting

### Backend Issues
- **Port 8000 already in use**: Change port in uvicorn command
- **Module import errors**: Ensure all pip packages installed
- **Firebase errors**: Check firebase-service-account.json file exists

### API Key Issues
- **Missing API keys**: System uses mock data, check console warnings
- **Invalid API keys**: Verify keys are correct and have proper permissions
- **Network errors**: Check internet connection and API service status

### Frontend Issues
- **Connection refused**: Ensure backend server is running on port 8000
- **Authentication errors**: Check Firebase configuration
- **Build errors**: Run `flutter clean && flutter pub get`

## 📊 System Status Monitoring

### Backend Health Check
```bash
curl http://localhost:8000/health
```

### API Endpoints
- `GET /health` - Server health status
- `POST /interviews/{id}/start-ai` - Start AI interview
- `GET /interviews/{id}/ai-status` - Check interview status
- `GET /interviews/{id}/ai-feedback` - Get AI analysis

### Log Monitoring
- Backend logs show API key configuration status
- Console warnings indicate when mock data is used
- Error messages provide debugging information

## 🔒 Security Notes

### API Key Security
- Never commit `.env` file to version control
- Use environment variables in production
- Rotate API keys regularly
- Limit API key permissions to required scopes

### Firebase Security
- Service account JSON file contains sensitive data
- Implement proper Firebase security rules
- Use authentication for all protected endpoints

## 🚀 Production Deployment

### Environment Variables
```bash
export GOOGLE_AI_API_KEY="your_production_key"
export VAPI_API_KEY="your_production_key"
export FIREBASE_PROJECT_ID="your_project_id"
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📈 Performance Optimization

### Backend Performance
- Enable API response caching for static data
- Implement connection pooling for database
- Use async/await for all I/O operations

### Frontend Performance
- Implement pagination for large interview lists
- Cache API responses locally
- Optimize state management with Riverpod

## 🎯 Feature Completeness

### ✅ Implemented Features
- Complete AI interview workflow
- Voice recording and analysis
- Real-time status monitoring  
- Comprehensive feedback generation
- Graceful fallback to mock data
- Robust error handling

### 🔄 Ready for Production
- All core features implemented
- API keys configurable via environment
- Error handling covers edge cases
- Documentation provides complete setup guide

## 🤝 Support

For technical issues:
1. Check console logs for error messages
2. Verify API key configuration
3. Ensure all dependencies are installed
4. Test with mock data first before using real APIs

The system is now **production-ready** with comprehensive error handling and fallback mechanisms!