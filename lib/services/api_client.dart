// API client for backend communication with Firebase token injection
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth_service.dart';
import '../config.dart';

class ApiClient {
  final AuthService _authService = AuthService();

  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getIdToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<Map<String, dynamic>> getProfile() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('${AppConfig.baseUrl}/me'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else if (response.statusCode == 401) {
      throw Exception('Unauthorized');
    } else {
      throw Exception('Failed to load profile: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> updateProfile(
    Map<String, dynamic> updates,
  ) async {
    final headers = await _getHeaders();
    final response = await http.put(
      Uri.parse('${AppConfig.baseUrl}/me'),
      headers: headers,
      body: json.encode(updates),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else if (response.statusCode == 401) {
      throw Exception('Unauthorized');
    } else {
      throw Exception('Failed to update profile: ${response.body}');
    }
  }

  // Interview endpoints
  Future<Map<String, dynamic>> createInterview(
    Map<String, dynamic> interviewData,
  ) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('${AppConfig.baseUrl}/interviews'),
      headers: headers,
      body: json.encode(interviewData),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else if (response.statusCode == 401) {
      throw Exception('Unauthorized');
    } else {
      throw Exception('Failed to create interview: ${response.body}');
    }
  }

  Future<List<Map<String, dynamic>>> getUserInterviews() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('${AppConfig.baseUrl}/interviews'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.cast<Map<String, dynamic>>();
    } else if (response.statusCode == 401) {
      throw Exception('Unauthorized');
    } else {
      throw Exception('Failed to load interviews: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> getInterview(String interviewId) async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('${AppConfig.baseUrl}/interviews/$interviewId'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else if (response.statusCode == 401) {
      throw Exception('Unauthorized');
    } else if (response.statusCode == 404) {
      throw Exception('Interview not found');
    } else {
      throw Exception('Failed to load interview: ${response.body}');
    }
  }

  // Feedback endpoints
  Future<Map<String, dynamic>> createFeedback(
    String interviewId,
    Map<String, dynamic> feedbackData,
  ) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('${AppConfig.baseUrl}/interviews/$interviewId/feedback'),
      headers: headers,
      body: json.encode(feedbackData),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else if (response.statusCode == 401) {
      throw Exception('Unauthorized');
    } else if (response.statusCode == 404) {
      throw Exception('Interview not found');
    } else {
      throw Exception('Failed to create feedback: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> getFeedback(String interviewId) async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('${AppConfig.baseUrl}/interviews/$interviewId/feedback'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else if (response.statusCode == 401) {
      throw Exception('Unauthorized');
    } else if (response.statusCode == 404) {
      throw Exception('Feedback not found');
    } else {
      throw Exception('Failed to load feedback: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> healthCheck() async {
    final response = await http.get(Uri.parse('${AppConfig.baseUrl}/health'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Health check failed');
    }
  }
}
