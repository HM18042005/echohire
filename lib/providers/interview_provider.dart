import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

/// Provider class for managing interview state using the Provider pattern
/// Extends ChangeNotifier to notify listeners when state changes
class InterviewProvider extends ChangeNotifier {
  final ApiService _apiService;

  InterviewProvider(this._apiService);

  // Private state variables
  List<InterviewSession> _interviews = [];
  bool _isLoading = false;
  String? _errorMessage;

  // Public getters for accessing state
  List<InterviewSession> get interviews => List.unmodifiable(_interviews);
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get hasError => _errorMessage != null;
  bool get hasInterviews => _interviews.isNotEmpty;

  /// Fetches all interviews for a specific user
  /// 
  /// [userId] - The ID of the user whose interviews to fetch
  /// 
  /// Sets loading state, calls API, and updates the interviews list
  /// Handles errors gracefully and notifies listeners of state changes
  Future<void> fetchInterviews(String userId) async {
    // Set loading state and clear previous errors
    _setLoading(true);
    _clearError();

    try {
      // Call the API service to get user interviews
      final fetchedInterviews = await _apiService.getUserInterviews(userId: userId);
      
      // Update the interviews list on successful fetch
      _interviews = fetchedInterviews;
      
      if (kDebugMode) {
        print('Successfully fetched ${_interviews.length} interviews for user: $userId');
      }
    } catch (e) {
      // Handle different types of exceptions
      String errorMsg;
      if (e is ApiException) {
        errorMsg = 'API Error: ${e.message}';
      } else if (e is NetworkException) {
        errorMsg = 'Network Error: ${e.message}';
      } else if (e is ParseException) {
        errorMsg = 'Data Error: ${e.message}';
      } else {
        errorMsg = 'Unexpected error: ${e.toString()}';
      }
      
      _setError(errorMsg);
      
      if (kDebugMode) {
        print('Error fetching interviews: $errorMsg');
      }
    } finally {
      // Always set loading to false and notify listeners
      _setLoading(false);
    }
  }

  /// Creates a new interview and refreshes the interviews list
  /// 
  /// [role] - The job role for the interview
  /// [type] - The type of interview (technical, behavioral, etc.)
  /// [level] - The difficulty level (junior, senior, etc.)
  /// [userId] - The ID of the user creating the interview
  /// 
  /// Returns the created InterviewSession or null if creation failed
  Future<InterviewSession?> createInterview({
    required String role,
    required String type,
    required String level,
    required String userId,
  }) async {
    // Set loading state and clear previous errors
    _setLoading(true);
    _clearError();

    try {
      // Generate the new interview using the API service
      final newInterview = await _apiService.generateInterview(
        role: role,
        type: type,
        level: level,
        userId: userId,
      );

      if (kDebugMode) {
        print('Successfully created interview: ${newInterview.id}');
      }

      // Add the new interview to the beginning of the list
      _interviews.insert(0, newInterview);
      
      // Notify listeners immediately with the new interview
      notifyListeners();

      // Optionally refresh the entire list to ensure synchronization
      // Comment out the line below if you want to avoid the extra API call
      await fetchInterviews(userId);

      return newInterview;
    } catch (e) {
      // Handle different types of exceptions
      String errorMsg;
      if (e is ApiException) {
        errorMsg = 'Failed to create interview: ${e.message}';
      } else if (e is NetworkException) {
        errorMsg = 'Network error while creating interview: ${e.message}';
      } else if (e is ParseException) {
        errorMsg = 'Data error while creating interview: ${e.message}';
      } else {
        errorMsg = 'Unexpected error creating interview: ${e.toString()}';
      }
      
      _setError(errorMsg);
      
      if (kDebugMode) {
        print('Error creating interview: $errorMsg');
      }
      
      return null;
    } finally {
      // Always set loading to false
      _setLoading(false);
    }
  }

  /// Refreshes the interviews list for a user
  /// This is a convenience method that calls fetchInterviews
  Future<void> refreshInterviews(String userId) async {
    await fetchInterviews(userId);
  }

  /// Clears all interviews from the local state
  /// Useful when switching users or logging out
  void clearInterviews() {
    _interviews.clear();
    _clearError();
    notifyListeners();
  }

  /// Removes a specific interview from the local state
  /// This is optimistic - it assumes the deletion was successful
  void removeInterview(String interviewId) {
    _interviews.removeWhere((interview) => interview.id == interviewId);
    notifyListeners();
  }

  /// Gets a specific interview by ID
  InterviewSession? getInterviewById(String interviewId) {
    try {
      return _interviews.firstWhere((interview) => interview.id == interviewId);
    } catch (e) {
      return null;
    }
  }

  // Private helper methods

  /// Sets the loading state and notifies listeners
  void _setLoading(bool loading) {
    if (_isLoading != loading) {
      _isLoading = loading;
      notifyListeners();
    }
  }

  /// Sets an error message and notifies listeners
  void _setError(String error) {
    _errorMessage = error;
    notifyListeners();
  }

  /// Clears the current error message
  void _clearError() {
    if (_errorMessage != null) {
      _errorMessage = null;
      // Note: We don't call notifyListeners() here as this is usually called
      // before other operations that will notify listeners
    }
  }

  /// Clears the error message and notifies listeners
  /// Use this when you want to manually clear errors from the UI
  void clearError() {
    if (_errorMessage != null) {
      _errorMessage = null;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    // Clean up resources when the provider is disposed
    _interviews.clear();
    super.dispose();
  }
}
