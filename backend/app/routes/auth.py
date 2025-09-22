"""
Routes d'authentification - TODO Backend
"""

from flask import Blueprint, jsonify

# Créer le blueprint d'authentification
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Route d'inscription - À implémenter dans BE-AUTH-02"""
    return jsonify({
        'message': 'Registration endpoint - TODO: implement in BE-AUTH-02',
        'status': 'not_implemented'
    }), 501

@auth_bp.route('/login', methods=['POST'])
def login():
    """Route de connexion - À implémenter dans BE-AUTH-02"""
    return jsonify({
        'message': 'Login endpoint - TODO: implement in BE-AUTH-02',
        'status': 'not_implemented'
    }), 501

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Route de déconnexion - À implémenter dans BE-AUTH-02"""
    return jsonify({
        'message': 'Logout endpoint - TODO: implement in BE-AUTH-02',
        'status': 'not_implemented'
    }), 501

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Route de rafraîchissement de token - À implémenter dans BE-AUTH-02"""
    return jsonify({
        'message': 'Token refresh endpoint - TODO: implement in BE-AUTH-02',
        'status': 'not_implemented'
    }), 501