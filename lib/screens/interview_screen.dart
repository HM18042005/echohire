import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../providers/interview_provider.dart';
import '../services/api_service.dart';
import 'interview_detail_screen.dart';

/// Screen that displays and manages interview sessions
/// Uses Provider pattern to manage state and react to changes
class InterviewScreen extends StatefulWidget {
  const InterviewScreen({super.key});

  @override
  State<InterviewScreen> createState() => _InterviewScreenState();
}

class _InterviewScreenState extends State<InterviewScreen> {
  String? _currentUserId;

  @override
  void initState() {
    super.initState();
    _initializeUser();
  }

  /// Initialize user and fetch interviews when the screen loads
  void _initializeUser() {
    final user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      _currentUserId = user.uid;
      // Fetch interviews after the widget is built
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          context.read<InterviewProvider>().fetchInterviews(_currentUserId!);
        }
      });
    }
  }

  /// Shows a dialog to create a new interview
  Future<void> _showCreateInterviewDialog() async {
    if (_currentUserId == null) return;

    final formKey = GlobalKey<FormState>();
    String role = '';
    String type = 'technical';
    String level = 'junior';

    return showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return AlertDialog(
          backgroundColor: const Color(0xFF1F222A),
          title: const Text(
            'Create New Interview',
            style: TextStyle(color: Colors.white),
          ),
          content: SingleChildScrollView(
            child: Form(
              key: formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Role input field
                  TextFormField(
                    style: const TextStyle(color: Colors.white),
                    decoration: const InputDecoration(
                      labelText: 'Job Role',
                      labelStyle: TextStyle(color: Colors.grey),
                      enabledBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.grey),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.blue),
                      ),
                    ),
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return 'Please enter a job role';
                      }
                      return null;
                    },
                    onSaved: (value) => role = value!.trim(),
                  ),
                  const SizedBox(height: 16),
                  
                  // Interview type dropdown
                  DropdownButtonFormField<String>(
                    initialValue: type,
                    dropdownColor: const Color(0xFF1F222A),
                    style: const TextStyle(color: Colors.white),
                    decoration: const InputDecoration(
                      labelText: 'Interview Type',
                      labelStyle: TextStyle(color: Colors.grey),
                      enabledBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.grey),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.blue),
                      ),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'technical', child: Text('Technical')),
                      DropdownMenuItem(value: 'behavioral', child: Text('Behavioral')),
                      DropdownMenuItem(value: 'system-design', child: Text('System Design')),
                      DropdownMenuItem(value: 'coding', child: Text('Coding')),
                    ],
                    onChanged: (value) => type = value!,
                  ),
                  const SizedBox(height: 16),
                  
                  // Experience level dropdown
                  DropdownButtonFormField<String>(
                    initialValue: level,
                    dropdownColor: const Color(0xFF1F222A),
                    style: const TextStyle(color: Colors.white),
                    decoration: const InputDecoration(
                      labelText: 'Experience Level',
                      labelStyle: TextStyle(color: Colors.grey),
                      enabledBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.grey),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.blue),
                      ),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'junior', child: Text('Junior')),
                      DropdownMenuItem(value: 'mid', child: Text('Mid-Level')),
                      DropdownMenuItem(value: 'senior', child: Text('Senior')),
                      DropdownMenuItem(value: 'lead', child: Text('Lead')),
                    ],
                    onChanged: (value) => level = value!,
                  ),
                ],
              ),
            ),
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancel', style: TextStyle(color: Colors.grey)),
            ),
            Consumer<InterviewProvider>(
              builder: (context, provider, child) {
                return ElevatedButton(
                  onPressed: provider.isLoading
                      ? null
                      : () async {
                          if (formKey.currentState!.validate()) {
                            formKey.currentState!.save();
                            
                            final newInterview = await provider.createInterview(
                              role: role,
                              type: type,
                              level: level,
                              userId: _currentUserId!,
                            );
                            
                            if (context.mounted) {
                              Navigator.of(context).pop();
                              
                              if (newInterview != null) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(
                                    content: Text('Interview created successfully!'),
                                    backgroundColor: Colors.green,
                                  ),
                                );
                              }
                            }
                          }
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                  ),
                  child: provider.isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : const Text('Create', style: TextStyle(color: Colors.white)),
                );
              },
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_currentUserId == null) {
      return const Scaffold(
        backgroundColor: Color(0xFF181A20),
        body: Center(
          child: Text(
            'Please log in to view interviews',
            style: TextStyle(color: Colors.white, fontSize: 18),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF181A20),
      appBar: AppBar(
        title: const Text(
          'My Interviews',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFF1F222A),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: () {
              context.read<InterviewProvider>().refreshInterviews(_currentUserId!);
            },
          ),
        ],
      ),
      body: Consumer<InterviewProvider>(
        builder: (context, provider, child) {
          // Show loading indicator
          if (provider.isLoading && !provider.hasInterviews) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Colors.blue),
                  SizedBox(height: 16),
                  Text(
                    'Loading interviews...',
                    style: TextStyle(color: Colors.grey, fontSize: 16),
                  ),
                ],
              ),
            );
          }

          // Show error message
          if (provider.hasError) {
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
                    provider.errorMessage!,
                    style: const TextStyle(color: Colors.red, fontSize: 16),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      provider.clearError();
                      provider.fetchInterviews(_currentUserId!);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                    ),
                    child: const Text(
                      'Retry',
                      style: TextStyle(color: Colors.white),
                    ),
                  ),
                ],
              ),
            );
          }

          // Show empty state
          if (!provider.hasInterviews) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.quiz_outlined,
                    color: Colors.grey,
                    size: 64,
                  ),
                  SizedBox(height: 16),
                  Text(
                    'No interviews yet',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Create your first interview to get started',
                    style: TextStyle(color: Colors.grey, fontSize: 16),
                  ),
                ],
              ),
            );
          }

          // Show interviews list
          return RefreshIndicator(
            onRefresh: () => provider.refreshInterviews(_currentUserId!),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: provider.interviews.length,
              itemBuilder: (context, index) {
                final interview = provider.interviews[index];
                return _InterviewCard(interview: interview);
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showCreateInterviewDialog,
        backgroundColor: Colors.blue,
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text(
          'New Interview',
          style: TextStyle(color: Colors.white),
        ),
      ),
    );
  }
}

/// Widget for displaying individual interview cards
class _InterviewCard extends StatelessWidget {
  final InterviewSession interview;

  const _InterviewCard({required this.interview});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFF1F222A),
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with role and type
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    interview.role,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getTypeColor(interview.type),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    interview.type.toUpperCase(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            
            // Level indicator
            Row(
              children: [
                const Icon(Icons.trending_up, color: Colors.grey, size: 16),
                const SizedBox(width: 4),
                Text(
                  'Level: ${interview.level.toUpperCase()}',
                  style: const TextStyle(color: Colors.grey, fontSize: 14),
                ),
              ],
            ),
            const SizedBox(height: 8),
            
            // Questions count
            Row(
              children: [
                const Icon(Icons.quiz, color: Colors.grey, size: 16),
                const SizedBox(width: 4),
                Text(
                  '${interview.questions.length} questions',
                  style: const TextStyle(color: Colors.grey, fontSize: 14),
                ),
              ],
            ),
            const SizedBox(height: 8),
            
            // Created date
            Row(
              children: [
                const Icon(Icons.access_time, color: Colors.grey, size: 16),
                const SizedBox(width: 4),
                Text(
                  'Created: ${_formatDate(interview.createdAt)}',
                  style: const TextStyle(color: Colors.grey, fontSize: 14),
                ),
              ],
            ),
            const SizedBox(height: 12),
            
            // Action button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  // Navigate to interview details screen
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => InterviewDetailScreen(
                        interview: interview,
                      ),
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                ),
                child: const Text('View Details'),
              ),
            ),
          ],
        ),
      ),
    );
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

  /// Formats the date string for display
  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month}/${date.year}';
    } catch (e) {
      return 'Unknown';
    }
  }
}
