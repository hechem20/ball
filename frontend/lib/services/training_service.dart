import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/training.dart';
import '../models/auth_models.dart';
import 'auth_service.dart';

class TrainingService {
  //static const String baseUrl = 'http://10.0.2.2:5000/api/training';
   static const String baseUrl = 'http://localhost:5000/api/training';
  
  final AuthService _authService = AuthService();

  /// Récupère les headers avec le token d'authentification
  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getAccessToken();
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  /// Analyser un entraînement avec vidéo
  Future<Map<String, dynamic>> analyzeTraining({
    required TrainingType type,
    required Uint8List videoBytes,
    required String fileName,
  }) async {
    try {
      final headers = await _getHeaders();
      
      // Créer un multipart request pour envoyer la vidéo
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/analyze'),
      );
      
      request.headers.addAll(headers);
      request.fields['type'] = type.name;
      request.files.add(
        http.MultipartFile.fromBytes(
          'video',
          videoBytes,
          filename: fileName,
        ),
      );
      
      print('📤 Envoi de la vidéo: $fileName (${videoBytes.length} bytes)');
      
      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 60),
        onTimeout: () {
          throw Exception('⏰ Timeout - L\'upload est trop long');
        },
      );
      
      final response = await http.Response.fromStream(streamedResponse);

      print('📥 Réponse analyse: ${response.statusCode}');
      print('📥 Body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        // ✅ Gérer les deux formats de réponse possibles
        // Format 1: { "status": "done", "result": { ... } }
        // Format 2: { "success": true, "analysis": { ... } }
        
        if (data['status'] == 'done' && data['result'] != null) {
          // Format 1
          return data['result'];
        } else if (data['success'] == true && data['analysis'] != null) {
          // Format 2
          return data['analysis'];
        } else {
          // Si la réponse contient directement les données
          return data;
        }
      } else {
        throw Exception('Erreur ${response.statusCode}: ${response.body}');
      }
    } on http.ClientException catch (e) {
      print('❌ Erreur de connexion: $e');
      throw Exception('Impossible de contacter le serveur. Vérifiez votre connexion.');
    } catch (e) {
      print('❌ Erreur analyzeTraining: $e');
      throw Exception(e.toString());
    }
  }

  
Future<Map<String, dynamic>> saveSession({
  required TrainingType type,
  required double score,
  required double duration,
  required SkillLevel level,
  required String playerId,
  String? videoUrl,
  Map<String, dynamic>? metrics,
  String? feedback,
}) async {
  try {
    final headers = await _getHeaders();

    final body = {
      'type': type.name,
      'score': score,
      'duration': duration,
      'level': level.name,
      'player_id': playerId,
      'video_url': videoUrl,
      'metrics': metrics ?? {},
      'feedback': feedback ?? '',
    };

    final response = await http.post(
      Uri.parse('$baseUrl/session'),
      headers: headers,
      body: json.encode(body),
    );

    print('📥 Réponse sauvegarde: ${response.statusCode}');
    print(response.body);


    if (response.statusCode == 201 || response.statusCode == 200) {

      final data = json.decode(response.body);

      return {
        'success': true,
        'reward': data['reward'] ?? 0.0,
        'newBalance': data['new_balance'] ?? 0.0,
        'session': data['session'] ?? {},
        'message': data['message'] ?? 'Session enregistrée',
      };

    } else {

      throw Exception(
        'Erreur HTTP ${response.statusCode}: ${response.body}',
      );

    }

  } catch (e) {

    print('❌ Erreur saveSession: $e');

    throw Exception(
      'Erreur lors de la sauvegarde: $e',
    );

  }
}



  Future<List<TrainingSession>> getPlayerSessions({
  String? playerId,
  TrainingType? type,
}) async {
  try {

    final headers = await _getHeaders();

    String url = '$baseUrl/sessions';

    if (type != null) {
      url += '?type=${type.name}';
    }

    print("📤 GET $url");
    print("🔑 Headers: $headers");


    final response = await http.get(
      Uri.parse(url),
      headers: headers,
    ).timeout(
      const Duration(seconds: 10),
    );


    print("📥 Status: ${response.statusCode}");
    print("📥 Body: ${response.body}");


    if (response.statusCode == 200) {

      final data = json.decode(response.body);


      final List sessionsJson = data['sessions'] ?? [];


      return sessionsJson
          .map((json) => TrainingSession.fromJson(json))
          .toList();

    } else {

      throw Exception(
        "Erreur serveur ${response.statusCode}: ${response.body}"
      );

    }

  } catch(e){

    print("❌ Erreur getPlayerSessions: $e");

    return [];

  }
}
  /// Récupérer la dernière session d'entraînement
  Future<TrainingSession?> getLastSession({
    String? playerId,
    TrainingType? type,
  }) async {
    try {
      final sessions = await getPlayerSessions(
        playerId: playerId,
        type: type,
      );
      if (sessions.isNotEmpty) {
        return sessions.first;
      }
      return null;
    } catch (e) {
      print('❌ Erreur getLastSession: $e');
      return null;
    }
  }

  /// Récupérer l'ID de l'utilisateur connecté
  Future<String?> _getCurrentUserId() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userData = prefs.getString('user_data');
      if (userData != null) {
        final user = User.fromJson(json.decode(userData));
        return user.id;
      }
      return null;
    } catch (e) {
      print('❌ Erreur _getCurrentUserId: $e');
      return null;
    }
  }

  /// Récupérer les statistiques d'entraînement
  Future<Map<String, dynamic>> getTrainingStats({String? playerId}) async {
    try {
      final headers = await _getHeaders();
      
      String finalPlayerId = playerId ?? await _getCurrentUserId() ?? '';
      
      String url = '$baseUrl/stats';
      if (finalPlayerId.isNotEmpty) {
        url += '?player_id=$finalPlayerId';
      }
      
      final response = await http.get(
        Uri.parse(url),
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
          return data['stats'] ?? {};
        } else {
          throw Exception(data['error'] ?? 'Erreur lors du chargement');
        }
      } else {
        throw Exception('Erreur ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('❌ Erreur getTrainingStats: $e');
      return {};
    }
  }

  /// Récupérer les statistiques par type d'entraînement
  Future<Map<TrainingType, Map<String, dynamic>>> getStatsByType() async {
    try {
      final stats = await getTrainingStats();
      final result = <TrainingType, Map<String, dynamic>>{};
      
      for (var type in TrainingType.values) {
        final typeName = type.name;
        if (stats[typeName] != null) {
          result[type] = Map<String, dynamic>.from(stats[typeName]);
        } else {
          result[type] = {
            'count': 0,
            'average_score': 0.0,
            'best_score': 0.0,
            'total_rewards': 0.0,
          };
        }
      }
      
      return result;
    } catch (e) {
      print('❌ Erreur getStatsByType: $e');
      return {};
    }
  }

  /// Analyser la progression du joueur
  Future<Map<String, dynamic>> analyzeProgress({String? playerId}) async {
    try {
      final sessions = await getPlayerSessions(playerId: playerId);
      
      if (sessions.isEmpty) {
        return {
          'message': 'Aucune session trouvée',
          'progress': 0.0,
          'trend': 'stable',
          'total_sessions': 0,
          'average_score': 0.0,
          'best_score': 0.0,
          'total_rewards': 0.0,
        };
      }
      
      // Trier par date
      final sorted = sessions.toList()..sort((a, b) => a.date.compareTo(b.date));
      
      // Calculer la progression
      final firstScore = sorted.first.score;
      final lastScore = sorted.last.score;
      final progress = ((lastScore - firstScore) / (firstScore + 0.01)) * 100;
      
      // Déterminer la tendance
      String trend;
      if (progress > 10) {
        trend = 'up';
      } else if (progress < -10) {
        trend = 'down';
      } else {
        trend = 'stable';
      }
      
      double totalScore = 0.0;
      double totalRewards = 0.0;
      double bestScore = 0.0;
      
      for (var session in sessions) {
        totalScore += session.score;
        totalRewards += session.reward;
        if (session.score > bestScore) {
          bestScore = session.score;
        }
      }
      
      return {
        'total_sessions': sessions.length,
        'progress': progress,
        'trend': trend,
        'first_score': firstScore,
        'last_score': lastScore,
        'average_score': totalScore / sessions.length,
        'best_score': bestScore,
        'total_rewards': totalRewards,
      };
    } catch (e) {
      print('❌ Erreur analyzeProgress: $e');
      return {
        'message': 'Erreur lors de l\'analyse',
        'progress': 0.0,
        'trend': 'stable',
      };
    }
  }

  /// Supprimer une session d'entraînement
  Future<bool> deleteSession(String sessionId) async {
    try {
      final headers = await _getHeaders();
      
      final response = await http.delete(
        Uri.parse('$baseUrl/session/$sessionId'),
        headers: headers,
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          throw Exception('⏰ Timeout - Le serveur ne répond pas');
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['success'] == true;
      } else {
        throw Exception('Erreur ${response.statusCode}');
      }
    } catch (e) {
      print('❌ Erreur deleteSession: $e');
      return false;
    }
  }
}