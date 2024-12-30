import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class DioClient {
  final Dio _dio = Dio();
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  DioClient() {
    _dio.options.baseUrl = 'http://10.0.2.2:8000'; // Ensure this is correct
    _dio.options.connectTimeout = const Duration(seconds: 5);
    _dio.options.receiveTimeout = const Duration(seconds: 3);

    // Add interceptor to attach the token to every request
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        String? token = await _storage.read(key: 'token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler
            .next(options);
      },
      onError: (DioError error, handler) async {
        if (error.response?.statusCode == 401) {
          // Token expired, try refreshing the token
          bool success = await _refreshToken();

          if (success) {
            // Retry the original request with the new token
            String? newToken = await _storage.read(key: 'token');
            if (newToken != null) {
              error.requestOptions.headers['Authorization'] = 'Bearer $newToken';
              final response = await _dio.request(
                error.requestOptions.path,
                options: Options(
                  method: error.requestOptions.method,
                  headers: error.requestOptions.headers,
                ),
                data: error.requestOptions.data,
                queryParameters: error.requestOptions.queryParameters,
              );
              return handler.resolve(response);
            }
          }
        }
        return handler.next(error);
      },      
    ));
  }

  Dio get dio => _dio;

  Future<bool> _refreshToken() async {
    try {
      String? refreshToken = await _storage.read(key: 'refresh_token');
      if (refreshToken == null) return false;

      final response = await _dio.post('/refresh-token', data: {
        'refresh_token': refreshToken,
      });

      if (response.statusCode == 200) {
        String newAccessToken = response.data['access_token'];
        String newRefreshToken = response.data['refresh_token'];

        // Store the new tokens
        await _storage.write(key: 'token', value: newAccessToken);
        await _storage.write(key: 'refresh_token', value: newRefreshToken);

        return true;
      }
    } catch (e) {
      print('Error refreshing token: $e');
    }
    return false;
  }
}
