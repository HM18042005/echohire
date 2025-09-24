import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/interview.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../services/api_service.dart';

/// InterviewResultsScreen shows detailed results for a completed interview
class InterviewResultsScreen extends ConsumerWidget {
  final Interview interview;

  const InterviewResultsScreen({super.key, required this.interview});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final api = ApiServiceSingleton.instance;
    return Scaffold(
      appBar: AppBar(title: const Text('Interview Results')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      interview.jobTitle,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (interview.companyName != null) ...[
                      const SizedBox(height: 6),
                      Text(
                        interview.companyName!,
                        style: Theme.of(
                          context,
                        ).textTheme.bodyMedium?.copyWith(color: Colors.grey),
                      ),
                    ],
                    const SizedBox(height: 12),
                    if (interview.overallScore != null) ...[
                      Row(
                        children: [
                          const Icon(Icons.star, color: Colors.amber),
                          const SizedBox(width: 8),
                          Text(
                            'Overall Score: ${interview.overallScore}/100',
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      LinearProgressIndicator(
                        value: (interview.overallScore ?? 0) / 100,
                        backgroundColor: Colors.grey.withOpacity(0.3),
                        valueColor: AlwaysStoppedAnimation<Color>(
                          (interview.overallScore ?? 0) >= 80
                              ? Colors.green
                              : (interview.overallScore ?? 0) >= 60
                              ? Colors.orange
                              : Colors.red,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // AI Insights
            FutureBuilder<Map<String, dynamic>>(
              future: interview.status == InterviewStatus.completed
                  ? api
                        .getAIFeedback(interview.id)
                        .catchError((_) => <String, dynamic>{})
                  : Future.value(<String, dynamic>{}),
              builder: (context, snap) {
                final feedback = (snap.data ?? const <String, dynamic>{});
                final keyInsights =
                    (feedback['keyInsights'] as List?)?.cast<String>() ??
                    interview.aiInsights ??
                    const [];
                final overallImpression =
                    feedback['overallImpression'] as String?;
                final overallScore =
                    feedback['overallScore'] as int? ?? interview.overallScore;

                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.psychology, color: Colors.purple),
                            const SizedBox(width: 8),
                            Text(
                              'AI Insights',
                              style: Theme.of(context).textTheme.titleMedium
                                  ?.copyWith(fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        if (overallImpression != null &&
                            overallImpression.isNotEmpty) ...[
                          Text(overallImpression),
                          const SizedBox(height: 12),
                        ],
                        if (overallScore != null) ...[
                          Row(
                            children: [
                              const Icon(Icons.star, color: Colors.amber),
                              const SizedBox(width: 8),
                              Text(
                                'Overall Score: $overallScore/100',
                                style: Theme.of(context).textTheme.titleMedium
                                    ?.copyWith(fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          LinearProgressIndicator(
                            value: (overallScore) / 100,
                            backgroundColor: Colors.grey.withOpacity(0.3),
                            valueColor: AlwaysStoppedAnimation<Color>(
                              (overallScore) >= 80
                                  ? Colors.green
                                  : (overallScore) >= 60
                                  ? Colors.orange
                                  : Colors.red,
                            ),
                          ),
                          const SizedBox(height: 12),
                        ],
                        if (interview.aiInsights != null &&
                            interview.aiInsights!.isNotEmpty &&
                            keyInsights.isEmpty)
                          ...interview.aiInsights!.map(
                            (i) => Padding(
                              padding: const EdgeInsets.only(bottom: 8.0),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    '• ',
                                    style: TextStyle(color: Colors.purple),
                                  ),
                                  Expanded(child: Text(i)),
                                ],
                              ),
                            ),
                          )
                        else if (keyInsights.isNotEmpty)
                          ...keyInsights.map(
                            (i) => Padding(
                              padding: const EdgeInsets.only(bottom: 8.0),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    '• ',
                                    style: TextStyle(color: Colors.purple),
                                  ),
                                  Expanded(child: Text(i)),
                                ],
                              ),
                            ),
                          )
                        else
                          const Text('No AI insights available.'),
                      ],
                    ),
                  ),
                );
              },
            ),

            const SizedBox(height: 16),

            // Transcript Section (Firestore text preferred)
            FutureBuilder<DocumentSnapshot<Map<String, dynamic>>>(
              future: FirebaseFirestore.instance
                  .collection('transcripts')
                  .doc(interview.id)
                  .get(),
              builder: (context, snapshot) {
                final hasDoc =
                    snapshot.hasData && snapshot.data?.exists == true;
                final transcript = hasDoc
                    ? snapshot.data!.data()!['transcript'] as String?
                    : null;

                if (transcript != null && transcript.isNotEmpty) {
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.description, color: Colors.cyan),
                              const SizedBox(width: 8),
                              Text(
                                'Transcript',
                                style: Theme.of(context).textTheme.titleMedium
                                    ?.copyWith(fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(transcript),
                        ],
                      ),
                    ),
                  );
                }

                if (interview.transcriptUrl != null) {
                  return Card(
                    child: ListTile(
                      leading: const Icon(Icons.description),
                      title: const Text('View Transcript'),
                      subtitle: Text(interview.transcriptUrl!),
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Opening transcript...'),
                          ),
                        );
                      },
                    ),
                  );
                }

                return const SizedBox.shrink();
              },
            ),
          ],
        ),
      ),
    );
  }
}
