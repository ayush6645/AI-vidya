import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../services/api_service.dart';

class StartPlanScreen extends StatefulWidget {
  const StartPlanScreen({super.key});

  @override
  State<StartPlanScreen> createState() => _StartPlanScreenState();
}

class _StartPlanScreenState extends State<StartPlanScreen> {
  final TextEditingController _topicController = TextEditingController();
  String _difficulty = 'Beginner';
  String _duration = '1 week';
  bool _isLoading = false;

  final List<String> _difficulties = [
    'Beginner', 
    'Beginner to Intermediate', 
    'Intermediate', 
    'Intermediate to Advanced', 
    'Advanced'
  ];
  
  final List<String> _durations = [
    '1 week', '2 weeks', '4 weeks', '8 weeks'
  ];

  Future<void> _generatePlan() async {
    if (_topicController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please enter a topic')));
      return;
    }

    setState(() => _isLoading = true);

    final result = await ApiService.generatePlan({
      'topic': _topicController.text,
      'difficulty': _difficulty,
      'duration': _duration, // You might need to parse this to days/hours depending on backend expectation
    });

    setState(() => _isLoading = false);

    if (!mounted) return;

    if (result['success']) {
      // Navigate to Course Details or Plan View
      // For now, just show success and go back to dashboard
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Plan Generated Successfully!')));
      Navigator.pop(context); 
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message']), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Create New Plan', style: TextStyle(color: Colors.white)),
        backgroundColor: AppColors.backgroundMain,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'What do you want to master?',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _topicController,
              maxLines: 2,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(
                hintText: 'e.g., Quantum Computing with Python',
                hintStyle: TextStyle(color: AppColors.textSecondary),
              ),
            ),
            const SizedBox(height: 30),

            const Text(
              'Choose your starting level',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: _difficulties.map((level) {
                final isSelected = _difficulty == level;
                return ChoiceChip(
                  label: Text(level),
                  selected: isSelected,
                  selectedColor: AppColors.primaryBlue,
                  labelStyle: TextStyle(color: isSelected ? Colors.white : AppColors.textSecondary),
                  backgroundColor: AppColors.inputBg,
                  onSelected: (selected) => setState(() => _difficulty = level),
                );
              }).toList(),
            ),
            const SizedBox(height: 30),
            
            const Text(
              'Duration',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 10),
             Wrap(
              spacing: 10,
              runSpacing: 10,
              children: _durations.map((d) {
                final isSelected = _duration == d;
                return ChoiceChip(
                  label: Text(d),
                  selected: isSelected,
                  selectedColor: AppColors.primaryBlue,
                  labelStyle: TextStyle(color: isSelected ? Colors.white : AppColors.textSecondary),
                  backgroundColor: AppColors.inputBg,
                  onSelected: (selected) => setState(() => _duration = d),
                );
              }).toList(),
            ),

            const SizedBox(height: 40),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _generatePlan,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  backgroundColor: AppColors.primaryBlue,
                ),
                child: _isLoading 
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text('Generate AI Plan', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
