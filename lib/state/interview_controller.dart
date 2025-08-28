import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_client.dart';
import '../models/interview.dart';

class InterviewState {
  final List<Interview> interviews;
  final bool isLoading;
  final String? error;

  InterviewState({
    this.interviews = const [],
    this.isLoading = false,
    this.error,
  });

  InterviewState copyWith({
    List<Interview>? interviews,
    bool? isLoading,
    String? error,
  }) {
    return InterviewState(
      interviews: interviews ?? this.interviews,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

class InterviewController extends StateNotifier<InterviewState> {
  final ApiClient _apiClient = ApiClient();

  InterviewController() : super(InterviewState());

  Future<void> loadInterviews() async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      final interviewsData = await _apiClient.getUserInterviews();
      final interviews = interviewsData
          .map((data) => Interview.fromJson(data))
          .toList();
      
      state = state.copyWith(
        interviews: interviews,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<Interview?> createInterview({
    required String jobTitle,
    required String companyName,
    required DateTime interviewDate,
    InterviewStatus status = InterviewStatus.pending,
  }) async {
    try {
      final interviewData = {
        'jobTitle': jobTitle,
        'companyName': companyName,
        'interviewDate': interviewDate.toIso8601String(),
        'status': status.toString().split('.').last,
      };

      final response = await _apiClient.createInterview(interviewData);
      final newInterview = Interview.fromJson(response);

      // Add to local state
      state = state.copyWith(
        interviews: [...state.interviews, newInterview],
      );

      return newInterview;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return null;
    }
  }

  Future<Interview?> getInterview(String interviewId) async {
    try {
      final response = await _apiClient.getInterview(interviewId);
      return Interview.fromJson(response);
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return null;
    }
  }

  void clearError() {
    state = state.copyWith(error: null);
  }

  List<Interview> getInterviewsByStatus(InterviewStatus status) {
    return state.interviews
        .where((interview) => interview.status == status)
        .toList();
  }

  Interview? getInterviewById(String id) {
    try {
      return state.interviews.firstWhere((interview) => interview.id == id);
    } catch (e) {
      return null;
    }
  }
}

// Providers
final interviewControllerProvider = StateNotifierProvider<InterviewController, InterviewState>((ref) {
  return InterviewController();
});

final interviewsProvider = Provider<List<Interview>>((ref) {
  return ref.watch(interviewControllerProvider).interviews;
});

final pendingInterviewsProvider = Provider<List<Interview>>((ref) {
  final controller = ref.watch(interviewControllerProvider.notifier);
  return controller.getInterviewsByStatus(InterviewStatus.pending);
});

final completedInterviewsProvider = Provider<List<Interview>>((ref) {
  final controller = ref.watch(interviewControllerProvider.notifier);
  return controller.getInterviewsByStatus(InterviewStatus.completed);
});

final scheduledInterviewsProvider = Provider<List<Interview>>((ref) {
  final controller = ref.watch(interviewControllerProvider.notifier);
  return controller.getInterviewsByStatus(InterviewStatus.scheduled);
});

final isLoadingInterviewsProvider = Provider<bool>((ref) {
  return ref.watch(interviewControllerProvider).isLoading;
});

final interviewErrorProvider = Provider<String?>((ref) {
  return ref.watch(interviewControllerProvider).error;
});
