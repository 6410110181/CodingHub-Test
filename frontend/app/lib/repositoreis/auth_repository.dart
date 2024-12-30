import 'package:app/service/dio_client.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';

class AuthRepository {
  final DioClient _dioClient = DioClient();
  final FlutterSecureStorage _storage = FlutterSecureStorage();

  Future<void> login(String username, String password) async {
    try {
      // Setting content-type to application/x-www-form-urlencoded
      final response = await _dioClient.dio.post(
        '/token',
        data: {
          'username': username,
          'password': password,
        },
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
        ),
      );

      if (response.statusCode == 200) {
        String accessToken = response.data['access_token'];
        String refreshToken = response.data['refresh_token'];

        // Store tokens securely
        await _storage.write(key: 'token', value: accessToken);
        await _storage.write(key: 'refresh_token', value: refreshToken);
      }
    } catch (e) {
        throw Exception('Login failed: $e');
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: 'token');
    await _storage.delete(key: 'refresh_token');
  }
}
