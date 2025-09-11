import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// Screen that displays detailed information about a specific interview session
/// Shows interview metadata and all questions in an organized, scrollable layout
class InterviewDetailScreen extends StatelessWidget {
  final InterviewSession interview;

  const InterviewDetailScreen({
    super.key,
    required this.interview,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF181A20),
      appBar: AppBar(
        title: Text(
          '${interview.role} Interview',
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: const Color(0xFF1F222A),
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline, color: Colors.white),
            onPressed: () {
              _showInterviewInfo(context);
            },
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Header section with interview details
          _buildHeaderSection(),
          const SizedBox(height: 24),
          
          // Questions section title
          _buildSectionTitle('Interview Questions'),
          const SizedBox(height: 16),
          
          // Questions list
          ...interview.questions.asMap().entries.map((entry) {
            final index = entry.key;
            final question = entry.value;
            return _QuestionCard(
              questionNumber: index + 1,
              question: question,
            );
          }),
          
          // Add some bottom padding for better scrolling experience
          const SizedBox(height: 24),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          // TODO: Navigate to interview session or start the interview
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Starting interview session...'),
              backgroundColor: Colors.blue,
            ),
          );
        },
        backgroundColor: Colors.blue,
        icon: const Icon(Icons.play_arrow, color: Colors.white),
        label: const Text(
          'Start Interview',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  /// Builds the header section with interview metadata
  Widget _buildHeaderSection() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1F222A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Colors.grey.withValues(alpha: 0.2),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Interview role title
          Text(
            interview.role,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          
          // Interview metadata in a grid layout
          Row(
            children: [
              Expanded(
                child: _buildMetadataItem(
                  icon: Icons.category,
                  label: 'Type',
                  value: _formatInterviewType(interview.type),
                  color: _getTypeColor(interview.type),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildMetadataItem(
                  icon: Icons.trending_up,
                  label: 'Level',
                  value: _formatLevel(interview.level),
                  color: _getLevelColor(interview.level),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          Row(
            children: [
              Expanded(
                child: _buildMetadataItem(
                  icon: Icons.quiz,
                  label: 'Questions',
                  value: '${interview.questions.length}',
                  color: Colors.purple,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildMetadataItem(
                  icon: Icons.access_time,
                  label: 'Created',
                  value: _formatDate(interview.createdAt),
                  color: Colors.orange,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds a metadata item with icon, label, and value
  Widget _buildMetadataItem({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: color.withValues(alpha: 0.3),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 16),
              const SizedBox(width: 4),
              Text(
                label,
                style: TextStyle(
                  color: color,
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds a section title with consistent styling
  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 20,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  /// Shows additional interview information in a dialog
  void _showInterviewInfo(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          backgroundColor: const Color(0xFF1F222A),
          title: const Text(
            'Interview Information',
            style: TextStyle(color: Colors.white),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildInfoRow('Interview ID', interview.id),
              _buildInfoRow('User ID', interview.userId),
              _buildInfoRow('Created At', interview.createdAt),
              _buildInfoRow('Total Questions', '${interview.questions.length}'),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text(
                'Close',
                style: TextStyle(color: Colors.blue),
              ),
            ),
          ],
        );
      },
    );
  }

  /// Builds an information row for the dialog
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              '$label:',
              style: const TextStyle(
                color: Colors.grey,
                fontSize: 14,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Formats the interview type for display
  String _formatInterviewType(String type) {
    return type.split('-').map((word) {
      return word[0].toUpperCase() + word.substring(1);
    }).join(' ');
  }

  /// Formats the level for display
  String _formatLevel(String level) {
    switch (level.toLowerCase()) {
      case 'junior':
        return 'Junior';
      case 'mid':
        return 'Mid-Level';
      case 'senior':
        return 'Senior';
      case 'lead':
        return 'Lead';
      default:
        return level[0].toUpperCase() + level.substring(1);
    }
  }

  /// Formats the date for display
  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      final months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return '${months[date.month - 1]} ${date.day}, ${date.year}';
    } catch (e) {
      return 'Unknown';
    }
  }

  /// Returns appropriate color for interview type
  Color _getTypeColor(String type) {
    switch (type.toLowerCase()) {
      case 'technical':
        return Colors.blue;
      case 'behavioral':
        return Colors.green;
      case 'system-design':
        return Colors.orange;
      case 'coding':
        return Colors.purple;
      default:
        return Colors.grey;
    }
  }

  /// Returns appropriate color for experience level
  Color _getLevelColor(String level) {
    switch (level.toLowerCase()) {
      case 'junior':
        return Colors.lightBlue;
      case 'mid':
        return Colors.amber;
      case 'senior':
        return Colors.deepOrange;
      case 'lead':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}

/// Custom widget for displaying individual interview questions
class _QuestionCard extends StatelessWidget {
  final int questionNumber;
  final InterviewQuestion question;

  const _QuestionCard({
    required this.questionNumber,
    required this.question,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1F222A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Colors.grey.withValues(alpha: 0.2),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Question header with number and category
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Question number
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.blue.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: Colors.blue.withValues(alpha: 0.5),
                    width: 1,
                  ),
                ),
                child: Text(
                  'Question $questionNumber',
                  style: const TextStyle(
                    color: Colors.blue,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              
              // Category and difficulty badges
              Row(
                children: [
                  _buildBadge(
                    question.category,
                    _getCategoryColor(question.category),
                  ),
                  const SizedBox(width: 8),
                  _buildBadge(
                    question.difficulty,
                    _getDifficultyColor(question.difficulty),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          // Question text
          Text(
            question.question,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              height: 1.5,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds a small badge for category or difficulty
  Widget _buildBadge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: color.withValues(alpha: 0.5),
          width: 1,
        ),
      ),
      child: Text(
        text.toUpperCase(),
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  /// Returns appropriate color for question category
  Color _getCategoryColor(String category) {
    switch (category.toLowerCase()) {
      case 'algorithms':
        return Colors.purple;
      case 'data structures':
        return Colors.indigo;
      case 'system design':
        return Colors.orange;
      case 'behavioral':
        return Colors.green;
      case 'coding':
        return Colors.blue;
      case 'databases':
        return Colors.teal;
      case 'networking':
        return Colors.cyan;
      default:
        return Colors.grey;
    }
  }

  /// Returns appropriate color for question difficulty
  Color _getDifficultyColor(String difficulty) {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return Colors.green;
      case 'medium':
        return Colors.orange;
      case 'hard':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}
