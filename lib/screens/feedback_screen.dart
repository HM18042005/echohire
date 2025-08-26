import 'package:flutter/material.dart';

class FeedbackScreen extends StatelessWidget {
  const FeedbackScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF181A20),
      appBar: AppBar(
        backgroundColor: const Color(0xFF181A20),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text(
          'Feedback on the Interview - Behavioral',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 8),
              const Text(
                'Overall Impression: 12/100',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 22,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Feb 28, 2025 • 3:45 PM',
                style: TextStyle(color: Colors.white54, fontSize: 14),
              ),
              const SizedBox(height: 16),
              const Text(
                'The candidate demonstrated a basic understanding of the role requirements but struggled to articulate their experiences effectively. Their responses lacked depth and specific examples, hindering a comprehensive assessment of their skills and qualifications.',
                style: TextStyle(color: Colors.white, fontSize: 15),
              ),
              const SizedBox(height: 24),
              const Text(
                'Breakdown of Evaluation',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 17),
              ),
              const SizedBox(height: 16),
              _EvaluationItem(
                checked: false,
                number: 1,
                title: 'Enthusiasm & Interest (0/20)',
                description: '- Responses were vague and lacked specific examples.\n- Difficulty in articulating past experiences effectively.\n- Limited demonstration of enthusiasm for the role.',
              ),
              _EvaluationItem(
                checked: true,
                number: 2,
                title: 'Communication Clarity (10/20)',
                description: '- Provided clear and concise answers to direct questions.\n- Demonstrated a foundational understanding of the industry.\n- Maintained a professional demeanor throughout the interview.',
              ),
              _EvaluationItem(
                checked: false,
                number: 3,
                title: 'Adaptability & Critical Thinking (2/20)',
                description: '- Struggled to adapt responses to follow-up questions.\n- Difficulty in thinking critically about hypothetical scenarios.\n- Limited ability to connect past experiences to future challenges.',
              ),
              const SizedBox(height: 28),
              const Text(
                'Final Verdict',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 17),
              ),
              const SizedBox(height: 8),
              const Text(
                'Not Recommended',
                style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold, fontSize: 15),
              ),
              const SizedBox(height: 8),
              const Text(
                'Based on the evaluation, the candidate’s performance does not meet the required standards for this role. Significant improvements are needed in articulating experiences, demonstrating enthusiasm, and adapting to challenging questions.',
                style: TextStyle(color: Colors.white, fontSize: 15),
              ),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF2972FF),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  onPressed: () {},
                  child: const Text('Retake Interview', style: TextStyle(fontSize: 16)),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Colors.white24),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  onPressed: () {},
                  child: const Text('Back to Dashboard', style: TextStyle(color: Colors.white, fontSize: 16)),
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}

class _EvaluationItem extends StatelessWidget {
  final bool checked;
  final int number;
  final String title;
  final String description;

  const _EvaluationItem({
    required this.checked,
    required this.number,
    required this.title,
    required this.description,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF23262A),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            checked ? Icons.check_circle : Icons.cancel,
            color: checked ? Colors.blueAccent : Colors.white24,
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$number. $title',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                    fontSize: 15,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: const TextStyle(color: Colors.white70, fontSize: 14),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
