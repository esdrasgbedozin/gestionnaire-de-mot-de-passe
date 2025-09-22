"""
Modèles de données pour le gestionnaire de mots de passe
"""

from datetime import datetime
import uuid
from extensions import db, bcrypt


class User(db.Model):
    """Modèle pour les utilisateurs"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relation avec les mots de passe
    passwords = db.relationship('Password', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, email, password):
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convertir en dictionnaire (sans le mot de passe)"""
        return {
            'id': str(self.id),
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Password(db.Model):
    """Modèle pour les mots de passe stockés"""
    
    __tablename__ = 'passwords'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    site_name = db.Column(db.String(255), nullable=False)
    site_url = db.Column(db.String(500), nullable=True)
    username = db.Column(db.String(255), nullable=False)
    encrypted_password = db.Column(db.Text, nullable=False)  # Mot de passe chiffré
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self, include_password=False):
        """Convertir en dictionnaire"""
        data = {
            'id': self.id,
            'site_name': self.site_name,
            'site_url': self.site_url,
            'username': self.username,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }
        
        if include_password:
            # Le déchiffrement sera fait par le service de chiffrement
            data['encrypted_password'] = self.encrypted_password
        
        return data


class AuditLog(db.Model):
    """Journal d'audit pour tracer les opérations sensibles"""
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)  # LOGIN, CREATE_PASSWORD, UPDATE_PASSWORD, etc.
    resource_type = db.Column(db.String(50), nullable=True)  # USER, PASSWORD
    resource_id = db.Column(db.String(36), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    user_agent = db.Column(db.Text, nullable=True)
    success = db.Column(db.Boolean, default=True, nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'success': self.success,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }