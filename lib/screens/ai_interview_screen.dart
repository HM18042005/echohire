import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'dart:async';
import 'dart:io';
import 'dart:typed_data';
import '../services/api_service.dart';
import '../models/interview.dart';
import '../providers/ai_interview_provider.dart';

// Mock questions for development - these would come from the Interview model
class InterviewQuestion {
  final String question;
  final String category;
  final String difficulty;

  InterviewQuestion({
    required this.question,
    required this.category,
    required this.difficulty,
  });
}

class ConversationEntry {
  final String speaker;
  final String message;
  final DateTime timestamp;
  final bool isQuestion;
  final bool isFeedback;

  ConversationEntry({
    required this.speaker,
    required this.message,
    required this.timestamp,
    this.isQuestion = false,
    this.isFeedback = false,
  });
}

class AIInterviewScreen extends ConsumerStatefulWidget {
  final Interview interview;
  final String aiSessionId;

  const AIInterviewScreen({
    Key? key,
    required this.interview,
    required this.aiSessionId,
  }) : super(key: key);

  @override
  ConsumerState<AIInterviewScreen> createState() => _AIInterviewScreenState();
}

class _AIInterviewScreenState extends ConsumerState<AIInterviewScreen>
    with SingleTickerProviderStateMixin {
  
  // Audio recording and TTS
  FlutterSoundRecorder? _recorder;
  FlutterTts? _flutterTts;
  bool _isRecording = false;
  bool _isInitialized = false;
  bool _isSpeaking = false;
  String? _recordingPath;
  
  // Interview state
  String _currentStatus = 'Initializing...';
  List<ConversationEntry> _conversationLog = [];
  int _currentQuestionIndex = 0;
  List<InterviewQuestion> _questions = [];
  Timer? _statusTimer;
  bool _interviewActive = false;
  bool _waitingForAnswer = false;
  
  // Animation
  late AnimationController _animationController;
  late Animation<double> _pulseAnimation;
  late Animation<Color?> _colorAnimation;
  
  // Colors
  static const Color backgroundColor = Color(0xFF181A20);
  static const Color primaryColor = Color(0xFF2972FF);
  static const Color surfaceColor = Color(0xFF262A34);
  static const Color successColor = Color(0xFF4CAF50);
  static const Color warningColor = Color(0xFFFF9800);
  static const Color errorColor = Color(0xFFF44336);

  @override
  void initState() {
    super.initState();
    _initializeServices();
    _setupAnimation();
    _loadQuestions();
  }

  void _setupAnimation() {
    _animationController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _colorAnimation = ColorTween(
      begin: primaryColor.withOpacity(0.6),
      end: successColor.withOpacity(0.9),
    ).animate(_animationController);
  }

  void _loadQuestions() {
    // In production, these would come from widget.interview.questions or similar
    _questions = [
      InterviewQuestion(
        question: "Tell me about yourself and your background in software engineering.",
        category: "introduction",
        difficulty: "easy",
      ),
      InterviewQuestion(
        question: "Describe a challenging technical problem you solved recently. What was your approach?",
        category: "problem-solving",
        difficulty: "medium",
      ),
      InterviewQuestion(
        question: "How do you approach debugging when you encounter a difficult bug in production?",
        category: "technical",
        difficulty: "medium",
      ),
      InterviewQuestion(
        question: "Where do you see yourself in your career in the next 5 years?",
        category: "career",
        difficulty: "easy",
      ),
    ];
  }

  Future<void> _initializeServices() async {
    try {
      await _initializeRecorder();
      await _initializeTTS();
      await _startAIInterview();
    } catch (e) {
      _updateStatus('Initialization failed: $e');
    }
  }

  Future<void> _initializeRecorder() async {
    try {
      // Request microphone permission
      final permission = await Permission.microphone.request();
      if (permission != PermissionStatus.granted) {
        _updateStatus('Microphone permission denied');
        return;
      }

      _recorder = FlutterSoundRecorder();
      await _recorder!.openRecorder();
      setState(() {
        _isInitialized = true;
      });
    } catch (e) {
      _updateStatus('Failed to initialize recorder: $e');
    }
  }

  Future<void> _initializeTTS() async {
    try {
      _flutterTts = FlutterTts();
      await _flutterTts!.setLanguage("en-US");
      await _flutterTts!.setSpeechRate(0.8);
      await _flutterTts!.setVolume(0.9);
      await _flutterTts!.setPitch(1.0);

      _flutterTts!.setStartHandler(() {
        setState(() {
          _isSpeaking = true;
        });
      });

      _flutterTts!.setCompletionHandler(() {
        setState(() {
          _isSpeaking = false;
        });
        // Auto-enable recording after AI finishes speaking
        if (_interviewActive && !_waitingForAnswer) {
          setState(() {
            _waitingForAnswer = true;
            _currentStatus = "Your turn to answer - Press record";
          });
        }
      });
    } catch (e) {
      _updateStatus('Failed to initialize TTS: $e');
    }
  }

  Future<void> _startAIInterview() async {
    try {
      _updateStatus('Starting AI interview...');
      
      // Start the AI interview session with Vapi
      final response = await ApiServiceSingleton.instance.startAIInterview(
        widget.interview.id,
        questions: _questions.map((q) => q.question).toList(),
      );
      
      _addToConversation(
        'System', 
        'AI Interview started successfully',
        isSystem: true,
      );
      
      setState(() {
        _interviewActive = true;
      });
      
      _updateStatus('Interview started - AI will ask the first question');
      
      // Start with the first question
      await _askNextQuestion();
      
    } catch (e) {
      _updateStatus('Failed to start AI interview: $e');
    }
  }

  Future<void> _askNextQuestion() async {
    if (_currentQuestionIndex >= _questions.length) {
      await _endInterview();
      return;
    }

    final question = _questions[_currentQuestionIndex];
    
    _addToConversation(
      'AI Interviewer', 
      question.question,
      isQuestion: true,
    );
    
    _updateStatus('AI is asking question ${_currentQuestionIndex + 1}...');
    
    // Speak the question using TTS
    await _speakText(question.question);
  }

  Future<void> _speakText(String text) async {
    if (_flutterTts != null) {
      await _flutterTts!.speak(text);
    }
  }

  Future<void> _startRecording() async {
    if (!_isInitialized || _recorder == null || _isRecording) return;

    try {
      _updateStatus('Recording your answer...');
      
      // Generate unique file path
      final directory = await Directory.systemTemp.createTemp();
      _recordingPath = '${directory.path}/interview_answer_${DateTime.now().millisecondsSinceEpoch}.aac';
      
      await _recorder!.startRecorder(
        toFile: _recordingPath,
        codec: Codec.aacADTS,
      );
      
      setState(() {
        _isRecording = true;
        _waitingForAnswer = false;
      });
      
      _animationController.repeat(reverse: true);
      
    } catch (e) {
      _updateStatus('Failed to start recording: $e');
    }
  }

  Future<void> _stopRecording() async {
    if (!_isRecording || _recorder == null) return;

    try {
      await _recorder!.stopRecorder();
      
      setState(() {
        _isRecording = false;
      });
      
      _animationController.stop();
      _updateStatus('Processing your answer...');
      
      if (_recordingPath != null) {
        await _processRecording(_recordingPath!);
      }
      
    } catch (e) {
      _updateStatus('Failed to stop recording: $e');
    }
  }

  Future<void> _processRecording(String audioPath) async {
    try {
      // Step 1: Transcribe the audio
      _updateStatus('Transcribing your answer...');
      final transcript = await _transcribeAudio(audioPath);
      
      if (transcript.isEmpty) {
        _updateStatus('Could not transcribe audio. Please try again.');
        setState(() {
          _waitingForAnswer = true;
        });
        return;
      }
      
      // Add user's answer to conversation
      _addToConversation('You', transcript);
      
      // Step 2: Get AI feedback
      _updateStatus('Analyzing your response...');
      final question = _questions[_currentQuestionIndex].question;
      final feedback = await _getAIFeedback(question, transcript);
      
      // Step 3: Speak the feedback
      _addToConversation('AI Interviewer', feedback, isFeedback: true);
      _updateStatus('AI is providing feedback...');
      await _speakText(feedback);
      
      // Move to next question
      _currentQuestionIndex++;
      
      // Small delay before next question
      await Future.delayed(const Duration(seconds: 2));
      await _askNextQuestion();
      
    } catch (e) {
      _updateStatus('Error processing answer: $e');
      setState(() {
        _waitingForAnswer = true;
      });
    }
  }

  Future<String> _transcribeAudio(String audioPath) async {
    try {
      // In production, this would call your backend transcription endpoint
      // For now, we'll simulate transcription
      await Future.delayed(const Duration(seconds: 2));
      
      // Mock transcription - in production, you'd send the audio file to /api/transcribe-answer
      final mockTranscripts = [
        "I have been working as a software engineer for 3 years, focusing mainly on full-stack development with React and Node.js. I enjoy solving complex problems and building user-friendly applications.",
        "Recently, I encountered a performance issue where our API was timing out. I used profiling tools to identify the bottleneck in our database queries, optimized them, and reduced response time by 60%.",
        "When debugging production issues, I start by checking logs and monitoring tools. I then reproduce the issue in a staging environment and use systematic debugging to isolate the root cause.",
        "In five years, I see myself leading a development team and contributing to architectural decisions. I want to mentor junior developers and drive innovation in the products we build."
      ];
      
      if (_currentQuestionIndex < mockTranscripts.length) {
        return mockTranscripts[_currentQuestionIndex];
      }
      
      return "Thank you for the question. I believe my experience and skills make me a good fit for this role.";
      
    } catch (e) {
      throw Exception('Transcription failed: $e');
    }
  }

  Future<String> _getAIFeedback(String question, String answer) async {
    try {
      // In production, this would call your backend analysis endpoint
      await Future.delayed(const Duration(seconds: 3));
      
      // Mock AI feedback - in production, you'd call /api/analyze-answer
      final mockFeedbacks = [
        "Great introduction! I appreciate how you highlighted your full-stack experience and passion for problem-solving. Consider mentioning specific technologies or projects that showcase your expertise.",
        "Excellent example of systematic problem-solving! Your approach of using profiling tools and achieving measurable results shows strong technical skills. The 60% improvement is impressive.",
        "Your debugging methodology is solid - starting with logs and using staging environments shows good practices. You might also mention how you prioritize issues and communicate with stakeholders during incidents.",
        "I like your focus on leadership and mentorship. Your 5-year vision shows good career planning. Consider being more specific about what kind of architectural decisions interest you."
      ];
      
      if (_currentQuestionIndex < mockFeedbacks.length) {
        return mockFeedbacks[_currentQuestionIndex];
      }
      
      return "Thank you for your response. That provides good insight into your background and approach.";
      
    } catch (e) {
      throw Exception('Feedback generation failed: $e');
    }
  }

  Future<void> _endInterview() async {
    try {
      _updateStatus('Interview completed! Generating final feedback...');
      
      setState(() {
        _interviewActive = false;
      });
      
      _addToConversation(
        'AI Interviewer', 
        'Thank you for completing the interview! Your responses have been recorded and analyzed. You can now view your detailed feedback.',
        isSystem: true,
      );
      
      await _speakText('Thank you for completing the interview! You can now view your detailed feedback.');
      
      // Stop the AI interview session
      await ApiServiceSingleton.instance.stopAIInterview(widget.interview.id);
      
      _updateStatus('Interview completed successfully');
      
      // Navigate to feedback screen after TTS completes
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) {
          Navigator.of(context).pop();
        }
      });
      
    } catch (e) {
      _updateStatus('Error ending interview: $e');
    }
  }

  void _updateStatus(String status) {
    setState(() {
      _currentStatus = status;
    });
    
    // Update provider state
    final provider = ref.read(aiInterviewProvider.notifier);
    provider.updateStatus(status);
  }

  void _addToConversation(String speaker, String message, {bool isQuestion = false, bool isFeedback = false, bool isSystem = false}) {
    setState(() {
      _conversationLog.add(ConversationEntry(
        speaker: speaker,
        message: message,
        timestamp: DateTime.now(),
        isQuestion: isQuestion,
        isFeedback: isFeedback,
      ));
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    _recorder?.closeRecorder();
    _flutterTts?.stop();
    _statusTimer?.cancel();
    super.dispose();
  }
      await _checkAIStatus();
    });
  }

  Future<void> _checkAIStatus() async {
    try {
      final status = await ApiServiceSingleton.instance.getAIInterviewStatus(widget.interview.id);
      final currentStatus = status['status'] as String;
      
      if (currentStatus == 'completed') {
        _updateStatus('Interview completed - Generating feedback...');
        _statusTimer?.cancel();
        await _getAIFeedback();
      } else if (currentStatus == 'failed') {
        _updateStatus('Interview failed - Please try again');
        _statusTimer?.cancel();
      }
    } catch (e) {
      print('Status check error: $e');
    }
  }

  Future<void> _getAIFeedback() async {
    try {
      final feedback = await ApiServiceSingleton.instance.getAIFeedback(widget.interview.id);
      _addToConversation('AI Feedback', 'Interview analysis complete');
      _updateStatus('Interview completed successfully');
      
      // Show feedback dialog
      _showFeedbackDialog(feedback);
    } catch (e) {
      _updateStatus('Failed to get AI feedback: $e');
    }
  }

  Future<void> _startRecording() async {
    if (!_isInitialized || _recorder == null) return;

    try {
      await _recorder!.startRecorder(toFile: 'audio_recording.aac');
      setState(() {
        _isRecording = true;
      });
      _updateStatus('Recording... AI is listening');
      _addToConversation('You', 'Started speaking...');
    } catch (e) {
      _updateStatus('Failed to start recording: $e');
    }
  }

  Future<void> _stopRecording() async {
    if (!_isRecording || _recorder == null) return;

    try {
      await _recorder!.stopRecorder();
      setState(() {
        _isRecording = false;
      });
      _updateStatus('Processing your response...');
      _addToConversation('You', 'Finished speaking');
      
      // Simulate AI response
      Future.delayed(const Duration(seconds: 3), () {
        _addToConversation('AI', 'Thank you for your response. Let me ask you another question...');
        _updateStatus('AI is speaking - Listen carefully');
      });
    } catch (e) {
      _updateStatus('Failed to stop recording: $e');
    }
  }

  void _updateStatus(String status) {
    setState(() {
      _currentStatus = status;
    });
  }

  void _addToConversation(String speaker, String message) {
    setState(() {
      _conversationLog.add('$speaker: $message');
    });
  }

  Future<void> _endInterview() async {
    try {
      await ApiServiceSingleton.instance.stopAIInterview(widget.interview.id);
      _updateStatus('Interview ended');
      _statusTimer?.cancel();
      
      if (mounted) {
        Navigator.of(context).pop();
      }
    } catch (e) {
      _updateStatus('Failed to end interview: $e');
    }
  }

  void _showFeedbackDialog(Map<String, dynamic> feedback) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: surfaceColor,
        title: const Text('Interview Complete!', style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Overall Score: ${feedback['overallScore']}/100', 
                 style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Text('${feedback['overallImpression']}', 
                 style: const TextStyle(color: Colors.white70)),
            const SizedBox(height: 12),
            const Text('Key Insights:', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ...(feedback['keyInsights'] as List).map((insight) => 
              Padding(
                padding: const EdgeInsets.only(left: 8, top: 4),
                child: Text('• $insight', style: const TextStyle(color: Colors.white70)),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              Navigator.of(context).pop(); // Return to previous screen
            },
            child: const Text('Done', style: TextStyle(color: primaryColor)),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _recorder?.closeRecorder();
    _animationController.dispose();
    _statusTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: backgroundColor,
      appBar: AppBar(
        backgroundColor: backgroundColor,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text(
          'AI Interview - ${widget.interview.jobTitle}',
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.stop, color: errorColor),
            onPressed: _endInterview,
          ),
        ],
      ),
      body: Column(
        children: [
          // Status Header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            margin: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: surfaceColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey.withOpacity(0.2)),
            ),
            child: Column(
              children: [
                Text(
                  _currentStatus,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  'Session ID: ${widget.aiSessionId.substring(0, 8)}...',
                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                ),
              ],
            ),
          ),

          // Recording Controls
          Expanded(
            flex: 2,
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Recording Button
                  AnimatedBuilder(
                    animation: _pulseAnimation,
                    builder: (context, child) {
                      return Transform.scale(
                        scale: _isRecording ? _pulseAnimation.value : 1.0,
                        child: GestureDetector(
                          onTap: _isRecording ? _stopRecording : _startRecording,
                          child: Container(
                            width: 120,
                            height: 120,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: _isRecording ? errorColor : primaryColor,
                              boxShadow: [
                                BoxShadow(
                                  color: (_isRecording ? errorColor : primaryColor).withOpacity(0.3),
                                  blurRadius: 20,
                                  spreadRadius: 5,
                                ),
                              ],
                            ),
                            child: Icon(
                              _isRecording ? Icons.stop : Icons.mic,
                              size: 50,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 20),
                  Text(
                    _isRecording ? 'Tap to stop recording' : 'Tap to start recording',
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Conversation Log
          Expanded(
            flex: 3,
            child: Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: surfaceColor,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.withOpacity(0.2)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Conversation Log',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Expanded(
                    child: ListView.builder(
                      itemCount: _conversationLog.length,
                      itemBuilder: (context, index) {
                        final entry = _conversationLog[index];
                        final isUser = entry.startsWith('You:');
                        final isAI = entry.startsWith('AI:');
                        
                        return Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: isUser 
                                ? primaryColor.withOpacity(0.1)
                                : isAI 
                                    ? successColor.withOpacity(0.1)
                                    : Colors.grey.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            entry,
                            style: TextStyle(
                              color: isUser 
                                  ? primaryColor
                                  : isAI 
                                      ? successColor
                                      : Colors.white70,
                              fontSize: 14,
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
