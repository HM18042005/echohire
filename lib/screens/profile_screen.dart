import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/auth_service.dart';
import '../state/profile_controller.dart';
import '../models/user_profile.dart';

/// ProfileScreen displays and allows editing of user profile information
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  final _authService = AuthService();
  bool _isEditMode = false;

  // Controllers for edit mode
  final _nameController = TextEditingController();
  final _headlineController = TextEditingController();
  final _locationController = TextEditingController();
  final _skillsController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _nameController.dispose();
    _headlineController.dispose();
    _locationController.dispose();
    _skillsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final profileState = ref.watch(profileControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          if (profileState.profile != null)
            IconButton(
              icon: Icon(_isEditMode ? Icons.close : Icons.edit),
              onPressed: () {
                if (_isEditMode) {
                  _cancelEdit();
                } else {
                  _startEdit(profileState.profile!);
                }
              },
            ),
          PopupMenuButton(
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'refresh',
                child: Row(
                  children: [
                    Icon(Icons.refresh),
                    SizedBox(width: 8),
                    Text('Refresh'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'logout',
                child: Row(
                  children: [
                    Icon(Icons.logout, color: Colors.red),
                    SizedBox(width: 8),
                    Text('Sign Out', style: TextStyle(color: Colors.red)),
                  ],
                ),
              ),
            ],
            onSelected: (value) {
              if (value == 'refresh') {
                ref.read(profileControllerProvider.notifier).loadProfile();
              } else if (value == 'logout') {
                _showLogoutDialog();
              }
            },
          ),
        ],
      ),
      body: _buildBody(profileState),
    );
  }

  Widget _buildBody(ProfileState profileState) {
    if (profileState.isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading profile...'),
          ],
        ),
      );
    }

    if (profileState.error != null) {
      return _buildErrorState(profileState.error!);
    }

    if (profileState.profile == null) {
      return _buildEmptyState();
    }

    return _isEditMode
        ? _buildEditMode(profileState.profile!)
        : _buildViewMode(profileState.profile!);
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
              'Failed to load profile',
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
              onPressed: () =>
                  ref.read(profileControllerProvider.notifier).loadProfile(),
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.person_outline, color: Colors.grey, size: 80),
            SizedBox(height: 16),
            Text(
              'No profile data available',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              'Please refresh or contact support if this persists.',
              style: TextStyle(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildViewMode(UserProfile profile) {
    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(profileControllerProvider.notifier).loadProfile();
      },
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Profile Header Card
            _buildProfileHeader(profile),

            const SizedBox(height: 16),

            // Profile Details Card
            _buildProfileDetails(profile),

            const SizedBox(height: 16),

            // Skills Card
            _buildSkillsCard(profile),

            const SizedBox(height: 16),

            // Account Information Card
            _buildAccountInfo(profile),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildEditMode(UserProfile profile) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Form(
        key: _formKey,
        child: Column(
          children: [
            // Edit Profile Header
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  children: [
                    CircleAvatar(
                      radius: 40,
                      backgroundColor: Colors.blue,
                      child: Text(
                        profile.displayName.substring(0, 1).toUpperCase(),
                        style: const TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Edit Profile',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Edit Form
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Name Field
                    TextFormField(
                      controller: _nameController,
                      decoration: const InputDecoration(
                        labelText: 'Full Name',
                        prefixIcon: Icon(Icons.person),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter your name';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 16),

                    // Headline Field
                    TextFormField(
                      controller: _headlineController,
                      decoration: const InputDecoration(
                        labelText: 'Professional Headline',
                        prefixIcon: Icon(Icons.work),
                      ),
                      maxLines: 2,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter your headline';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 16),

                    // Location Field
                    TextFormField(
                      controller: _locationController,
                      decoration: const InputDecoration(
                        labelText: 'Location',
                        prefixIcon: Icon(Icons.location_on),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter your location';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 16),

                    // Skills Field
                    TextFormField(
                      controller: _skillsController,
                      decoration: const InputDecoration(
                        labelText: 'Skills (comma-separated)',
                        prefixIcon: Icon(Icons.star),
                        hintText: 'e.g., Flutter, Dart, Firebase',
                      ),
                      maxLines: 3,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter your skills';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 24),

                    // Action Buttons
                    Row(
                      children: [
                        Expanded(
                          child: TextButton(
                            onPressed: _cancelEdit,
                            child: const Text('Cancel'),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: _saveProfile,
                            child: const Text('Save'),
                          ),
                        ),
                      ],
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

  Widget _buildProfileHeader(UserProfile profile) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            CircleAvatar(
              radius: 50,
              backgroundColor: Colors.blue,
              child: Text(
                profile.displayName.substring(0, 1).toUpperCase(),
                style: const TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              profile.displayName,
              style: Theme.of(
                context,
              ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              profile.headline,
              style: Theme.of(
                context,
              ).textTheme.bodyLarge?.copyWith(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileDetails(UserProfile profile) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Profile Details',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _buildDetailRow(Icons.location_on, 'Location', profile.location),
            _buildDetailRow(Icons.email, 'Email', profile.email),
            _buildDetailRow(
              Icons.calendar_today,
              'Member since',
              _formatDate(profile.createdAt),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSkillsCard(UserProfile profile) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Skills',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: profile.skills
                  .map(
                    (skill) => Chip(
                      label: Text(skill),
                      backgroundColor: Colors.blue.withOpacity(0.2),
                      labelStyle: const TextStyle(color: Colors.blue),
                    ),
                  )
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAccountInfo(UserProfile profile) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Account Information',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _buildDetailRow(Icons.fingerprint, 'User ID', profile.uid),
            _buildDetailRow(
              Icons.update,
              'Last updated',
              _formatDate(profile.updatedAt),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Row(
        children: [
          Icon(icon, color: Colors.grey, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: Theme.of(
                    context,
                  ).textTheme.bodySmall?.copyWith(color: Colors.grey),
                ),
                const SizedBox(height: 2),
                Text(value, style: Theme.of(context).textTheme.bodyMedium),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _startEdit(UserProfile profile) {
    setState(() {
      _isEditMode = true;
    });

    // Populate form fields
    _nameController.text = profile.displayName;
    _headlineController.text = profile.headline;
    _locationController.text = profile.location;
    _skillsController.text = profile.skills.join(', ');
  }

  void _cancelEdit() {
    setState(() {
      _isEditMode = false;
    });

    // Clear form fields
    _nameController.clear();
    _headlineController.clear();
    _locationController.clear();
    _skillsController.clear();
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) return;

    try {
      final skills = _skillsController.text
          .split(',')
          .map((skill) => skill.trim())
          .where((skill) => skill.isNotEmpty)
          .toList();

      await ref
          .read(profileControllerProvider.notifier)
          .updateProfile(
            displayName: _nameController.text.trim(),
            headline: _headlineController.text.trim(),
            location: _locationController.text.trim(),
            skills: skills,
          );

      if (mounted) {
        setState(() {
          _isEditMode = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Profile updated successfully!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to update profile: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
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

  String _formatDate(String dateString) {
    try {
      final date = DateTime.parse(dateString);
      return '${date.day}/${date.month}/${date.year}';
    } catch (e) {
      return dateString;
    }
  }
}
