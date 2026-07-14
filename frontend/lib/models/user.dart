enum UserRole {
  player,
  coach,
}

class User {
  final String id;
  final String fullName;
  final String email;
  final String phone;
  final UserRole role;
  final String? experience; // Pour les coachs
  final DateTime createdAt;
  final bool isVerified;

  User({
    required this.id,
    required this.fullName,
    required this.email,
    required this.phone,
    required this.role,
    this.experience,
    required this.createdAt,
    this.isVerified = false,
  });

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'fullName': fullName,
      'email': email,
      'phone': phone,
      'role': role.name,
      'experience': experience,
      'createdAt': createdAt.toIso8601String(),
      'isVerified': isVerified,
    };
  }

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      fullName: json['fullName'],
      email: json['email'],
      phone: json['phone'],
      role: UserRole.values.firstWhere((e) => e.name == json['role']),
      experience: json['experience'],
      createdAt: DateTime.parse(json['createdAt']),
      isVerified: json['isVerified'] ?? false,
    );
  }
}