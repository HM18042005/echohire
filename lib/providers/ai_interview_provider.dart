import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../models/interview.dart';

/// AI Interview states
enum AIInterviewState {
  idle,
  starting,
  recording,
  processing,
  completed,
  failed,
  stopped
}

/// AI Interview status model
class AIInterviewStatus {
  final String aiSessionId;
  final AIInterviewState state;
  final String message;
  final int? duration;
  final String? transcriptUrl;
  final String? audioRecordingUrl;
  final Map<String, dynamic>? feedback;
  final String? error;

  AIInterviewStatus({
    required this.aiSessionId,
    required this.state,
    required this.message,
    this.duration,
    this.transcriptUrl,
    this.audioRecordingUrl,
    this.feedback,
    this.error,
  });

  AIInterviewStatus copyWith({
    String? aiSessionId,
    AIInterviewState? state,
    String? message,
    int? duration,
    String? transcriptUrl,
    String? audioRecordingUrl,
    Map<String, dynamic>? feedback,
    String? error,
  }) {
    return AIInterviewStatus(
      aiSessionId: aiSessionId ?? this.aiSessionId,
      state: state ?? this.state,
      message: message ?? this.message,
      duration: duration ?? this.duration,
      transcriptUrl: transcriptUrl ?? this.transcriptUrl,
      audioRecordingUrl: audioRecordingUrl ?? this.audioRecordingUrl,
      feedback: feedback ?? this.feedback,
      error: error ?? this.error,
    );
  }
}

/// AI Interview Provider for state management
class AIInterviewProvider extends StateNotifier<AIInterviewStatus?> {
  AIInterviewProvider() : super(null);

  /// Start an AI interview session
  Future<void> startAIInterview(Interview interview) async {
    try {
      state = AIInterviewStatus(
        aiSessionId: '',
        state: AIInterviewState.starting,
        message: 'Starting AI interview...',
      );

      final response = await ApiServiceSingleton.instance.startAIInterview(interview.id);
      final aiSessionId = response['aiSessionId'] as String;

      state = AIInterviewStatus(
        aiSessionId: aiSessionId,
        state: AIInterviewState.recording,
        message: 'AI interview started successfully',
      );

      // Start polling for status updates
      _startStatusPolling(interview.id);
      
    } catch (e) {
      state = AIInterviewStatus(
        aiSessionId: '',
        state: AIInterviewState.failed,
        message: 'Failed to start AI interview',
        error: e.toString(),
      );
    }
  }

  /// Stop the AI interview session
  Future<void> stopAIInterview(String interviewId) async {
    try {
      if (state?.aiSessionId != null) {
        await ApiServiceSingleton.instance.stopAIInterview(interviewId);
        
        state = state?.copyWith(
          state: AIInterviewState.stopped,
          message: 'Interview stopped',
        );
      }
    } catch (e) {
      if (kDebugMode) {
        print('Error stopping AI interview: $e');
      }
    }
  }

  /// Update interview state
  void updateState(AIInterviewState newState, String message) {
    if (state != null) {
      state = state!.copyWith(
        state: newState,
        message: message,
      );
    }
  }

  /// Start polling for status updates
  void _startStatusPolling(String interviewId) {
    // This would typically use a Timer.periodic in a real implementation
    // For now, we'll simulate status updates
    Future.delayed(const Duration(seconds: 30), () {
      if (state?.state == AIInterviewState.recording) {
        _checkInterviewStatus(interviewId);
      }
    });
  }

  /// Check interview status
  Future<void> _checkInterviewStatus(String interviewId) async {
    try {
      final statusResponse = await ApiServiceSingleton.instance.getAIInterviewStatus(interviewId);
      final status = statusResponse['status'] as String;

      if (status == 'completed' && state != null) {
        // Get AI feedback
        final feedback = await ApiServiceSingleton.instance.getAIFeedback(interviewId);
        
        state = state!.copyWith(
          state: AIInterviewState.completed,
          message: 'Interview completed - Feedback generated',
          feedback: feedback,
          duration: statusResponse['duration'] as int?,
          transcriptUrl: statusResponse['transcriptUrl'] as String?,
          audioRecordingUrl: statusResponse['audioRecordingUrl'] as String?,
        );
      } else if (status == 'failed' && state != null) {
        state = state!.copyWith(
          state: AIInterviewState.failed,
          message: 'Interview failed',
        );
      }
    } catch (e) {
      if (kDebugMode) {
        print('Error checking interview status: $e');
      }
    }
  }

  /// Reset the provider state
  void reset() {
    state = null;
  }
}

/// Provider instance
final aiInterviewProvider = StateNotifierProvider<AIInterviewProvider, AIInterviewStatus?>(
  (ref) => AIInterviewProvider(),
);

/// Helper providers for specific state checks
final isAIInterviewActiveProvider = Provider<bool>((ref) {
  final status = ref.watch(aiInterviewProvider);
  return status?.state == AIInterviewState.recording || 
         status?.state == AIInterviewState.processing;
});

final aiInterviewMessageProvider = Provider<String>((ref) {
  final status = ref.watch(aiInterviewProvider);
  return status?.message ?? 'No active interview';
});

final aiInterviewFeedbackProvider = Provider<Map<String, dynamic>?>((ref) {
  final status = ref.watch(aiInterviewProvider);
  return status?.feedback;
});