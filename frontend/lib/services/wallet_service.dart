import 'package:shared_preferences/shared_preferences.dart';

class WalletService {
  double _balance = 0.0;
  final List<Map<String, dynamic>> _transactions = [];

  WalletService() {
    _loadBalance();
  }

  double getBalance() {
    return _balance;
  }

  Future<void> _loadBalance() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _balance = prefs.getDouble('wallet_balance') ?? 100.0;
    } catch (e) {
      print('❌ Erreur _loadBalance: $e');
    }
  }

  /// Mettre à jour le solde
  Future<void> updateBalance(double newBalance) async {
    try {
      _balance = newBalance;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setDouble('wallet_balance', newBalance);
    } catch (e) {
      print('❌ Erreur updateBalance: $e');
    }
  }

  /// Ajouter une récompense
  Future<void> addReward(double amount) async {
    _balance += amount;
    await updateBalance(_balance);
    
    _transactions.add({
      'amount': amount,
      'type': 'reward',
      'date': DateTime.now().toIso8601String(),
      'description': 'Récompense entraînement',
    });
  }

  /// Déduire un montant
  Future<bool> deductAmount(double amount) async {
    if (_balance >= amount) {
      _balance -= amount;
      await updateBalance(_balance);
      
      _transactions.add({
        'amount': amount,
        'type': 'payment',
        'date': DateTime.now().toIso8601String(),
        'description': 'Paiement service',
      });
      return true;
    }
    return false;
  }

  /// Récupérer les transactions
  List<Map<String, dynamic>> getTransactions() {
    return List.from(_transactions.reversed);
  }

  /// Recharger le solde depuis le backend
  Future<double> refreshBalance() async {
    try {
      // Appel API pour récupérer le solde réel
      // Pour l'instant, retourne le solde local
      return _balance;
    } catch (e) {
      print('❌ Erreur refreshBalance: $e');
      return _balance;
    }
  }
}