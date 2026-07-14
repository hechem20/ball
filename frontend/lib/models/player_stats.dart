import 'training.dart';

class PlayerStats {
  final String playerId;
  final String playerName;
  final String email;
  final String phone;
  final DateTime joinedDate;
  final double speedScore;
  final double controlBallScore;
  final double shootScore;
  final double passScore;
  final double totalScore;
  final double totalRewards;
  final int trainingSessionsCount;
  final Map<TrainingType, double> bestScores;
  final Map<TrainingType, int> sessionsCount;
  final SkillLevel overallLevel;
  final double progressRate;

  PlayerStats({
    required this.playerId,
    required this.playerName,
    required this.email,
    required this.phone,
    required this.joinedDate,
    required this.speedScore,
    required this.controlBallScore,
    required this.shootScore,
    required this.passScore,
    required this.totalScore,
    required this.totalRewards,
    required this.trainingSessionsCount,
    required this.bestScores,
    required this.sessionsCount,
    required this.overallLevel,
    required this.progressRate,
  });

  factory PlayerStats.fromJson(Map<String, dynamic> json) {
    return PlayerStats(
      playerId: json['playerId'],
      playerName: json['playerName'],
      email: json['email'],
      phone: json['phone'] ?? '',
      joinedDate: DateTime.parse(json['joinedDate']),
      speedScore: json['speedScore']?.toDouble() ?? 0.0,
      controlBallScore: json['controlBallScore']?.toDouble() ?? 0.0,
      shootScore: json['shootScore']?.toDouble() ?? 0.0,
      passScore: json['passScore']?.toDouble() ?? 0.0,
      totalScore: json['totalScore']?.toDouble() ?? 0.0,
      totalRewards: json['totalRewards']?.toDouble() ?? 0.0,
      trainingSessionsCount: json['trainingSessionsCount'] ?? 0,
      bestScores: (json['bestScores'] as Map<String, dynamic>?)?.map(
        (k, v) => MapEntry(TrainingType.values.firstWhere((e) => e.name == k), v.toDouble()),
      ) ?? {},
      sessionsCount: (json['sessionsCount'] as Map<String, dynamic>?)?.map(
        (k, v) => MapEntry(TrainingType.values.firstWhere((e) => e.name == k), v as int),
      ) ?? {},
      overallLevel: SkillLevel.values.firstWhere(
        (e) => e.name == json['overallLevel'],
        orElse: () => SkillLevel.beginner,
      ),
      progressRate: json['progressRate']?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'playerId': playerId,
      'playerName': playerName,
      'email': email,
      'phone': phone,
      'joinedDate': joinedDate.toIso8601String(),
      'speedScore': speedScore,
      'controlBallScore': controlBallScore,
      'shootScore': shootScore,
      'passScore': passScore,
      'totalScore': totalScore,
      'totalRewards': totalRewards,
      'trainingSessionsCount': trainingSessionsCount,
      'bestScores': bestScores.map((k, v) => MapEntry(k.name, v)),
      'sessionsCount': sessionsCount.map((k, v) => MapEntry(k.name, v)),
      'overallLevel': overallLevel.name,
      'progressRate': progressRate,
    };
  }
}