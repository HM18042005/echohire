# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- This repo contains a Flutter mobile app (lib/, android/) and a Python FastAPI backend (backend/).
- Mobile uses Firebase (Auth, Firestore) and talks to the backend via AppConfig.baseUrl loaded from .env files.
- The backend secures routes with Firebase ID tokens and persists to Firestore; it integrates with Google Gemini (analysis) and Vapi (voice AI), with mock fallbacks when services are unavailable.

Environment configuration (Flutter)
- AppConfig selects the .env file via a Dart define named ENV:
  - ENV=dev => .env
  - ENV=device => .env.device
  - ENV=prod => .env.production
- Defaults to dev when ENV is not provided.
- For Android emulator, BASE_URL should typically be http://10.0.2.2:8000.

Common commands (Windows PowerShell, pwsh)
- Flutter setup and run
  - Install deps: flutter pub get
  - Run app (dev): flutter run
  - Run with explicit environment:
    - flutter run --dart-define=ENV=dev
    - flutter run --dart-define=ENV=device
    - flutter run --dart-define=ENV=prod
  - Analyze (lint): flutter analyze
  - Tests (all): flutter test
  - Single test by file: flutter test test/path_to_test.dart
  - Single test by name: flutter test -n "partial test name"
  - Build release APK (uses ENV=prod mapping):
    - flutter build apk --release --dart-define=ENV=prod
  - Build Play Store bundle:
    - flutter build appbundle --release --dart-define=ENV=prod

- Android signing (app/android)
  - app/build.gradle.kts is configured to use a release keystore if keystore.properties exists at the Android project root; otherwise debug signing is used for local runs.
  - To enable release signing, provide keystore.properties with storeFile, storePassword, keyAlias, keyPassword.

- Backend (FastAPI)
  - Prereqs: Python 3.13+, Firebase project, service account JSON (preferably via env var), Gemini and Vapi keys.
  - Create venv and install:
    - python -m venv .venv
    - .\.venv\Scripts\Activate.ps1
    - pip install -r backend/requirements.txt
  - Configure env (preferred):
    - Set FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_JSON_BASE64 to the service account content; or set ALLOW_FIREBASE_FILE=1 and place firebase-service-account.json in backend/.
    - GOOGLE_AI_API_KEY, VAPI_API_KEY as needed.
  - Run (simple): python backend/main.py
  - Run (hot reload): python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
  - Health checks: curl http://localhost:8000/health and curl http://localhost:8000/health/db
  - Lint: (from backend/) flake8 .
  - Tests (if present): (from backend/) python -m pytest
  - Single test (examples): (from backend/) python -m pytest tests/test_file.py::TestClass::test_name or python -m pytest -k "substring"

Important repository specifics
- Flutter environment selection is driven by a Dart define (ENV) that maps to .env files. Use prod, not production, when building for release.
- The Flutter app fetches a Firebase ID token (AuthService) and attaches it as Authorization: Bearer <token> for backend requests (ApiService).
- The backend verifies Firebase tokens and will return mock data in development when Firebase is not configured (DEBUG=true) or unavailable, preventing the app from hanging.
- Emulator networking: use 10.0.2.2 for Android emulator to reach the host machine’s backend.
- Firebase setup required: android/app/google-services.json and proper firebase_options.dart in lib/.

High-level architecture
- Flutter app
  - Entry: lib/main.dart initializes Firebase, loads AppConfig, and wraps the app in Riverpod’s ProviderScope. AuthWrapper routes to LoginScreen or HomeScreen based on Firebase auth state.
  - State management: Riverpod StateNotifier (e.g., InterviewController) orchestrates API calls and local state, with mock fallbacks when AppConfig.enableMocks is true.
  - Services: lib/services/ApiService attaches Firebase ID tokens, handles errors, and exposes methods for interview operations (generate, list, fetch). Base URL comes from AppConfig.baseUrl.
  - Models: lib/models/* define Interview, InterviewFeedback, UserProfile data structures used across screens and state.
  - UI: lib/screens/* organize flows for login/signup, home, interview creation, AI interview, and results.

- Backend (FastAPI)
  - Auth: verify_firebase_token extracts and verifies the Firebase ID token from Authorization headers. In DEBUG mode or when Firebase is unavailable, development mock users are returned to keep flows unblocked.
  - Persistence: Firestore collections profiles, interviews, feedback store user data and interview artifacts.
  - AI services: backend/ai_services.py provides GeminiAnalysisService for transcript analysis (with structured fallbacks). backend/vapi_workflows.py and VapiInterviewService manage voice AI sessions and workflows.
  - Endpoints (high-level):
    - /health, /health/db — service and Firestore checks
    - /me (GET, PUT) — profile management
    - /interviews (POST, GET) — create and list user interviews
    - /interviews/{id} (GET) — fetch a single interview
    - /api/generate-interview (POST) — create AI interview sessions (mock questions when AI off)
    - /interviews/{id}/start-ai, /ai-status, /ai-feedback, /stop-ai — manage live AI interview lifecycle

Notes pulled from README.md
- Emulator base URL and multi-environment .env setup (.env, .env.device, .env.production) are required for correct mobile-to-backend networking.
- Backend can be run directly (python backend/main.py). Provide Google AI and Vapi keys via env.
- Flutter builds for distribution use --dart-define=ENV=prod and require proper Firebase configuration.

What Warp should assume
- Use PowerShell commands on Windows (this repo provides Windows-friendly setup in README). Prefer python -m invocations for tools like uvicorn and pytest.
- Prefer environment variables for sensitive config (Firebase service account, API keys). Do not echo secrets.
