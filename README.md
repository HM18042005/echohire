# EchoHire - AI-Powered Interview Platform

<div align="center">

🎯 **Modern AI-driven interview management with real-time voice analysis and automated feedback**

[![Flutter](https://img.shields.io/badge/Flutter-3.9.0+-02569B?logo=flutter)](https://flutter.dev)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Firebase](https://img.shields.io/badge/Firebase-Latest-FFCA28?logo=firebase)](https://firebase.google.com)

</div>

## 🚀 Overview

EchoHire is a comprehensive AI-powered interview platform that combines Flutter mobile technology with advanced AI services to revolutionize the interview process. The platform features live AI-conducted interviews, real-time transcript analysis, and automated candidate evaluation.

### Key Features
- 🤖 **Live AI Interviews** - Vapi-powered voice AI conducts interviews
- 📝 **Real-time Transcription** - Automatic speech-to-text with Firestore storage
- 🧠 **Gemini AI Analysis** - Comprehensive candidate evaluation and insights
- 🎨 **Modern UI** - Dark-themed Material Design interface
- 🔐 **Secure Authentication** - Firebase Auth with token-based API protection
- 📊 **Comprehensive Analytics** - Detailed feedback and scoring system

## 📋 Project Status

### ✅ Production-Ready Features

#### 🔐 Authentication & Security
- Firebase Authentication with secure token validation
- User profile management with Riverpod state management
- Protected API endpoints with Firebase ID token verification

#### 🎨 User Interface
- Modern dark theme (`#181A20` background, `#2972FF` primary)
- Complete screen stack: Login, Signup, Home, Profile, Interview Management
- Responsive design with Material Design components
- Status indicators and real-time visual feedback

#### 🤖 AI Integration (Live)
- **Vapi Integration**: Real AI-conducted interviews via web calls
- **Environment-Driven**: Mock/live modes controlled by `ENABLE_MOCKS` flag
- **Gemini Analysis**: Automated transcript analysis with scoring and insights
- **Real-time Status**: Live polling of interview completion status
- **Transcript Storage**: Automatic Firestore persistence of interview transcripts

#### 🗄️ Backend Infrastructure
```
FastAPI Server with comprehensive endpoints:
├── Authentication & Profiles
│   ├── GET/PUT /me - User profile management
├── Interview Management  
│   ├── POST/GET /interviews - Persistent interview records
│   ├── GET /interviews/{id} - Individual interview details
│   ├── POST/GET /interviews/{id}/feedback - Feedback management
├── AI Interview System
│   ├── POST /api/generate-interview - Generate question sets
│   ├── GET /api/interviews/{user_id} - List AI sessions
│   ├── POST /interviews/{id}/start-ai - Start live AI interview
│   ├── GET /interviews/{id}/ai-status - Real-time status polling
│   ├── GET /interviews/{id}/ai-feedback - Generated AI insights
│   └── POST /interviews/{id}/stop-ai - Stop active sessions
└── Health & Monitoring
    └── GET /health - Server health check
```

#### 📱 Mobile App Features
- Interview creation and management
- Live AI interview participation with \"Join AI Call\" links
- Real-time status monitoring during interviews
- Results viewing with AI-generated feedback
- Transcript display from Firestore storage
- Environment-based configuration (`.env` files)

### 🔄 Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flutter Mobile App                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Screens   │  │    State    │  │      Services       │  │
│  │             │  │ (Riverpod)  │  │                     │  │
│  │ • Login     │  │             │  │ • ApiService        │  │
│  │ • Home      │◄─┤ • Profile   │  │ • AuthService       │  │
│  │ • AI Inter. │  │ • Interview │  │ • AppConfig (.env)  │  │
│  │ • Results   │  │ • Feedback  │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/Firebase
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    API      │  │    AI       │  │     Firebase        │  │
│  │ Endpoints   │  │ Services    │  │   Integration       │  │
│  │             │  │             │  │                     │  │
│  │ • /me       │  │ • Gemini    │◄─┤ • Admin SDK         │  │
│  │ • /interviews│  │ • Vapi     │  │ • Firestore         │  │
│  │ • /ai-*     │  │ • Analysis  │  │ • Auth Verification │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                External AI Services                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Google    │  │    Vapi     │  │     Firebase        │  │
│  │   Gemini    │  │Voice AI API │  │   Cloud Services    │  │
│  │             │  │             │  │                     │  │
│  │ • Analysis  │  │ • Calls     │  │ • Authentication    │  │
│  │ • Scoring   │  │ • Transcript│  │ • Firestore DB      │  │
│  │ • Insights  │  │ • Recording │  │ • Real-time Sync    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Frontend (Flutter App)
- **Framework**: Flutter 3.9.0+ with Dart
- **State Management**: Riverpod 2.4.9 for reactive state
- **Authentication**: Firebase Auth with secure token handling
- **HTTP Client**: Native `http` package with custom API service
- **Configuration**: `flutter_dotenv` for environment management
- **Audio/Voice**: `flutter_sound`, `flutter_tts` for interview features
- **Permissions**: `permission_handler` for microphone access
- **UI**: Material Design 3 with custom dark theme

### Backend (Python API)
- **Framework**: FastAPI with Pydantic validation
- **Server**: Uvicorn ASGI server
- **Database**: Firebase Firestore (NoSQL)
- **Authentication**: Firebase Admin SDK
- **AI Services**: 
  - Google Gemini Pro for analysis
  - Vapi for voice AI interviews
- **HTTP Client**: `httpx` for async external API calls
- **Configuration**: `python-dotenv` for environment management

### Infrastructure & Services
- **Authentication**: Firebase Authentication
- **Database**: Firebase Firestore with real-time sync
- **AI Analysis**: Google Gemini Pro API
- **Voice AI**: Vapi voice interview platform
- **Storage**: Firestore for transcripts, Firebase Storage (future)
- **Deployment**: Local development, production-ready architecture

## 🚀 Quick Start

### Prerequisites
- Flutter 3.9.0+ SDK
- Python 3.13+ with pip
- Firebase project with Authentication and Firestore enabled
- Google AI API key (Gemini)
- Vapi API key for voice interviews

### 1. Clone & Setup
```powershell
git clone https://github.com/yourusername/echohire.git
cd echohire
```

### 2. Backend Setup
```powershell
# Navigate to backend
cd backend

# Create and activate virtual environment (Windows)
python -m venv .venv
.\.venv\\Scripts\\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys:
# - GOOGLE_AI_API_KEY=your_gemini_key
# - VAPI_API_KEY=your_vapi_key

# Add Firebase service account
# Place firebase-service-account.json in backend/

# Start server
python main.py
```
Backend runs at: `http://localhost:8000`

### 3. Flutter App Setup
```powershell
# Return to project root
cd ..

# Install Flutter dependencies
flutter pub get

# Configure Firebase
# Place android/app/google-services.json
# Update lib/firebase_options.dart

# Configure environment for development
# Edit .env for local development:
# BASE_URL=http://10.0.2.2:8000  # Android emulator
# ENABLE_MOCKS=false              # Use live AI services

# Run the app
flutter run
# For device testing with real backend:
flutter run --dart-define=ENV=device
```

### 4. Environment Configuration

The app supports multiple environments through `.env` files:

#### `.env` (Development)
```env
BASE_URL=http://10.0.2.2:8000
ENABLE_MOCKS=false
```

#### `.env.device` (Device Testing)
```env
BASE_URL=http://192.168.1.100:8000  # Your PC's LAN IP
ENABLE_MOCKS=false
```

#### `.env.production` (Production)
```env
BASE_URL=https://api.yourdomain.com
ENABLE_MOCKS=false
```

Use with: `flutter run --dart-define=ENV=device` or `ENV=production`

## 🎯 Usage Guide

### For Interviewers
1. **Sign Up/Login**: Create account or log in with existing credentials
2. **Create Interview**: Add job details, company, and schedule
3. **Start AI Interview**: Launch live AI-conducted interview session
4. **Monitor Progress**: Real-time status updates during interview
5. **Review Results**: View AI-generated feedback, scores, and transcript

### Interview Flow
```
Create Interview → Start AI Session → Join AI Call → Interview Completion → Results & Analysis
      ↓                ↓              ↓                    ↓                    ↓
   Firestore       Vapi API      Browser/App        Status Polling      Gemini Analysis
```

### For Candidates
1. Receive interview link from interviewer
2. Join AI-powered voice interview
3. Participate in structured Q&A session
4. Automatic transcript and analysis generation

## 🔧 Configuration

### Environment Variables

#### Backend (`backend/.env`)
```env
# AI Service Keys (Required)
GOOGLE_AI_API_KEY=your_gemini_api_key_here
VAPI_API_KEY=your_vapi_private_key_here

# Firebase Configuration
FIREBASE_PROJECT_ID=your_firebase_project_id

# Server Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

#### Frontend (`.env` files)
```env
# API Configuration
BASE_URL=http://10.0.2.2:8000

# Feature Flags
ENABLE_MOCKS=false  # Set to true for offline development
```

### Firebase Setup
1. Create Firebase project with Authentication and Firestore
2. Enable Email/Password authentication
3. Download `google-services.json` for Android
4. Download service account JSON for backend
5. Configure Firestore security rules

### API Keys Setup
1. **Google AI (Gemini)**: Get key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Vapi**: Register at [Vapi.ai](https://vapi.ai) and get API keys
3. **Firebase**: Service account from Firebase Console

## 🏗️ Project Structure

```
echohire/
├── 📱 lib/                          # Flutter app source
│   ├── 🎨 screens/                  # UI screens
│   │   ├── login_screen.dart
│   │   ├── home_screen.dart
│   │   ├── ai_interview_screen.dart # Live AI interview UI
│   │   ├── interview_results_screen.dart
│   │   └── ...
│   ├── 🔄 state/                    # Riverpod controllers
│   │   ├── profile_controller.dart
│   │   ├── interview_controller.dart
│   │   └── feedback_controller.dart
│   ├── 🛠️ services/                 # API and utilities
│   │   ├── api_service.dart         # HTTP client
│   │   └── auth_service.dart        # Firebase auth
│   ├── 📊 models/                   # Data models
│   │   ├── interview.dart
│   │   ├── user_profile.dart
│   │   └── interview_feedback.dart
│   ├── ⚙️ config.dart               # Environment configuration
│   └── 🚀 main.dart                 # App entry point
├── 🐍 backend/                      # FastAPI server
│   ├── 🎯 main.py                   # FastAPI application
│   ├── 🤖 ai_services.py            # Gemini & Vapi integration
│   ├── 📋 requirements.txt          # Python dependencies
│   ├── 🔑 .env                      # Environment variables
│   └── 📜 firebase-service-account.json
├── 🤖 android/                      # Android configuration
│   ├── 📦 app/build.gradle.kts      # Build configuration
│   ├── 🔑 app/google-services.json  # Firebase config
│   └── 🔒 keystore.properties.example
├── ⚙️ Configuration files
│   ├── .env                         # Development environment
│   ├── .env.device                  # Device testing environment  
│   ├── .env.production              # Production environment
│   └── .env.example                 # Template
└── 📚 Documentation
    ├── README.md                    # This file
    ├── SETUP_GUIDE.md              # Detailed setup instructions
    └── PHASE_1_COMPLETE.md         # Development milestones
```

## 🧪 Development

### Running Tests
```powershell
# Flutter tests
flutter test

# Backend tests (if available)
cd backend
python -m pytest
```

### Code Quality
```powershell
# Flutter analysis
flutter analyze

# Python linting
cd backend
flake8 .
```

### Building for Production
```powershell
# Android APK
flutter build apk --release --dart-define=ENV=production

# Android App Bundle (Play Store)
flutter build appbundle --release --dart-define=ENV=production
```

## 🔐 Security & Privacy

### Data Protection
- All API endpoints require Firebase authentication
- User data is isolated by Firebase UID
- Interview transcripts stored securely in Firestore
- API keys and secrets managed via environment variables

### Permissions
- **Microphone**: Required for interview recording
- **Internet**: API communication and Firebase sync
- **Network State**: Connection status monitoring

### Privacy Considerations
- Interview recordings processed by Vapi and Gemini AI
- Transcripts stored in your Firebase project
- No data shared with third parties beyond AI processing
- Users control their data through Firebase Authentication

## 🚀 Deployment

### Backend Deployment Options

#### Option 1: Cloud Run (Google Cloud)
```dockerfile
# Dockerfile example
FROM python:3.13-slim
WORKDIR /app
COPY backend/ .
RUN pip install -r requirements.txt
CMD [\"python\", \"main.py\"]
```

#### Option 2: Railway/Render
- Push backend/ to Git repository
- Configure environment variables in platform dashboard
- Deploy automatically on push

#### Option 3: VPS/Dedicated Server
```bash
# Ubuntu/Debian setup
sudo apt update
sudo apt install python3 python3-pip nginx certbot
# Configure reverse proxy and SSL
```

### Mobile App Distribution

#### Internal Testing
```powershell
# Build signed APK
flutter build apk --release --dart-define=ENV=production
```

#### Play Store Release
```powershell
# Build App Bundle
flutter build appbundle --release --dart-define=ENV=production
# Upload to Google Play Console
```

## 🐛 Troubleshooting

### Common Issues

#### \"No file or variants found for asset: .env\"
```powershell
# Ensure .env files exist
ls .env*
# Run with explicit environment
flutter run --dart-define=ENV=device
```

#### \"Failed to connect to backend\"
```powershell
# Check backend is running
curl http://localhost:8000/health
# For Android emulator, use 10.0.2.2
# For physical device, use your PC's IP address
```

#### \"Firebase token expired\"
```powershell
# Restart the app to refresh token
# Or implement token refresh in AuthService
```

#### \"Vapi call failed\"
- Verify `VAPI_API_KEY` in backend `.env`
- Check Vapi dashboard for account status
- Ensure sufficient Vapi credits

#### \"Gemini analysis error\"
- Verify `GOOGLE_AI_API_KEY` in backend `.env`
- Check Google AI Studio for quota limits
- Validate API key permissions

### Network Configuration

#### Android Emulator
```env
BASE_URL=http://10.0.2.2:8000  # Maps to localhost:8000
```

#### Physical Device (same network)
```env
BASE_URL=http://192.168.1.100:8000  # Replace with your PC's IP
```

#### ADB Reverse (USB debugging)
```powershell
adb reverse tcp:8000 tcp:8000
# Then use BASE_URL=http://127.0.0.1:8000
```

## 📈 Roadmap

### Phase 2 (Current Development)
- [ ] Enhanced AI analysis with behavioral insights
- [ ] Multi-language support for interviews
- [ ] Calendar integration for scheduling
- [ ] Team collaboration features

### Phase 3 (Future)
- [ ] Video interview support
- [ ] Advanced analytics dashboard
- [ ] Integration with HR systems
- [ ] Mobile interviewer tools

### Phase 4 (Enterprise)
- [ ] White-label solutions
- [ ] Advanced security features
- [ ] Custom AI model training
- [ ] Enterprise SSO integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow Flutter/Dart style guidelines
- Maintain Python PEP 8 standards
- Update documentation for new features
- Add tests for critical functionality
- Ensure environment variable configuration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links & Resources

- **Flutter Documentation**: [flutter.dev](https://flutter.dev/docs)
- **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Firebase Console**: [console.firebase.google.com](https://console.firebase.google.com)
- **Google AI Studio**: [makersuite.google.com](https://makersuite.google.com)
- **Vapi Documentation**: [docs.vapi.ai](https://docs.vapi.ai)

## 📞 Support

For technical support or questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the detailed setup guide in `SETUP_GUIDE.md`

---

<div align=\"center\">

**EchoHire** - Revolutionizing interviews with AI  
*Built with ❤️ using Flutter, FastAPI, and cutting-edge AI*

**Last Updated**: September 24, 2025 | **Version**: 1.2.0 | **Status**: Production Ready

</div>