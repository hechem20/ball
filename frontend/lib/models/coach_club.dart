import 'user.dart';

class CoachClub {
  final String id;
  final String coachId;
  final String coachName;
  String clubName;
  String description;
  final String logoUrl;
  double budget; // Changé de final à non-final
  double subscriptionFee; // Changé de final à non-final
  final int maxPlayers;
  List<String> currentPlayers; // Changé de final à non-final
  final List<String> specialties;
  final double rating;
  final int totalPlayers;
  bool isActive; // Changé de final à non-final
  final DateTime createdAt;

  CoachClub({
    required this.id,
    required this.coachId,
    required this.coachName,
    required this.clubName,
    required this.description,
    required this.logoUrl,
    required this.budget,
    required this.subscriptionFee,
    required this.maxPlayers,
    required this.currentPlayers,
    required this.specialties,
    required this.rating,
    required this.totalPlayers,
    required this.isActive,
    required this.createdAt,
  });

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'coachId': coachId,
      'coachName': coachName,
      'clubName': clubName,
      'description': description,
      'logoUrl': logoUrl,
      'budget': budget,
      'subscriptionFee': subscriptionFee,
      'maxPlayers': maxPlayers,
      'currentPlayers': currentPlayers,
      'specialties': specialties,
      'rating': rating,
      'totalPlayers': totalPlayers,
      'isActive': isActive,
      'createdAt': createdAt.toIso8601String(),
    };
  }

 factory CoachClub.fromJson(Map<String, dynamic> json) {
  return CoachClub(
    id: json['id']?.toString() ?? "",

    coachId: json['coach_id']?.toString() ?? "",

    coachName: json['coach_name']?.toString() ?? "",

    clubName: json['club_name'] ?? "",

    description: json['description'] ?? "",

    logoUrl: json['logo_url'] ?? "",

    budget: (json['budget'] ?? 0).toDouble(),

    subscriptionFee: (json['subscription_fee'] ?? 0).toDouble(),

    maxPlayers: json['max_players'] ?? 0,

    currentPlayers:
        List<String>.from(json['current_players'] ?? []),

    specialties:
        List<String>.from(json['specialties'] ?? []),

    rating: (json['rating'] ?? 0).toDouble(),

    totalPlayers: json['total_players'] ?? 0,

    isActive: json['is_active'] ?? true,

    createdAt: json['created_at'] != null
        ? DateTime.parse(json['created_at'])
        : DateTime.now(),
  );
}

  int get availableSlots => maxPlayers - currentPlayers.length;
  bool get hasAvailableSlots => availableSlots > 0;

  // Méthodes pour mettre à jour les propriétés modifiables
  void updateBudget(double newBudget) {
    budget = newBudget;
  }

  void updateSubscriptionFee(double newFee) {
    subscriptionFee = newFee;
  }

  void addPlayer(String playerId) {
    if (hasAvailableSlots) {
      currentPlayers.add(playerId);
    }
  }

  void removePlayer(String playerId) {
    currentPlayers.remove(playerId);
  }

  void toggleActive() {
    isActive = !isActive;
  }
}