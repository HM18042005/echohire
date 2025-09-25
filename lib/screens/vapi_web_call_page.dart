import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:echohire/services/api_service.dart';
import 'package:echohire/config.dart';

class VapiWebCallPage extends StatefulWidget {
  final String publicKey;
  final String assistantId;
  final Map<String, dynamic> metadata;
  final String interviewId;
  final VoidCallback? onCallEnded;

  const VapiWebCallPage({
    super.key,
    required this.publicKey,
    required this.assistantId,
    required this.metadata,
    required this.interviewId,
    this.onCallEnded,
  });

  @override
  State<VapiWebCallPage> createState() => _VapiWebCallPageState();
}

class _VapiWebCallPageState extends State<VapiWebCallPage> {
  late final WebViewController _controller;
  bool _isLoading = true;

  String get _html =>
      '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>EchoHire AI Interview</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  <!-- Vapi SDK will be loaded dynamically (jsdelivr ➜ unpkg fallback) -->
    <style>
      html, body { margin: 0; padding: 0; height: 100%; background: #0b1021; color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; }
      #app { display: flex; align-items: center; justify-content: center; height: 100%; flex-direction: column; gap: 20px; text-align: center; padding: 20px; }
      .badge { padding: 8px 14px; border-radius: 999px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); }
      button { padding: 12px 22px; background: #3b82f6; color: #fff; border: none; border-radius: 12px; font-size: 16px; cursor: pointer; }
      button:disabled { background: #666; }
      .hidden { display: none; }
    </style>
  </head>
  <body>
    <div id="app">
      <div style="font-size:18px; opacity:.9">EchoHire • AI Interview</div>
      <div id="status" class="badge">Preparing interview…</div>
      <button id="endBtn" class="hidden" disabled>End Interview</button>
    </div>
    <script>
      (async () => {
        const statusEl = document.getElementById('status');
        const endBtn = document.getElementById('endBtn');

        function updateStatus(msg, showBtn=false){
          statusEl.textContent = msg;
          if(showBtn){ endBtn.style.display='inline-block'; endBtn.disabled=false; }
          try {
            if (typeof statusUpdate !== 'undefined' && statusUpdate.postMessage) {
              statusUpdate.postMessage(msg);
            }
          } catch (e) { /* no-op */ }
        }

        try {
          const publicKey = ${jsonEncode(widget.publicKey)};
          const assistantId = ${jsonEncode(widget.assistantId)};
          const metadata = ${jsonEncode(widget.metadata)};

          // Capture global errors and unhandled promise rejections to aid debugging
          window.onerror = function(message, source, lineno, colno, error) {
            try {
              const payload = {
                type: 'window.onerror', message, source, lineno, colno,
                error: error && { name: error.name, message: error.message, stack: error.stack }
              };
              if (typeof statusUpdate !== 'undefined' && statusUpdate.postMessage) {
                statusUpdate.postMessage('[VapiWebView] GlobalError: ' + JSON.stringify(payload));
              }
            } catch(_){}
          };
          window.addEventListener('unhandledrejection', function(ev){
            try {
              const reason = ev && (ev.reason || ev.detail || ev.message || ev);
              const payload = { type: 'unhandledrejection', reason };
              if (typeof statusUpdate !== 'undefined' && statusUpdate.postMessage) {
                statusUpdate.postMessage('[VapiWebView] UnhandledRejection: ' + (typeof reason === 'object' ? JSON.stringify(reason) : String(reason)));
              }
            } catch(_){}
          });

          // Dynamically load Vapi SDK UMD build from CDN with fallbacks
          async function loadScript(src) {
            return new Promise((resolve, reject) => {
              const s = document.createElement('script');
              s.src = src;
              s.async = true;
              s.crossOrigin = 'anonymous';
              s.onload = () => resolve();
              s.onerror = (e) => reject(e);
              document.head.appendChild(s);
            });
          }

          updateStatus('Loading Vapi SDK…');
          const cdnBases = [
            'https://cdn.jsdelivr.net/npm/@vapi-ai/web@latest',
            'https://fastly.jsdelivr.net/npm/@vapi-ai/web@latest',
            'https://unpkg.com/@vapi-ai/web@latest',
          ];
          const paths = [
            // The official dist contains vapi.js (no minified UMD published)
            '/dist/vapi.js',
            // additional alt names as last resorts (in case packaging changes)
            '/vapi.js',
          ];
          for (let i = 0; !window.Vapi && i < cdnBases.length; i++) {
            for (let j = 0; !window.Vapi && j < paths.length; j++) {
              const url = cdnBases[i] + paths[j];
              try {
                updateStatus('Loading SDK from: ' + url);
                await loadScript(url);
              } catch (e) {
                // Continue trying next
              }
            }
          }

          if (!window.Vapi) {
            // Fallback: try dynamic ESM imports when the CDN serves non-UMD builds
            updateStatus('Falling back to ESM import…');
            const esmCandidates = [
              'https://cdn.jsdelivr.net/npm/@vapi-ai/web@latest/+esm',
              'https://unpkg.com/@vapi-ai/web@latest?module',
              'https://esm.sh/@vapi-ai/web@latest',
            ];
            let esmModule = null;
            for (let k = 0; !esmModule && k < esmCandidates.length; k++) {
              const url = esmCandidates[k];
              try {
                updateStatus('Importing ESM from: ' + url);
                // Dynamic import may fail on very old WebViews; try-catch continues to next candidate
                // @ts-ignore
                esmModule = await import(url);
              } catch (e) {
                // continue
              }
            }
            if (esmModule && (esmModule.default || esmModule.Vapi)) {
              // Attach constructor for uniform handling below
              window.Vapi = esmModule.default || esmModule.Vapi;
            }
            // As a last resort, inject a module script that imports and binds to window.Vapi
            if (!window.Vapi) {
              for (let m = 0; !window.Vapi && m < esmCandidates.length; m++) {
                const url = esmCandidates[m];
                try {
                  updateStatus('Injecting module script from: ' + url);
                  await new Promise((resolve, reject) => {
                    const script = document.createElement('script');
                    script.type = 'module';
                    script.crossOrigin = 'anonymous';
                    script.textContent = "import * as Mod from '" + url + "'; window.Vapi = Mod.default || Mod.Vapi; window.dispatchEvent(new Event('VapiReady'));";
                    const onReady = () => { window.removeEventListener('VapiReady', onReady); resolve(); };
                    window.addEventListener('VapiReady', onReady);
                    script.onerror = reject;
                    document.head.appendChild(script);
                  });
                } catch (e) {
                  // continue
                }
              }
            }
          }

          if (!window.Vapi) {
            throw new Error('Vapi SDK failed to load');
          }

          // Helpful: log UA to Flutter for debugging
          try { updateStatus('UA: ' + navigator.userAgent); } catch (_) {}

          updateStatus('Creating Vapi client…');
          let client;
          let VapiCtor = null;
          if (typeof window.Vapi === 'function') VapiCtor = window.Vapi;
          else if (window.Vapi && typeof window.Vapi.default === 'function') VapiCtor = window.Vapi.default;
          else if (window.Vapi && typeof window.Vapi.Vapi === 'function') VapiCtor = window.Vapi.Vapi;
          if (!VapiCtor) {
            throw new Error('Vapi constructor not found after SDK load');
          }
          try {
            client = new VapiCtor(publicKey);
          } catch (_) {
            client = new VapiCtor({ publicKey });
          }

          // Attach critical listeners BEFORE starting the call to avoid uncaught 'error' events
          const logError = (label, e) => {
            try {
              const msg = (e && e.message) ? e.message : (typeof e === 'object' ? JSON.stringify(e) : String(e));
              updateStatus(label + ': ' + msg, true);
              if (typeof statusUpdate !== 'undefined' && statusUpdate.postMessage) {
                const details = {
                  label,
                  name: e && e.name,
                  message: e && e.message,
                  stack: e && e.stack,
                  code: e && (e.code || e.error || e.type),
                };
                statusUpdate.postMessage('[VapiWebView] Error: ' + JSON.stringify(details));
              }
            } catch(_){}
          };
          client.on('error', (e) => logError('Error', e));
          // Common additional events for deeper insight
          try { client.on('warning', (e) => updateStatus('Warning: ' + (e && e.message ? e.message : e), true)); } catch(_){}
          try { client.on('call-failed', (e) => logError('Call failed', e)); } catch(_){}
          try { client.on('daily-error', (e) => logError('Daily error', e)); } catch(_){}

          // Helper: attempt to extract a callId from various shapes
          const tryExtractId = (obj) => {
            if (!obj) return null;
            const candidates = ['id', 'callId', 'call_id', 'uuid', 'roomId', 'roomName'];
            for (const k of candidates) {
              if (obj && typeof obj[k] === 'string' && obj[k]) return obj[k];
            }
            // nested common containers
            if (obj.call) {
              for (const k of candidates) {
                if (obj.call && typeof obj.call[k] === 'string' && obj.call[k]) return obj.call[k];
              }
            }
            if (obj.data) {
              for (const k of candidates) {
                if (obj.data && typeof obj.data[k] === 'string' && obj.data[k]) return obj.data[k];
              }
            }
            return null;
          };
          const safeStringify = (v) => { try { return JSON.stringify(v); } catch(_) { return String(v); } };
          let sentCallId = false;
          const maybeSendCallId = (src, payload) => {
            if (sentCallId) return;
            const cid = tryExtractId(payload) || tryExtractId(client) || tryExtractId((client && client.call) || null);
            if (cid && typeof vapiCallId !== 'undefined' && vapiCallId.postMessage) {
              try {
                vapiCallId.postMessage(JSON.stringify({ callId: cid, assistantId, metadata }));
                sentCallId = true;
                updateStatus('Call ID captured from ' + src + ': ' + cid, true);
              } catch(_){}
            }
          };

          updateStatus('Starting interview…');
          // Start the call: SDK expects assistantId (string). Metadata association is handled server-side.
          let call;
          try {
            call = await client.start(assistantId);
          } catch (e) {
            logError('Start failed', e);
            throw e; // ensure UI shows error state and button appears
          }
          // Log returned call payload for diagnostics
          try { updateStatus('Start returned: ' + safeStringify(call)); } catch(_){}
          const immediateId = tryExtractId(call);
          updateStatus('Interview started (ID: ' + (immediateId || 'unknown') + ')', true);
          maybeSendCallId('start()', call);

          // Notify Flutter about the real callId so it can send to backend
          try {
            if (call && call.id && typeof vapiCallId !== 'undefined' && vapiCallId.postMessage) {
              vapiCallId.postMessage(JSON.stringify({ callId: call.id, assistantId, metadata }));
            }
          } catch (_) {}

          client.on('call-start', (evt) => { updateStatus('Interview in progress…', true); try { updateStatus('call-start evt: ' + safeStringify(evt)); } catch(_){} maybeSendCallId('call-start', evt); });
          client.on('speech-start', () => updateStatus('Listening…', true));
          client.on('speech-end', () => updateStatus('Processing your response…', true));
          client.on('call-end', () => { updateStatus('Interview completed.'); if (typeof callEnded !== 'undefined' && callEnded.postMessage) { callEnded.postMessage('done'); } });

          endBtn.onclick = async () => { try { endBtn.disabled=true; updateStatus('Ending…'); await client.stop(); updateStatus('Ended.'); if (typeof callEnded !== 'undefined' && callEnded.postMessage) { callEnded.postMessage('ended'); } } catch(e){ updateStatus('Failed to end: ' + (e && e.message ? e.message : e)); endBtn.disabled=false; } };
        } catch (e){ updateStatus('Error: ' + (e && e.message ? e.message : e)); endBtn.style.display='inline-block'; endBtn.disabled=false; }
      })();
    </script>
  </body>
</html>
''';

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageFinished: (_) => setState(() => _isLoading = false),
        ),
      )
      ..addJavaScriptChannel(
        'statusUpdate',
        onMessageReceived: (JavaScriptMessage message) {
          // Print status updates from the embedded page to help diagnose SDK loading
          // and call lifecycle events.
          // Example messages: "Loading SDK from: <url>", "Creating Vapi client…", etc.
          // You can also surface these in the UI if needed.
          // ignore: avoid_print
          print('[VapiWebView] ${message.message}');
        },
      )
      ..addJavaScriptChannel(
        'vapiCallId',
        onMessageReceived: (JavaScriptMessage message) async {
          try {
            final payload = jsonDecode(message.message) as Map<String, dynamic>;
            final callId = payload['callId']?.toString();
            final assistantId = payload['assistantId']?.toString();
            final meta = (payload['metadata'] is Map<String, dynamic>)
                ? payload['metadata'] as Map<String, dynamic>
                : <String, dynamic>{};
            if (callId != null && callId.isNotEmpty) {
              // Send to backend so status polling can use real callId
              await ApiServiceSingleton.instance.sendVapiCallId(
                interviewId: widget.interviewId,
                callId: callId,
                assistantId: assistantId,
                metadata: meta,
              );
            }
          } catch (e) {
            // no-op
          }
        },
      )
      ..addJavaScriptChannel(
        'callEnded',
        onMessageReceived: (JavaScriptMessage _) {
          widget.onCallEnded?.call();
          if (mounted) Navigator.of(context).pop();
        },
      );

    // Android-specific permission grants for WebRTC/microphone
    if (_controller.platform is AndroidWebViewController) {
      final androidController =
          _controller.platform as AndroidWebViewController;
      AndroidWebViewController.enableDebugging(true);
      androidController.setMediaPlaybackRequiresUserGesture(false);
      androidController.setOnPlatformPermissionRequest((request) {
        // Grant all requested resources (e.g., AUDIO_CAPTURE, VIDEO_CAPTURE)
        request.grant();
      });
    }

    _prepareAndLoad();
  }

  Future<void> _prepareAndLoad() async {
    // Ensure OS microphone permission is granted before initializing the SDK
    final status = await Permission.microphone.request();
    if (!status.isGranted) {
      // Still load the page; SDK will likely fail to capture mic until granted
    }
    // Prefer loading the backend-hosted page to ensure a proper HTTPS origin for WebRTC
    try {
      final uri = Uri.parse(AppConfig.baseUrl).replace(
        path: '/client/vapi-web',
        queryParameters: {
          'publicKey': widget.publicKey,
          'assistantId': widget.assistantId,
          'interviewId': widget.interviewId,
          // Pass raw JSON; Uri will encode it and the page will decode+parse
          'metadata': jsonEncode(widget.metadata),
        },
      );
      await _controller.loadRequest(uri);
    } catch (e) {
      // Fallback: inline HTML (may hit null-origin/CORS in some environments)
      await _controller.loadHtmlString(_html);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0b1021),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        iconTheme: const IconThemeData(color: Colors.white),
        title: const Text(
          'AI Interview',
          style: TextStyle(color: Colors.white),
        ),
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_isLoading) const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}
