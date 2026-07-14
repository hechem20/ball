import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../models/player_stats.dart';
import '../../models/training.dart';

class PlayerStatsDetailScreen extends StatefulWidget {
  final PlayerStats playerStats;

  const PlayerStatsDetailScreen({
    super.key,
    required this.playerStats,
  });

  @override
  State<PlayerStatsDetailScreen> createState() => _PlayerStatsDetailScreenState();
}

class _PlayerStatsDetailScreenState extends State<PlayerStatsDetailScreen> {
  @override
  Widget build(BuildContext context) {
    final player = widget.playerStats;
    
    return Scaffold(
      body: AnnotatedRegion<SystemUiOverlayStyle>(
        value: SystemUiOverlayStyle.light,
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                const Color(0xFF1A237E),
                const Color(0xFF0D47A1),
                const Color(0xFF01579B),
              ],
            ),
          ),
          child: SafeArea(
            child: Column(
              children: [
                // En-tête avec retour
                _buildHeader(),
                // Contenu
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      children: [
                        // Profil du joueur
                        _buildPlayerProfile(player),
                        const SizedBox(height: 20),
                        // Scores par compétence
                        _buildSkillsSection(player),
                        const SizedBox(height: 20),
                        // Statistiques globales
                        _buildStatsSection(player),
                        const SizedBox(height: 20),
                        // Performance par type
                        _buildPerformanceSection(player),
                        const SizedBox(height: 20),
                        // Progression
                        _buildProgressSection(player),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          IconButton(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(
              Icons.arrow_back_ios,
              color: Colors.white,
            ),
            padding: EdgeInsets.zero,
          ),
          const SizedBox(width: 8),
          const Text(
            'Détails du Joueur',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPlayerProfile(PlayerStats player) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 20,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        children: [
          CircleAvatar(
            radius: 50,
            backgroundColor: const Color(0xFF1A237E).withOpacity(0.1),
            child: Text(
              player.playerName[0].toUpperCase(),
              style: const TextStyle(
                fontSize: 40,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1A237E),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            player.playerName,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1A237E),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            player.email,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 4),
          Text(
            player.phone,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                decoration: BoxDecoration(
                  color: _getLevelColor(player.overallLevel).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  'Niveau ${_getLevelLabel(player.overallLevel)}',
                  style: TextStyle(
                    color: _getLevelColor(player.overallLevel),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.calendar_today,
                      size: 14,
                      color: Colors.green,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      'Membre depuis ${player.joinedDate.day}/${player.joinedDate.month}/${player.joinedDate.year}',
                      style: const TextStyle(
                        color: Colors.green,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSkillsSection(PlayerStats player) {
    final skills = [
      {
        'label': 'Vitesse',
        'score': player.speedScore,
        'color': const Color(0xFFFF6B6B),
        'icon': Icons.speed,
      },
      {
        'label': 'Contrôle Ballon',
        'score': player.controlBallScore,
        'color': const Color(0xFF4ECDC4),
        'icon': Icons.sports_soccer,
      },
      {
        'label': 'Tir',
        'score': player.shootScore,
        'color': const Color(0xFFFFD93D),
        'icon': Icons.sports_score,
      },
      {
        'label': 'Passe',
        'score': player.passScore,
        'color': const Color(0xFF6C5CE7),
        'icon': Icons.swap_horiz,
      },
    ];

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 20,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(
                Icons.assessment,
                color: Color(0xFF1A237E),
              ),
              SizedBox(width: 8),
              Text(
                'Scores par Compétence',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1A237E),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ...skills.map((skill) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(
                            skill['icon'] as IconData,
                            size: 16,
                            color: skill['color'] as Color,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            skill['label'] as String,
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                      Text(
                        '${(skill['score'] as double).toStringAsFixed(1)}%',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: skill['color'] as Color,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Container(
                    height: 8,
                    decoration: BoxDecoration(
                      color: Colors.grey[200],
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Stack(
                      children: [
                        Container(
                          width: ((skill['score'] as double) / 100) * double.infinity,
                          height: 8,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [
                                (skill['color'] as Color).withOpacity(0.7),
                                skill['color'] as Color,
                              ],
                            ),
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildStatsSection(PlayerStats player) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 20,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              children: [
                Text(
                  player.totalScore.toStringAsFixed(1),
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1A237E),
                  ),
                ),
                const Text(
                  'Score Total',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey,
                  ),
                ),
              ],
            ),
          ),
          Container(
            width: 1,
            height: 60,
            color: Colors.grey[300],
          ),
          Expanded(
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.attach_money,
                      size: 20,
                      color: Colors.green,
                    ),
                    Text(
                      player.totalRewards.toStringAsFixed(2),
                      style: const TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Colors.green,
                      ),
                    ),
                  ],
                ),
                const Text(
                  'Récompenses Total',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey,
                  ),
                ),
              ],
            ),
          ),
          Container(
            width: 1,
            height: 60,
            color: Colors.grey[300],
          ),
          Expanded(
            child: Column(
              children: [
                Text(
                  player.trainingSessionsCount.toString(),
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1A237E),
                  ),
                ),
                const Text(
                  'Sessions',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPerformanceSection(PlayerStats player) {
    final performances = [
      {
        'label': 'Meilleur Score',
        'value': player.bestScores.values.reduce((a, b) => a > b ? a : b),
        'color': Colors.green,
        'icon': Icons.star,
      },
      {
        'label': 'Score Moyen',
        'value': player.totalScore / 4,
        'color': Colors.blue,
        'icon': Icons.trending_up,
      },
      {
        'label': 'Progression',
        'value': player.progressRate,
        'color': player.progressRate >= 70 ? Colors.green : Colors.amber,
        'icon': Icons.timeline,
      },
    ];

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 20,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Performance Générale',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1A237E),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: performances.map((perf) {
              return Expanded(
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: (perf['color'] as Color).withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: (perf['color'] as Color).withOpacity(0.2),
                    ),
                  ),
                  child: Column(
                    children: [
                      Icon(
                        perf['icon'] as IconData,
                        color: perf['color'] as Color,
                        size: 24,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        (perf['value'] as double).toStringAsFixed(1),
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: perf['color'] as Color,
                        ),
                      ),
                      Text(
                        perf['label'] as String,
                        style: TextStyle(
                          fontSize: 10,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressSection(PlayerStats player) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 20,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(
                Icons.trending_up,
                color: Color(0xFF1A237E),
              ),
              SizedBox(width: 8),
              Text(
                'Progression',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1A237E),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                flex: 8,
                child: Container(
                  height: 12,
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Stack(
                    children: [
                      Container(
                        width: (player.progressRate / 100) * double.infinity,
                        height: 12,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              _getProgressColor(player.progressRate).withOpacity(0.7),
                              _getProgressColor(player.progressRate),
                            ],
                          ),
                          borderRadius: BorderRadius.circular(6),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: Text(
                  '${player.progressRate.toStringAsFixed(0)}%',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: _getProgressColor(player.progressRate),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            _getProgressMessage(player.progressRate),
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }

  Color _getLevelColor(SkillLevel level) {
    switch (level) {
      case SkillLevel.expert:
        return Colors.purple;
      case SkillLevel.advanced:
        return Colors.blue;
      case SkillLevel.intermediate:
        return Colors.green;
      case SkillLevel.beginner:
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  String _getLevelLabel(SkillLevel level) {
    switch (level) {
      case SkillLevel.expert:
        return 'Expert';
      case SkillLevel.advanced:
        return 'Avancé';
      case SkillLevel.intermediate:
        return 'Intermédiaire';
      case SkillLevel.beginner:
        return 'Débutant';
      default:
        return '';
    }
  }

  Color _getProgressColor(double progress) {
    if (progress >= 80) return Colors.green;
    if (progress >= 50) return Colors.amber;
    return Colors.red;
  }

  String _getProgressMessage(double progress) {
    if (progress >= 80) {
      return '🏆 Excellent progrès! Le joueur est en pleine forme.';
    } else if (progress >= 50) {
      return '📈 Bonne progression continue! Encore des améliorations possibles.';
    } else {
      return '💪 Le joueur a besoin de plus d\'entraînement. Encouragez-le!';
    }
  }
}