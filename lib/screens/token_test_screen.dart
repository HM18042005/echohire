// Simple Flutter screen to get Firebase ID tokens for API testing
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:firebase_auth/firebase_auth.dart';

class TokenTestScreen extends StatefulWidget {
  const TokenTestScreen({super.key});

  @override
  State<TokenTestScreen> createState() => _TokenTestScreenState();
}

class _TokenTestScreenState extends State<TokenTestScreen> {
  String? _currentToken;
  bool _isLoading = false;

  Future<void> _getToken() async {
    setState(() => _isLoading = true);

    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user != null) {
        final token = await user.getIdToken();
        setState(() => _currentToken = token);
      } else {
        setState(() => _currentToken = 'No user logged in');
      }
    } catch (e) {
      setState(() => _currentToken = 'Error: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _copyToken() {
    if (_currentToken != null && _currentToken != 'No user logged in') {
      Clipboard.setData(ClipboardData(text: _currentToken!));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Token copied to clipboard!')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Firebase Token Test'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Get Firebase ID Token for API Testing',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _isLoading ? null : _getToken,
              child: _isLoading
                  ? const CircularProgressIndicator()
                  : const Text('Get Current Token'),
            ),
            const SizedBox(height: 20),
            if (_currentToken != null) ...[
              const Text(
                'Current Token:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: SelectableText(
                  _currentToken!,
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                ),
              ),
              const SizedBox(height: 10),
              ElevatedButton(
                onPressed: _copyToken,
                child: const Text('Copy Token'),
              ),
            ],
            const SizedBox(height: 40),
            const Text(
              'How to use this token:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              '1. Copy the token above\n'
              '2. Replace "YOUR_FIREBASE_TOKEN_HERE" in test scripts\n'
              '3. Use in Postman Authorization header: Bearer <token>\n'
              '4. Or use in curl: -H "Authorization: Bearer <token>"',
              style: TextStyle(fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}
