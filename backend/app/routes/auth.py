"""
Routes d'authentification
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import re

from app.models import User, AuditLog
from extensions import db  # Import de l'instance db partagée
# from ..services.jwt_service import JWTService, token_required, TokenBlacklist
from simple_jwt import SimpleJWTService  # Service JWT simplifié pour débogger

# Créer le blueprint d'authentification
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/debug', methods=['GET'])
def debug():
    """Route de debug pour tester le blueprint"""
    return jsonify({'message': 'Debug endpoint works!', 'status': 'ok'}), 200

@auth_bp.route('/test-db', methods=['GET'])
def test_db():
    """Tester la connexion à la base de données"""
    try:
        # Test de comptage d'utilisateurs
        user_count = User.query.count()
        return jsonify({'message': 'Database connected', 'user_count': user_count}), 200
    except Exception as e:
        return jsonify({'error': f'Database connection failed: {str(e)}'}), 500

@auth_bp.route('/test-simple-register', methods=['POST'])
def test_simple_register():
    """Version de test ultra-simplifiée de l'inscription"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Missing email or password'}), 400
        
        # Vérifier si l'utilisateur existe
        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({'error': 'User exists'}), 409
        
        # Créer l'utilisateur
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User created', 'user_id': user.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Test registration failed: {str(e)}'}), 500

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
    """Route d'inscription - version debug"""
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
            return jsonify({'error': 'Email already registered'}), 409
        
        # Créer le nouvel utilisateur
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        # Générer les tokens
        tokens = SimpleJWTService.generate_tokens(new_user)
        
        # Pas d'audit log pour le moment pour débogger
        
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
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

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
        tokens = SimpleJWTService.generate_tokens(user)
        
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

"""
@auth_bp.route('/logout', methods=['POST'])
# @token_required  # Temporairement désactivé
def logout():  # current_user_id
    \"\"\"Route de déconnexion - temporairement désactivée\"\"\"
    return jsonify({'message': 'Logout endpoint - temporarily disabled for testing'}), 501

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    \"\"\"Route de rafraîchissement de token - temporairement désactivée\"\"\"
    return jsonify({'message': 'Refresh endpoint - temporarily disabled for testing'}), 501

@auth_bp.route('/me', methods=['GET'])
# @token_required  # Temporairement désactivé
def get_current_user():  # current_user_id
    \"\"\"Obtenir les informations de l'utilisateur connecté - temporairement désactivé\"\"\"
    return jsonify({'message': 'Me endpoint - temporarily disabled for testing'}), 501
"""