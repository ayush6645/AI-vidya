import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../services/api_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  int _currentStep = 1;

  // Controllers - Step 1
  final TextEditingController _firstName = TextEditingController();
  final TextEditingController _lastName = TextEditingController();
  final TextEditingController _dob = TextEditingController();

  // Controllers - Step 2
  final TextEditingController _email = TextEditingController();
  final TextEditingController _phone = TextEditingController();
  final TextEditingController _username = TextEditingController();
  final TextEditingController _password = TextEditingController();
  final TextEditingController _confirmPass = TextEditingController();

  // Controllers - Step 3
  String? _selectedEducation;

  final List<String> _educationOptions = [
    'SSC', 'HSC', 'Currently in Graduation', 'Graduation Completed',
    'Currently in Post-Graduation', 'PG Completed', 'PhD', 'Diploma', 'Certification Course', 'Other'
  ];

  bool _isLoading = false;

  Future<void> _handleRegister() async {
    // Basic validation
    if (_password.text != _confirmPass.text) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Passwords do not match'), backgroundColor: Colors.red));
      return;
    }

    setState(() => _isLoading = true);

    final userData = {
      'first_name': _firstName.text,
      'last_name': _lastName.text,
      'date_of_birth': _dob.text,
      'email': _email.text,
      'phone_number': _phone.text,
      'username': _username.text,
      'password': _password.text,
      'confirm_password': _confirmPass.text,
      'education': _selectedEducation,
    };

    final result = await ApiService.register(userData);

    setState(() => _isLoading = false);

    if (!mounted) return;

    if (result['success']) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message']), backgroundColor: Colors.green));
      Navigator.pop(context); // Go back to login
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message']), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          color: AppColors.backgroundDark,
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Container(
              constraints: const BoxConstraints(maxWidth: 550),
              padding: const EdgeInsets.all(30),
              decoration: BoxDecoration(
                color: AppColors.cardBg.withOpacity(0.7),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.borderColor),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.5),
                    blurRadius: 40,
                    offset: const Offset(0, 15),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Header
                  const Text(
                    'Create Your Account',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'Join AIvidya and start your personalized learning journey today.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 30),

                  // Progress Bar
                  _buildProgressBar(),
                  const SizedBox(height: 30),

                  // Form Steps
                  if (_currentStep == 1) _buildStep1(),
                  if (_currentStep == 2) _buildStep2(),
                  if (_currentStep == 3) _buildStep3(),

                  const SizedBox(height: 20),
                  
                  // Login Link
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text(
                        'Already have an account? ',
                        style: TextStyle(color: AppColors.textSecondary),
                      ),
                      TextButton(
                        onPressed: () {
                          Navigator.pop(context);
                        },
                        child: const Text('Login', style: TextStyle(color: AppColors.primaryBlueLight)),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildProgressBar() {
    return Column(
      children: [
        Stack(
          alignment: Alignment.centerLeft,
          children: [
            Container(height: 2, color: AppColors.borderColor),
            AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              height: 2,
              width: MediaQuery.of(context).size.width * 0.2 * _currentStep, // Approximate logic
              color: AppColors.primaryBlue,
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _buildStepIndicator(1, 'Personal'),
            _buildStepIndicator(2, 'Account'),
            _buildStepIndicator(3, 'Education'),
          ],
        ),
      ],
    );
  }

  Widget _buildStepIndicator(int step, String label) {
    bool isActive = step <= _currentStep;
    return Column(
      children: [
        Container(
          width: 30,
          height: 30,
          decoration: BoxDecoration(
            color: isActive ? AppColors.primaryBlue : AppColors.inputBg,
            shape: BoxShape.circle,
            border: Border.all(color: isActive ? AppColors.primaryBlue : AppColors.borderColor),
          ),
        ),
        const SizedBox(height: 5),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: isActive ? AppColors.primaryBlue : AppColors.textSecondary,
            fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ],
    );
  }

  Widget _buildStep1() {
    return Column(
      children: [
        Row(
          children: [
            Expanded(child: _buildInput(_firstName, 'First Name', Icons.person)),
            const SizedBox(width: 15),
            Expanded(child: _buildInput(_lastName, 'Last Name', Icons.person)),
          ],
        ),
        const SizedBox(height: 20),
        _buildInput(_dob, 'Date of Birth', Icons.calendar_today, isDate: true),
        const SizedBox(height: 30),
        Align(
          alignment: Alignment.centerRight,
          child: ElevatedButton.icon(
            onPressed: () => setState(() => _currentStep = 2),
            icon: const Icon(Icons.arrow_forward),
            label: const Text('Next'),
          ),
        ),
      ],
    );
  }

  Widget _buildStep2() {
    return Column(
      children: [
        Row(
          children: [
            Expanded(child: _buildInput(_email, 'Email ID', Icons.email)),
            const SizedBox(width: 15),
            Expanded(child: _buildInput(_phone, 'Phone Number', Icons.phone)),
          ],
        ),
        const SizedBox(height: 20),
        _buildInput(_username, 'Username', Icons.alternate_email),
        const SizedBox(height: 20),
        _buildInput(_password, 'Password', Icons.lock, isPassword: true),
        const SizedBox(height: 20),
        _buildInput(_confirmPass, 'Confirm Password', Icons.lock, isPassword: true),
        const SizedBox(height: 30),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            OutlinedButton(
              onPressed: () => setState(() => _currentStep = 1),
              child: const Text('Back'),
            ),
            ElevatedButton.icon(
              onPressed: () => setState(() => _currentStep = 3),
              icon: const Icon(Icons.arrow_forward),
              label: const Text('Next'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildStep3() {
    return Column(
      children: [
        DropdownButtonFormField<String>(
          value: _selectedEducation,
          dropdownColor: AppColors.inputBg,
          style: const TextStyle(color: Colors.white),
          decoration: const InputDecoration(
            labelText: 'Highest Educational Qualification',
            prefixIcon: Icon(Icons.school, color: AppColors.textSecondary),
          ),
          items: _educationOptions.map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
          onChanged: (val) => setState(() => _selectedEducation = val),
        ),
        const SizedBox(height: 30),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            OutlinedButton(
              onPressed: () => setState(() => _currentStep = 2),
              child: const Text('Back'),
            ),
            ElevatedButton(
              onPressed: _isLoading ? null : _handleRegister,
              child: _isLoading 
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) 
                : const Text('Register'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildInput(TextEditingController controller, String label, IconData icon, 
      {bool isPassword = false, bool isDate = false}) {
    return TextFormField(
      controller: controller,
      obscureText: isPassword,
      readOnly: isDate,
      style: const TextStyle(color: Colors.white),
      onTap: isDate ? () async {
        DateTime? picked = await showDatePicker(
          context: context,
          initialDate: DateTime.now(),
          firstDate: DateTime(1900),
          lastDate: DateTime.now(),
        );
        if (picked != null) {
          controller.text = "${picked.year}-${picked.month.toString().padLeft(2,'0')}-${picked.day.toString().padLeft(2,'0')}";
        }
      } : null,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: AppColors.textSecondary),
      ),
    );
  }
}
