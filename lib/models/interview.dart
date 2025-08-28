// Interview data model
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
    );
  }
}

enum InterviewStatus {
  pending,
  completed,
  scheduled,
  cancelled,
}
