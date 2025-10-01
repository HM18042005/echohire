import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConfig {
  static Future<void> load() async {
    // Support multiple env files by ENV dart-define
    const env = String.fromEnvironment('ENV', defaultValue: 'dev');
    final fileName = switch (env) {
      'device' => '.env.device',
      'prod' => '.env.production',
      _ => '.env',
    };
    await dotenv.load(fileName: fileName);
  }

  static String get baseUrl {
    final value = dotenv.env['BASE_URL'];
    if (value == null || value.isEmpty) {
      throw StateError('BASE_URL is not configured.');
    }
    return value;
  }

  /// Returns the current environment name from dart-define `ENV`.
  /// Defaults to `dev` when not provided.
  static String get envName =>
      const String.fromEnvironment('ENV', defaultValue: 'dev');

  /// True in development builds (`ENV=dev`) by default.
  static bool get isDev => envName == 'dev';

  /// Whether mock/offline fallbacks are enabled.
  /// Controlled by `.env` key `ENABLE_MOCKS`. Defaults to `false` when absent.
  static bool get enableMocks {
    final v = dotenv.env['ENABLE_MOCKS'];
    if (v == null) return false;
    final lower = v.toLowerCase();
    return lower == '1' || lower == 'true' || lower == 'yes';
  }

  /// Vapi Web Public Key for client-side web calls
  static String? get vapiPublicKey => dotenv.env['VAPI_PUBLIC_KEY'];

  /// Optional assistant Id to scope calls
  static String? get vapiAssistantId => dotenv.env['VAPI_ASSISTANT_ID'];
}
