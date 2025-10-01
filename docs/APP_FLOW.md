# EchoHire App Flow

## Environment Loading
- `AppConfig.load()` picks an `.env` file based on the `ENV` dart-define (`dev`, `device`, or `prod`) and loads runtime configuration.
- A `BASE_URL` entry is required; the app throws a `StateError` when it is missing to prevent silent fallbacks.
- Optional keys:
  - `VAPI_PUBLIC_KEY` – required for in-app web calls.
  - `VAPI_ASSISTANT_ID` – associates calls with a specific Vapi assistant.
  - `ENABLE_MOCKS` – explicitly opt-in to mock data in development; no longer defaults to on.

## Authentication
- `AuthService` wraps Firebase Authentication and exposes the current user and ID token retrieval.
- HTTP clients (`ApiService`, `ApiClient`) inject Firebase ID tokens into the `Authorization` header when available.

## Interview Lifecycle
1. **Guided creation**
   - `AIGuidedInterviewScreen` collects optional candidate details, interview type, and experience level.
   - The form submits to `ApiService.createAIGuidedInterview`, which returns both the interview record and initial start payload.
   - The returned payload is forwarded to `AIInterviewLauncher.launchFromStartData` to immediately begin the session.
2. **Workflow-assisted creation**
   - `WorkflowSetupScreen` orchestrates the conversational workflow endpoints (`/workflow/*`).
   - Once finalized, the workflow response is passed to `AIInterviewLauncher` to start the interview without hitting the deprecated AI screen.
3. **Existing interviews**
   - `InterviewDetailScreen` triggers `AIInterviewLauncher.startAndLaunch`, which requests `/interviews/{id}/start-ai` payloads for persisted interviews.

## AI Interview Launching
- `AIInterviewLauncher` normalizes backend responses and selects the appropriate launch path:
  - `status == ready_for_client_init` → in-app `VapiWebCallPage` (requires Vapi public key + assistant ID).
  - Web link present → opens in the external browser via `url_launcher`.
  - Call ID only → notifies the user to expect a phone call via a snackbar message.
- On successful in-app call completion, the user is routed to `InterviewResultsScreen`.

## Vapi Web Call Experience
- `VapiWebCallPage` embeds the hosted `/client/vapi-web` experience using `WebViewController`.
- Diagnostic messages from the embedded page are only surfaced in debug builds.
- The page sends the real `callId` back through a JavaScript channel so the app can notify the backend (`/interviews/{id}/vapi-call-id`).
- When the call ends, the page posts a message that leads to `/interviews/{id}/complete-ai` and then navigates back.

## State Management
- `InterviewController` and `ProfileController` use Riverpod `StateNotifier` classes to load data via `ApiService`/`ApiClient` without mock fallbacks.
- Errors from API calls now surface through controller state so UI layers can handle them explicitly.

## Deployment Readiness Highlights
- No console prints or debug logging remain in production code paths (logs guarded by `kDebugMode`).
- Mock data and silent fallback behaviour have been removed, ensuring failures are visible during testing.
- Environment configuration must be supplied before runtime, preventing accidental connections to invalid backends.
