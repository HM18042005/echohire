import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'new_interview_screen.dart';
import 'profile_screen.dart';
import '../state/interview_controller.dart';
import '../models/interview.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  void initState() {
    super.initState();
    // Load interviews when the screen initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(interviewControllerProvider.notifier).loadInterviews();
    });
  }

  @override
  Widget build(BuildContext context) {
    final interviewState = ref.watch(interviewControllerProvider);
    final interviews = interviewState.interviews;
    final isLoading = interviewState.isLoading;
    final error = interviewState.error;

    return Scaffold(
      backgroundColor: const Color(0xFF181A20),
      appBar: AppBar(
        backgroundColor: const Color(0xFF181A20),
        elevation: 0,
        title: const Text('EchoHire', style: TextStyle(color: Colors.white)),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Hello, Alex!',
              style: TextStyle(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Recent Interviews',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16),
            // Interview list
            Expanded(
              child: _buildInterviewList(interviews, isLoading, error),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.of(context).push(
            MaterialPageRoute(builder: (context) => const NewInterviewScreen()),
          );
        },
        backgroundColor: const Color(0xFF2972FF),
        child: const Icon(Icons.add, color: Colors.white),
      ),
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: const Color(0xFF181A20),
        selectedItemColor: Colors.white,
        unselectedItemColor: Colors.white54,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.assignment),
            label: 'Reports',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
        onTap: (index) {
          if (index == 2) {
            Navigator.of(context).push(
              MaterialPageRoute(builder: (context) => const ProfileScreen()),
            );
          }
        },
      ),
    );
  }

  Widget _buildInterviewList(List<Interview> interviews, bool isLoading, String? error) {
    if (isLoading) {
      return const Center(
        child: CircularProgressIndicator(
          valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF2972FF)),
        ),
      );
    }

    if (error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              color: Colors.red,
              size: 48,
            ),
            const SizedBox(height: 16),
            Text(
              'Error loading interviews',
              style: TextStyle(color: Colors.white, fontSize: 18),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style: TextStyle(color: Colors.grey, fontSize: 14),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                ref.read(interviewControllerProvider.notifier).loadInterviews();
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF2972FF),
              ),
              child: const Text('Retry', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      );
    }

    if (interviews.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.assignment_outlined,
              color: Colors.grey,
              size: 64,
            ),
            const SizedBox(height: 16),
            const Text(
              'No interviews yet',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Tap the + button to schedule your first interview',
              style: TextStyle(color: Colors.grey, fontSize: 16),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: interviews.length,
      itemBuilder: (context, index) {
        final interview = interviews[index];
        return _InterviewCard(
          interview: interview,
          onTap: () {
            // Navigate to interview details
            _showInterviewDetails(context, interview);
          },
        );
      },
    );
  }

  void _showInterviewDetails(BuildContext context, Interview interview) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF181A20),
        title: Text(
          interview.jobTitle,
          style: const TextStyle(color: Colors.white),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Company: ${interview.companyName ?? 'N/A'}',
              style: const TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 8),
            Text(
              'Date: ${_formatDate(interview.interviewDate)}',
              style: const TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 8),
            Text(
              'Status: ${interview.status.toString().split('.').last}',
              style: TextStyle(
                color: _getStatusColor(interview.status),
                fontWeight: FontWeight.w600,
              ),
            ),
            if (interview.overallScore != null) ...[
              const SizedBox(height: 8),
              Text(
                'Score: ${interview.overallScore!.toStringAsFixed(1)}/100',
                style: const TextStyle(color: Colors.white),
              ),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text(
              'Close',
              style: TextStyle(color: Color(0xFF2972FF)),
            ),
          ),
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
    final months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }

  Color _getStatusColor(InterviewStatus status) {
    switch (status) {
      case InterviewStatus.pending:
        return Colors.orange;
      case InterviewStatus.scheduled:
        return const Color(0xFF2972FF);
      case InterviewStatus.completed:
        return Colors.green;
      case InterviewStatus.cancelled:
        return Colors.red;
    }
  }
}

class _InterviewCard extends StatelessWidget {
  final Interview interview;
  final VoidCallback? onTap;

  const _InterviewCard({
    required this.interview,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF262A34),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: _getCardColor(interview.status),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                _getCardIcon(interview.status),
                color: const Color(0xFF181A20),
                size: 24,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    interview.jobTitle,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    interview.companyName ?? 'Company',
                    style: const TextStyle(
                      color: Colors.grey,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _formatDate(interview.interviewDate),
                    style: const TextStyle(
                      color: Colors.grey,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: _getStatusColor(interview.status).withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                interview.status.toString().split('.').last,
                style: TextStyle(
                  color: _getStatusColor(interview.status),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getCardColor(InterviewStatus status) {
    switch (status) {
      case InterviewStatus.pending:
        return const Color(0xFFF5EEDC);
      case InterviewStatus.scheduled:
        return const Color(0xFFE3F2FD);
      case InterviewStatus.completed:
        return const Color(0xFFE8F5E8);
      case InterviewStatus.cancelled:
        return const Color(0xFFFFEBEE);
    }
  }

  IconData _getCardIcon(InterviewStatus status) {
    switch (status) {
      case InterviewStatus.pending:
        return Icons.schedule;
      case InterviewStatus.scheduled:
        return Icons.event;
      case InterviewStatus.completed:
        return Icons.check_circle;
      case InterviewStatus.cancelled:
        return Icons.cancel;
    }
  }

  Color _getStatusColor(InterviewStatus status) {
    switch (status) {
      case InterviewStatus.pending:
        return Colors.orange;
      case InterviewStatus.scheduled:
        return const Color(0xFF2972FF);
      case InterviewStatus.completed:
        return Colors.green;
      case InterviewStatus.cancelled:
        return Colors.red;
    }
  }

  String _formatDate(DateTime date) {
    final months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }
}
              color: Color(0xFFB6D7A8),
            ),
            _InterviewCard(
              title: 'UX Designer',
              date: 'Oct 15, 2024',
              logo: Icons.design_services,
              color: Color(0xFFF9E6D3),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF2972FF),
          onPressed: () {
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (context) => const NewInterviewScreen(),
              ),
            );
          },
        child: const Icon(Icons.add, color: Colors.white),
      ),
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: const Color(0xFF181A20),
        selectedItemColor: Colors.white,
        unselectedItemColor: Colors.white54,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
        currentIndex: 0,
        onTap: (index) {
          if (index == 1) {
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (context) => const ProfileScreen(),
              ),
            );
          }
        },
      ),
    );
  }
}

class _InterviewCard extends StatelessWidget {
  final String title;
  final String date;
  final IconData logo;
  final Color color;

  const _InterviewCard({
    required this.title,
    required this.date,
    required this.logo,
    required this.color,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: Row(
        children: [
          Container(
            width: 64,
            height: 48,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(logo, size: 32, color: Colors.black87),
          ),
          const SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Text(
                date,
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
