import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_sound/flutter_sound.dart';
import '../models/interview.dart';
import '../services/api_service.dart';
import '../services/ai_interview_launcher.dart';
import 'interview_results_screen.dart';

/// InterviewDetailScreen displays comprehensive interview information and actions
class InterviewDetailScreen extends ConsumerStatefulWidget {
  final Interview interview;

  const InterviewDetailScreen({super.key, required this.interview});

  @override
  ConsumerState<InterviewDetailScreen> createState() =>
      _InterviewDetailScreenState();
}

class _InterviewDetailScreenState extends ConsumerState<InterviewDetailScreen> {
  bool _isStartingInterview = false;
  FlutterSoundPlayer? _player;
  bool _isPlaying = false;

  @override
  void initState() {
    super.initState();
    // Initialize audio player lazily to avoid blocking build
    Future.microtask(_initPlayer);
  }

  Future<void> _initPlayer() async {
    try {
      _player = FlutterSoundPlayer();
      await _player!.openPlayer();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to initialize player: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.interview.jobTitle),
        actions: [
          PopupMenuButton(
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'edit',
                child: Row(
                  children: [
                    Icon(Icons.edit),
                    SizedBox(width: 8),
                    Text('Edit Interview'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'delete',
                child: Row(
                  children: [
                    Icon(Icons.delete, color: Colors.red),
                    SizedBox(width: 8),
                    Text(
                      'Delete Interview',
                      style: TextStyle(color: Colors.red),
                    ),
                  ],
                ),
              ),
            ],
            onSelected: (value) {
              if (value == 'delete') {
                _showDeleteDialog();
              }
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Interview Overview Card
            _buildOverviewCard(),

            const SizedBox(height: 16),

            // Interview Status Card
            _buildStatusCard(),

            const SizedBox(height: 16),

            // Questions Section (if available)
            if (widget.interview.questions != null &&
                widget.interview.questions!.isNotEmpty)
              _buildQuestionsSection(),

            // AI Insights Section (if available)
            if (widget.interview.aiInsights != null &&
                widget.interview.aiInsights!.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildAIInsightsSection(),
            ],

            // Performance Section (if completed)
            if (widget.interview.status == InterviewStatus.completed) ...[
              const SizedBox(height: 16),
              _buildPerformanceSection(),
            ],

            const SizedBox(height: 24),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomActions(),
    );
  }

  Widget _buildOverviewCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 24,
                  backgroundColor: _getStatusColor().withOpacity(0.2),
                  child: Icon(
                    _getStatusIcon(),
                    color: _getStatusColor(),
                    size: 24,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.interview.jobTitle,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (widget.interview.companyName != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          widget.interview.companyName!,
                          style: Theme.of(
                            context,
                          ).textTheme.bodyLarge?.copyWith(color: Colors.grey),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Interview Details
            _buildDetailRow(
              'Interview Date',
              _formatDate(widget.interview.interviewDate),
            ),
            _buildDetailRow('Created', _formatDate(widget.interview.createdAt)),
            if (widget.interview.type != null)
              _buildDetailRow('Type', widget.interview.type!),
            if (widget.interview.level != null)
              _buildDetailRow('Level', widget.interview.level!),
            if (widget.interview.interviewDuration != null)
              _buildDetailRow(
                'Duration',
                '${widget.interview.interviewDuration! ~/ 60} minutes',
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Interview Status',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: _getStatusColor().withOpacity(0.2),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(_getStatusIcon(), color: _getStatusColor(), size: 16),
                  const SizedBox(width: 8),
                  Text(
                    widget.interview.status
                        .toString()
                        .split('.')
                        .last
                        .toUpperCase(),
                    style: TextStyle(
                      color: _getStatusColor(),
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Text(
              _getStatusDescription(),
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuestionsSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Interview Questions',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            ...widget.interview.questions!.asMap().entries.map((entry) {
              final index = entry.key;
              final question = entry.value;
              return Padding(
                padding: const EdgeInsets.only(bottom: 12.0),
                child: Container(
                  padding: const EdgeInsets.all(12.0),
                  decoration: BoxDecoration(
                    color: Colors.grey.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Question ${index + 1}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.blue,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        question.question,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildAIInsightsSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.psychology, color: Colors.purple),
                const SizedBox(width: 8),
                Text(
                  'AI Insights',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...widget.interview.aiInsights!.map(
              (insight) => Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('• ', style: TextStyle(color: Colors.purple)),
                    Expanded(
                      child: Text(
                        insight,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPerformanceSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.analytics, color: Colors.green),
                const SizedBox(width: 8),
                Text(
                  'Performance Summary',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (widget.interview.overallScore != null) ...[
              Row(
                children: [
                  const Icon(Icons.star, color: Colors.amber),
                  const SizedBox(width: 8),
                  Text(
                    'Overall Score: ${widget.interview.overallScore}/100',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              LinearProgressIndicator(
                value: widget.interview.overallScore! / 100,
                backgroundColor: Colors.grey.withOpacity(0.3),
                valueColor: AlwaysStoppedAnimation<Color>(
                  widget.interview.overallScore! >= 80
                      ? Colors.green
                      : widget.interview.overallScore! >= 60
                      ? Colors.orange
                      : Colors.red,
                ),
              ),
            ],
            if (widget.interview.audioRecordingUrl != null) ...[
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _togglePlayback,
                icon: Icon(_isPlaying ? Icons.pause : Icons.play_arrow),
                label: Text(_isPlaying ? 'Pause Recording' : 'Play Recording'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: Colors.grey),
            ),
          ),
          Expanded(
            child: Text(value, style: Theme.of(context).textTheme.bodyMedium),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomActions() {
    return Container(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (widget.interview.status == InterviewStatus.pending ||
              widget.interview.status == InterviewStatus.scheduled) ...[
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isStartingInterview ? null : _startAIInterview,
                icon: _isStartingInterview
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.mic),
                label: Text(
                  _isStartingInterview ? 'Starting...' : 'Start AI Interview',
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ),
          ] else if (widget.interview.status == InterviewStatus.completed) ...[
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) =>
                          InterviewResultsScreen(interview: widget.interview),
                    ),
                  );
                },
                icon: const Icon(Icons.analytics),
                label: const Text('View Detailed Results'),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _startAIInterview() async {
    setState(() {
      _isStartingInterview = true;
    });

    try {
      // Call backend to start AI interview
      final response = await ApiServiceSingleton.instance.startAIInterview(
        widget.interview.id,
      );

      if (!mounted) return;

      await AIInterviewLauncher.launchFromStartData(
        context,
        interview: widget.interview,
        startData: response,
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to start interview: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isStartingInterview = false;
        });
      }
    }
  }

  void _showDeleteDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Interview'),
        content: const Text(
          'Are you sure you want to delete this interview? This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context); // Go back to previous screen
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Interview deleted'),
                  backgroundColor: Colors.orange,
                ),
              );
            },
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  Future<void> _togglePlayback() async {
    final url = widget.interview.audioRecordingUrl;
    if (url == null || url.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('No recording available.')));
      return;
    }

    if (_player == null) {
      await _initPlayer();
    }

    try {
      if (!_isPlaying) {
        await _player!.startPlayer(
          fromURI: url,
          codec: Codec.aacADTS,
          whenFinished: () {
            if (mounted) {
              setState(() => _isPlaying = false);
            }
          },
        );
        if (mounted) setState(() => _isPlaying = true);
      } else {
        await _player!.stopPlayer();
        if (mounted) setState(() => _isPlaying = false);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Playback error: $e')));
      }
    }
  }

  Color _getStatusColor() {
    switch (widget.interview.status) {
      case InterviewStatus.completed:
        return Colors.green;
      case InterviewStatus.inProgress:
        return Colors.blue;
      case InterviewStatus.scheduled:
        return Colors.orange;
      case InterviewStatus.cancelled:
        return Colors.red;
      case InterviewStatus.pending:
        return Colors.grey;
    }
  }

  IconData _getStatusIcon() {
    switch (widget.interview.status) {
      case InterviewStatus.completed:
        return Icons.check_circle;
      case InterviewStatus.inProgress:
        return Icons.play_circle;
      case InterviewStatus.scheduled:
        return Icons.schedule;
      case InterviewStatus.cancelled:
        return Icons.cancel;
      case InterviewStatus.pending:
        return Icons.pending;
    }
  }

  String _getStatusDescription() {
    switch (widget.interview.status) {
      case InterviewStatus.completed:
        return 'This interview has been completed. You can review your performance and insights.';
      case InterviewStatus.inProgress:
        return 'This interview is currently in progress.';
      case InterviewStatus.scheduled:
        return 'This interview is scheduled and ready to start.';
      case InterviewStatus.cancelled:
        return 'This interview has been cancelled.';
      case InterviewStatus.pending:
        return 'This interview is ready to begin whenever you are.';
    }
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }

  @override
  void dispose() {
    _player?.closePlayer();
    super.dispose();
  }
}
