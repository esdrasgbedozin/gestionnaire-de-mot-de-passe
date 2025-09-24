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
    username = db.Column(db.String(100), nullable=True, index=True)  # Nom d'utilisateur optionnel
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relation avec les mots de passe
    passwords = db.relationship('Password', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, email, password, username=None):
        self.email = email
        self.username = username
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convertir en dictionnaire (sans le mot de passe)"""
        return {
            'id': str(self.id),
            'email': self.email,
            'username': self.username,
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
    
    # Informations du site/service
    site_name = db.Column(db.String(255), nullable=False, index=True)
    site_url = db.Column(db.String(500), nullable=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    
    # Mot de passe chiffré
    encrypted_password = db.Column(db.Text, nullable=False)
    
    # Organisation et métadonnées
    category = db.Column(db.String(100), nullable=True, index=True)  # Personnel, Travail, Social, etc.
    tags = db.Column(db.String(500), nullable=True)  # Tags séparés par des virgules
    notes = db.Column(db.Text, nullable=True)
    
    # Favoris et priorité
    is_favorite = db.Column(db.Boolean, default=False, nullable=False, index=True)
    priority = db.Column(db.Integer, default=0)  # 0=normal, 1=important, 2=critique
    
    # Sécurité
    password_strength = db.Column(db.Integer, nullable=True)  # Score de 1 à 5
    requires_2fa = db.Column(db.Boolean, default=False)
    
    # Dates et usage
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Notifications et rappels
    expires_at = db.Column(db.DateTime, nullable=True)  # Date d'expiration du mot de passe
    remind_before_expiry = db.Column(db.Integer, default=30)  # Jours avant expiration pour rappel
    
    # Index composés pour optimiser les recherches
    __table_args__ = (
        db.Index('idx_user_category', 'user_id', 'category'),
        db.Index('idx_user_favorite', 'user_id', 'is_favorite'),
        db.Index('idx_user_site', 'user_id', 'site_name'),
    )
    
    def to_dict(self, include_password=False):
        """Convertir en dictionnaire"""
        data = {
            'id': self.id,
            'site_name': self.site_name,
            'site_url': self.site_url,
            'username': self.username,
            'email': self.email,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else [],
            'notes': self.notes,
            'is_favorite': self.is_favorite,
            'priority': self.priority,
            'password_strength': self.password_strength,
            'requires_2fa': self.requires_2fa,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'password_changed_at': self.password_changed_at.isoformat() if self.password_changed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'remind_before_expiry': self.remind_before_expiry
        }
        
        if include_password:
            # Le déchiffrement sera fait par le service de chiffrement
            data['encrypted_password'] = self.encrypted_password
        
        return data
    
    def set_tags(self, tags_list):
        """Définir les tags à partir d'une liste"""
        if isinstance(tags_list, list):
            self.tags = ','.join([tag.strip() for tag in tags_list if tag.strip()])
        else:
            self.tags = tags_list
    
    def get_tags(self):
        """Récupérer les tags sous forme de liste"""
        return self.tags.split(',') if self.tags else []


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