import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth_service.dart';
import 'package:echohire/config.dart';

// Data Models

/// Represents an interview question with category and difficulty
class InterviewQuestion {
  final String question;
  final String category;
  final String difficulty;

  InterviewQuestion({
    required this.question,
    required this.category,
    required this.difficulty,
  });

  factory InterviewQuestion.fromJson(Map<String, dynamic> json) {
    return InterviewQuestion(
      question: json['question'] as String,
      category: json['category'] as String,
      difficulty: json['difficulty'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'question': question,
      'category': category,
      'difficulty': difficulty,
    };
  }

  @override
  String toString() {
    return 'InterviewQuestion(question: $question, category: $category, difficulty: $difficulty)';
  }
}

/// Represents a complete interview session with questions
class InterviewSession {
  final String id;
  final String userId;
  final String role;
  final String type;
  final String level;
  final List<InterviewQuestion> questions;
  final String createdAt;

  InterviewSession({
    required this.id,
    required this.userId,
    required this.role,
    required this.type,
    required this.level,
    required this.questions,
    required this.createdAt,
  });

  factory InterviewSession.fromJson(Map<String, dynamic> json) {
    final questionsJson = json['questions'] as List<dynamic>? ?? [];
    final questions = questionsJson
        .map((q) => InterviewQuestion.fromJson(q as Map<String, dynamic>))
        .toList();

    return InterviewSession(
      id: json['id'] as String,
      userId: json['userId'] as String,
      role: json['role'] as String,
      type: json['type'] as String,
      level: json['level'] as String,
      questions: questions,
      createdAt: json['createdAt'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'userId': userId,
      'role': role,
      'type': type,
      'level': level,
      'questions': questions.map((q) => q.toJson()).toList(),
      'createdAt': createdAt,
    };
  }

  @override
  String toString() {
    return 'InterviewSession(id: $id, userId: $userId, role: $role, type: $type, level: $level, questions: ${questions.length}, createdAt: $createdAt)';
  }
}

// Custom Exceptions

/// Exception thrown when API request fails
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, [this.statusCode]);

  @override
  String toString() {
    if (statusCode != null) {
      return 'ApiException($statusCode): $message';
    }
    return 'ApiException: $message';
  }
}

/// Exception thrown when network request fails
class NetworkException implements Exception {
  final String message;

  NetworkException(this.message);

  @override
  String toString() => 'NetworkException: $message';
}

/// Exception thrown when JSON parsing fails
class ParseException implements Exception {
  final String message;

  ParseException(this.message);

  @override
  String toString() => 'ParseException: $message';
}

// API Service

/// Service class for handling API communication with the FastAPI backend
class ApiService {
  // Base URL for Android emulator compatibility
  // Derive from AppConfig so environments (.env) are respected
  static String get _baseUrl => AppConfig.baseUrl;

  final http.Client _client;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  /// Disposes the HTTP client
  void dispose() {
    _client.close();
  }

  /// Generates headers for API requests
  Map<String, String> _getHeaders() {
    return {'Content-Type': 'application/json', 'Accept': 'application/json'};
  }

  /// Get headers with Firebase authentication token
  Future<Map<String, String>> _getAuthHeaders() async {
    final authService = AuthService();
    final token = await authService.getIdToken();

    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  /// Handles HTTP response and throws appropriate exceptions for errors
  void _handleResponse(http.Response response, String operation) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return; // Success
    }

    String errorMessage;
    try {
      final errorBody = json.decode(response.body);
      errorMessage =
          errorBody['detail'] ?? errorBody['message'] ?? 'Unknown error';
    } catch (e) {
      errorMessage = response.body.isNotEmpty
          ? response.body
          : 'HTTP ${response.statusCode}';
    }

    switch (response.statusCode) {
      case 400:
        throw ApiException('Bad Request: $errorMessage', response.statusCode);
      case 401:
        throw ApiException('Unauthorized: $errorMessage', response.statusCode);
      case 403:
        throw ApiException('Forbidden: $errorMessage', response.statusCode);
      case 404:
        throw ApiException('Not Found: $errorMessage', response.statusCode);
      case 429:
        throw ApiException(
          'Too Many Requests: $errorMessage',
          response.statusCode,
        );
      case 500:
        throw ApiException(
          'Internal Server Error: $errorMessage',
          response.statusCode,
        );
      case 502:
        throw ApiException('Bad Gateway: $errorMessage', response.statusCode);
      case 503:
        throw ApiException(
          'Service Unavailable: $errorMessage',
          response.statusCode,
        );
      default:
        throw ApiException(
          '$operation failed: $errorMessage',
          response.statusCode,
        );
    }
  }

  /// Generates an interview session based on role, type, level, and userId
  ///
  /// [role] - The job role for the interview (e.g., "Software Engineer")
  /// [type] - The type of interview (e.g., "technical", "behavioral")
  /// [level] - The difficulty level (e.g., "junior", "senior")
  /// [userId] - The ID of the user requesting the interview
  ///
  /// Returns a [Future<InterviewSession>] containing the generated interview
  ///
  /// Throws [ApiException] for API errors, [NetworkException] for network errors,
  /// or [ParseException] for JSON parsing errors
  Future<InterviewSession> generateInterview({
    required String role,
    required String type,
    required String level,
    required String userId,
  }) async {
    try {
      final url = Uri.parse('$_baseUrl/api/generate-interview');

      final requestBody = {
        'role': role,
        'type': type,
        'level': level,
        'userId': userId,
      };

      final response = await _client
          .post(
            url,
            headers: await _getAuthHeaders(),
            body: json.encode(requestBody),
          )
          .timeout(
            const Duration(seconds: 30),
            onTimeout: () => throw NetworkException('Request timeout'),
          );

      _handleResponse(response, 'Generate interview');

      try {
        final responseData = json.decode(response.body) as Map<String, dynamic>;
        return InterviewSession.fromJson(responseData);
      } catch (e) {
        throw ParseException('Failed to parse interview session response: $e');
      }
    } catch (e) {
      if (e is ApiException || e is NetworkException || e is ParseException) {
        rethrow;
      }
      // Handle other network-related exceptions
      throw NetworkException('Failed to generate interview: $e');
    }
  }

  /// Retrieves all interview sessions for a specific user
  ///
  /// [userId] - The ID of the user whose interviews to retrieve
  ///
  /// Returns a [Future<List<InterviewSession>>] containing the user's interviews
  ///
  /// Throws [ApiException] for API errors, [NetworkException] for network errors,
  /// or [ParseException] for JSON parsing errors
  Future<List<InterviewSession>> getUserInterviews({
    required String userId,
  }) async {
    try {
      final url = Uri.parse('$_baseUrl/api/interviews/$userId');
      final headers = await _getAuthHeaders();

      final response = await _client
          .get(url, headers: headers)
          .timeout(
            const Duration(seconds: 15),
            onTimeout: () => throw NetworkException('Request timeout'),
          );

      _handleResponse(response, 'Get user interviews');

      try {
        final responseData = json.decode(response.body);

        if (responseData is! List) {
          throw ParseException(
            'Expected a list of interviews, got ${responseData.runtimeType}',
          );
        }

        return responseData
            .map(
              (interview) =>
                  InterviewSession.fromJson(interview as Map<String, dynamic>),
            )
            .toList();
      } catch (e) {
        if (e is ParseException) rethrow;
        throw ParseException('Failed to parse interviews response: $e');
      }
    } catch (e) {
      if (e is ApiException || e is NetworkException || e is ParseException) {
        rethrow;
      }
      // Handle other network-related exceptions
      throw NetworkException('Failed to get user interviews: $e');
    }
  }

  /// Retrieves all persisted interview records (InterviewOut) for the
  /// authenticated user. This differs from [getUserInterviews] which returns
  /// AI "interview sessions" (generation sessions with role/type/level/questions)
  /// from the /api/interviews/{userId} endpoint.
  ///
  /// The FastAPI backend exposes GET /interviews returning InterviewOut objects
  /// linked to the authenticated user (userId inferred from the Firebase token).
  Future<List<Map<String, dynamic>>> getInterviews() async {
    try {
      final url = Uri.parse('$_baseUrl/interviews');
      final response = await _client
          .get(url, headers: await _getAuthHeaders())
          .timeout(
            const Duration(seconds: 15),
            onTimeout: () => throw NetworkException('Request timeout'),
          );

      _handleResponse(response, 'Get interviews');

      final decoded = json.decode(response.body);
      if (decoded is! List) {
        throw ParseException(
          'Expected a list of interviews, got ${decoded.runtimeType}',
        );
      }
      return decoded.cast<Map<String, dynamic>>();
    } catch (e) {
      if (e is ApiException || e is NetworkException || e is ParseException) {
        rethrow;
      }
      throw NetworkException('Failed to get interviews: $e');
    }
  }

  /// Health check endpoint to verify API connectivity
  ///
  /// Returns a [Future<bool>] indicating if the API is healthy
  Future<bool> healthCheck() async {
    try {
      final url = Uri.parse('$_baseUrl/health');

      final response = await _client
          .get(url, headers: _getHeaders())
          .timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // AI Interview Methods

  /// Start an AI-conducted interview session
  Future<Map<String, dynamic>> startAIInterview(
    String interviewId, {
    String? phoneNumber,
  }) async {
    final url = Uri.parse('$_baseUrl/interviews/$interviewId/start-ai');

    try {
      final response = await _client
          .post(
            url,
            headers: await _getAuthHeaders(),
            body: jsonEncode({
              'interviewId': interviewId,
              if (phoneNumber != null) 'candidatePhoneNumber': phoneNumber,
            }),
          )
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiException(
          'Failed to start AI interview: ${response.statusCode}',
          response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error starting AI interview: $e', 500);
    }
  }

  /// Get the status of an AI interview session
  Future<Map<String, dynamic>> getAIInterviewStatus(String interviewId) async {
    final url = Uri.parse('$_baseUrl/interviews/$interviewId/ai-status');

    try {
      final response = await _client
          .get(url, headers: await _getAuthHeaders())
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiException(
          'Failed to get AI interview status: ${response.statusCode}',
          response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error getting AI status: $e', 500);
    }
  }

  /// Get AI-generated feedback for a completed interview
  Future<Map<String, dynamic>> getAIFeedback(String interviewId) async {
    final url = Uri.parse('$_baseUrl/interviews/$interviewId/ai-feedback');

    try {
      final response = await _client
          .get(url, headers: await _getAuthHeaders())
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiException(
          'Failed to get AI feedback: ${response.statusCode}',
          response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error getting AI feedback: $e', 500);
    }
  }

  /// Stop an ongoing AI interview session
  Future<bool> stopAIInterview(String interviewId) async {
    final url = Uri.parse('$_baseUrl/interviews/$interviewId/stop-ai');

    try {
      final response = await _client
          .post(url, headers: await _getAuthHeaders(), body: jsonEncode({}))
          .timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// Creates a new interview record
  Future<Map<String, dynamic>> createInterview(
    Map<String, dynamic> interviewData,
  ) async {
    try {
      final url = Uri.parse('$_baseUrl/interviews');

      final response = await _client
          .post(
            url,
            headers: await _getAuthHeaders(),
            body: json.encode(interviewData),
          )
          .timeout(
            const Duration(seconds: 30),
            onTimeout: () => throw Exception('Request timeout'),
          );
      if (response.statusCode == 200 || response.statusCode == 201) {
        try {
          return json.decode(response.body) as Map<String, dynamic>;
        } catch (e) {
          throw ParseException(
            'Failed to parse interview creation response: $e',
          );
        }
      }
      // Use unified handler for richer error surface
      _handleResponse(response, 'Create interview');
      // _handleResponse will throw above for non-2xx; this return is unreachable
      return {};
    } catch (e) {
      if (e is ApiException || e is NetworkException || e is ParseException) {
        rethrow;
      }
      throw NetworkException('Failed to create interview: $e');
    }
  }

  /// Gets a specific interview by ID
  Future<Map<String, dynamic>> getInterview(String interviewId) async {
    try {
      final url = Uri.parse('$_baseUrl/interviews/$interviewId');

      final response = await _client
          .get(url, headers: await _getAuthHeaders())
          .timeout(
            const Duration(seconds: 30),
            onTimeout: () => throw Exception('Request timeout'),
          );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get interview: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get interview: $e');
    }
  }
}

/// Singleton instance of ApiService for global access
class ApiServiceSingleton {
  static ApiService? _instance;

  static ApiService get instance {
    _instance ??= ApiService();
    return _instance!;
  }

  static void dispose() {
    _instance?.dispose();
    _instance = null;
  }
}
