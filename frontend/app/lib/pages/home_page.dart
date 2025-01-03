import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_fonts/google_fonts.dart';

class HomePage extends StatelessWidget {
  HomePage({super.key});

  // Initialize FlutterSecureStorage
  final FlutterSecureStorage _storage = FlutterSecureStorage();

  // Logout function to clear tokens
  Future<void> _logout(BuildContext context) async {
    // Delete the stored tokens
    await _storage.delete(key: 'token');
    await _storage.delete(key: 'refresh_token');

    // Navigate to login page after logout (you can replace with your own login page)
    Navigator.pushReplacementNamed(context, '/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Home Page'),
      ),
      body: Center(
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 10),
            backgroundColor: Color.fromARGB(255, 52, 76, 214),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          onPressed: () => _logout(context),
          child: Text(
            'Logout'.toUpperCase(),
            style: GoogleFonts.dosis(
              fontWeight: FontWeight.bold,
              fontSize: 15,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}
