import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AIGuidedInterviewScreen extends StatefulWidget {
  const AIGuidedInterviewScreen({super.key});

  @override
  State<AIGuidedInterviewScreen> createState() =>
      _AIGuidedInterviewScreenState();
}

class _AIGuidedInterviewScreenState extends State<AIGuidedInterviewScreen> {
  final _formKey = GlobalKey<FormState>();
  final _companyNameController = TextEditingController();

  bool _loading = false;
  String? _statusMessage;

  @override
  void dispose() {
    _companyNameController.dispose();
    super.dispose();
  }

  Future<void> _startAIGuidedInterview() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _loading = true;
      _statusMessage = 'Setting up your AI guided interview...';
    });

    try {
      final apiService = ApiService();
      final result = await apiService.createAIGuidedInterview(
        companyName: _companyNameController.text.trim(),
      );

      setState(() {
        _statusMessage = 'Interview session created successfully!';
        _loading = false;
      });

      _showSuccessDialog(result);
    } catch (e) {
      setState(() {
        _statusMessage = 'Error: ${e.toString()}';
        _loading = false;
      });
    }
  }

  void _showSuccessDialog(Map<String, dynamic> result) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('🤖 AI Interview Session Ready'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Your AI guided interview session has been created successfully!',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 16),
            Text('Session ID: ${result['sessionId'] ?? 'N/A'}'),
            Text('Interview ID: ${result['interviewId'] ?? 'N/A'}'),
            Text('Status: ${result['status'] ?? 'Created'}'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              Navigator.of(context).pop(); // Go back to home
            },
            child: const Text('Got it!'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🤖 AI Guided Interview'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'AI Guided Interview',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              const Text(
                'Start with just your company name. Our AI assistant will ask about job role, experience level, and interview type during the conversation.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, color: Colors.grey),
              ),
              const SizedBox(height: 32),
              TextFormField(
                controller: _companyNameController,
                decoration: const InputDecoration(
                  labelText: 'Company Name *',
                  hintText: 'e.g., InnovateTech Solutions',
                  prefixIcon: Icon(Icons.business),
                  border: OutlineInputBorder(),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter the company name';
                  }
                  return null;
                },
                textCapitalization: TextCapitalization.words,
              ),
              const SizedBox(height: 32),
              ElevatedButton.icon(
                onPressed: _loading ? null : _startAIGuidedInterview,
                icon: _loading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.rocket_launch),
                label: Text(
                  _loading ? 'Setting up...' : 'Start AI Guided Interview',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
              const SizedBox(height: 24),
              if (_statusMessage != null)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: _statusMessage!.startsWith('Error')
                        ? Colors.red.shade50
                        : Colors.green.shade50,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _statusMessage!.startsWith('Error')
                          ? Colors.red.shade200
                          : Colors.green.shade200,
                    ),
                  ),
                  child: Text(
                    _statusMessage!,
                    style: TextStyle(
                      color: _statusMessage!.startsWith('Error')
                          ? Colors.red.shade700
                          : Colors.green.shade700,
                      fontSize: 14,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
