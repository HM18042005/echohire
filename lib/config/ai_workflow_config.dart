/// AI Workflow Configuration
///
/// This file contains the universal workflow ID for AI guided interviews.
/// All AI guided interviews will use this single workflow configuration.
class AIWorkflowConfig {
  // Universal Vapi Workflow ID for all AI guided interviews
  static const String universalWorkflowId =
      '7894c32f-8b29-4e71-90f3-a19047832a21';

  // Workflow display name for UI purposes
  static const String workflowDisplayName = 'AI Guided Interview Workflow';

  // Workflow description
  static const String workflowDescription =
      'Standardized AI workflow for conducting comprehensive interview sessions';

  // Workflow version (for tracking updates)
  static const String workflowVersion = '1.0.0';

  // Whether the workflow is in production mode
  static const bool isProduction = true;

  /// Get the workflow ID to use for AI guided interviews
  static String getWorkflowId() {
    return universalWorkflowId;
  }

  /// Get a truncated version of the workflow ID for display purposes
  static String getDisplayWorkflowId() {
    return '${universalWorkflowId.substring(0, 8)}...${universalWorkflowId.substring(universalWorkflowId.length - 4)}';
  }

  /// Validate if a workflow ID matches the universal one
  static bool isValidWorkflowId(String? workflowId) {
    return workflowId != null && workflowId.trim() == universalWorkflowId;
  }
}
