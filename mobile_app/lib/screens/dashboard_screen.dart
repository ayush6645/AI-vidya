import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_colors.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  String _userName = 'User';
  String _userInitial = 'U';

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    final prefs = await SharedPreferences.getInstance();
    final userDataStr = prefs.getString('user_data');
    if (userDataStr != null) {
      final userData = jsonDecode(userDataStr);
      setState(() {
        _userName = userData['name'] ?? userData['username'] ?? 'User';
        _userInitial = _userName.isNotEmpty ? _userName[0].toUpperCase() : 'U';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: AppColors.backgroundMain,
        elevation: 0,
        title: const Text('AI-vidya', style: TextStyle(color: AppColors.primaryBlue, fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.search, color: AppColors.textSecondary),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.notifications_none, color: AppColors.textSecondary),
            onPressed: () {},
          ),
          CircleAvatar(
            backgroundColor: AppColors.primaryBlue,
            radius: 16,
            child: Text(_userInitial, style: const TextStyle(color: Colors.white)),
          ),
          const SizedBox(width: 15),
        ],
        iconTheme: const IconThemeData(color: AppColors.textSecondary),
      ),
      drawer: _buildDrawer(context),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Hero Section
            _buildHeroCard(),
            const SizedBox(height: 20),
            
            // Profile Summary
            _buildProfileCard(),
            const SizedBox(height: 20),

            // Stats Grid
            Row(
              children: [
                Expanded(child: _buildStatCard('Plans', '12', Icons.layers, Colors.purple)),
                const SizedBox(width: 10),
                Expanded(child: _buildStatCard('Topics', '34', Icons.check_circle, Colors.green)),
              ],
            ),
            const SizedBox(height: 10),
            _buildStatCard('Quiz Accuracy', '85%', Icons.ads_click, Colors.orange),

            const SizedBox(height: 20),
            
            // Actions
            const Text('Quick Actions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
            const SizedBox(height: 10),
            _buildActionCard(context, 'Start New Plan', 'Create personalized plan', Icons.play_arrow, () {}),
            _buildActionCard(context, 'Browse Courses', 'Explore library', Icons.book, () {}),
            _buildActionCard(context, 'Take Quiz', 'Test knowledge', Icons.science, () {}),
          ],
        ),
      ),
    );
  }

  Widget _buildDrawer(BuildContext context) {
    return Drawer(
      backgroundColor: AppColors.cardBg,
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          const DrawerHeader(
            decoration: BoxDecoration(color: AppColors.backgroundMain),
            child: Center(
              child: Text(
                'AI-vidya',
                style: TextStyle(color: AppColors.primaryBlue, fontSize: 24, fontWeight: FontWeight.bold),
              ),
            ),
          ),
          _buildDrawerItem(Icons.dashboard, 'Dashboard', true, () => Navigator.pop(context)),
          _buildDrawerItem(Icons.rocket_launch, 'Start Plan', false, () => Navigator.pushNamed(context, '/start_plan')),
          _buildDrawerItem(Icons.menu_book, 'My Courses', false, () {}),
          _buildDrawerItem(Icons.quiz, 'Quizzes', false, () {}),
          _buildDrawerItem(Icons.settings, 'Settings', false, () {}),
          const Divider(color: AppColors.borderColor),
          _buildDrawerItem(Icons.logout, 'Logout', false, () {
             Navigator.pushReplacementNamed(context, '/login');
          }),
        ],
      ),
    );
  }

  Widget _buildDrawerItem(IconData icon, String title, bool isActive, VoidCallback onTap) {
    return ListTile(
      leading: Icon(icon, color: isActive ? AppColors.primaryBlue : AppColors.textSecondary),
      title: Text(
        title,
        style: TextStyle(
          color: isActive ? Colors.white : AppColors.textSecondary,
          fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
        ),
      ),
      selected: isActive,
      selectedTileColor: AppColors.primaryBlue.withOpacity(0.1),
      onTap: onTap,
    );
  }

  Widget _buildHeroCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: Colors.yellow.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.star, color: Colors.yellow, size: 16),
                SizedBox(width: 5),
                Text('AI-Powered Learning', style: TextStyle(color: Colors.yellow, fontSize: 12)),
              ],
            ),
          ),
          const SizedBox(height: 15),
          RichText(
            text: const TextSpan(
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, height: 1.2),
              children: [
                TextSpan(text: 'Continue Your '),
                TextSpan(text: 'Learning Journey', style: TextStyle(color: AppColors.primaryBlue)),
              ],
            ),
          ),
          const SizedBox(height: 10),
          const Text(
            'Track your progress and achieve your goals.',
            style: TextStyle(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: () {},
                  child: const Text('Start a Plan'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton(
                  onPressed: () {},
                  child: const Text('View Progress'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildProfileCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderColor),
      ),
      child: Column(
        children: [
          CircleAvatar(radius: 30, backgroundColor: AppColors.primaryBlue, child: Text(_userInitial, style: const TextStyle(fontSize: 24, color: Colors.white))),
          const SizedBox(height: 10),
          Text('Welcome back, $_userName! 👋', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 15),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildProfileStat('1200', 'XP Points'),
              _buildProfileStat('5', 'Day Streak'),
              _buildProfileStat('L1', 'Level'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildProfileStat(String value, String label) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
        Text(label, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
      ],
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: AppColors.borderColor),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(width: 15),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
              Text(value, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionCard(BuildContext context, String title, String subtitle, IconData icon, VoidCallback onTap) {
    return Card(
      color: AppColors.cardBg,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15), side: const BorderSide(color: AppColors.borderColor)),
      child: ListTile(
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.inputBg,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: AppColors.primaryBlue),
        ),
        title: Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        subtitle: Text(subtitle, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
        trailing: const Icon(Icons.arrow_forward_ios, color: AppColors.textSecondary, size: 16),
        onTap: onTap,
      ),
    );
  }
}
