// Interview data model
import '../services/api_service.dart' show InterviewQuestion;

class Interview {
  final String id;
  final String jobTitle;
  final String? companyName;
  final DateTime interviewDate;
  final InterviewStatus status;
  final int? overallScore;
  final String? userId;
  final DateTime createdAt;
  final DateTime updatedAt;
  
  // Interview configuration fields
  final String? role;               // Job role for backward compatibility
  final String? type;               // Interview type (technical, behavioral, etc.)
  final String? level;              // Experience level (junior, mid, senior)
  final List<InterviewQuestion>? questions; // Interview questions
  
  // AI-specific fields
  final String? aiSessionId;        // Vapi session ID
  final String? audioRecordingUrl;  // Recording URL
  final String? transcriptUrl;      // Transcript URL
  final List<String>? aiInsights;   // AI-generated insights
  final String? vapiCallId;         // Vapi call identifier
  final int? interviewDuration;     // Duration in seconds

  Interview({
    required this.id,
    required this.jobTitle,
    this.companyName,
    required this.interviewDate,
    required this.status,
    this.overallScore,
    this.userId,
    required this.createdAt,
    required this.updatedAt,
    this.role,
    this.type,
    this.level,
    this.questions,
    this.aiSessionId,
    this.audioRecordingUrl,
    this.transcriptUrl,
    this.aiInsights,
    this.vapiCallId,
    this.interviewDuration,
  });

  factory Interview.fromJson(Map<String, dynamic> json) {
    return Interview(
      id: json['id'] ?? '',
      jobTitle: json['jobTitle'] ?? '',
      companyName: json['companyName'],
      interviewDate: DateTime.parse(json['interviewDate']),
      status: InterviewStatus.values.firstWhere(
        (e) => e.toString().split('.').last == json['status'],
        orElse: () => InterviewStatus.pending,
      ),
      overallScore: json['overallScore'],
      userId: json['userId'],
      createdAt: DateTime.parse(json['createdAt']),
      updatedAt: DateTime.parse(json['updatedAt']),
      role: json['role'] ?? json['jobTitle'], // Use jobTitle as fallback for role
      type: json['type'],
      level: json['level'],
      questions: json['questions'] != null 
          ? (json['questions'] as List).map((q) => InterviewQuestion.fromJson(q)).toList()
          : null,
      aiSessionId: json['aiSessionId'],
      audioRecordingUrl: json['audioRecordingUrl'],
      transcriptUrl: json['transcriptUrl'],
      aiInsights: json['aiInsights'] != null ? List<String>.from(json['aiInsights']) : null,
      vapiCallId: json['vapiCallId'],
      interviewDuration: json['interviewDuration'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'jobTitle': jobTitle,
      'companyName': companyName,
      'interviewDate': interviewDate.toIso8601String(),
      'status': status.toString().split('.').last,
      'overallScore': overallScore,
      'userId': userId,
      'createdAt': createdAt.toIso8601String(),
      'updatedAt': updatedAt.toIso8601String(),
      'role': role,
      'type': type,
      'level': level,
      'questions': questions?.map((q) => q.toJson()).toList(),
      'aiSessionId': aiSessionId,
      'audioRecordingUrl': audioRecordingUrl,
      'transcriptUrl': transcriptUrl,
      'aiInsights': aiInsights,
      'vapiCallId': vapiCallId,
      'interviewDuration': interviewDuration,
    };
  }

  Interview copyWith({
    String? id,
    String? jobTitle,
    String? companyName,
    DateTime? interviewDate,
    InterviewStatus? status,
    int? overallScore,
    String? userId,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? role,
    String? type,
    String? level,
    List<InterviewQuestion>? questions,
    String? aiSessionId,        // NEW: AI-specific fields
    String? audioRecordingUrl,
    String? transcriptUrl,
    List<String>? aiInsights,
    String? vapiCallId,
    int? interviewDuration,
  }) {
    return Interview(
      id: id ?? this.id,
      jobTitle: jobTitle ?? this.jobTitle,
      companyName: companyName ?? this.companyName,
      interviewDate: interviewDate ?? this.interviewDate,
      status: status ?? this.status,
      overallScore: overallScore ?? this.overallScore,
      userId: userId ?? this.userId,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      role: role ?? this.role,
      type: type ?? this.type,
      level: level ?? this.level,
      questions: questions ?? this.questions,
      aiSessionId: aiSessionId ?? this.aiSessionId,
      audioRecordingUrl: audioRecordingUrl ?? this.audioRecordingUrl,
      transcriptUrl: transcriptUrl ?? this.transcriptUrl,
      aiInsights: aiInsights ?? this.aiInsights,
      vapiCallId: vapiCallId ?? this.vapiCallId,
      interviewDuration: interviewDuration ?? this.interviewDuration,
    );
  }
}

enum InterviewStatus {
  pending,
  inProgress,    // NEW: AI is conducting the interview
  completed,
  scheduled,
  cancelled,
}
