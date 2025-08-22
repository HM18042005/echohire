// API client for backend communication with Firebase token injection
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth_service.dart';

class ApiClient {
  // Use 10.0.2.2 for Android emulator (maps to host machine's localhost)
  static const String baseUrl = 'http://10.0.2.2:8000';
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
      Uri.parse('$baseUrl/me'),
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

  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> updates) async {
    final headers = await _getHeaders();
    final response = await http.put(
      Uri.parse('$baseUrl/me'),
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

  Future<Map<String, dynamic>> healthCheck() async {
    final response = await http.get(Uri.parse('$baseUrl/health'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Health check failed');
    }
  }
}
