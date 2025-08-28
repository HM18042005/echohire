import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'feedback_screen.dart';
import '../services/auth_service.dart';
import '../state/profile_controller.dart';
import '../main.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  final _authService = AuthService();

  @override
  void initState() {
    super.initState();
    // Load profile data when the screen is first displayed
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(profileControllerProvider.notifier).loadProfile().catchError((error) {
        print('Profile loading error: $error');
        // If profile loading fails, we can still show the UI with basic user info
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final profileState = ref.watch(profileControllerProvider);
    final currentUser = _authService.currentUser;

    return Scaffold(
      backgroundColor: const Color(0xFF181A20),
      appBar: AppBar(
        backgroundColor: const Color(0xFF181A20),
        elevation: 0,
        title: const Text('Profile', style: TextStyle(color: Colors.white)),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.white),
            onPressed: () async {
              await _authService.signOut();
              // Pop all screens to go back to the AuthWrapper
              if (context.mounted) {
                Navigator.of(context).popUntil((route) => route.isFirst);
              }
            },
          ),
        ],
      ),
      body: SafeArea(
        child: profileState.isLoading
            ? const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(color: Color(0xFF2972FF)),
                    SizedBox(height: 16),
                    Text('Loading profile...', style: TextStyle(color: Colors.white54)),
                  ],
                ),
              )
            : SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 8),
                    Text(
                      profileState.profile?.displayName ?? currentUser?.displayName ?? 'User',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 24,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      profileState.profile?.email ?? currentUser?.email ?? '',
                      style: const TextStyle(color: Colors.white54, fontSize: 15),
                    ),
                    if (profileState.error != null) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.orange.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.orange.withOpacity(0.3)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.warning, color: Colors.orange, size: 20),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Profile sync failed',
                                    style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold),
                                  ),
                                  const Text(
                                    'Using basic account info. Check your connection.',
                                    style: TextStyle(color: Colors.white70, fontSize: 12),
                                  ),
                                ],
                              ),
                            ),
                            TextButton(
                              onPressed: () => ref.read(profileControllerProvider.notifier).loadProfile(),
                              child: const Text('Retry', style: TextStyle(color: Colors.orange)),
                            ),
                          ],
                        ),
                      ),
                    ],
                        if (profileState.profile?.headline != null && profileState.profile!.headline!.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Text(
                            profileState.profile!.headline!,
                            style: const TextStyle(color: Colors.white70, fontSize: 16),
                          ),
                        ],
                        if (profileState.profile?.location != null && profileState.profile!.location!.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              const Icon(Icons.location_on, color: Colors.white54, size: 16),
                              const SizedBox(width: 4),
                              Text(
                                profileState.profile!.location!,
                                style: const TextStyle(color: Colors.white54, fontSize: 14),
                              ),
                            ],
                          ),
                        ],
                        if (profileState.profile?.skills != null && profileState.profile!.skills.isNotEmpty) ...[
                          const SizedBox(height: 16),
                          const Text(
                            'Skills',
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          const SizedBox(height: 8),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: profileState.profile!.skills.map((skill) {
                              return Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF2972FF).withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(color: const Color(0xFF2972FF).withOpacity(0.5)),
                                ),
                                child: Text(
                                  skill,
                                  style: const TextStyle(color: Colors.white, fontSize: 12),
                                ),
                              );
                            }).toList(),
                          ),
                        ],
                        const SizedBox(height: 24),
                        const Text(
                          'Previous Interviews',
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
                        ),
                        const SizedBox(height: 16),
                        _InterviewHistoryCard(
                          title: 'Product Manager',
                          date: 'Oct 26, 2024',
                          score: 78,
                          onViewFeedback: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (context) => const FeedbackScreen(),
                              ),
                            );
                          },
                        ),
                        _InterviewHistoryCard(
                          title: 'Software Engineer',
                          date: 'Oct 20, 2024',
                          score: 85,
                          onViewFeedback: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (context) => const FeedbackScreen(),
                              ),
                            );
                          },
                        ),
                        _InterviewHistoryCard(
                          title: 'UX Designer',
                          date: 'Oct 15, 2024',
                          score: 67,
                          onViewFeedback: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (context) => const FeedbackScreen(),
                              ),
                            );
                          },
                        ),
                        const SizedBox(height: 32),
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
                            onPressed: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (context) => const EditProfileScreen(),
                                ),
                              );
                            },
                            child: const Text('Edit Profile', style: TextStyle(fontSize: 16)),
                          ),
                        ),
                        const SizedBox(height: 24),
                      ],
                    ),
                  ),
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
        currentIndex: 1,
        onTap: (index) {
          if (index == 0) {
            Navigator.of(context).pop();
          }
        },
      ),
    );
  }
}

class _InterviewHistoryCard extends StatelessWidget {
  final String title;
  final String date;
  final int score;
  final VoidCallback onViewFeedback;

  const _InterviewHistoryCard({
    required this.title,
    required this.date,
    required this.score,
    required this.onViewFeedback,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF23262A),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  date,
                  style: const TextStyle(color: Colors.white54, fontSize: 14),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Text('Overall Score: ', style: TextStyle(color: Colors.white70, fontSize: 14)),
                    Text('$score/100', style: const TextStyle(color: Colors.blueAccent, fontWeight: FontWeight.bold, fontSize: 15)),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF2972FF),
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            onPressed: onViewFeedback,
            child: const Text('View Feedback', style: TextStyle(fontSize: 14)),
          ),
        ],
      ),
    );
  }
}
