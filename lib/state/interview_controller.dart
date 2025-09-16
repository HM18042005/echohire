import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
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
  final AuthService _authService = AuthService();

  InterviewController() : super(InterviewState());

  Future<void> loadInterviews() async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      // Get current user ID
      final currentUser = _authService.currentUser;
      if (currentUser == null) {
        throw Exception('User not authenticated');
      }
      
      // Add a timeout to prevent infinite loading
      final interviewSessions = await ApiServiceSingleton.instance.getUserInterviews(
        userId: currentUser.uid,
      ).timeout(const Duration(seconds: 10));
      
      // Convert InterviewSession to Interview
      final interviews = interviewSessions.map((session) => Interview(
        id: session.id,
        jobTitle: session.role,
        companyName: null,
        interviewDate: DateTime.now(), // Placeholder
        status: InterviewStatus.pending,
        userId: session.userId,
        createdAt: DateTime.parse(session.createdAt),
        updatedAt: DateTime.parse(session.createdAt),
        role: session.role,
        type: session.type,
        level: session.level,
        questions: session.questions,
      )).toList();
      
      state = state.copyWith(
        interviews: interviews,
        isLoading: false,
      );
    } catch (e) {
      print('Error loading interviews: $e');
      
      // If it's a timeout or connection error, provide fallback data
      if (e.toString().contains('TimeoutException') || 
          e.toString().contains('SocketException') ||
          e.toString().contains('connection') ||
          e.toString().contains('Failed to fetch interviews')) {
        print('Connection issue detected, using fallback data');
        
        // Provide some mock data for development
        final mockInterviews = [
          Interview(
            id: 'mock-1',
            jobTitle: 'Flutter Developer',
            companyName: 'Tech Corp',
            interviewDate: DateTime.now().add(const Duration(days: 1)),
            status: InterviewStatus.scheduled,
            userId: 'user123',
            createdAt: DateTime.now(),
            updatedAt: DateTime.now(),
            role: 'Flutter Developer',
            type: 'Technical',
            level: 'Mid-level',
          ),
        ];
        
        state = state.copyWith(
          interviews: mockInterviews,
          isLoading: false,
          error: 'Using offline mode - ${e.toString()}',
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          error: e.toString(),
        );
      }
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

      final response = await ApiServiceSingleton.instance.createInterview(interviewData);
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
      final response = await ApiServiceSingleton.instance.getInterview(interviewId);
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
