// Interview feedback data model
class InterviewFeedback {
  final String id;
  final String interviewId;
  final String userId;
  final int overallScore;
  final String overallImpression;
  final List<EvaluationCriteria> breakdown;
  final String finalVerdict;
  final FeedbackRecommendation recommendation;
  final DateTime createdAt;

  InterviewFeedback({
    required this.id,
    required this.interviewId,
    required this.userId,
    required this.overallScore,
    required this.overallImpression,
    required this.breakdown,
    required this.finalVerdict,
    required this.recommendation,
    required this.createdAt,
  });

  factory InterviewFeedback.fromJson(Map<String, dynamic> json) {
    return InterviewFeedback(
      id: json['id'] ?? '',
      interviewId: json['interviewId'] ?? '',
      userId: json['userId'] ?? '',
      overallScore: json['overallScore'] ?? 0,
      overallImpression: json['overallImpression'] ?? '',
      breakdown: (json['breakdown'] as List? ?? [])
          .map((item) => EvaluationCriteria.fromJson(item))
          .toList(),
      finalVerdict: json['finalVerdict'] ?? '',
      recommendation: FeedbackRecommendation.values.firstWhere(
        (e) => e.toString().split('.').last == json['recommendation'],
        orElse: () => FeedbackRecommendation.notRecommended,
      ),
      createdAt: DateTime.parse(json['createdAt']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'interviewId': interviewId,
      'userId': userId,
      'overallScore': overallScore,
      'overallImpression': overallImpression,
      'breakdown': breakdown.map((item) => item.toJson()).toList(),
      'finalVerdict': finalVerdict,
      'recommendation': recommendation.toString().split('.').last,
      'createdAt': createdAt.toIso8601String(),
    };
  }
}

class EvaluationCriteria {
  final String title;
  final int score;
  final int maxScore;
  final String feedback;
  final bool isPassed;

  EvaluationCriteria({
    required this.title,
    required this.score,
    required this.maxScore,
    required this.feedback,
    required this.isPassed,
  });

  factory EvaluationCriteria.fromJson(Map<String, dynamic> json) {
    return EvaluationCriteria(
      title: json['title'] ?? '',
      score: json['score'] ?? 0,
      maxScore: json['maxScore'] ?? 0,
      feedback: json['feedback'] ?? '',
      isPassed: json['isPassed'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'score': score,
      'maxScore': maxScore,
      'feedback': feedback,
      'isPassed': isPassed,
    };
  }
}

enum FeedbackRecommendation {
  recommended,
  notRecommended,
  conditionallyRecommended,
}
