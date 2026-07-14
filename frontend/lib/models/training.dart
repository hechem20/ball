import 'package:flutter/material.dart';

enum TrainingType {
  speed,
  control_ball,
  shoot,
  pass,
}

enum SkillLevel {
  beginner,
  intermediate,
  advanced,
  expert,
}

class TrainingSession {
  final String id;
  final String playerId;
  final TrainingType type;
  final DateTime date;
  final double score;
  final double duration;
  final SkillLevel level;
  final double reward;
  final String? videoUrl;
  final String? aiFeedback;
  final Map<String, dynamic> metrics;

  TrainingSession({
    required this.id,
    required this.playerId,
    required this.type,
    required this.date,
    required this.score,
    required this.duration,
    required this.level,
    required this.reward,
    this.videoUrl,
    this.aiFeedback,
    this.metrics = const {},
  });

  factory TrainingSession.fromJson(Map<String, dynamic> json) {
    // ✅ Gérer les valeurs null avec des valeurs par défaut
    return TrainingSession(
      id: json['id']?.toString() ?? 'unknown_${DateTime.now().millisecondsSinceEpoch}',
      playerId: json['player_id']?.toString() ?? json['playerId']?.toString() ?? 'unknown',
      type: _parseTrainingType(json['type']?.toString() ?? 'speed'),
      date: _parseDateTime(json['date'] ?? json['created_at']),
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      duration: (json['duration'] as num?)?.toDouble() ?? 0.0,
      level: _parseSkillLevel(json['level']?.toString() ?? 'beginner'),
      reward: (json['reward'] as num?)?.toDouble() ?? 0.0,
      videoUrl: json['video_url']?.toString() ?? json['videoUrl']?.toString(),
      aiFeedback: json['ai_feedback']?.toString() ?? json['feedback']?.toString(),
      metrics: json['metrics'] as Map<String, dynamic>? ?? {},
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'player_id': playerId,
      'type': type.name,
      'date': date.toIso8601String(),
      'score': score,
      'duration': duration,
      'level': level.name,
      'reward': reward,
      'video_url': videoUrl,
      'ai_feedback': aiFeedback,
      'metrics': metrics,
    };
  }

  static TrainingType _parseTrainingType(String value) {
    try {
      return TrainingType.values.firstWhere(
        (e) => e.name == value.toLowerCase(),
        orElse: () => TrainingType.speed,
      );
    } catch (e) {
      return TrainingType.speed;
    }
  }

  static SkillLevel _parseSkillLevel(String value) {
    try {
      return SkillLevel.values.firstWhere(
        (e) => e.name == value.toLowerCase(),
        orElse: () => SkillLevel.beginner,
      );
    } catch (e) {
      return SkillLevel.beginner;
    }
  }

  static DateTime _parseDateTime(dynamic value) {
    if (value == null) return DateTime.now();
    if (value is DateTime) return value;
    if (value is String) {
      try {
        return DateTime.parse(value);
      } catch (e) {
        return DateTime.now();
      }
    }
    return DateTime.now();
  }
}