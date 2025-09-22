"""
Service de gestion des tokens JWT
"""

import jwt
from datetime import datetime, timedelta
from flask import current_app
from functools import wraps
from flask import request, jsonify


class JWTService:
    """Service pour gérer les tokens JWT"""
    
    @staticmethod
    def generate_tokens(user):
        """Générer les tokens d'accès et de rafraîchissement"""
        now = datetime.utcnow()
        
        # Token d'accès (15 minutes)
        access_payload = {
            'user_id': user.id,
            'email': user.email,
            'iat': now,
            'exp': now + timedelta(minutes=15),
            'type': 'access'
        }
        
        # Token de rafraîchissement (7 jours)
        refresh_payload = {
            'user_id': user.id,
            'email': user.email,
            'iat': now,
            'exp': now + timedelta(days=7),
            'type': 'refresh'
        }
        
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 900,  # 15 minutes en secondes
            'expires_at': (now + timedelta(minutes=15)).isoformat()
        }
    
    @staticmethod
    def decode_token(token):
        """Décoder et valider un token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload, None
        except jwt.ExpiredSignatureError:
            return None, 'Token expired'
        except jwt.InvalidTokenError as e:
            return None, f'Invalid token: {str(e)}'
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """Générer un nouveau token d'accès à partir du refresh token"""
        payload, error = JWTService.decode_token(refresh_token)
        
        if error:
            return None, error
            
        if payload.get('type') != 'refresh':
            return None, 'Invalid token type'
        
        # Créer un nouveau token d'accès
        now = datetime.utcnow()
        access_payload = {
            'user_id': payload['user_id'],
            'email': payload['email'],
            'iat': now,
            'exp': now + timedelta(minutes=15),
            'type': 'access'
        }
        
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 900,  # 15 minutes
            'expires_at': (now + timedelta(minutes=15)).isoformat()
        }, None


def token_required(f):
    """Décorateur pour protéger les routes avec JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                # Format: "Bearer <token>"
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload, error = JWTService.decode_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        if payload.get('type') != 'access':
            return jsonify({'error': 'Invalid token type'}), 401
        
        # Ajouter l'utilisateur actuel au contexte
        current_user_id = payload['user_id']
        
        return f(current_user_id=current_user_id, *args, **kwargs)
    
    return decorated


# Service de blacklist des tokens (pour logout)
class TokenBlacklist:
    """Service simple de blacklist des tokens (en mémoire)"""
    
    _blacklisted_tokens = set()
    
    @classmethod
    def add_token(cls, token):
        """Ajouter un token à la blacklist"""
        cls._blacklisted_tokens.add(token)
    
    @classmethod
    def is_blacklisted(cls, token):
        """Vérifier si un token est blacklisté"""
        return token in cls._blacklisted_tokens
    
    @classmethod
    def clear_expired(cls):
        """Nettoyer les tokens expirés (à implémenter avec Redis en production)"""
        # En production, utiliser Redis avec TTL automatique
        pass