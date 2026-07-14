class RegisterRequest {
  final String fullName;
  final String email;
  final String password;
  final String phone;
  final String role;
  final String? experience;
  final String? clubName;
  final String? clubDescription;

  RegisterRequest({
    required this.fullName,
    required this.email,
    required this.password,
    required this.phone,
    required this.role,
    this.experience,
    this.clubName,
    this.clubDescription,
  });

  Map<String, dynamic> toJson() {
    return {
      'full_name': fullName,
      'email': email,
      'password': password,
      'phone': phone,
      'role': role,
      'experience': experience,
      'club_name': clubName,
      'club_description': clubDescription,
    };
  }
}

class LoginRequest {
  final String email;
  final String password;

  LoginRequest({
    required this.email,
    required this.password,
  });

  Map<String, dynamic> toJson() {
    return {
      'email': email,
      'password': password,
    };
  }
}

class AuthResponse {
  final bool success;
  final String? accessToken;
  final String? refreshToken;
  final User? user;
  final String? message;

  AuthResponse({
    required this.success,
    this.accessToken,
    this.refreshToken,
    this.user,
    this.message,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      success: json['success'] ?? false,
      accessToken: json['access_token'],
      refreshToken: json['refresh_token'],
      user: json['user'] != null ? User.fromJson(json['user']) : null,
      message: json['message'],
    );
  }
}

class User {
  final String id;
  final String fullName;
  final String email;
  final String phone;
  final String role;
  final String? experience;
  final bool isVerified;
  final double walletBalance;
  final DateTime createdAt;

  User({
    required this.id,
    required this.fullName,
    required this.email,
    required this.phone,
    required this.role,
    this.experience,
    required this.isVerified,
    required this.walletBalance,
    required this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] ?? '',
      fullName: json['full_name'] ?? '',
      email: json['email'] ?? '',
      phone: json['phone'] ?? '',
      role: json['role'] ?? 'player',
      experience: json['experience'],
      isVerified: json['is_verified'] ?? false,
      walletBalance: (json['wallet_balance'] ?? 0.0).toDouble(),
      createdAt: json['created_at'] != null 
          ? DateTime.parse(json['created_at']) 
          : DateTime.now(),
    );
  }
}