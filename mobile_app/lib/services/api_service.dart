import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // Production Google Cloud Run URL
  static const String baseUrl = 'https://ai-vidya-990444310222.asia-south1.run.app'; 

  static Future<Map<String, dynamic>> login({
    required String loginType, // loginUsername, loginEmail, loginPhone
    required String loginValue,
    required String authType, // authPassword, authOTP
    required String authValue,
  }) async {
    final url = Uri.parse('$baseUrl/login');
    
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'loginType': loginType,
          'login_value': loginValue,
          'authType': authType,
          'auth_value': authValue,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        // Save token
        final token = data['access_token'];
        if (token != null) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('access_token', token);
          
          // Save user info if available
          if (data['user'] != null) {
             await prefs.setString('user_data', jsonEncode(data['user']));
          }
        }
        return {'success': true, 'data': data};
      } else {
        return {'success': false, 'message': data['detail'] ?? 'Login failed'};
      }
    } catch (e) {
      return {'success': false, 'message': 'Network error: $e'};
    }
  }

  static Future<Map<String, dynamic>> register(Map<String, dynamic> userData) async {
    final url = Uri.parse('$baseUrl/register');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(userData),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        return {'success': true, 'message': data['message'] ?? 'Registration successful'};
      } else {
        return {'success': false, 'message': data['detail'] ?? 'Registration failed'};
      }
    } catch (e) {
      return {'success': false, 'message': 'Network error: $e'};
    }
  }

  static Future<Map<String, dynamic>> generatePlan(Map<String, dynamic> planData) async {
    final url = Uri.parse('$baseUrl/api/v1/plans/generate'); // Assuming this endpoint path
    final token = await getToken();

    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(planData),
      );

      // Handle long-running generation (timeout?) 
      // For now basic implementation
      if (response.statusCode == 200) {
        return {'success': true, 'data': jsonDecode(response.body)};
      } else {
        final data = jsonDecode(response.body);
        return {'success': false, 'message': data['detail'] ?? 'Plan generation failed'};
      }
    } catch (e) {
      return {'success': false, 'message': 'Error: $e'};
    }
  }
  
  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('user_data');
  }
  
  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }
}
