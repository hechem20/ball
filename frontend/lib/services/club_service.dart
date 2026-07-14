import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/coach_club.dart';
import '../models/player_stats.dart';
import 'auth_service.dart';
import '../models/training.dart'; 

class ClubService {
  static const String baseUrl = 'http://localhost:5000/api/clubs';
  final AuthService _authService = AuthService();

  // Headers avec token d'authentification
  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getAccessToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  // Récupérer tous les clubs disponibles
  Future<List<CoachClub>> getAvailableClubs() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/available'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final clubsList = data['clubs'] as List;
        return clubsList.map((json) => CoachClub.fromJson(json)).toList();
      } else {
        throw Exception('Erreur lors du chargement des clubs');
      }
    } catch (e) {
      print('❌ Erreur getAvailableClubs: $e');
      return [];
    }
  }

  // Récupérer le club du coach connecté
  Future<CoachClub?> getMyClub() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/my-club'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return CoachClub.fromJson(data);
      } else if (response.statusCode == 404) {
        return null;
      } else {
        throw Exception('Erreur lors du chargement du club');
      }
    } catch (e) {
      print('❌ Erreur getMyClub: $e');
      return null;
    }
  }

  // Récupérer un club par son ID
  Future<CoachClub?> getClubById(String clubId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/$clubId'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return CoachClub.fromJson(data);
      } else {
        return null;
      }
    } catch (e) {
      print('❌ Erreur getClubById: $e');
      return null;
    }
  }

  // Récupérer le club par l'ID du coach
  Future<CoachClub?> getClubByCoachId(String coachId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/coach/$coachId'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return CoachClub.fromJson(data);
      } else {
        return null;
      }
    } catch (e) {
      print('❌ Erreur getClubByCoachId: $e');
      return null;
    }
  }

  // Récupérer le club d'un coach (méthode alternative)
  Future<CoachClub?> getCoachClub(String coachId) async {
    return getClubByCoachId(coachId);
  }

  // Créer un nouveau club
  Future<CoachClub?> createClub(Map<String, dynamic> clubData) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse(baseUrl),
        headers: headers,
        body: json.encode(clubData),
      );

      if (response.statusCode == 201) {
        final data = json.decode(response.body);
        return CoachClub.fromJson(data['club']);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['error'] ?? 'Erreur lors de la création du club');
      }
    } catch (e) {
      print('❌ Erreur createClub: $e');
      return null;
    }
  }

  // Mettre à jour le budget
  Future<bool> updateBudget(String clubId, double newBudget) async {
    try {
      final headers = await _getHeaders();
      final response = await http.put(
        Uri.parse('$baseUrl/$clubId/budget'),
        headers: headers,
        body: json.encode({'budget': newBudget}),
      );

      if (response.statusCode == 200) {
        return true;
      } else {
        final error = json.decode(response.body);
        throw Exception(error['error'] ?? 'Erreur lors de la mise à jour du budget');
      }
    } catch (e) {
      print('❌ Erreur updateBudget: $e');
      return false;
    }
  }

  // Mettre à jour les frais d'abonnement
  Future<bool> updateSubscriptionFee(String clubId, double newFee) async {
    try {
      final headers = await _getHeaders();
      final response = await http.put(
        Uri.parse('$baseUrl/$clubId/subscription-fee'),
        headers: headers,
        body: json.encode({'subscription_fee': newFee}),
      );

      if (response.statusCode == 200) {
        return true;
      } else {
        final error = json.decode(response.body);
        throw Exception(error['error'] ?? 'Erreur lors de la mise à jour des frais');
      }
    } catch (e) {
      print('❌ Erreur updateSubscriptionFee: $e');
      return false;
    }
  }

  // Mettre à jour les informations du club
  Future<CoachClub?> updateClub(String clubId, Map<String, dynamic> updates) async {
    try {
      final headers = await _getHeaders();
      final response = await http.put(
        Uri.parse('$baseUrl/$clubId'),
        headers: headers,
        body: json.encode(updates),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return CoachClub.fromJson(data['club']);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['error'] ?? 'Erreur lors de la mise à jour');
      }
    } catch (e) {
      print('❌ Erreur updateClub: $e');
      return null;
    }
  }

  // Ajouter un joueur au club
  Future<bool> addPlayerToClub(String clubId, String playerId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/$clubId/add-player/$playerId'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return true;
      } else {
        final error = json.decode(response.body);
        throw Exception(error['error'] ?? 'Erreur lors de l\'ajout du joueur');
      }
    } catch (e) {
      print('❌ Erreur addPlayerToClub: $e');
      return false;
    }
  }

  // Retirer un joueur du club
  Future<bool> removePlayerFromClub(String clubId, String playerId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.delete(
        Uri.parse('$baseUrl/$clubId/remove-player/$playerId'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return true;
      } else {
        final error = json.decode(response.body);
        throw Exception(error['error'] ?? 'Erreur lors du retrait du joueur');
      }
    } catch (e) {
      print('❌ Erreur removePlayerFromClub: $e');
      return false;
    }
  }

  // Activer/Désactiver le club
  Future<bool> toggleClubActive(String clubId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.put(
        Uri.parse('$baseUrl/$clubId/toggle-active'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return true;
      } else {
        final error = json.decode(response.body);
        throw Exception(error['error'] ?? 'Erreur lors du changement de statut');
      }
    } catch (e) {
      print('❌ Erreur toggleClubActive: $e');
      return false;
    }
  }

  // Récupérer tous les clubs (pour admin)
  Future<List<CoachClub>> getAllClubs() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse(baseUrl),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final clubsList = data['clubs'] as List;
        return clubsList.map((json) => CoachClub.fromJson(json)).toList();
      } else {
        throw Exception('Erreur lors du chargement des clubs');
      }
    } catch (e) {
      print('❌ Erreur getAllClubs: $e');
      return [];
    }
  }

  // Récupérer les joueurs d'un club
  /// Récupérer les joueurs d'un club - RETOURNE UNE LISTE DE PLAYERSTATS
/// Récupérer les joueurs d'un club
Future<List<PlayerStats>> getClubPlayers(String clubId) async {
  try {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/$clubId/players'),
      headers: headers,
    ).timeout(
      const Duration(seconds: 10),
      onTimeout: () {
        throw Exception('⏰ Timeout - Le serveur ne répond pas');
      },
    );

    print('📥 getClubPlayers status: ${response.statusCode}');
    print('📥 getClubPlayers body: ${response.body}');

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      
      if (data['success'] == true) {
        final playersList = data['players'] as List? ?? [];
        
        return playersList.map((json) {
          try {
            return PlayerStats(
              playerId: json['id']?.toString() ?? '',
              playerName: json['full_name']?.toString() ?? 'Inconnu',
              email: json['email']?.toString() ?? '',
              phone: json['phone']?.toString() ?? '',
              joinedDate: json['joined_date'] != null 
                  ? DateTime.parse(json['joined_date']) 
                  : DateTime.now(),
              speedScore: (json['speed_score'] ?? 0.0).toDouble(),
              controlBallScore: (json['control_ball_score'] ?? 0.0).toDouble(),
              shootScore: (json['shoot_score'] ?? 0.0).toDouble(),
              passScore: (json['pass_score'] ?? 0.0).toDouble(),
              totalScore: (json['total_score'] ?? 0.0).toDouble(),
              totalRewards: (json['total_rewards'] ?? 0.0).toDouble(),
              trainingSessionsCount: json['training_sessions_count'] ?? 0,
              bestScores: {},
              sessionsCount: {},
              overallLevel: _parseSkillLevel(json['overall_level']?.toString() ?? 'beginner'),
              progressRate: (json['progress_rate'] ?? 0.0).toDouble(),
            );
          } catch (e) {
            print('⚠️ Erreur conversion joueur: $e');
            return null;
          }
        }).whereType<PlayerStats>().toList();
        
      } else {
        print('⚠️ Erreur API: ${data['error'] ?? 'Erreur inconnue'}');
        return [];
      }
    } else {
      print('❌ Erreur HTTP: ${response.statusCode}');
      return [];
    }
  } on http.ClientException catch (e) {
    print('❌ Erreur de connexion: $e');
    return [];
  } catch (e) {
    print('❌ Erreur getClubPlayers: $e');
    return [];
  }
}

/// Parser le niveau
SkillLevel _parseSkillLevel(String value) {
  switch (value.toLowerCase()) {
    case 'expert':
      return SkillLevel.expert;
    case 'advanced':
      return SkillLevel.advanced;
    case 'intermediate':
      return SkillLevel.intermediate;
    default:
      return SkillLevel.beginner;
  }
}
  // Récupérer le classement du club
  Future<List<Map<String, dynamic>>> getLeaderboard(String clubId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/$clubId/leaderboard'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return List<Map<String, dynamic>>.from(data['leaderboard']);
      } else {
        throw Exception('Erreur lors du chargement du classement');
      }
    } catch (e) {
      print('❌ Erreur getLeaderboard: $e');
      return [];
    }
  }

  // Ajouter un coach (méthode utilitaire)
  Future<Map<String, dynamic>> addCoach(Map<String, dynamic> coachData) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/coaches'),
        headers: headers,
        body: json.encode(coachData),
      );

      if (response.statusCode == 201) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['error'] ?? 'Erreur lors de l\'ajout du coach');
      }
    } catch (e) {
      print('❌ Erreur addCoach: $e');
      return {};
    }
  }

  // Supprimer un club (admin seulement)
  Future<bool> deleteClub(String clubId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.delete(
        Uri.parse('$baseUrl/$clubId'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return true;
      } else {
        final error = json.decode(response.body);
        throw Exception(error['error'] ?? 'Erreur lors de la suppression');
      }
    } catch (e) {
      print('❌ Erreur deleteClub: $e');
      return false;
    }
  }
}