import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:frontend/services/training_service.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:frontend/models/training.dart';
import 'package:frontend/services/wallet_service.dart';
import 'package:frontend/services/club_service.dart';

class TrainingScreen extends StatefulWidget {
  final String coachId;
  final String clubId;

  const TrainingScreen({
    super.key,
    required this.coachId,
    required this.clubId,
  });

  @override
  State<TrainingScreen> createState() => _TrainingScreenState();
}

class _TrainingScreenState extends State<TrainingScreen> {
  final TrainingService _trainingService = TrainingService();
  final AuthService _authService = AuthService();
  final WalletService _walletService = WalletService();
  final ClubService _clubService = ClubService();

  TrainingType? _selectedTraining;
  bool _isLoading = false;
  bool _isAnalyzing = false;
  PlatformFile? _videoFile;
  TrainingSession? _lastSession;
  Map<String, dynamic> _aiAnalysis = {};
  String? _playerId;
  double _walletBalance = 0.0;
  String? _playerName;

  final List<TrainingOption> _trainingOptions = [
    TrainingOption(
      type: TrainingType.speed,
      title: 'Vitesse',
      icon: Icons.speed,
      color: const Color(0xFFFF6B6B),
      description: 'Testez et améliorez votre vitesse de course',
    ),
    TrainingOption(
      type: TrainingType.control_ball,
      title: 'Contrôle du ballon',
      icon: Icons.sports_soccer,
      color: const Color(0xFF4ECDC4),
      description: 'Perfectionnez votre contrôle et dribble',
    ),
    TrainingOption(
      type: TrainingType.shoot,
      title: 'Tir',
      icon: Icons.sports_score,
      color: const Color(0xFFFFD93D),
      description: 'Améliorez votre précision et puissance de tir',
    ),
    TrainingOption(
      type: TrainingType.pass,
      title: 'Passe',
      icon: Icons.swap_horiz,
      color: const Color(0xFF6C5CE7),
      description: 'Travaillez votre précision de passe',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    try {
      final user = await _authService.getCurrentUser();
      if (user != null) {
        setState(() {
          _playerId = user.id;
          _playerName = user.fullName;
        });
        _loadWalletBalance();
        _loadLastSession();
      }
    } catch (e) {
      print('❌ Erreur chargement utilisateur: $e');
    }
  }

  Future<void> _loadWalletBalance() async {
    try {
      final balance = await _walletService.getBalance();
      setState(() {
        _walletBalance = balance;
      });
    } catch (e) {
      print('❌ Erreur chargement wallet: $e');
    }
  }

  Future<void> _loadLastSession() async {
    if (_playerId == null) return;
    try {
      final session = await _trainingService.getLastSession(
        playerId: _playerId,
      );
      setState(() {
        _lastSession = session;
      });
    } catch (e) {
      print('❌ Erreur chargement dernière session: $e');
    }
  }

  @override
  void dispose() {
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
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
                _buildHeader(),
                Expanded(
                  child: _isLoading || _isAnalyzing
                      ? Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const CircularProgressIndicator(
                                color: Colors.white,
                              ),
                              const SizedBox(height: 16),
                              Text(
                                _isAnalyzing
                                    ? "🤖 Analyse de la vidéo en cours..."
                                    : "⏳ Chargement en cours...",
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                ),
                              ),
                              if (_isAnalyzing)
                                const SizedBox(height: 8),
                              if (_isAnalyzing)
                                Text(
                                  "Cela peut prendre quelques secondes",
                                  style: TextStyle(
                                    color: Colors.white.withOpacity(0.7),
                                    fontSize: 14,
                                  ),
                                ),
                            ],
                          ),
                        )
                      : SingleChildScrollView(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            children: [
                              if (_lastSession != null) _buildLastSessionCard(),
                              if (_lastSession != null) const SizedBox(height: 16),
                              _buildTrainingGrid(),
                              const SizedBox(height: 16),
                              if (_aiAnalysis.isNotEmpty) _buildAIAnalysisCard(),
                              if (_aiAnalysis.isNotEmpty) const SizedBox(height: 16),
                              _buildVideoUploadSection(),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Entraînement',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  Text(
                    'Améliorez vos compétences',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.white.withOpacity(0.7),
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.account_balance_wallet_outlined,
                      color: Colors.white,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '${_walletBalance.toStringAsFixed(2)} DT',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (_playerName != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                '👋 Bonjour $_playerName',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.8),
                  fontSize: 14,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildTrainingGrid() {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 0.85,
      ),
      itemCount: _trainingOptions.length,
      itemBuilder: (context, index) {
        final option = _trainingOptions[index];
        final isSelected = _selectedTraining == option.type;
        return GestureDetector(
          onTap: () => _showTrainingDialog(option),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            decoration: BoxDecoration(
              color: isSelected ? option.color.withOpacity(0.2) : Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isSelected ? option.color : Colors.white.withOpacity(0.3),
                width: isSelected ? 3 : 1,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black12,
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: option.color.withOpacity(0.15),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    option.icon,
                    color: option.color,
                    size: 40,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  option.title,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: isSelected ? option.color : const Color(0xFF1A237E),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  option.description,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showTrainingDialog(TrainingOption option) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(30),
            topRight: Radius.circular(30),
          ),
        ),
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: option.color.withOpacity(0.15),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(option.icon, color: option.color),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      'Entraînement ${option.title}',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1A237E),
                      ),
                    ),
                  ],
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Text(
              _videoFile == null
                  ? '📹 Importe une vidéo de ton exercice pour lancer l\'analyse IA.'
                  : '✅ Vidéo prête : ${_videoFile!.name}',
              style: TextStyle(fontSize: 14, color: Colors.grey[600]),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: _buildTrainingOptionButton(
                    'Commencer',
                    Icons.play_arrow,
                    option.color,
                    () {
                      Navigator.pop(context);
                      _startTraining(option.type);
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildTrainingOptionButton(
                    'Historique',
                    Icons.history,
                    Colors.grey,
                    () {
                      Navigator.pop(context);
                      _showTrainingHistory(option.type);
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              '💡 Filme ton exercice de profil, ballon et joueur bien visibles, '
              'pour une analyse IA plus précise.',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[500],
                fontStyle: FontStyle.italic,
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildTrainingOptionButton(
      String label, IconData icon, Color color, VoidCallback onPressed) {
    return ElevatedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon, size: 20),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }

  Future<bool> _pickVideo() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.video,
        allowMultiple: false,
        withData: true,
      );

      if (result == null || result.files.isEmpty) {
        return false;
      }

      final file = result.files.single;
      if (file.bytes == null) {
        return false;
      }

      setState(() {
        _videoFile = file;
      });
      return true;
    } catch (e) {
      print('❌ Erreur sélection vidéo: $e');
      return false;
    }
  }

  Future<void> _startTraining(TrainingType type) async {
    if (_playerId == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('❌ Utilisateur non connecté'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // Si aucune vidéo n'a été sélectionnée, on la demande maintenant
    if (_videoFile == null) {
      final picked = await _pickVideo();
      if (!picked) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('📹 Une vidéo est nécessaire pour lancer l\'analyse.'),
            duration: Duration(seconds: 2),
          ),
        );
        return;
      }
    }

    setState(() {
      _isLoading = true;
      _isAnalyzing = true;
      _selectedTraining = type;
    });

    try {
      // Convertir le fichier en bytes
      final bytes = _videoFile!.bytes;
      if (bytes == null) {
        throw Exception('Erreur: Vidéo invalide');
      }

      final analysis = await _trainingService.analyzeTraining(
  type: type,
  videoBytes: bytes,
  fileName: _videoFile!.name,
);

     // ✅ Extraire les données correctement
final score = (analysis['score'] as num?)?.toDouble() ?? 0.0;
final feedback = analysis['feedback'] as String? ?? 'Analyse terminée';

// ✅ Récupérer le niveau depuis l'analyse ou le calculer
final levelFromAnalysis = analysis['level'] as String?;
final level = levelFromAnalysis != null 
    ? _getSkillLevelFromString(levelFromAnalysis) 
    : _getSkillLevel(score);

// ✅ Récupérer les métriques spécifiques
final metrics = analysis['metrics'] as Map<String, dynamic>? ?? {};

// Calculer la récompense
double reward = 0.0;
      // Sauvegarder la session
      final result = await _trainingService.saveSession(
  type: type,
  score: score,
  duration: 5.0,
  level: level,
  playerId: _playerId!,
  feedback: analysis['feedback'] as String?,
  metrics: analysis['metrics'] as Map<String, dynamic>?,
);
reward = (result['reward'] as num?)?.toDouble() ?? 0.0;
      // Mettre à jour le wallet
      await _walletService.addReward(reward);
      await _loadWalletBalance();

      final session = TrainingSession(
        id: 'session_${DateTime.now().millisecondsSinceEpoch}',
        playerId: _playerId!,
        type: type,
        date: DateTime.now(),
        score: score,
        duration: 5.0,
        level: level,
        reward: reward,
        aiFeedback: analysis['feedback'] as String?,
        metrics: analysis['metrics'] as Map<String, dynamic>? ?? {},
        videoUrl: analysis['video_url'] as String?,
      );

      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _isAnalyzing = false;
        _lastSession = session;
        _aiAnalysis = analysis;
        _videoFile = null; // Réinitialiser pour un nouvel envoi
      });

      _showResultsDialog(session);

    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _isAnalyzing = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  double _calculateReward(double score, TrainingType type) {
    final baseReward = 1.0;
    final multiplier = score / 100;
    final typeBonus = {
      TrainingType.speed: 1.2,
      TrainingType.control_ball: 1.0,
      TrainingType.shoot: 1.1,
      TrainingType.pass: 0.9,
    };
    final bonus = typeBonus[type] ?? 1.0;
    return double.parse((baseReward * multiplier * 10 * bonus).toStringAsFixed(2));
  }

  SkillLevel _getSkillLevel(double score) {
    if (score >= 90) return SkillLevel.expert;
    if (score >= 75) return SkillLevel.advanced;
    if (score >= 50) return SkillLevel.intermediate;
    return SkillLevel.beginner;
  }

  void _showResultsDialog(TrainingSession session) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Row(
          children: [
            Icon(Icons.emoji_events, color: Colors.amber, size: 32),
            SizedBox(width: 12),
            Text('Résultats'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey[50],
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Score'),
                      Text(
                        '${session.score.toStringAsFixed(1)}%',
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1A237E),
                        ),
                      ),
                    ],
                  ),
                  const Divider(),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Niveau'),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: _getLevelColor(session.level).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          _getLevelLabel(session.level),
                          style: TextStyle(
                            color: _getLevelColor(session.level),
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const Divider(),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Récompense'),
                      Text(
                        '+${session.reward.toStringAsFixed(2)} ',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.green,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            if (session.aiFeedback != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.blue.withOpacity(0.2)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.psychology, color: Colors.blue, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        session.aiFeedback!,
                        style: TextStyle(fontSize: 13, color: Colors.grey[700]),
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Continuer'),
          ),
        ],
      ),
    );
  }

  Widget _buildLastSessionCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.assessment, color: Color(0xFF1A237E)),
              const SizedBox(width: 8),
              const Text(
                'Dernier entraînement',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1A237E),
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getLevelColor(_lastSession!.level).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  _getLevelLabel(_lastSession!.level),
                  style: TextStyle(
                    color: _getLevelColor(_lastSession!.level),
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: Column(
                  children: [
                    Text(
                      _lastSession!.score.toStringAsFixed(1),
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1A237E),
                      ),
                    ),
                    const Text('Score', style: TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ),
              ),
              Container(width: 1, height: 40, color: Colors.grey[300]),
              Expanded(
                child: Column(
                  children: [
                    Text(
                      '+${_lastSession!.reward.toStringAsFixed(2)}',
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.green,
                      ),
                    ),
                    const Text('Récompense', style: TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ),
              ),
              Container(width: 1, height: 40, color: Colors.grey[300]),
              Expanded(
                child: Column(
                  children: [
                    
                    const Text('seconde', style: TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAIAnalysisCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.psychology_alt, color: Color(0xFF6C5CE7)),
              const SizedBox(width: 8),
              const Text(
                'Analyse IA',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1A237E),
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'IA v2.0',
                  style: TextStyle(
                    color: Colors.green,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (_aiAnalysis['feedback'] != null)
            Text(
              _aiAnalysis['feedback'],
              style: TextStyle(fontSize: 14, color: Colors.grey[700]),
            ),
          const SizedBox(height: 12),
          if (_aiAnalysis['metrics'] != null)
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: (_aiAnalysis['metrics'] as Map<String, dynamic>).entries.map((entry) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1A237E).withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${entry.key}: ${entry.value}',
                    style: const TextStyle(fontSize: 12, color: Color(0xFF1A237E)),
                  ),
                );
              }).toList(),
            ),
        ],
      ),
    );
  }

  Widget _buildVideoUploadSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.95),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.video_library, color: Color(0xFFFF6B6B)),
              const SizedBox(width: 8),
              const Text(
                'Vidéo d\'entraînement',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1A237E),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            height: 100,
            decoration: BoxDecoration(
              color: Colors.grey[50],
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey[300]!),
            ),
            child: InkWell(
              onTap: () async {
                final picked = await _pickVideo();
                if (!mounted) return;
                if (picked) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('📹 Vidéo sélectionnée : ${_videoFile!.name}'),
                      backgroundColor: Colors.green,
                      duration: const Duration(seconds: 2),
                    ),
                  );
                }
              },
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    _videoFile == null
                        ? Icons.cloud_upload_outlined
                        : Icons.check_circle_outline,
                    size: 32,
                    color: _videoFile == null ? Colors.grey[400] : Colors.green,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _videoFile == null
                        ? 'Appuyez pour importer une vidéo'
                        : _videoFile!.name,
                    style: TextStyle(
                      fontSize: 14,
                      color: _videoFile == null ? Colors.grey[500] : Colors.green[700],
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showTrainingHistory(TrainingType type) {
    if (_playerId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('❌ Utilisateur non connecté'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.7,
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(30),
            topRight: Radius.circular(30),
          ),
        ),
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Historique des entraînements',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1A237E),
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Expanded(
              child: FutureBuilder<List<TrainingSession>>(
                future: _trainingService.getPlayerSessions(
                  playerId: _playerId,
                  type: type,
                ),
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(
                      child: CircularProgressIndicator(),
                    );
                  }
                  if (snapshot.hasError) {
                    return Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.error_outline,
                            size: 64,
                            color: Colors.grey[400],
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Erreur: ${snapshot.error}',
                            style: TextStyle(
                              color: Colors.grey[600],
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    );
                  }
                  final sessions = snapshot.data ?? [];
                  if (sessions.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.history,
                            size: 64,
                            color: Colors.grey[300],
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Aucun historique trouvé',
                            style: TextStyle(
                              color: Colors.grey[500],
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Commencez votre premier entraînement!',
                            style: TextStyle(
                              color: Colors.grey[400],
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    );
                  }
                  return ListView.separated(
                    itemCount: sessions.length,
                    separatorBuilder: (context, index) => const Divider(),
                    itemBuilder: (context, index) {
                      final session = sessions[index];
                      return ListTile(
                        leading: CircleAvatar(
                          backgroundColor: _getLevelColor(session.level).withOpacity(0.2),
                          child: Text(
                            session.score.toStringAsFixed(0),
                            style: TextStyle(
                              color: _getLevelColor(session.level),
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ),
                        title: Text(
                          '${session.date.day}/${session.date.month}/${session.date.year}',
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        subtitle: Text(
                          '${session.duration.toStringAsFixed(0)} min • ${session.metrics['repetitions'] ?? 0} répétitions',
                        ),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              '+${session.reward.toStringAsFixed(2)} ',
                              style: const TextStyle(
                                color: Colors.green,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              '${session.score.toStringAsFixed(1)}%',
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ],
        ),
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
SkillLevel _getSkillLevelFromString(String level) {
  switch (level.toLowerCase()) {
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

class TrainingOption {
  final TrainingType type;
  final String title;
  final IconData icon;
  final Color color;
  final String description;

  TrainingOption({
    required this.type,
    required this.title,
    required this.icon,
    required this.color,
    required this.description,
  });
}