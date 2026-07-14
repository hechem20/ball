import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/auth_models.dart';

class AuthService {
  static const String baseUrl = 'http://localhost:5000/api/auth';
  static const String tokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userKey = 'user_data';

  Future<AuthResponse> register(RegisterRequest request) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/register'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(request.toJson()),
      );

      final data = json.decode(response.body);
      
      if (response.statusCode == 201) {
        // Sauvegarder les données
        await _saveAuthData(data);
        return AuthResponse(
          success: true,
          accessToken: data['access_token'],
          refreshToken: data['refresh_token'],
          user: data['user'] != null ? User.fromJson(data['user']) : null,
          message: data['message'],
        );
      } else {
        return AuthResponse(
          success: false,
          message: data['error'] ?? 'Erreur lors de l\'inscription',
        );
      }
    } catch (e) {
      return AuthResponse(
        success: false,
        message: 'Erreur de connexion au serveur',
      );
    }
  }
/// Récupérer l'ID de l'utilisateur connecté
Future<String?> getCurrentUserId() async {
  try {
    final prefs = await SharedPreferences.getInstance();
    final userData = prefs.getString(userKey);
    if (userData != null) {
      final user = User.fromJson(json.decode(userData));
      return user.id;
    }
    return null;
  } catch (e) {
    print('❌ Erreur getCurrentUserId: $e');
    return null;
  }
}
  Future<AuthResponse> login(LoginRequest request) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/login'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(request.toJson()),
      );

      final data = json.decode(response.body);
      
      if (response.statusCode == 200) {
        await _saveAuthData(data);
        return AuthResponse(
          success: true,
          accessToken: data['access_token'],
          refreshToken: data['refresh_token'],
          user: data['user'] != null ? User.fromJson(data['user']) : null,
          message: data['message'],
        );
      } else {
        return AuthResponse(
          success: false,
          message: data['error'] ?? 'Email ou mot de passe incorrect',
        );
      }
    } catch (e) {
      return AuthResponse(
        success: false,
        message: 'Erreur de connexion au serveur',
      );
    }
  }

  Future<void> _saveAuthData(Map<String, dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();
    if (data['access_token'] != null) {
      await prefs.setString(tokenKey, data['access_token']);
    }
    if (data['refresh_token'] != null) {
      await prefs.setString(refreshTokenKey, data['refresh_token']);
    }
    if (data['user'] != null) {
      await prefs.setString(userKey, json.encode(data['user']));
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(tokenKey);
    await prefs.remove(refreshTokenKey);
    await prefs.remove(userKey);
  }

  Future<User?> getCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userData = prefs.getString(userKey);
    if (userData != null) {
      return User.fromJson(json.decode(userData));
    }
    return null;
  }

  Future<String?> getAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(tokenKey);
  }

  Future<bool> isAuthenticated() async {
    final token = await getAccessToken();
    return token != null;
  }
}