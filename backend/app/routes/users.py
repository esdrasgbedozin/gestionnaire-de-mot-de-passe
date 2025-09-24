"""
Routes de gestion des utilisateurs
"""

from flask import Blueprint, jsonify, request, g
from app.services.jwt_service import token_required
from app.models import User, db
from sqlalchemy.exc import SQLAlchemyError
from validators import validate_user_data as xss_validate_user, SecurityValidator
from rate_limiter import rate_limit_middleware
import logging

# Créer le blueprint de gestion des utilisateurs
users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Obtenir le profil utilisateur"""
    try:
        return jsonify({
            'user': {
                'id': current_user.id,
                'email': current_user.email,
                'created_at': current_user.created_at.isoformat(),
                'updated_at': current_user.updated_at.isoformat() if current_user.updated_at else None,
                'failed_login_attempts': current_user.failed_login_attempts,
                'is_active': current_user.is_active,
                'last_login': current_user.last_login.isoformat() if current_user.last_login else None
            },
            'status': 'success'
        }), 200
        
    except Exception as e:
        logging.error(f"Erreur lors de récupération profil: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur lors de récupération du profil',
            'status': 'error'
        }), 500

@users_bp.route('/profile', methods=['PUT'])
@rate_limit_middleware
@token_required
@xss_validate_user
def update_profile(current_user):
    """Modifier le profil utilisateur"""
    try:
        # Utiliser les données validées du décorateur XSS
        data = getattr(g, 'validated_data', None)
        
        # Fallback vers request.get_json() si pas de données validées
        if data is None:
            data = request.get_json()
            
        if not data:
            return jsonify({
                'error': 'Données JSON requises',
                'status': 'error'
            }), 400
            
        # Mise à jour des champs autorisés
        if 'email' in data:
            # Vérifier unicité de l'email
            existing_user = User.query.filter(
                User.email == data['email'],
                User.id != current_user.id
            ).first()
            if existing_user:
                return jsonify({
                    'error': 'Cette adresse email est déjà utilisée',
                    'status': 'error'
                }), 409
            current_user.email = data['email']
            
        # Mise à jour du username si fourni
        if 'username' in data:
            username = data['username'].strip() if data['username'] else None
            if username and len(username) > 100:
                return jsonify({
                    'error': 'Le nom d\'utilisateur est trop long (max 100 caractères)',
                    'status': 'error'
                }), 400
            current_user.username = username
            
        db.session.commit()
        
        return jsonify({
            'message': 'Profil mis à jour avec succès',
            'user': current_user.to_dict(),
            'status': 'success'
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Erreur base de données lors de mise à jour profil: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur lors de la mise à jour',
            'status': 'error'
        }), 500

@users_bp.route('/account', methods=['DELETE'])
@token_required
def delete_account(current_user):
    """Supprimer le compte utilisateur et toutes ses données"""
    try:
        # Supprimer l'utilisateur (les passwords et audit_logs seront supprimés en cascade)
        db.session.delete(current_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Compte supprimé avec succès',
            'status': 'success'
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Erreur base de données lors de suppression compte: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur lors de la suppression',
            'status': 'error'  
        }), 500