import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_client.dart';
import '../models/interview_feedback.dart';

class FeedbackState {
  final Map<String, InterviewFeedback> feedbackByInterviewId;
  final bool isLoading;
  final String? error;

  FeedbackState({
    this.feedbackByInterviewId = const {},
    this.isLoading = false,
    this.error,
  });

  FeedbackState copyWith({
    Map<String, InterviewFeedback>? feedbackByInterviewId,
    bool? isLoading,
    String? error,
  }) {
    return FeedbackState(
      feedbackByInterviewId: feedbackByInterviewId ?? this.feedbackByInterviewId,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

class FeedbackController extends StateNotifier<FeedbackState> {
  final ApiClient _apiClient = ApiClient();

  FeedbackController() : super(FeedbackState());

  Future<InterviewFeedback?> createFeedback({
    required String interviewId,
    required double overallScore,
    required String overallImpression,
    required List<EvaluationCriteria> breakdown,
    required String finalVerdict,
    required FeedbackRecommendation recommendation,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final feedbackData = {
        'overallScore': overallScore,
        'overallImpression': overallImpression,
        'breakdown': breakdown.map((criteria) => criteria.toJson()).toList(),
        'finalVerdict': finalVerdict,
        'recommendation': recommendation.toString().split('.').last,
      };

      final response = await _apiClient.createFeedback(interviewId, feedbackData);
      final feedback = InterviewFeedback.fromJson(response);

      // Add to local state
      final updatedFeedback = Map<String, InterviewFeedback>.from(state.feedbackByInterviewId);
      updatedFeedback[interviewId] = feedback;

      state = state.copyWith(
        feedbackByInterviewId: updatedFeedback,
        isLoading: false,
      );

      return feedback;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      return null;
    }
  }

  Future<InterviewFeedback?> getFeedback(String interviewId) async {
    // Check if we already have it in state
    if (state.feedbackByInterviewId.containsKey(interviewId)) {
      return state.feedbackByInterviewId[interviewId];
    }

    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.getFeedback(interviewId);
      final feedback = InterviewFeedback.fromJson(response);

      // Add to local state
      final updatedFeedback = Map<String, InterviewFeedback>.from(state.feedbackByInterviewId);
      updatedFeedback[interviewId] = feedback;

      state = state.copyWith(
        feedbackByInterviewId: updatedFeedback,
        isLoading: false,
      );

      return feedback;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      return null;
    }
  }

  void clearError() {
    state = state.copyWith(error: null);
  }

  InterviewFeedback? getCachedFeedback(String interviewId) {
    return state.feedbackByInterviewId[interviewId];
  }

  bool hasFeedback(String interviewId) {
    return state.feedbackByInterviewId.containsKey(interviewId);
  }

  List<InterviewFeedback> getAllFeedback() {
    return state.feedbackByInterviewId.values.toList();
  }

  List<InterviewFeedback> getFeedbackByRecommendation(FeedbackRecommendation recommendation) {
    return state.feedbackByInterviewId.values
        .where((feedback) => feedback.recommendation == recommendation)
        .toList();
  }

  double getAverageScore() {
    final feedbacks = getAllFeedback();
    if (feedbacks.isEmpty) return 0.0;
    
    final totalScore = feedbacks.fold<double>(
      0.0,
      (sum, feedback) => sum + feedback.overallScore,
    );
    
    return totalScore / feedbacks.length;
  }
}

// Providers
final feedbackControllerProvider = StateNotifierProvider<FeedbackController, FeedbackState>((ref) {
  return FeedbackController();
});

final feedbackProvider = Provider.family<InterviewFeedback?, String>((ref, interviewId) {
  return ref.watch(feedbackControllerProvider).feedbackByInterviewId[interviewId];
});

final allFeedbackProvider = Provider<List<InterviewFeedback>>((ref) {
  final controller = ref.watch(feedbackControllerProvider.notifier);
  return controller.getAllFeedback();
});

final recommendedCandidatesProvider = Provider<List<InterviewFeedback>>((ref) {
  final controller = ref.watch(feedbackControllerProvider.notifier);
  return controller.getFeedbackByRecommendation(FeedbackRecommendation.recommended);
});

final averageScoreProvider = Provider<double>((ref) {
  final controller = ref.watch(feedbackControllerProvider.notifier);
  return controller.getAverageScore();
});

final isLoadingFeedbackProvider = Provider<bool>((ref) {
  return ref.watch(feedbackControllerProvider).isLoading;
});

final feedbackErrorProvider = Provider<String?>((ref) {
  return ref.watch(feedbackControllerProvider).error;
});
