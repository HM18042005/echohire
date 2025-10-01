import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../models/interview.dart';
import '../config/ai_workflow_config.dart';
import '../services/ai_interview_launcher.dart';

class AIGuidedInterviewScreen extends ConsumerStatefulWidget {
  const AIGuidedInterviewScreen({super.key});

  @override
  ConsumerState<AIGuidedInterviewScreen> createState() =>
      _AIGuidedInterviewScreenState();
}

class _AIGuidedInterviewScreenState
    extends ConsumerState<AIGuidedInterviewScreen> {
  final _formKey = GlobalKey<FormState>();
  // Universal workflow ID is now handled by AIWorkflowConfig
  final _candidateNameController = TextEditingController();
  final _jobTitleController = TextEditingController();
  final _companyNameController = TextEditingController();
  final _phoneController = TextEditingController();

  String _interviewType = 'technical';
  String _experienceLevel = 'mid';
  bool _usePhone = false;
  bool _loading = false;

  String? _errorMessage;

  final List<String> _interviewTypes = [
    'technical',
    'behavioral',
    'system_design',
    'cultural_fit',
    'mixed',
  ];

  final List<String> _experienceLevels = [
    'junior',
    'mid',
    'senior',
    'lead',
    'principal',
  ];

  @override
  void dispose() {
    _candidateNameController.dispose();
    _jobTitleController.dispose();
    _companyNameController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _startAIGuidedInterview() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _loading = true;
      _errorMessage = null;
    });

    try {
      final result = await ApiServiceSingleton.instance.createAIGuidedInterview(
        // workflowId is now universal and handled automatically by backend
        candidateName: _candidateNameController.text.trim().isNotEmpty
            ? _candidateNameController.text.trim()
            : null,
        jobTitle: _jobTitleController.text.trim().isNotEmpty
            ? _jobTitleController.text.trim()
            : null,
        companyName: _companyNameController.text.trim().isNotEmpty
            ? _companyNameController.text.trim()
            : null,
        interviewType: _interviewType,
        experienceLevel: _experienceLevel,
        phone: _usePhone && _phoneController.text.trim().isNotEmpty
            ? _phoneController.text.trim()
            : null,
      );

      final interviewId = result['interviewId']?.toString();

      if (interviewId == null || interviewId.isEmpty) {
        setState(() {
          _errorMessage =
              'Interview was created but no interview ID was returned.';
        });
        return;
      }

      final interview = Interview(
        id: interviewId,
        jobTitle: _jobTitleController.text.trim().isNotEmpty
            ? _jobTitleController.text.trim()
            : 'AI Guided Interview',
        companyName: _companyNameController.text.trim().isNotEmpty
            ? _companyNameController.text.trim()
            : 'AI Guided',
        interviewDate: DateTime.now(),
        status: InterviewStatus.inProgress,
        overallScore: null,
        userId: '',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      if (!mounted) return;

      await AIInterviewLauncher.launchFromStartData(
        context,
        interview: interview,
        startData: result,
      );
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🤖 AI Guided Interview'),
        backgroundColor: Colors.blue.shade600,
        foregroundColor: Colors.white,
      ),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header Card
              Card(
                color: Colors.blue.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            Icons.auto_awesome,
                            color: Colors.blue.shade600,
                            size: 28,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'AI Guided Interview Setup',
                                  style: Theme.of(context)
                                      .textTheme
                                      .headlineSmall
                                      ?.copyWith(
                                        color: Colors.blue.shade800,
                                        fontWeight: FontWeight.bold,
                                      ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Let AI guide you through a personalized interview experience',
                                  style: TextStyle(color: Colors.blue.shade600),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Workflow Configuration (Auto-configured)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blue.shade200),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.settings_applications,
                      color: Colors.blue.shade700,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'AI Workflow Configured',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: Colors.blue.shade700,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Using universal workflow: ${AIWorkflowConfig.getDisplayWorkflowId()}',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.blue.shade600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Icon(Icons.check_circle, color: Colors.green.shade600),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Candidate Information
              Text(
                'Candidate Information (Optional)',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),

              TextFormField(
                controller: _candidateNameController,
                decoration: const InputDecoration(
                  labelText: 'Candidate Name',
                  hintText: 'Alex Johnson',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.person),
                ),
              ),

              const SizedBox(height: 16),

              TextFormField(
                controller: _jobTitleController,
                decoration: const InputDecoration(
                  labelText: 'Target Job Title',
                  hintText: 'Full Stack Developer',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.work),
                ),
              ),

              const SizedBox(height: 16),

              TextFormField(
                controller: _companyNameController,
                decoration: const InputDecoration(
                  labelText: 'Company Name',
                  hintText: 'TechCorp Inc',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.business),
                ),
              ),

              const SizedBox(height: 24),

              // Interview Settings
              Text(
                'Interview Settings',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),

              // Interview Type Dropdown
              DropdownButtonFormField<String>(
                value: _interviewType,
                decoration: const InputDecoration(
                  labelText: 'Interview Type',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.quiz),
                ),
                items: _interviewTypes.map((type) {
                  return DropdownMenuItem(
                    value: type,
                    child: Text(type.replaceAll('_', ' ').toUpperCase()),
                  );
                }).toList(),
                onChanged: (value) {
                  setState(() {
                    _interviewType = value!;
                  });
                },
              ),

              const SizedBox(height: 16),

              // Experience Level Dropdown
              DropdownButtonFormField<String>(
                value: _experienceLevel,
                decoration: const InputDecoration(
                  labelText: 'Experience Level',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.trending_up),
                ),
                items: _experienceLevels.map((level) {
                  return DropdownMenuItem(
                    value: level,
                    child: Text(level.toUpperCase()),
                  );
                }).toList(),
                onChanged: (value) {
                  setState(() {
                    _experienceLevel = value!;
                  });
                },
              ),

              const SizedBox(height: 24),

              // Phone Call Option
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.phone, color: Colors.green.shade600),
                          const SizedBox(width: 12),
                          Text(
                            'Phone Call Option',
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      SwitchListTile(
                        title: const Text('Use Phone Call'),
                        subtitle: const Text(
                          'Enable phone-based interview instead of web',
                        ),
                        value: _usePhone,
                        onChanged: (value) {
                          setState(() {
                            _usePhone = value;
                          });
                        },
                      ),
                      if (_usePhone) ...[
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _phoneController,
                          decoration: const InputDecoration(
                            labelText: 'Phone Number',
                            hintText: '+1234567890',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.phone),
                          ),
                          validator: _usePhone
                              ? (value) {
                                  if (value == null || value.trim().isEmpty) {
                                    return 'Phone number is required when phone call is enabled';
                                  }
                                  return null;
                                }
                              : null,
                        ),
                      ],
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 32),

              // Start Interview Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _loading ? null : _startAIGuidedInterview,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue.shade600,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _loading
                      ? const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2,
                              ),
                            ),
                            SizedBox(width: 12),
                            Text('Creating AI Guided Interview...'),
                          ],
                        )
                      : const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.rocket_launch),
                            SizedBox(width: 8),
                            Text('Start AI Guided Interview'),
                          ],
                        ),
                ),
              ),

              const SizedBox(height: 24),

              // Error Message
              if (_errorMessage != null)
                Card(
                  color: Colors.red.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      children: [
                        Icon(Icons.error, color: Colors.red.shade600),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Error',
                                style: TextStyle(
                                  color: Colors.red.shade800,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                _errorMessage!,
                                style: TextStyle(color: Colors.red.shade700),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
