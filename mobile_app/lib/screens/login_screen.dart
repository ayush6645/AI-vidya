import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  // Toggle states
  String _loginType = 'loginUsername'; // loginUsername, loginEmail, loginPhone
  String _authType = 'authPassword'; // authPassword, authOTP

  // Controllers
  final TextEditingController _userController = TextEditingController();
  final TextEditingController _passController = TextEditingController();
  
  bool _isLoading = false;

  Future<void> _handleLogin() async {
    setState(() => _isLoading = true);
    
    final result = await ApiService.login(
      loginType: _loginType,
      loginValue: _userController.text,
      authType: _authType,
      authValue: _passController.text,
    );
    
    setState(() => _isLoading = false);
    
    if (!mounted) return;
    
    if (result['success']) {
      Navigator.pushReplacementNamed(context, '/dashboard');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['message']),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    // Glassmorphism card effect simulation
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          color: AppColors.backgroundDark, // Could add particle effect background here later
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Container(
              constraints: const BoxConstraints(maxWidth: 450),
              padding: const EdgeInsets.all(40),
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
                  // Logo
                  const Text(
                    'AIvidya',
                    style: TextStyle(
                      fontSize: 40,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primaryBlue,
                    ),
                  ),
                  const SizedBox(height: 20),
                  
                  // Header
                  const Text(
                    'Welcome Back',
                    style: TextStyle(
                      fontSize: 24, // 1.8rem approx
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 5),
                  const Text(
                    'Enter your credentials to continue your journey.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 30),

                  // Login Type Toggle
                  _buildToggleSwitch(
                    values: ['loginUsername', 'loginEmail', 'loginPhone'],
                    labels: ['Username', 'Email', 'Phone'],
                    groupValue: _loginType,
                    onChanged: (val) => setState(() => _loginType = val),
                  ),
                  const SizedBox(height: 25),

                  // Login Input
                  TextField(
                    controller: _userController,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      labelText: _getLoginLabel(),
                      floatingLabelBehavior: FloatingLabelBehavior.auto,
                    ),
                  ),
                  const SizedBox(height: 25),

                  // Auth Type Toggle
                  _buildToggleSwitch(
                    values: ['authPassword', 'authOTP'],
                    labels: ['Password', 'OTP'],
                    groupValue: _authType,
                    onChanged: (val) => setState(() => _authType = val),
                  ),
                  const SizedBox(height: 25),

                  // Password/OTP Input
                  TextField(
                    controller: _passController,
                    obscureText: _authType == 'authPassword',
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      labelText: _authType == 'authPassword' ? 'Password' : 'OTP',
                    ),
                  ),
                  const SizedBox(height: 25),

                  // Submit Button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : _handleLogin,
                      child: _isLoading 
                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : const Text('Login'),
                    ),
                  ),

                  const SizedBox(height: 20),
                  
                  // Links
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      TextButton(
                        onPressed: () {},
                        child: const Text('Forgot Password?', style: TextStyle(color: AppColors.primaryBlueLight)),
                      ),
                      const Text('|', style: TextStyle(color: AppColors.textSecondary)),
                      TextButton(
                        onPressed: () {
                          // TODO: Navigate to Register
                        },
                        child: const Text('Create an Account', style: TextStyle(color: AppColors.primaryBlueLight)),
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

  String _getLoginLabel() {
    switch (_loginType) {
      case 'loginEmail': return 'Email Address';
      case 'loginPhone': return 'Phone Number';
      case 'loginUsername': default: return 'Username';
    }
  }

  Widget _buildToggleSwitch({
    required List<String> values,
    required List<String> labels,
    required String groupValue,
    required Function(String) onChanged,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.inputBg,
        borderRadius: BorderRadius.circular(30),
      ),
      padding: const EdgeInsets.all(5),
      child: Row(
        children: List.generate(values.length, (index) {
          final isSelected = groupValue == values[index];
          return Expanded(
            child: GestureDetector(
              onTap: () => onChanged(values[index]),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                padding: const EdgeInsets.symmetric(vertical: 8),
                decoration: BoxDecoration(
                  color: isSelected ? AppColors.primaryBlue : Colors.transparent,
                  borderRadius: BorderRadius.circular(30),
                  boxShadow: isSelected
                      ? [const BoxShadow(color: AppColors.glowColor, blurRadius: 10)]
                      : [],
                ),
                child: Text(
                  labels[index],
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: isSelected ? Colors.white : AppColors.textSecondary,
                    fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}
