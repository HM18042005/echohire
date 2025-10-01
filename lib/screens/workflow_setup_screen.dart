import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../services/ai_interview_launcher.dart';
import '../models/interview.dart';

class WorkflowSetupScreen extends ConsumerStatefulWidget {
  const WorkflowSetupScreen({super.key});

  @override
  ConsumerState<WorkflowSetupScreen> createState() =>
      _WorkflowSetupScreenState();
}

class _WorkflowSetupScreenState extends ConsumerState<WorkflowSetupScreen> {
  final List<_Message> _messages = [];
  final TextEditingController _input = TextEditingController();
  final ScrollController _scroll = ScrollController();

  String? _sessionId;
  bool _loading = false;
  bool _finalizing = false;

  // Optional finalize extras
  final TextEditingController _companyCtrl = TextEditingController();
  DateTime? _interviewDate;

  Map<String, dynamic>? _latestState; // session_state from backend

  @override
  void initState() {
    super.initState();
    _startWorkflow();
  }

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    _companyCtrl.dispose();
    super.dispose();
  }

  Future<void> _startWorkflow() async {
    setState(() => _loading = true);
    try {
      final res = await ApiServiceSingleton.instance.workflowStart();
      _sessionId = res['sessionId']?.toString();
      final aiText = res['ai_response']?.toString() ?? 'Hello!';
      _latestState = res['session_state'] as Map<String, dynamic>?;
      _messages.add(_Message.ai(aiText));
      setState(() {});
      _scrollToBottom();
    } catch (e) {
      _showError('Failed to start workflow: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _sendMessage() async {
    final text = _input.text.trim();
    if (text.isEmpty || _sessionId == null) return;

    setState(() => _loading = true);
    _messages.add(_Message.user(text));
    _input.clear();
    _scrollToBottom();

    try {
      final res = await ApiServiceSingleton.instance.workflowMessage(
        sessionId: _sessionId!,
        text: text,
      );
      final ai = res['ai_response']?.toString() ?? '';
      _latestState = res['session_state'] as Map<String, dynamic>?;
      if (ai.isNotEmpty) _messages.add(_Message.ai(ai));
      setState(() {});
      _scrollToBottom();
    } catch (e) {
      _showError('Failed to send message: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  bool get _readyToFinalize {
    final s = _latestState ?? {};
    final hasRole = (s['job_role']?.toString().isNotEmpty ?? false);
    final hasType = (s['interview_type']?.toString().isNotEmpty ?? false);
    final hasLevel = (s['experience_level']?.toString().isNotEmpty ?? false);
    return hasRole && hasType && hasLevel;
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final initial = _interviewDate ?? now.add(const Duration(days: 1));
    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: now,
      lastDate: now.add(const Duration(days: 365)),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: Theme.of(
              context,
            ).colorScheme.copyWith(primary: Colors.blue),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) setState(() => _interviewDate = picked);
  }

  Future<void> _finalize() async {
    if (!_readyToFinalize || _sessionId == null) {
      _showError('Please complete role, type, and level first.');
      return;
    }

    setState(() => _finalizing = true);

    try {
      final iso = _interviewDate?.toUtc().toIso8601String();
      final res = await ApiServiceSingleton.instance.workflowFinalize(
        sessionId: _sessionId!,
        companyName: _companyCtrl.text.trim().isNotEmpty
            ? _companyCtrl.text.trim()
            : null,
        interviewDateIso: iso,
        autoStart: true,
      );

      final interviewJson = (res['interview'] ?? {}) as Map<String, dynamic>;
      if (interviewJson.isEmpty) throw Exception('No interview in response');
      final interview = Interview.fromJson(interviewJson);

      final start = res['start'] as Map<String, dynamic>?;

      if (!mounted) return;

      await AIInterviewLauncher.launchFromStartData(
        context,
        interview: interview,
        startData: start,
      );
    } catch (e) {
      _showError('Failed to finalize: $e');
    } finally {
      if (mounted) setState(() => _finalizing = false);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent + 80,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E1E1E),
        title: const Text('Guided Setup (AI)'),
        actions: [
          if (_readyToFinalize)
            TextButton.icon(
              onPressed: _finalizing ? null : _finalize,
              icon: const Icon(
                Icons.play_circle_fill,
                color: Colors.blueAccent,
              ),
              label: Text(
                _finalizing ? 'Starting…' : 'Start Interview',
                style: const TextStyle(color: Colors.blueAccent),
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          // Messages
          Expanded(
            child: ListView.builder(
              controller: _scroll,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length + 1,
              itemBuilder: (context, i) {
                if (i == _messages.length) {
                  return _FinalizeExtras(
                    companyCtrl: _companyCtrl,
                    interviewDate: _interviewDate,
                    onPickDate: _pickDate,
                    ready: _readyToFinalize,
                  );
                }
                final m = _messages[i];
                final isAi = m.isAi;
                return Align(
                  alignment: isAi
                      ? Alignment.centerLeft
                      : Alignment.centerRight,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(12),
                    constraints: const BoxConstraints(maxWidth: 640),
                    decoration: BoxDecoration(
                      color: isAi ? const Color(0xFF1E1E1E) : Colors.blue,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      m.text,
                      style: TextStyle(
                        color: isAi ? Colors.white : Colors.white,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),

          // Input row
          Container(
            color: const Color(0xFF0A0A0A),
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _input,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      isDense: true,
                      filled: true,
                      fillColor: const Color(0xFF2C2C2C),
                      hintText: _loading
                          ? 'Please wait…'
                          : 'Type your response…',
                      hintStyle: const TextStyle(color: Colors.grey),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    enabled: !_loading,
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _loading ? null : _sendMessage,
                  child: _loading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send, size: 18),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FinalizeExtras extends StatelessWidget {
  final TextEditingController companyCtrl;
  final DateTime? interviewDate;
  final VoidCallback onPickDate;
  final bool ready;

  const _FinalizeExtras({
    required this.companyCtrl,
    required this.interviewDate,
    required this.onPickDate,
    required this.ready,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 8),
        Text(
          'Optional details before starting',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Colors.grey,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: companyCtrl,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            labelText: 'Company',
            labelStyle: const TextStyle(color: Colors.grey),
            filled: true,
            fillColor: const Color(0xFF2C2C2C),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none,
            ),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 14,
                ),
                decoration: BoxDecoration(
                  color: const Color(0xFF2C2C2C),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  interviewDate == null
                      ? 'Interview Date (optional)'
                      : '${interviewDate!.day}/${interviewDate!.month}/${interviewDate!.year}',
                  style: const TextStyle(color: Colors.white),
                ),
              ),
            ),
            const SizedBox(width: 8),
            ElevatedButton.icon(
              onPressed: onPickDate,
              icon: const Icon(Icons.calendar_today),
              label: const Text('Pick'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        if (!ready)
          Row(
            children: [
              const Icon(Icons.info_outline, size: 16, color: Colors.orange),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'Complete role, type, and level with the assistant to enable Start.',
                  style: Theme.of(
                    context,
                  ).textTheme.bodySmall?.copyWith(color: Colors.orange),
                ),
              ),
            ],
          ),
        const SizedBox(height: 8),
      ],
    );
  }
}

class _Message {
  final String text;
  final bool isAi;
  _Message(this.text, this.isAi);
  factory _Message.ai(String t) => _Message(t, true);
  factory _Message.user(String t) => _Message(t, false);
}
