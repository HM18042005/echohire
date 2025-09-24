import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../state/interview_controller.dart';
import '../models/interview.dart';
import 'new_interview_screen.dart';
import 'interview_detail_screen.dart';
import 'workflow_setup_screen.dart';

/// InterviewScreen displays all user interviews with filtering options
class InterviewScreen extends ConsumerStatefulWidget {
  const InterviewScreen({super.key});

  @override
  ConsumerState<InterviewScreen> createState() => _InterviewScreenState();
}

class _InterviewScreenState extends ConsumerState<InterviewScreen> {
  InterviewStatus? _selectedFilter;

  @override
  void initState() {
    super.initState();
    // Ensure interviews are loaded when screen is first shown
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(interviewControllerProvider.notifier).loadInterviews();
    });
  }

  @override
  Widget build(BuildContext context) {
    final interviewState = ref.watch(interviewControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Interviews'),
        actions: [
          PopupMenuButton<InterviewStatus?>(
            icon: const Icon(Icons.filter_list),
            onSelected: (status) {
              setState(() {
                _selectedFilter = status;
              });
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: null, child: Text('All Interviews')),
              const PopupMenuItem(
                value: InterviewStatus.pending,
                child: Text('Pending'),
              ),
              const PopupMenuItem(
                value: InterviewStatus.scheduled,
                child: Text('Scheduled'),
              ),
              const PopupMenuItem(
                value: InterviewStatus.inProgress,
                child: Text('In Progress'),
              ),
              const PopupMenuItem(
                value: InterviewStatus.completed,
                child: Text('Completed'),
              ),
              const PopupMenuItem(
                value: InterviewStatus.cancelled,
                child: Text('Cancelled'),
              ),
            ],
          ),
        ],
      ),
      body: _buildBody(interviewState),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showCreateOptions,
        icon: const Icon(Icons.add),
        label: const Text('Create'),
        backgroundColor: Colors.blue,
      ),
    );
  }

  Widget _buildBody(InterviewState interviewState) {
    if (interviewState.isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading interviews...'),
          ],
        ),
      );
    }

    if (interviewState.error != null) {
      return _buildErrorState(interviewState.error!);
    }

    final filteredInterviews = _getFilteredInterviews(
      interviewState.interviews,
    );

    if (filteredInterviews.isEmpty) {
      return _buildEmptyState();
    }

    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(interviewControllerProvider.notifier).loadInterviews();
      },
      child: Column(
        children: [
          if (_selectedFilter != null) _buildFilterChip(),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16.0),
              itemCount: filteredInterviews.length,
              itemBuilder: (context, index) {
                final interview = filteredInterviews[index];
                return _InterviewListCard(
                  interview: interview,
                  onTap: () => _navigateToInterviewDetail(interview),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      child: Row(
        children: [
          Chip(
            label: Text(
              'Filter: ${_selectedFilter.toString().split('.').last.toUpperCase()}',
              style: const TextStyle(fontSize: 12),
            ),
            onDeleted: () {
              setState(() {
                _selectedFilter = null;
              });
            },
            backgroundColor: Colors.blue.withOpacity(0.2),
            labelStyle: const TextStyle(color: Colors.blue),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 64),
            const SizedBox(height: 16),
            Text(
              'Failed to load interviews',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => ref
                  .read(interviewControllerProvider.notifier)
                  .loadInterviews(),
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    final isFiltered = _selectedFilter != null;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              isFiltered ? Icons.search_off : Icons.work_outline,
              color: Colors.grey,
              size: 80,
            ),
            const SizedBox(height: 16),
            Text(
              isFiltered
                  ? 'No ${_selectedFilter.toString().split('.').last} interviews found'
                  : 'No interviews yet',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              isFiltered
                  ? 'Try adjusting your filter or create a new interview.'
                  : 'Create your first interview to start practicing with AI.',
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => _navigateToNewInterview(),
              icon: const Icon(Icons.add),
              label: const Text('Create Interview'),
            ),
            if (isFiltered) ...[
              const SizedBox(height: 12),
              TextButton(
                onPressed: () {
                  setState(() {
                    _selectedFilter = null;
                  });
                },
                child: const Text('Clear Filter'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  List<Interview> _getFilteredInterviews(List<Interview> interviews) {
    if (_selectedFilter == null) {
      return interviews;
    }
    return interviews
        .where((interview) => interview.status == _selectedFilter)
        .toList();
  }

  void _navigateToNewInterview() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const NewInterviewScreen()),
    );
  }

  void _navigateToInterviewDetail(Interview interview) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => InterviewDetailScreen(interview: interview),
      ),
    );
  }

  void _showCreateOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1E1E1E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Create Interview',
                style: Theme.of(context)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              ListTile(
                leading: const Icon(Icons.edit_calendar),
                title: const Text('Manual Setup (Form)'),
                subtitle: const Text('Fill in job, company, date'),
                onTap: () {
                  Navigator.pop(ctx);
                  _navigateToNewInterview();
                },
              ),
              const SizedBox(height: 8),
              ListTile(
                leading: const Icon(Icons.auto_awesome),
                title: const Text('Guided Setup (AI)'),
                subtitle: const Text('Let AI collect details and start interview'),
                onTap: () {
                  Navigator.pop(ctx);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const WorkflowSetupScreen(),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Enhanced interview card for the list view
class _InterviewListCard extends StatelessWidget {
  final Interview interview;
  final VoidCallback onTap;

  const _InterviewListCard({required this.interview, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16.0),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          interview.jobTitle,
                          style: Theme.of(context).textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        if (interview.companyName != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            interview.companyName!,
                            style: Theme.of(context).textTheme.bodyMedium
                                ?.copyWith(color: Colors.grey),
                          ),
                        ],
                      ],
                    ),
                  ),
                  CircleAvatar(
                    radius: 20,
                    backgroundColor: _getStatusColor(
                      interview.status,
                    ).withOpacity(0.2),
                    child: Icon(
                      _getStatusIcon(interview.status),
                      color: _getStatusColor(interview.status),
                      size: 20,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 12),

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Chip(
                    label: Text(
                      interview.status.toString().split('.').last.toUpperCase(),
                      style: const TextStyle(fontSize: 11),
                    ),
                    backgroundColor: _getStatusColor(
                      interview.status,
                    ).withOpacity(0.2),
                    labelStyle: TextStyle(
                      color: _getStatusColor(interview.status),
                    ),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                  Text(
                    _formatDate(interview.interviewDate),
                    style: Theme.of(
                      context,
                    ).textTheme.bodySmall?.copyWith(color: Colors.grey),
                  ),
                ],
              ),

              if (interview.level != null || interview.type != null) ...[
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: [
                    if (interview.type != null)
                      _buildInfoChip(interview.type!, Icons.category),
                    if (interview.level != null)
                      _buildInfoChip(interview.level!, Icons.trending_up),
                  ],
                ),
              ],

              if (interview.overallScore != null) ...[
                const SizedBox(height: 12),
                Row(
                  children: [
                    const Icon(Icons.star, color: Colors.amber, size: 16),
                    const SizedBox(width: 4),
                    Text(
                      'Score: ${interview.overallScore}/100',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoChip(String label, IconData icon) {
    return Chip(
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12),
          const SizedBox(width: 4),
          Text(label, style: const TextStyle(fontSize: 10)),
        ],
      ),
      backgroundColor: Colors.grey.withOpacity(0.2),
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
  }

  Color _getStatusColor(InterviewStatus status) {
    switch (status) {
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

  IconData _getStatusIcon(InterviewStatus status) {
    switch (status) {
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

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = date.difference(now).inDays;

    if (difference == 0) {
      return 'Today';
    } else if (difference == 1) {
      return 'Tomorrow';
    } else if (difference == -1) {
      return 'Yesterday';
    } else if (difference > 0) {
      return 'In $difference days';
    } else {
      return '${-difference} days ago';
    }
  }
}
