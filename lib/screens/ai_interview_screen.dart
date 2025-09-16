import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:permission_handler/permission_handler.dart';
import '../models/interview.dart';

/// AIInterviewScreen manages the live AI interview experience
class AIInterviewScreen extends ConsumerStatefulWidget {
  final Interview interview;
  final Map<String, dynamic> sessionData;

  const AIInterviewScreen({
    super.key,
    required this.interview,
    required this.sessionData,
  });

  @override
  ConsumerState<AIInterviewScreen> createState() => _AIInterviewScreenState();
}

class _AIInterviewScreenState extends ConsumerState<AIInterviewScreen>
    with TickerProviderStateMixin {
  // Audio recording and TTS
  FlutterSoundRecorder? _recorder;
  FlutterTts? _flutterTts;

  // Interview state
  InterviewState _currentState = InterviewState.initializing;
  int _currentQuestionIndex = 0;
  String _currentQuestion = '';

  // Conversation log
  final List<ConversationEntry> _conversationLog = [];

  // Controllers
  final ScrollController _conversationScrollController = ScrollController();

  // Animation controllers
  late AnimationController _pulseAnimationController;
  late AnimationController _waveAnimationController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _waveAnimation;

  // Timing
  Duration _recordingDuration = Duration.zero;
  Duration _totalInterviewDuration = Duration.zero;

  // UI state
  bool _isRecording = false;
  bool _isSpeaking = false;
  bool _showInstructions = true;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _initializeAudio();
    _startInterview();
  }

  @override
  void dispose() {
    _pulseAnimationController.dispose();
    _waveAnimationController.dispose();
    _conversationScrollController.dispose();
    _recorder?.closeRecorder();
    _flutterTts?.stop();
    super.dispose();
  }

  void _initializeAnimations() {
    _pulseAnimationController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    _waveAnimationController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );

    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(
        parent: _pulseAnimationController,
        curve: Curves.easeInOut,
      ),
    );

    _waveAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _waveAnimationController,
        curve: Curves.easeInOut,
      ),
    );
  }

  Future<void> _initializeAudio() async {
    try {
      // Request microphone permission
      final status = await Permission.microphone.request();
      if (status != PermissionStatus.granted) {
        _showError('Microphone permission is required for the interview');
        return;
      }

      // Initialize recorder
      _recorder = FlutterSoundRecorder();
      await _recorder!.openRecorder();

      // Initialize TTS
      _flutterTts = FlutterTts();
      await _flutterTts!.setLanguage('en-US');
      await _flutterTts!.setSpeechRate(0.5);
      await _flutterTts!.setVolume(1.0);
      await _flutterTts!.setPitch(1.0);

      // Set TTS completion callback
      _flutterTts!.setCompletionHandler(() {
        setState(() {
          _isSpeaking = false;
          _currentState = InterviewState.waitingForAnswer;
        });
      });
    } catch (e) {
      _showError('Failed to initialize audio: $e');
    }
  }

  Future<void> _startInterview() async {
    setState(() {
      _currentState = InterviewState.starting;
    });

    _addToConversationLog(
      ConversationEntry(
        speaker: Speaker.ai,
        content:
            'Welcome to your AI interview practice session! I\'ll be asking you questions about the ${widget.interview.jobTitle} position. Let\'s begin.',
        timestamp: DateTime.now(),
      ),
    );

    await _speakText(
      'Welcome to your AI interview practice session! I\'ll be asking you questions about the ${widget.interview.jobTitle} position. Let\'s begin.',
    );

    await Future.delayed(const Duration(seconds: 2));
    _askNextQuestion();
  }

  Future<void> _askNextQuestion() async {
    if (_currentQuestionIndex >= _getMockQuestions().length) {
      _endInterview();
      return;
    }

    setState(() {
      _currentState = InterviewState.askingQuestion;
      _currentQuestion = _getMockQuestions()[_currentQuestionIndex];
    });

    _addToConversationLog(
      ConversationEntry(
        speaker: Speaker.ai,
        content: 'Question ${_currentQuestionIndex + 1}: $_currentQuestion',
        timestamp: DateTime.now(),
      ),
    );

    await _speakText(
      'Question ${_currentQuestionIndex + 1}: $_currentQuestion',
    );
  }

  Future<void> _speakText(String text) async {
    if (_flutterTts == null) return;

    setState(() {
      _isSpeaking = true;
    });

    _pulseAnimationController.repeat(reverse: true);
    await _flutterTts!.speak(text);
  }

  Future<void> _startRecording() async {
    if (_recorder == null || _isRecording) return;

    try {
      setState(() {
        _isRecording = true;
        _currentState = InterviewState.recording;
        _recordingDuration = Duration.zero;
      });

      _waveAnimationController.repeat();

      await _recorder!.startRecorder(
        toFile: 'temp_recording.aac',
        codec: Codec.aacADTS,
      );

      // Start timer for recording duration
      _startRecordingTimer();
    } catch (e) {
      _showError('Failed to start recording: $e');
      setState(() {
        _isRecording = false;
      });
    }
  }

  Future<void> _stopRecording() async {
    if (_recorder == null || !_isRecording) return;

    try {
      final path = await _recorder!.stopRecorder();

      setState(() {
        _isRecording = false;
        _currentState = InterviewState.processingAnswer;
      });

      _waveAnimationController.stop();
      _waveAnimationController.reset();

      // Add user's response to conversation log
      _addToConversationLog(
        ConversationEntry(
          speaker: Speaker.user,
          content: 'Audio response recorded ($_recordingDuration seconds)',
          timestamp: DateTime.now(),
          audioPath: path,
        ),
      );

      // Simulate processing and AI feedback
      await _processUserResponse();
    } catch (e) {
      _showError('Failed to stop recording: $e');
    }
  }

  void _startRecordingTimer() {
    Future.delayed(const Duration(seconds: 1), () {
      if (_isRecording) {
        setState(() {
          _recordingDuration = Duration(
            seconds: _recordingDuration.inSeconds + 1,
          );
        });
        _startRecordingTimer();
      }
    });
  }

  Future<void> _processUserResponse() async {
    // Simulate AI processing time
    await Future.delayed(const Duration(seconds: 2));

    // Generate mock feedback
    final feedback = _generateMockFeedback();

    _addToConversationLog(
      ConversationEntry(
        speaker: Speaker.ai,
        content: feedback,
        timestamp: DateTime.now(),
      ),
    );

    await _speakText(feedback);

    // Move to next question
    _currentQuestionIndex++;
    await Future.delayed(const Duration(seconds: 1));
    _askNextQuestion();
  }

  Future<void> _endInterview() async {
    setState(() {
      _currentState = InterviewState.completed;
    });

    _pulseAnimationController.stop();
    _waveAnimationController.stop();

    final endMessage =
        'Congratulations! You\'ve completed the interview. I\'ll now generate your performance report.';

    _addToConversationLog(
      ConversationEntry(
        speaker: Speaker.ai,
        content: endMessage,
        timestamp: DateTime.now(),
      ),
    );

    await _speakText(endMessage);

    // Show completion dialog after a delay
    Future.delayed(const Duration(seconds: 3), () {
      _showCompletionDialog();
    });
  }

  void _addToConversationLog(ConversationEntry entry) {
    setState(() {
      _conversationLog.add(entry);
    });

    // Auto-scroll to bottom
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_conversationScrollController.hasClients) {
        _conversationScrollController.animateTo(
          _conversationScrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async {
        final shouldExit = await _showExitDialog();
        return shouldExit ?? false;
      },
      child: Scaffold(
        backgroundColor: const Color(0xFF0A0A0A),
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          title: Text('AI Interview - ${widget.interview.jobTitle}'),
          leading: IconButton(
            icon: const Icon(Icons.close, color: Colors.white),
            onPressed: () async {
              final shouldExit = await _showExitDialog();
              if (shouldExit == true && mounted) {
                Navigator.pop(context);
              }
            },
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.info_outline),
              onPressed: () => _showInstructionsDialog(),
            ),
          ],
        ),
        body: Column(
          children: [
            // Status Bar
            _buildStatusBar(),

            // Main Content
            Expanded(
              child: _showInstructions
                  ? _buildInstructions()
                  : _buildInterviewInterface(),
            ),

            // Controls
            _buildControls(),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: _getStatusColor().withOpacity(0.2),
        border: Border(
          bottom: BorderSide(color: _getStatusColor().withOpacity(0.3)),
        ),
      ),
      child: Row(
        children: [
          Icon(_getStatusIcon(), color: _getStatusColor(), size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _getStatusText(),
              style: TextStyle(
                color: _getStatusColor(),
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          Text(
            'Q${_currentQuestionIndex + 1}/${_getMockQuestions().length}',
            style: const TextStyle(color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildInstructions() {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.school, size: 80, color: Colors.blue),
          const SizedBox(height: 24),
          Text(
            'Interview Instructions',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 16),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '📍 How the AI Interview Works:',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  SizedBox(height: 12),
                  Text('• The AI will ask you questions one by one'),
                  Text('• Listen carefully to each question'),
                  Text('• Tap the microphone to start recording your answer'),
                  Text('• Speak clearly and at a normal pace'),
                  Text('• Tap stop when you\'re finished answering'),
                  Text(
                    '• The AI will provide feedback and move to the next question',
                  ),
                  SizedBox(height: 16),
                  Text(
                    '💡 Tips for Success:',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  SizedBox(height: 8),
                  Text('• Find a quiet environment'),
                  Text('• Speak at a moderate pace'),
                  Text('• Be specific and give examples'),
                  Text('• Stay calm and confident'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _showInstructions = false;
              });
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue,
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
            ),
            child: const Text('Start Interview'),
          ),
        ],
      ),
    );
  }

  Widget _buildInterviewInterface() {
    return Column(
      children: [
        // Conversation Log
        Expanded(flex: 3, child: _buildConversationLog()),

        // Visual Feedback Area
        Expanded(flex: 2, child: _buildVisualFeedback()),
      ],
    );
  }

  Widget _buildConversationLog() {
    return Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.withOpacity(0.1),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(12),
                topRight: Radius.circular(12),
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.chat, color: Colors.blue),
                const SizedBox(width: 8),
                const Text(
                  'Conversation Log',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                Text(
                  '${_conversationLog.length} messages',
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView.builder(
              controller: _conversationScrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _conversationLog.length,
              itemBuilder: (context, index) {
                final entry = _conversationLog[index];
                return _buildConversationEntry(entry);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConversationEntry(ConversationEntry entry) {
    final isAI = entry.speaker == Speaker.ai;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isAI) const Spacer(),
          Flexible(
            flex: 4,
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isAI
                    ? Colors.blue.withOpacity(0.2)
                    : Colors.green.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: isAI
                      ? Colors.blue.withOpacity(0.3)
                      : Colors.green.withOpacity(0.3),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        isAI ? Icons.smart_toy : Icons.person,
                        size: 16,
                        color: isAI ? Colors.blue : Colors.green,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        isAI ? 'AI Interviewer' : 'You',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: isAI ? Colors.blue : Colors.green,
                          fontSize: 12,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '${entry.timestamp.hour.toString().padLeft(2, '0')}:${entry.timestamp.minute.toString().padLeft(2, '0')}',
                        style: const TextStyle(
                          color: Colors.grey,
                          fontSize: 10,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    entry.content,
                    style: const TextStyle(color: Colors.white),
                  ),
                  if (entry.audioPath != null) ...[
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(
                          Icons.audiotrack,
                          size: 16,
                          color: Colors.grey,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          'Audio Recording',
                          style: TextStyle(
                            color: Colors.grey[400],
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),
          if (isAI) const Spacer(),
        ],
      ),
    );
  }

  Widget _buildVisualFeedback() {
    return Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.withOpacity(0.3)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (_isRecording) ...[
            AnimatedBuilder(
              animation: _waveAnimation,
              builder: (context, child) {
                return Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: Colors.red.withOpacity(
                        0.5 + 0.5 * _waveAnimation.value,
                      ),
                      width: 3,
                    ),
                  ),
                  child: const Icon(Icons.mic, size: 48, color: Colors.red),
                );
              },
            ),
            const SizedBox(height: 16),
            Text(
              'Recording... ${_recordingDuration.inSeconds}s',
              style: const TextStyle(
                color: Colors.red,
                fontWeight: FontWeight.bold,
              ),
            ),
          ] else if (_isSpeaking) ...[
            AnimatedBuilder(
              animation: _pulseAnimation,
              builder: (context, child) {
                return Transform.scale(
                  scale: _pulseAnimation.value,
                  child: Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.blue.withOpacity(0.3),
                      border: Border.all(color: Colors.blue, width: 3),
                    ),
                    child: const Icon(
                      Icons.volume_up,
                      size: 48,
                      color: Colors.blue,
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 16),
            const Text(
              'AI is speaking...',
              style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
            ),
          ] else ...[
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.grey.withOpacity(0.2),
                border: Border.all(color: Colors.grey, width: 2),
              ),
              child: Icon(_getMainIcon(), size: 48, color: Colors.grey),
            ),
            const SizedBox(height: 16),
            Text(
              _getMainMessage(),
              style: const TextStyle(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildControls() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        border: Border(top: BorderSide(color: Colors.grey.withOpacity(0.3))),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          // Recording Control
          if (_currentState == InterviewState.waitingForAnswer) ...[
            if (!_isRecording) ...[
              ElevatedButton.icon(
                onPressed: _startRecording,
                icon: const Icon(Icons.mic),
                label: const Text('Start Recording'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                ),
              ),
            ] else ...[
              ElevatedButton.icon(
                onPressed: _stopRecording,
                icon: const Icon(Icons.stop),
                label: const Text('Stop Recording'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.grey,
                  foregroundColor: Colors.white,
                ),
              ),
            ],
          ] else ...[
            ElevatedButton.icon(
              onPressed: null,
              icon: Icon(_getStatusIcon()),
              label: Text(_getControlButtonText()),
            ),
          ],

          // Skip Question (optional)
          if (_currentState == InterviewState.waitingForAnswer) ...[
            TextButton.icon(
              onPressed: () => _showSkipDialog(),
              icon: const Icon(Icons.skip_next),
              label: const Text('Skip'),
            ),
          ],
        ],
      ),
    );
  }

  // Helper methods for UI state
  Color _getStatusColor() {
    switch (_currentState) {
      case InterviewState.initializing:
        return Colors.grey;
      case InterviewState.starting:
        return Colors.blue;
      case InterviewState.askingQuestion:
        return Colors.blue;
      case InterviewState.waitingForAnswer:
        return Colors.green;
      case InterviewState.recording:
        return Colors.red;
      case InterviewState.processingAnswer:
        return Colors.orange;
      case InterviewState.completed:
        return Colors.purple;
    }
  }

  IconData _getStatusIcon() {
    switch (_currentState) {
      case InterviewState.initializing:
        return Icons.hourglass_empty;
      case InterviewState.starting:
        return Icons.play_arrow;
      case InterviewState.askingQuestion:
        return Icons.volume_up;
      case InterviewState.waitingForAnswer:
        return Icons.mic;
      case InterviewState.recording:
        return Icons.fiber_manual_record;
      case InterviewState.processingAnswer:
        return Icons.analytics;
      case InterviewState.completed:
        return Icons.check_circle;
    }
  }

  String _getStatusText() {
    switch (_currentState) {
      case InterviewState.initializing:
        return 'Initializing interview...';
      case InterviewState.starting:
        return 'Starting interview...';
      case InterviewState.askingQuestion:
        return 'AI is asking a question';
      case InterviewState.waitingForAnswer:
        return 'Your turn to answer';
      case InterviewState.recording:
        return 'Recording your answer';
      case InterviewState.processingAnswer:
        return 'Processing your response';
      case InterviewState.completed:
        return 'Interview completed';
    }
  }

  IconData _getMainIcon() {
    switch (_currentState) {
      case InterviewState.waitingForAnswer:
        return Icons.mic_none;
      case InterviewState.processingAnswer:
        return Icons.analytics;
      case InterviewState.completed:
        return Icons.celebration;
      default:
        return Icons.chat;
    }
  }

  String _getMainMessage() {
    switch (_currentState) {
      case InterviewState.waitingForAnswer:
        return 'Tap the microphone to record your answer';
      case InterviewState.processingAnswer:
        return 'Analyzing your response...';
      case InterviewState.completed:
        return 'Great job! Interview completed.';
      default:
        return 'Listen to the AI interviewer';
    }
  }

  String _getControlButtonText() {
    switch (_currentState) {
      case InterviewState.initializing:
        return 'Initializing...';
      case InterviewState.starting:
        return 'Starting...';
      case InterviewState.askingQuestion:
        return 'Listening...';
      case InterviewState.processingAnswer:
        return 'Processing...';
      case InterviewState.completed:
        return 'Completed';
      default:
        return 'Please wait...';
    }
  }

  // Mock data and helper methods
  List<String> _getMockQuestions() {
    return [
      'Tell me about yourself and your experience with ${widget.interview.jobTitle}.',
      'What interests you most about this ${widget.interview.jobTitle} position?',
      'Can you describe a challenging project you\'ve worked on recently?',
      'How do you stay updated with the latest technologies in your field?',
      'Where do you see yourself in the next 5 years?',
    ];
  }

  String _generateMockFeedback() {
    final feedbacks = [
      'Great answer! Your experience really shines through. Try to be more specific about your achievements next time.',
      'Good response. I appreciate the examples you provided. Consider elaborating more on the technical details.',
      'Excellent! Your passion for the role is evident. Make sure to tie your answers back to the job requirements.',
      'Well articulated. Your problem-solving approach is impressive. Try to mention specific tools or technologies you used.',
      'Nice work! Your career goals align well with this position. Consider mentioning how this role fits into your plans.',
    ];
    return feedbacks[_currentQuestionIndex % feedbacks.length];
  }

  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 4),
        ),
      );
    }
  }

  Future<bool?> _showExitDialog() {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Exit Interview'),
        content: const Text(
          'Are you sure you want to exit? Your progress will be lost.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Continue Interview'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Exit', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  void _showSkipDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Skip Question'),
        content: const Text(
          'Are you sure you want to skip this question? You won\'t be able to answer it later.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _currentQuestionIndex++;
              _askNextQuestion();
            },
            child: const Text('Skip'),
          ),
        ],
      ),
    );
  }

  void _showInstructionsDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Interview Instructions'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('• Listen to each question carefully'),
              Text('• Tap the microphone to start recording'),
              Text('• Speak clearly and at normal pace'),
              Text('• Tap stop when finished answering'),
              Text('• Wait for AI feedback before the next question'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  void _showCompletionDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('Interview Completed!'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.celebration, size: 64, color: Colors.green),
            SizedBox(height: 16),
            Text(
              'Congratulations! You\'ve successfully completed your AI interview practice session.',
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 8),
            Text(
              'Your performance report will be generated shortly.',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context); // Close dialog
              Navigator.pop(context); // Go back to interview detail
            },
            child: const Text('View Results'),
          ),
        ],
      ),
    );
  }
}

// Enums and data classes
enum InterviewState {
  initializing,
  starting,
  askingQuestion,
  waitingForAnswer,
  recording,
  processingAnswer,
  completed,
}

enum Speaker { ai, user }

class ConversationEntry {
  final Speaker speaker;
  final String content;
  final DateTime timestamp;
  final String? audioPath;

  ConversationEntry({
    required this.speaker,
    required this.content,
    required this.timestamp,
    this.audioPath,
  });
}
