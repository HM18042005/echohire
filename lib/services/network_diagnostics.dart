import 'dart:io';
import 'package:http/http.dart' as http;

class NetworkDiagnostics {
  static Future<void> runDiagnostics(String baseUrl) async {
    print('🔍 Running network diagnostics...');

    try {
      // Test DNS resolution
      final uri = Uri.parse(baseUrl);
      print('🌐 Testing DNS resolution for: ${uri.host}');

      final addresses = await InternetAddress.lookup(uri.host);
      if (addresses.isNotEmpty) {
        print(
          '✅ DNS resolved to: ${addresses.map((a) => a.address).join(', ')}',
        );
      } else {
        print('❌ DNS resolution failed');
        return;
      }

      // Test basic connectivity
      print('🔗 Testing HTTP connectivity...');
      final client = http.Client();

      final response = await client
          .get(
            Uri.parse('$baseUrl/health'),
            headers: {
              'User-Agent': 'EchoHire-Diagnostics/1.0',
              'Accept': 'application/json',
            },
          )
          .timeout(
            const Duration(seconds: 30),
            onTimeout: () => throw Exception('Connection timeout'),
          );

      print('📡 Response status: ${response.statusCode}');
      print('📄 Response body: ${response.body}');
      print('🔧 Response headers: ${response.headers}');

      if (response.statusCode == 200) {
        print('✅ Network connectivity test passed!');
      } else {
        print('❌ Unexpected response status: ${response.statusCode}');
      }

      client.close();
    } catch (e) {
      print('❌ Network diagnostics failed: $e');
    }
  }
}
