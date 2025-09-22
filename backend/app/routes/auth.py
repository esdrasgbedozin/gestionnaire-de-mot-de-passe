"""
Routes d'authentification
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import re

from app.models import User, AuditLog
from extensions import db
from ..services.jwt_service import JWTService, token_required, TokenBlacklist

# Créer le blueprint d'authentification
auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Valider le format de l'email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valider la force du mot de passe"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

def log_audit_event(user_id, action, success, ip_address, user_agent, error_message=None):
    """Enregistrer un événement d'audit"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type='USER',
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        # Ne pas faire échouer la requête pour un problème d'audit
        print(f"Audit log error: {str(e)}")

@auth_bp.route('/register', methods=['POST'])
def register():
    """Route d'inscription"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation des champs requis
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Validation du format email
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validation de la force du mot de passe
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Log de tentative d'inscription avec email existant
            log_audit_event(
                user_id=None,
                action='REGISTER_FAILED',
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                error_message='Email already exists'
            )
            return jsonify({'error': 'Email already registered'}), 409
        
        # Créer le nouvel utilisateur
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        # Générer les tokens
        tokens = JWTService.generate_tokens(new_user)
        
        # Log de succès
        log_audit_event(
            user_id=new_user.id,
            action='REGISTER_SUCCESS',
            success=True,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'User registered successfully',
            'user': new_user.to_dict(),
            'tokens': tokens
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Email already registered'}), 409
    
    except Exception as e:
        db.session.rollback()
        log_audit_event(
            user_id=None,
            action='REGISTER_ERROR',
            success=False,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            error_message=str(e)
        )
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Route de connexion"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation des champs requis
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Chercher l'utilisateur
        user = User.query.filter_by(email=email).first()
        
        if not user:
            log_audit_event(
                user_id=None,
                action='LOGIN_FAILED',
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                error_message='User not found'
            )
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Vérifier si le compte est actif
        if not user.is_active:
            log_audit_event(
                user_id=user.id,
                action='LOGIN_FAILED',
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                error_message='Account disabled'
            )
            return jsonify({'error': 'Account is disabled'}), 401
        
        # Vérifier le verrouillage du compte
        if user.locked_until and datetime.utcnow() < user.locked_until:
            log_audit_event(
                user_id=user.id,
                action='LOGIN_FAILED',
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                error_message='Account locked'
            )
            return jsonify({'error': 'Account is temporarily locked'}), 401
        
        # Vérifier le mot de passe
        if not user.check_password(password):
            # Incrémenter le compteur d'échecs
            user.failed_login_attempts += 1
            
            # Verrouiller après 5 tentatives
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            
            db.session.commit()
            
            log_audit_event(
                user_id=user.id,
                action='LOGIN_FAILED',
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                error_message='Invalid password'
            )
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Connexion réussie - réinitialiser les compteurs
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Générer les tokens
        tokens = JWTService.generate_tokens(user)
        
        # Log de succès
        log_audit_event(
            user_id=user.id,
            action='LOGIN_SUCCESS',
            success=True,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'tokens': tokens
        }), 200
        
    except Exception as e:
        log_audit_event(
            user_id=None,
            action='LOGIN_ERROR',
            success=False,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            error_message=str(e)
        )
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user_id):
    """Route de déconnexion"""
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if auth_header else None
        
        if token:
            # Ajouter le token à la blacklist
            TokenBlacklist.add_token(token)
        
        # Log de déconnexion
        log_audit_event(
            user_id=current_user_id,
            action='LOGOUT_SUCCESS',
            success=True,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        log_audit_event(
            user_id=current_user_id,
            action='LOGOUT_ERROR',
            success=False,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            error_message=str(e)
        )
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Route de rafraîchissement de token"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        # Vérifier si le token est blacklisté
        if TokenBlacklist.is_blacklisted(refresh_token):
            return jsonify({'error': 'Token has been revoked'}), 401
        
        # Générer un nouveau token d'accès
        new_tokens, error = JWTService.refresh_access_token(refresh_token)
        
        if error:
            return jsonify({'error': error}), 401
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'tokens': new_tokens
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user_id):
    """Obtenir les informations de l'utilisateur connecté"""
    try:
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get user information'}), 500