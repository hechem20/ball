import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/auth_models.dart';
import 'auth_service.dart';

class PaymentService {
  static const String baseUrl = 'http://localhost:5000/api/payments';
  final AuthService _authService = AuthService();

  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getAccessToken();
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  /// Traiter un paiement
  Future<Map<String, dynamic>> processPayment({
    required String playerId,
    required String coachId,
    required String clubId,
    required double amount,
    String? description,
  }) async {
    try {
      final headers = await _getHeaders();
      
      final body = {
        'player_id': playerId,  // ✅ Ajout de player_id
        'coach_id': coachId,
        'club_id': clubId,
        'amount': amount,
        'description': description ?? 'Abonnement au club',
      };
      
      print('📤 Traitement paiement: ${json.encode(body)}');
      
      final response = await http.post(
        Uri.parse('$baseUrl/process'),
        headers: headers,
        body: json.encode(body),
      ).timeout(
        const Duration(seconds: 30),
        onTimeout: () {
          throw Exception('⏰ Timeout - Le serveur ne répond pas');
        },
      );

      print('📥 Réponse paiement: ${response.statusCode}');
      print('📥 Body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          return data;
        } else {
          throw Exception(data['error'] ?? 'Erreur lors du paiement');
        }
      } else {
        throw Exception('Erreur ${response.statusCode}: ${response.body}');
      }
    } on http.ClientException catch (e) {
      print('❌ Erreur de connexion: $e');
      throw Exception('Impossible de contacter le serveur. Vérifiez votre connexion.');
    } catch (e) {
      print('❌ Erreur processPayment: $e');
      throw Exception(e.toString());
    }
  }

  /// Récupérer les transactions d'un utilisateur
  Future<List<Map<String, dynamic>>> getTransactions() async {
    try {
      final headers = await _getHeaders();
      
      final response = await http.get(
        Uri.parse('$baseUrl/transactions'),
        headers: headers,
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          throw Exception('⏰ Timeout - Le serveur ne répond pas');
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          return List<Map<String, dynamic>>.from(data['transactions'] ?? []);
        } else {
          throw Exception(data['error'] ?? 'Erreur');
        }
      } else {
        throw Exception('Erreur ${response.statusCode}');
      }
    } catch (e) {
      print('❌ Erreur getTransactions: $e');
      return [];
    }
  }

  /// Vérifier si un joueur est dans un club
  Future<bool> isPlayerInClub(String clubId) async {
    try {
      final user = await _authService.getCurrentUser();
      if (user == null) return false;
      
      final headers = await _getHeaders();
      
      final response = await http.get(
        Uri.parse('$baseUrl/club/$clubId/players'),
        headers: headers,
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          throw Exception('⏰ Timeout - Le serveur ne répond pas');
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          final players = data['players'] as List;
          return players.any((p) => p['id'] == user.id);
        }
        return false;
      } else {
        return false;
      }
    } catch (e) {
      print('❌ Erreur isPlayerInClub: $e');
      return false;
    }
  }

  /// Récupérer la liste des joueurs d'un club
  Future<List<Map<String, dynamic>>> getClubPlayers(String clubId) async {
    try {
      final headers = await _getHeaders();
      
      final response = await http.get(
        Uri.parse('$baseUrl/club/$clubId/players'),
        headers: headers,
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          throw Exception('⏰ Timeout - Le serveur ne répond pas');
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          return List<Map<String, dynamic>>.from(data['players'] ?? []);
        } else {
          throw Exception(data['error'] ?? 'Erreur');
        }
      } else {
        throw Exception('Erreur ${response.statusCode}');
      }
    } catch (e) {
      print('❌ Erreur getClubPlayers: $e');
      return [];
    }
  }
}