"""
Version simplifiée du service JWT pour déboguer
"""

import jwt
from datetime import datetime, timedelta
import os

class SimpleJWTService:
    """Service JWT simplifié"""
    
    @staticmethod
    def get_secret_key():
        """Obtenir la clé secrète"""
        return os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key_change_in_production')
    
    @staticmethod
    def generate_tokens(user):
        """Générer les tokens d'accès et de rafraîchissement"""
        now = datetime.utcnow()
        secret = SimpleJWTService.get_secret_key()
        
        # Token d'accès (15 minutes)
        access_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'iat': now,
            'exp': now + timedelta(minutes=15),
            'type': 'access'
        }
        
        # Token de rafraîchissement (7 jours)
        refresh_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'iat': now,
            'exp': now + timedelta(days=7),
            'type': 'refresh'
        }
        
        access_token = jwt.encode(access_payload, secret, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, secret, algorithm='HS256')
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 900,  # 15 minutes en secondes
            'expires_at': (now + timedelta(minutes=15)).isoformat()
        }