import 'package:flutter/material.dart';
import '../models/coach_club.dart';
import '../services/club_service.dart';

class BudgetManagement extends StatefulWidget {
  final CoachClub club;

  const BudgetManagement({super.key, required this.club});

  @override
  State<BudgetManagement> createState() => _BudgetManagementState();
}

class _BudgetManagementState extends State<BudgetManagement> {
  final ClubService _clubService = ClubService();
  bool _isEditing = false;
  final _budgetController = TextEditingController();
  final _feeController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _budgetController.text = widget.club.budget.toString();
    _feeController.text = widget.club.subscriptionFee.toString();
  }

  @override
  void dispose() {
    _budgetController.dispose();
    _feeController.dispose();
    super.dispose();
  }

  Future<void> _updateBudget() async {
    if (_budgetController.text.isNotEmpty) {
      final newBudget = double.parse(_budgetController.text);
      await _clubService.updateBudget(widget.club.id, newBudget);
      setState(() {
        widget.club.budget = newBudget;
        _isEditing = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Budget mis à jour avec succès!'),
          backgroundColor: Colors.green,
        ),
      );
    }
  }

  Future<void> _updateSubscriptionFee() async {
    if (_feeController.text.isNotEmpty) {
      final newFee = double.parse(_feeController.text);
      await _clubService.updateSubscriptionFee(widget.club.id, newFee);
      setState(() {
        widget.club.subscriptionFee = newFee;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Frais d\'abonnement mis à jour!'),
          backgroundColor: Colors.green,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(
                Icons.account_balance_wallet_outlined,
                color: Color(0xFF1A237E),
              ),
              SizedBox(width: 8),
              Text(
                'Gestion du Budget',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1A237E),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Budget actuel
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  const Color(0xFF1A237E).withOpacity(0.1),
                  const Color(0xFF1A237E).withOpacity(0.05),
                ],
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Budget total',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey,
                      ),
                    ),
                    Text(
                      '${widget.club.budget.toStringAsFixed(2)} DT',
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1A237E),
                      ),
                    ),
                  ],
                ),
                IconButton(
                  onPressed: () {
                    setState(() => _isEditing = !_isEditing);
                  },
                  icon: Icon(
                    _isEditing ? Icons.close : Icons.edit_outlined,
                    color: const Color(0xFF1A237E),
                  ),
                ),
              ],
            ),
          ),
          if (_isEditing) ...[
            const SizedBox(height: 12),
            TextFormField(
              controller: _budgetController,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'Nouveau budget',
                prefixText: 'DT ',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Colors.grey[300]!),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(
                    color: Color(0xFF1A237E),
                    width: 2,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _updateBudget,
                    icon: const Icon(Icons.save),
                    label: const Text('Mettre à jour'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1A237E),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
          const SizedBox(height: 16),
          // Frais d'abonnement
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Frais d\'abonnement',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                  Text(
                    '${widget.club.subscriptionFee.toStringAsFixed(2)} DT/mois',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1A237E),
                    ),
                  ),
                ],
              ),
              SizedBox(
                width: 120,
                child: TextFormField(
                  controller: _feeController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    prefixText: 'DT ',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: Colors.grey[300]!),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(
                        color: Color(0xFF1A237E),
                        width: 2,
                      ),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 8,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(
                Icons.info_outline,
                size: 16,
                color: Colors.grey,
              ),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  'Les joueurs paieront ce montant pour rejoindre votre club',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ),
              TextButton.icon(
                onPressed: _updateSubscriptionFee,
                icon: const Icon(Icons.save, size: 16),
                label: const Text('Mettre à jour'),
                style: TextButton.styleFrom(
                  foregroundColor: const Color(0xFF1A237E),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Statistiques de revenus
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.withOpacity(0.05),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.green.withOpacity(0.2)),
            ),
            child: Row(
              children: [
                const Icon(Icons.trending_up, color: Colors.green),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Revenus potentiels',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey,
                        ),
                      ),
                      Text(
                        '${(widget.club.currentPlayers.length * widget.club.subscriptionFee).toStringAsFixed(2)} DT/mois',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.green,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '+${widget.club.currentPlayers.length} joueurs',
                    style: const TextStyle(
                      color: Colors.green,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}