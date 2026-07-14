import 'user.dart';

enum TransactionStatus {
  pending,
  completed,
  failed,
  refunded,
}

class Transaction {
  final String id;
  final String playerId;
  final String coachId;
  final String clubId;
  final double amount;
  final DateTime date;
  final TransactionStatus status;
  final String? description;

  Transaction({
    required this.id,
    required this.playerId,
    required this.coachId,
    required this.clubId,
    required this.amount,
    required this.date,
    required this.status,
    this.description,
  });

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'playerId': playerId,
      'coachId': coachId,
      'clubId': clubId,
      'amount': amount,
      'date': date.toIso8601String(),
      'status': status.name,
      'description': description,
    };
  }

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'],
      playerId: json['playerId'],
      coachId: json['coachId'],
      clubId: json['clubId'],
      amount: json['amount'],
      date: DateTime.parse(json['date']),
      status: TransactionStatus.values.firstWhere(
        (e) => e.name == json['status'],
      ),
      description: json['description'],
    );
  }
}