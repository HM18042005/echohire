import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/auth_service.dart';
import '../state/profile_controller.dart';

class SignUpScreen extends ConsumerStatefulWidget {
  const SignUpScreen({super.key});

  @override
  ConsumerState<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends ConsumerState<SignUpScreen> {
  final _authService = AuthService();
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _displayNameController = TextEditingController();
  final _headlineController = TextEditingController();
  final _locationController = TextEditingController();
  final _skillsController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _displayNameController.dispose();
    _headlineController.dispose();
    _locationController.dispose();
    _skillsController.dispose();
    super.dispose();
  }

  Future<void> _signUp() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    try {
      // Create Firebase user account
      final userCredential = await _authService.createUserWithEmailAndPassword(
        _emailController.text.trim(),
        _passwordController.text,
      );
      
      // Parse skills from comma-separated string
      final skillsText = _skillsController.text.trim();
      final skills = skillsText.isNotEmpty 
          ? skillsText.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList()
          : <String>[];
      
      // Save additional profile data using ProfileController
      await ref.read(profileControllerProvider.notifier).updateProfile(
        displayName: _displayNameController.text.trim(),
        headline: _headlineController.text.trim().isNotEmpty ? _headlineController.text.trim() : null,
        location: _locationController.text.trim().isNotEmpty ? _locationController.text.trim() : null,
        skills: skills.isNotEmpty ? skills : null,
      );
      
      // Check for any profile update errors
      final profileState = ref.read(profileControllerProvider);
      if (profileState.error != null) {
        throw Exception('Failed to save profile: ${profileState.error}');
      }
      
      // Show success message and navigate
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Account created successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        // Navigate to home screen or wherever appropriate
        Navigator.of(context).pushReplacementNamed('/home');
      }
      
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Sign up failed: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
    if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF181A20),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Center(
            child: Container(
              width: 350,
              margin: const EdgeInsets.symmetric(vertical: 32),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
              decoration: BoxDecoration(
                color: const Color(0xFF23262A),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Center(
                      child: Text(
                        'EchoHire',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    
                    // Full Name
                    const Text('Full Name', style: TextStyle(color: Colors.white)),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _displayNameController,
                      decoration: InputDecoration(
                        hintText: 'Enter your full name',
                        filled: true,
                        fillColor: const Color(0xFF181A20),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                        hintStyle: const TextStyle(color: Colors.white54),
                      ),
                      style: const TextStyle(color: Colors.white),
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Full name is required';
                        }
                        if (value.trim().length > 80) {
                          return 'Name must be 80 characters or less';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // Email
                    const Text('Email', style: TextStyle(color: Colors.white)),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _emailController,
                      decoration: InputDecoration(
                        hintText: 'Enter your email',
                        filled: true,
                        fillColor: const Color(0xFF181A20),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                        hintStyle: const TextStyle(color: Colors.white54),
                      ),
                      style: const TextStyle(color: Colors.white),
                      keyboardType: TextInputType.emailAddress,
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Email is required';
                        }
                        if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value)) {
                          return 'Enter a valid email';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // Password
                    const Text('Password', style: TextStyle(color: Colors.white)),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _passwordController,
                      decoration: InputDecoration(
                        hintText: 'Enter your password',
                        filled: true,
                        fillColor: const Color(0xFF181A20),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                        hintStyle: const TextStyle(color: Colors.white54),
                      ),
                      style: const TextStyle(color: Colors.white),
                      obscureText: true,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Password is required';
                        }
                        if (value.length < 6) {
                          return 'Password must be at least 6 characters';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // Confirm Password
                    const Text('Confirm Password', style: TextStyle(color: Colors.white)),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _confirmPasswordController,
                      decoration: InputDecoration(
                        hintText: 'Confirm your password',
                        filled: true,
                        fillColor: const Color(0xFF181A20),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                        hintStyle: const TextStyle(color: Colors.white54),
                      ),
                      style: const TextStyle(color: Colors.white),
                      obscureText: true,
                      validator: (value) {
                        if (value != _passwordController.text) {
                          return 'Passwords do not match';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // Headline (optional)
                    const Text('Headline (optional)', style: TextStyle(color: Colors.white)),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _headlineController,
                      decoration: InputDecoration(
                        hintText: 'e.g., Software Developer',
                        filled: true,
                        fillColor: const Color(0xFF181A20),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                        hintStyle: const TextStyle(color: Colors.white54),
                      ),
                      style: const TextStyle(color: Colors.white),
                      validator: (value) {
                        if (value != null && value.length > 140) {
                          return 'Headline must be 140 characters or less';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // Location (optional)
                    const Text('Location (optional)', style: TextStyle(color: Colors.white)),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _locationController,
                      decoration: InputDecoration(
                        hintText: 'e.g., San Francisco, CA',
                        filled: true,
                        fillColor: const Color(0xFF181A20),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                        hintStyle: const TextStyle(color: Colors.white54),
                      ),
                      style: const TextStyle(color: Colors.white),
                      validator: (value) {
                        if (value != null && value.length > 100) {
                          return 'Location must be 100 characters or less';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // Skills (optional)
                    const Text('Skills (optional)', style: TextStyle(color: Colors.white)),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _skillsController,
                      decoration: InputDecoration(
                        hintText: 'e.g., Flutter, Dart, JavaScript',
                        filled: true,
                        fillColor: const Color(0xFF181A20),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                        hintStyle: const TextStyle(color: Colors.white54),
                        helperText: 'Separate skills with commas',
                        helperStyle: const TextStyle(color: Colors.white38),
                      ),
                      style: const TextStyle(color: Colors.white),
                      maxLines: 2,
                      validator: (value) {
                        if (value != null && value.isNotEmpty) {
                          final skills = value.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
                          if (skills.length > 50) {
                            return 'Maximum 50 skills allowed';
                          }
                          for (final skill in skills) {
                            if (skill.length > 40) {
                              return 'Each skill must be 40 characters or less';
                            }
                          }
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 24),
                    
                    // Sign Up Button
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
                        onPressed: _isLoading ? null : _signUp,
                        child: _isLoading
                            ? const CircularProgressIndicator(color: Colors.white)
                            : const Text('Sign Up', style: TextStyle(fontSize: 16)),
                      ),
                    ),
                    const SizedBox(height: 12),
                    
                    // Already have account link
                    Center(
                      child: GestureDetector(
                        onTap: () => Navigator.of(context).pop(),
                        child: const Text(
                          "Already have an account? Log In",
                          style: TextStyle(color: Colors.white54, decoration: TextDecoration.underline),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
