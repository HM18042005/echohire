import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class VapiWebCallPage extends StatefulWidget {
  final String publicKey;
  final String assistantId;
  final Map<String, dynamic> metadata;
  final VoidCallback? onCallEnded;

  const VapiWebCallPage({
    super.key,
    required this.publicKey,
    required this.assistantId,
    required this.metadata,
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
    <script src="https://cdn.jsdelivr.net/npm/@vapi-ai/web@latest/dist/vapi-web.min.js"></script>
    <style>
      html, body { margin: 0; padding: 0; height: 100%; background: #0b1021; color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; }
      #app { display: flex; align-items: center; justify-content: center; height: 100%; flex-direction: column; gap: 20px; text-align: center; padding: 20px; }
      .badge { padding: 8px 14px; border-radius: 999px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); }
      button { padding: 12px 22px; background: #3b82f6; color: #fff; border: none; border-radius: 12px; font-size: 16px; cursor: pointer; }
      button:disabled { background: #666; }
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

          updateStatus('Loading Vapi SDK…');
          if(!window.Vapi){ throw new Error('Vapi SDK failed to load'); }

          updateStatus('Creating Vapi client…');
          const client = new window.Vapi({ publicKey });

          updateStatus('Starting interview…');
          const call = await client.start({ assistantId, metadata });
          updateStatus('Interview started (ID: ' + (call && call.id ? call.id : 'unknown') + ')', true);

          client.on('call-start', () => updateStatus('Interview in progress…', true));
          client.on('speech-start', () => updateStatus('Listening…', true));
          client.on('speech-end', () => updateStatus('Processing your response…', true));
          client.on('call-end', () => { updateStatus('Interview completed.'); if (typeof callEnded !== 'undefined' && callEnded.postMessage) { callEnded.postMessage('done'); } });
          client.on('error', (e) => { updateStatus('Error: ' + (e && e.message ? e.message : e)); endBtn.style.display='inline-block'; endBtn.disabled=false; });

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
        onMessageReceived: (JavaScriptMessage message) {},
      )
      ..addJavaScriptChannel(
        'callEnded',
        onMessageReceived: (JavaScriptMessage _) {
          widget.onCallEnded?.call();
          if (mounted) Navigator.of(context).pop();
        },
      )
      ..loadHtmlString(_html);
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
