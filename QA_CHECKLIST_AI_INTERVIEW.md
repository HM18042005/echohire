# EchoHire AI Interview QA Checklist

This checklist enumerates common problem areas and test cases for the end-to-end Vapi Web SDK + FastAPI + Flutter WebView integration. Use it to triage failures quickly.

## 1) Environment and Secrets

- GOOGLE_AI_API_KEY
  - Present and non-placeholder
  - In non-prod environments, Gemini should be optional; backend must not crash without it
  - /debug/ai shows service_is_configured=true and model_ready=true when configured
- VAPI_API_KEY (private)
  - Present, sufficiently long (>= 20 chars)
  - Ends with expected suffix (sanity check)
  - /debug/env and /debug/ai report present and length
- VAPI_PUBLIC_KEY
  - Present for client-side init
  - Matches the key configured in Vapi dashboard
- VAPI_ASSISTANT_ID
  - Present or intentionally omitted (client will still need a valid assistantId)
- BACKEND_PUBLIC_URL (optional)
  - Set if needed for webhooks; we’re using client-posted callId flow (no webhook secret)

## 2) Backend Readiness

- Start endpoint returns ready_for_client_init for web calls
  - Fields: callId=web_call_client_side, assistantId, publicKey, metadata
- Status endpoint returns ready_for_client_init until real callId is posted
- Endpoint to accept real callId from client exists and stores/associates it
- GeminiAnalysisService
  - Optional import guarded; no crash if package missing
  - Early fallback used when key or package not available
- Logging
  - Key suffixes only (no secrets)
  - Response codes and bodies logged on error while avoiding sensitive data

## 3) Client (Flutter) WebView

- WebView permissions
  - Android: RECORD_AUDIO permission granted at OS level
  - WebView: onPermissionRequest grants for audio/camera (camera optional)
- Microphone contention
  - Ensure FlutterSound or other audio libraries are not active during WebView usage
- JavaScript enabled and channels wired
  - vapiCallId channel receives real call.id and posts to backend
  - callEnded channel signals completion

## 4) Vapi Web SDK Load

- CDN URLs
  - Primary: https://cdn.vapi.ai/sdk/vapi.min.js
  - Fallbacks:
    - https://cdn.jsdelivr.net/npm/@vapi-ai/web@latest/dist/vapi.min.js
    - https://unpkg.com/@vapi-ai/web@latest/dist/vapi.min.js
- Global detection
  - window.Vapi should exist after script load
  - Handle variations: window.Vapi.default or constructor under global
- Start invocation
  - Instantiate: const client = new Vapi(PUBLIC_KEY)
  - Start: client.start(ASSISTANT_ID)
  - Optionally attach metadata via backend association (not required by start)

## 5) Network/Device Constraints

- Device can reach CDN domains (cd n.vapi.ai, jsdelivr, unpkg)
- If CDNs blocked, self-host vapi.min.js under a known URL and load from there
- Mixed content: use HTTPS only; avoid http:// in any assets loaded by WebView

## 6) Call Lifecycle

- On start, receive real call.id from client and post to backend
- Backend status transitions from ready_for_client_init to in_progress/completed
- Transcript URL available after completion; backend get_call_transcript works or falls back

## 7) Error Handling Cases

- Vapi API 4xx/5xx are logged with body and mapped to user-friendly messages
- httpx timeouts yield timeout_error and recoverable UX
- Network errors produce network_error with retry guidance
- Unparseable Gemini output => text-based fallback analysis

## 8) Security & Privacy

- No secret logs; only last 8 chars displayed
- CORS/allowed origins configured on backend if needed by web clients
- If enabling webhooks later, ensure secret verification is implemented before switching on

## 9) Manual Test Steps (Happy Path)

1. Create interview; backend returns ready_for_client_init with assistantId/publicKey
2. WebView loads SDK (verify window.Vapi present)
3. client.start(assistantId) begins; callId received
4. Flutter posts callId to backend; status now in_progress
5. Complete call; verify status completed and transcript available
6. Run AI analysis; when Gemini configured, structured output is returned; otherwise fallback

## 10) Troubleshooting Quick Checks

- /debug/env and /debug/ai endpoints for configuration state
- Device logs for WebView permission prompts (deny vs allow)
- Console log inside WebView: did script load? is window.Vapi defined?
- Validate assistantId and publicKey pair against Vapi dashboard
- Disable competing audio capture libraries while testing
