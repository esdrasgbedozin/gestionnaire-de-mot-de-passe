"""
Routes de gestion des utilisateurs
"""

from flask import Blueprint, jsonify, request
from app.services.jwt_service import token_required
from app.models import User, db
from sqlalchemy.exc import SQLAlchemyError
import logging

# Créer le blueprint de gestion des utilisateurs
users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    """Obtenir le profil utilisateur"""
    try:
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'error': 'Utilisateur non trouvé',
                'status': 'error'
            }), 404
            
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                'login_attempts': user.login_attempts,
                'is_locked': user.is_locked,
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            'status': 'success'
        }), 200
        
    except SQLAlchemyError as e:
        logging.error(f"Erreur base de données lors de récupération profil: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur lors de récupération du profil',
            'status': 'error'
        }), 500

@users_bp.route('/profile', methods=['PUT'])
@token_required  
def update_profile(current_user_id):
    """Modifier le profil utilisateur"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Données JSON requises',
                'status': 'error'
            }), 400
            
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'error': 'Utilisateur non trouvé',
                'status': 'error' 
            }), 404
            
        # Mise à jour des champs autorisés
        if 'username' in data:
            # Vérifier unicité du username
            existing_user = User.query.filter(
                User.username == data['username'], 
                User.id != current_user_id
            ).first()
            if existing_user:
                return jsonify({
                    'error': 'Ce nom d\'utilisateur est déjà utilisé',
                    'status': 'error'
                }), 409
            user.username = data['username']
            
        if 'email' in data:
            # Vérifier unicité de l'email
            existing_user = User.query.filter(
                User.email == data['email'],
                User.id != current_user_id
            ).first()
            if existing_user:
                return jsonify({
                    'error': 'Cette adresse email est déjà utilisée',
                    'status': 'error'
                }), 409
            user.email = data['email']
            
        db.session.commit()
        
        return jsonify({
            'message': 'Profil mis à jour avec succès',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'updated_at': user.updated_at.isoformat()
            },
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
def delete_account(current_user_id):
    """Supprimer le compte utilisateur et toutes ses données"""
    try:
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'error': 'Utilisateur non trouvé',
                'status': 'error'
            }), 404
            
        # Supprimer l'utilisateur (les passwords et audit_logs seront supprimés en cascade)
        db.session.delete(user)
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