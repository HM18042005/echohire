import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../state/interview_controller.dart';
import '../models/interview.dart';

/// NewInterviewScreen provides a form to create new interview sessions
class NewInterviewScreen extends ConsumerStatefulWidget {
  const NewInterviewScreen({super.key});

  @override
  ConsumerState<NewInterviewScreen> createState() => _NewInterviewScreenState();
}

class _NewInterviewScreenState extends ConsumerState<NewInterviewScreen> {
  final _formKey = GlobalKey<FormState>();
  final _jobTitleController = TextEditingController();
  final _companyNameController = TextEditingController();

  DateTime _selectedDate = DateTime.now().add(const Duration(days: 1));
  bool _isLoading = false;

  @override
  void dispose() {
    _jobTitleController.dispose();
    _companyNameController.dispose();
    super.dispose();
  }

  Future<void> _createInterview() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final interviewController = ref.read(
        interviewControllerProvider.notifier,
      );

      final newInterview = await interviewController.createInterview(
        jobTitle: _jobTitleController.text.trim(),
        companyName: _companyNameController.text.trim(),
        interviewDate: _selectedDate,
        status: InterviewStatus.pending,
      );

      if (newInterview != null && mounted) {
        // Show success message
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Interview created successfully!'),
            backgroundColor: Colors.green,
          ),
        );

        // Navigate back
        Navigator.pop(context);
      } else if (mounted) {
        _showErrorSnackBar('Failed to create interview. Please try again.');
      }
    } catch (e) {
      if (mounted) {
        _showErrorSnackBar(e.toString());
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 4),
      ),
    );
  }

  Future<void> _selectDate() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: Theme.of(
              context,
            ).colorScheme.copyWith(primary: Colors.blue),
          ),
          child: child!,
        );
      },
    );

    if (picked != null && picked != _selectedDate) {
      setState(() {
        _selectedDate = picked;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Create New Interview'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header Section
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    children: [
                      const Icon(
                        Icons.work_outline,
                        size: 48,
                        color: Colors.blue,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'New Interview Setup',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Fill in the details for your upcoming interview practice session.',
                        style: Theme.of(
                          context,
                        ).textTheme.bodyMedium?.copyWith(color: Colors.grey),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Job Title Field
              TextFormField(
                controller: _jobTitleController,
                decoration: const InputDecoration(
                  labelText: 'Job Title *',
                  prefixIcon: Icon(Icons.work_outline),
                  hintText: 'e.g., Senior Flutter Developer',
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter the job title';
                  }
                  if (value.length < 2) {
                    return 'Job title must be at least 2 characters';
                  }
                  return null;
                },
              ),

              const SizedBox(height: 16),

              // Company Name Field
              TextFormField(
                controller: _companyNameController,
                decoration: const InputDecoration(
                  labelText: 'Company Name *',
                  prefixIcon: Icon(Icons.business),
                  hintText: 'e.g., Google, Apple, Microsoft',
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter the company name';
                  }
                  if (value.length < 2) {
                    return 'Company name must be at least 2 characters';
                  }
                  return null;
                },
              ),

              const SizedBox(height: 16),

              // Interview Date Field
              InkWell(
                onTap: _selectDate,
                child: InputDecorator(
                  decoration: const InputDecoration(
                    labelText: 'Interview Date *',
                    prefixIcon: Icon(Icons.calendar_today),
                  ),
                  child: Text(
                    '${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Tips Section
              Card(
                color: Colors.blue.withOpacity(0.1),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(
                            Icons.lightbulb_outline,
                            color: Colors.blue,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'Tips for Better Practice',
                            style: Theme.of(context).textTheme.titleSmall
                                ?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.blue,
                                ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        '• Be specific with the job title for better question relevance\n'
                        '• Research the company beforehand\n'
                        '• Choose a date that gives you time to prepare\n'
                        '• Make sure you\'re in a quiet environment for the AI interview',
                        style: TextStyle(color: Colors.blue),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 32),

              // Create Button
              ElevatedButton(
                onPressed: _isLoading ? null : _createInterview,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(
                            Colors.white,
                          ),
                        ),
                      )
                    : const Text('Create Interview'),
              ),

              const SizedBox(height: 16),

              // Cancel Button
              TextButton(
                onPressed: _isLoading ? null : () => Navigator.pop(context),
                child: const Text('Cancel'),
              ),

              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
