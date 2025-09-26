import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/auth_service.dart';
import '../state/interview_controller.dart';
import '../state/profile_controller.dart';
import '../models/interview.dart';
import 'interview_screen.dart';
import 'profile_screen.dart';
import 'interview_detail_screen.dart';
import 'ai_guided_interview_screen.dart';

/// HomeScreen serves as the main dashboard for authenticated users
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _currentIndex = 0;
  final _authService = AuthService();

  @override
  void initState() {
    super.initState();
    // Load initial data when the screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(interviewControllerProvider.notifier).loadInterviews();
      ref.read(profileControllerProvider.notifier).loadProfile();
    });
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> pages = [
      _buildHomeView(),
      const InterviewScreen(),
      const ProfileScreen(),
    ];

    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: pages),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => const AIGuidedInterviewScreen(),
            ),
          );
        },
        icon: const Icon(Icons.auto_awesome),
        label: const Text('AI Interview'),
        backgroundColor: Colors.blue.shade600,
        foregroundColor: Colors.white,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.work_outline),
            activeIcon: Icon(Icons.work),
            label: 'Interviews',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            activeIcon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
        type: BottomNavigationBarType.fixed,
        backgroundColor: const Color(0xFF1E1E1E),
        selectedItemColor: Colors.blue,
        unselectedItemColor: Colors.grey,
      ),
    );
  }

  Widget _buildHomeView() {
    final profileState = ref.watch(profileControllerProvider);
    final interviewState = ref.watch(interviewControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Welcome${profileState.profile?.displayName != null ? ', ${profileState.profile!.displayName.split(' ').first}' : ''}',
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => _showLogoutDialog(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await ref.read(interviewControllerProvider.notifier).loadInterviews();
          await ref.read(profileControllerProvider.notifier).loadProfile();
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Welcome Card
              _buildWelcomeCard(profileState.profile),

              const SizedBox(height: 24),

              // Quick Stats
              _buildQuickStats(interviewState.interviews),

              const SizedBox(height: 24),

              // Recent Interviews Section
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Recent Interviews',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  TextButton(
                    onPressed: () => setState(() => _currentIndex = 1),
                    child: const Text('View All'),
                  ),
                ],
              ),

              const SizedBox(height: 16),

              // Interview List
              _buildRecentInterviews(interviewState),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildWelcomeCard(dynamic profile) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: Colors.blue,
                  child: Text(
                    profile?.displayName?.substring(0, 1).toUpperCase() ?? 'U',
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        profile?.displayName ?? 'User',
                        style: Theme.of(context).textTheme.headlineSmall
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      if (profile?.headline != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          profile!.headline,
                          style: Theme.of(
                            context,
                          ).textTheme.bodyMedium?.copyWith(color: Colors.grey),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              'Ready to practice your next interview? Start by creating a new interview session or review your previous performance.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickStats(List<Interview> interviews) {
    final completedCount = interviews
        .where((i) => i.status == InterviewStatus.completed)
        .length;
    final pendingCount = interviews
        .where((i) => i.status == InterviewStatus.pending)
        .length;
    final totalCount = interviews.length;

    return Row(
      children: [
        Expanded(
          child: _buildStatCard(
            'Total Interviews',
            totalCount.toString(),
            Icons.work_outline,
            Colors.blue,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            'Completed',
            completedCount.toString(),
            Icons.check_circle_outline,
            Colors.green,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            'Pending',
            pendingCount.toString(),
            Icons.pending_outlined,
            Colors.orange,
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard(
    String title,
    String value,
    IconData icon,
    Color color,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              title,
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentInterviews(InterviewState interviewState) {
    if (interviewState.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (interviewState.error != null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 48),
              const SizedBox(height: 8),
              Text(
                'Failed to load interviews',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 4),
              Text(
                interviewState.error!,
                style: Theme.of(
                  context,
                ).textTheme.bodySmall?.copyWith(color: Colors.grey),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref
                    .read(interviewControllerProvider.notifier)
                    .loadInterviews(),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    if (interviewState.interviews.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            children: [
              const Icon(Icons.work_outline, color: Colors.grey, size: 64),
              const SizedBox(height: 16),
              Text(
                'No interviews yet',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                'Create your first interview to get started with AI practice sessions.',
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(color: Colors.grey),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => setState(() => _currentIndex = 1),
                child: const Text('Create Interview'),
              ),
            ],
          ),
        ),
      );
    }

    // Show recent interviews (max 5)
    final recentInterviews = interviewState.interviews.take(5).toList();

    return Column(
      children: recentInterviews
          .map(
            (interview) => _InterviewCard(
              interview: interview,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) =>
                      InterviewDetailScreen(interview: interview),
                ),
              ),
            ),
          )
          .toList(),
    );
  }

  void _showLogoutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sign Out'),
        content: const Text('Are you sure you want to sign out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              await _authService.signOut();
            },
            child: const Text('Sign Out'),
          ),
        ],
      ),
    );
  }
}

/// Reusable interview card widget
class _InterviewCard extends StatelessWidget {
  final Interview interview;
  final VoidCallback onTap;

  const _InterviewCard({required this.interview, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12.0),
      child: ListTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor: _getStatusColor(interview.status).withOpacity(0.2),
          child: Icon(
            _getStatusIcon(interview.status),
            color: _getStatusColor(interview.status),
          ),
        ),
        title: Text(
          interview.jobTitle,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (interview.companyName != null) ...[
              Text(interview.companyName!),
              const SizedBox(height: 4),
            ],
            Row(
              children: [
                Chip(
                  label: Text(
                    interview.status.toString().split('.').last.toUpperCase(),
                    style: const TextStyle(fontSize: 10),
                  ),
                  backgroundColor: _getStatusColor(
                    interview.status,
                  ).withOpacity(0.2),
                  labelStyle: TextStyle(
                    color: _getStatusColor(interview.status),
                  ),
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                const Spacer(),
                Text(
                  '${interview.interviewDate.day}/${interview.interviewDate.month}/${interview.interviewDate.year}',
                  style: Theme.of(
                    context,
                  ).textTheme.bodySmall?.copyWith(color: Colors.grey),
                ),
              ],
            ),
          ],
        ),
        trailing: const Icon(Icons.arrow_forward_ios, size: 16),
      ),
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
}
