import 'package:flutter/material.dart';
import '../models/player_stats.dart';
import '../models/training.dart';
import '../services/club_service.dart';

class PlayersListScreen extends StatefulWidget {
  final String coachId;
  final String clubId;

  const PlayersListScreen({
    super.key,
    required this.coachId,
    required this.clubId,
  });

  @override
  State<PlayersListScreen> createState() => _PlayersListScreenState();
}

class _PlayersListScreenState extends State<PlayersListScreen> {
  final ClubService _clubService = ClubService();
  List<PlayerStats> _players = [];
  bool _isLoading = true;
  String _sortBy = 'total_score'; // 'total_score', 'speed', 'control', 'shoot', 'pass'
  bool _sortAscending = false;

  @override
  void initState() {
    super.initState();
    _loadPlayers();
  }

  Future<void> _loadPlayers() async {
    setState(() => _isLoading = true);
    try {
      _players = await _clubService.getClubPlayers(widget.clubId);
      _sortPlayers();
      print('✅ ${_players.length} joueurs chargés');
    } catch (e) {
      print('❌ Erreur de chargement des joueurs: $e');
    }
    setState(() => _isLoading = false);
  }

  void _sortPlayers() {
    _players.sort((a, b) {
      double scoreA = 0.0;
      double scoreB = 0.0;
      
      switch (_sortBy) {
        case 'total_score':
          scoreA = a.totalScore;
          scoreB = b.totalScore;
          break;
        case 'speed':
          scoreA = a.speedScore;
          scoreB = b.speedScore;
          break;
        case 'control':
          scoreA = a.controlBallScore;
          scoreB = b.controlBallScore;
          break;
        case 'shoot':
          scoreA = a.shootScore;
          scoreB = b.shootScore;
          break;
        case 'pass':
          scoreA = a.passScore;
          scoreB = b.passScore;
          break;
        default:
          scoreA = a.totalScore;
          scoreB = b.totalScore;
      }
      
      return _sortAscending ? scoreA.compareTo(scoreB) : scoreB.compareTo(scoreA);
    });
  }

  void _toggleSort(String field) {
    if (_sortBy == field) {
      setState(() {
        _sortAscending = !_sortAscending;
        _sortPlayers();
      });
    } else {
      setState(() {
        _sortBy = field;
        _sortAscending = false;
        _sortPlayers();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Liste des Joueurs'),
        backgroundColor: const Color(0xFF1A237E),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadPlayers,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _players.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.people_outline,
                        size: 64,
                        color: Colors.grey[400],
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Aucun joueur dans ce club',
                        style: TextStyle(
                          fontSize: 18,
                          color: Colors.grey[600],
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Les joueurs apparaîtront après leur paiement',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[400],
                        ),
                      ),
                    ],
                  ),
                )
              : Column(
                  children: [
                    // ✅ Barre de tri
                    Container(
                      padding: const EdgeInsets.all(8),
                      color: Colors.grey[100],
                      child: SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            _buildSortChip('Score Total', 'total_score'),
                            _buildSortChip('Vitesse', 'speed'),
                            _buildSortChip('Contrôle', 'control'),
                            _buildSortChip('Tir', 'shoot'),
                            _buildSortChip('Passe', 'pass'),
                            const SizedBox(width: 8),
                            Text(
                              '${_players.length} joueurs',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[600],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    // ✅ Liste des joueurs
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _players.length,
                        itemBuilder: (context, index) {
                          final player = _players[index];
                          return _buildPlayerCard(player, index + 1);
                        },
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _buildSortChip(String label, String field) {
    final isSelected = _sortBy == field;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: FilterChip(
        label: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(label),
            if (isSelected)
              Icon(
                _sortAscending ? Icons.arrow_upward : Icons.arrow_downward,
                size: 14,
              ),
          ],
        ),
        selected: isSelected,
        onSelected: (_) => _toggleSort(field),
        backgroundColor: Colors.grey[200],
        selectedColor: const Color(0xFF1A237E).withOpacity(0.2),
        labelStyle: TextStyle(
          color: isSelected ? const Color(0xFF1A237E) : Colors.grey[700],
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          fontSize: 12,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
    );
  }

  Widget _buildPlayerCard(PlayerStats player, int rank) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: const Color(0xFF1A237E).withOpacity(0.1),
          child: Text(
            rank.toString(),
            style: const TextStyle(
              color: Color(0xFF1A237E),
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ),
        title: Text(
          player.playerName,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              player.email,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 4),
            // ✅ Afficher le score total et le niveau
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: _getLevelColor(player.overallLevel).withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    _getLevelLabel(player.overallLevel),
                    style: TextStyle(
                      fontSize: 10,
                      color: _getLevelColor(player.overallLevel),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  'Score: ${player.totalScore.toStringAsFixed(0)} pts',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFF1A237E),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  '+${player.totalRewards.toStringAsFixed(1)} DT',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.green,
                  ),
                ),
              ],
            ),
          ],
        ),
        trailing: Icon(
          Icons.chevron_right,
          color: Colors.grey[400],
        ),
        children: [
          // ✅ Détails des scores par compétence
          Container(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Scores par compétence',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1A237E),
                  ),
                ),
                const SizedBox(height: 12),
                _buildSkillRow('🏃 Vitesse', player.speedScore, Colors.blue),
                _buildSkillRow('⚽ Contrôle', player.controlBallScore, Colors.green),
                _buildSkillRow('🎯 Tir', player.shootScore, Colors.orange),
                _buildSkillRow('🔄 Passe', player.passScore, Colors.purple),
                const SizedBox(height: 12),
                _buildStatRow('Sessions', player.trainingSessionsCount.toString()),
                _buildStatRow('Récompenses', '+${player.totalRewards.toStringAsFixed(2)} DT'),
                _buildStatRow('Date d\'inscription', 
                    '${player.joinedDate.day}/${player.joinedDate.month}/${player.joinedDate.year}'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSkillRow(String label, double score, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Container(
              height: 8,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(4),
              ),
              child: Stack(
                children: [
                  Container(
                    width: (score / 100) * double.infinity,
                    height: 8,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          color.withOpacity(0.5),
                          color,
                        ],
                      ),
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '${score.toStringAsFixed(0)}%',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 13,
              color: Colors.grey[600],
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
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
    }
  }
}