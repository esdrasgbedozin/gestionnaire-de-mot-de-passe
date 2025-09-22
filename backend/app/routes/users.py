"""
Routes de gestion des utilisateurs - TODO Backend
"""

from flask import Blueprint, jsonify

# Créer le blueprint de gestion des utilisateurs
users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
def get_profile():
    """Obtenir le profil utilisateur - À implémenter dans BE-PROF-01"""
    return jsonify({
        'message': 'Get user profile endpoint - TODO: implement in BE-PROF-01',
        'status': 'not_implemented'
    }), 501

@users_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Modifier le profil utilisateur - À implémenter dans BE-PROF-01"""
    return jsonify({
        'message': 'Update user profile endpoint - TODO: implement in BE-PROF-01',
        'status': 'not_implemented'
    }), 501

@users_bp.route('/account', methods=['DELETE'])
def delete_account():
    """Supprimer le compte utilisateur - À implémenter dans BE-PROF-04"""
    return jsonify({
        'message': 'Delete user account endpoint - TODO: implement in BE-PROF-04',
        'status': 'not_implemented'
    }), 501