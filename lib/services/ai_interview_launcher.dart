import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config.dart';
import '../models/interview.dart';
import '../screens/interview_results_screen.dart';
import '../screens/vapi_web_call_page.dart';
import 'api_service.dart';

class AIInterviewLauncher {
  const AIInterviewLauncher._();

  /// Starts an AI interview via the backend and launches the appropriate
  /// client experience (web call page, external link, or phone instructions).
  static Future<void> startAndLaunch(
    BuildContext context, {
    required Interview interview,
    String? phoneNumber,
  }) async {
    try {
      final response = await ApiServiceSingleton.instance.startAIInterview(
        interview.id,
        phoneNumber: phoneNumber,
      );
      await _handleStartResponse(context, interview, response);
    } catch (e) {
      _showError(context, 'Failed to start interview: $e');
    }
  }

  /// Launches an AI interview using existing start data that has already been
  /// returned by the backend (for example, from workflow finalization).
  static Future<void> launchFromStartData(
    BuildContext context, {
    required Interview interview,
    Map<String, dynamic>? startData,
  }) async {
    if (startData == null || startData.isEmpty) {
      _showError(context, 'Interview start data was not provided.');
      return;
    }

    await _handleStartResponse(context, interview, startData);
  }

  static Future<void> _handleStartResponse(
    BuildContext context,
    Interview interview,
    Map<String, dynamic> data,
  ) async {
    final status = (data['status'] ?? '').toString().toLowerCase();
    final callId = data['callId']?.toString() ?? data['call_id']?.toString();
    final webCallUrl =
        data['webCallUrl'] ?? data['web_call_url'] ?? data['clientUrl'];
    final assistantId =
        (data['assistantId'] ??
                data['assistant_id'] ??
                AppConfig.vapiAssistantId ??
                '')
            .toString();
    final publicKey =
        (data['publicKey'] ?? data['public_key'] ?? AppConfig.vapiPublicKey)
            ?.toString();
    final metadata = data['metadata'];
    final metadataMap = metadata is Map<String, dynamic>
        ? Map<String, dynamic>.from(metadata)
        : <String, dynamic>{};

    if (status == 'ready_for_client_init') {
      if (assistantId.isEmpty || publicKey == null || publicKey.isEmpty) {
        _showError(
          context,
          'Missing Vapi configuration. Please check assistant ID and public key.',
        );
        return;
      }

      var callCompleted = false;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => VapiWebCallPage(
            publicKey: publicKey,
            assistantId: assistantId,
            metadata: metadataMap,
            interviewId: interview.id,
            onCallEnded: () {
              callCompleted = true;
            },
          ),
        ),
      );

      if (callCompleted && context.mounted) {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => InterviewResultsScreen(interview: interview),
          ),
        );
      }
      return;
    }

    if (webCallUrl != null) {
      final uri = Uri.tryParse(webCallUrl.toString());
      if (uri != null) {
        final launched = await launchUrl(
          uri,
          mode: LaunchMode.externalApplication,
        );
        if (!launched) {
          _showError(context, 'Could not open the interview link.');
        }
      } else {
        _showError(context, 'Invalid interview link received.');
      }
      return;
    }

    if (callId != null && callId.isNotEmpty) {
      _showInfo(
        context,
        'The interview has been scheduled. You will receive a call shortly (ID: $callId).',
      );
      return;
    }

    _showInfo(
      context,
      'Interview starting. Please check your device for further instructions.',
    );
  }

  static void _showError(BuildContext context, String message) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  static void _showInfo(BuildContext context, String message) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }
}
