"""
Routes d'authentification
"""

from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
import re

import uuid
from app.models import User, AuditLog
from app.services.encryption_service import EncryptionService
from extensions import db
from ..services.jwt_service import JWTService, token_required
from validators import validate_user_data as xss_validate_user, SecurityValidator
from rate_limiter import rate_limit_middleware

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
    """Enregistrer un événement d'audit avec session séparée"""
    try:
        # Utiliser une session séparée pour éviter les conflits
        from extensions import db
        
        # Convertir user_id en string si c'est un UUID
        user_id_str = str(user_id) if user_id else None
        
        # Créer une nouvelle session pour l'audit
        audit_session = db.session
        
        audit_log = AuditLog(
            user_id=user_id_str,
            action=action,
            resource_type='USER',
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        audit_session.add(audit_log)
        audit_session.commit()
        
    except Exception as e:
        # Ne pas faire échouer la requête principale pour un problème d'audit
        try:
            audit_session.rollback()
        except:
            pass
        # Log l'erreur d'audit en mode silencieux
        print(f"Audit log error (non-critical): {str(e)}")

@auth_bp.route('/register', methods=['POST'])
@rate_limit_middleware
@xss_validate_user
def register():
    """Route d'inscription"""
    try:
        # Utiliser les données validées du décorateur XSS
        data = getattr(g, 'validated_data', None)
        
        # Fallback vers request.get_json() si pas de données validées
        if data is None:
            data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        username = data.get('username', '').strip() if data.get('username') else None
        
        # Validation des champs requis
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Validation du format email
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validation du username s'il est fourni
        if username and len(username) > 100:
            return jsonify({'error': 'Username too long (max 100 characters)'}), 400
        
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
        
        # Unicité du username (Q5)
        if username and User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409
        
        # Créer le nouvel utilisateur + provisionner son coffre (zero-knowledge, C1)
        new_user = User(email=email, username=username)
        kdf_salt, wrapped_vmk, vmk = EncryptionService.provision_vault(password)
        new_user.kdf_salt = kdf_salt
        new_user.wrapped_vault_key = wrapped_vmk
        db.session.add(new_user)
        db.session.commit()
        
        # Créer la session stable + ancrer la VMK (jamais recopiée)
        session_id = str(uuid.uuid4())
        current_app.session_key_store.store_session(
            session_id, vmk,
            current_app.config['VAULT_SESSION_IDLE_TTL_SECONDS'],
            current_app.config['VAULT_SESSION_ABSOLUTE_TTL_SECONDS'])
        tokens, refresh_jti = JWTService.generate_tokens(new_user, session_id)
        current_app.refresh_registry.register(
            refresh_jti, session_id,
            current_app.config['VAULT_SESSION_ABSOLUTE_TTL_SECONDS'])
        
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
@rate_limit_middleware
@xss_validate_user
def login():
    """Route de connexion"""
    try:
        # Utiliser les données validées du décorateur XSS
        data = getattr(g, 'validated_data', None)
        
        # Fallback vers request.get_json() si pas de données validées
        if data is None:
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
            # Anti-énumération par timing (Q3) : payer le coût Argon2id même sans compte
            EncryptionService.waste_argon2()
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
        
        # Vérifier le verrouillage du compte (comparaison timezone-safe — Bug A)
        locked_until = user.locked_until
        if locked_until is not None and locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until is not None and datetime.now(timezone.utc) < locked_until:
            log_audit_event(
                user_id=user.id,
                action='LOGIN_FAILED',
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                error_message='Account locked'
            )
            return jsonify({'error': 'Account is temporarily locked'}), 401
        
        # Authentification = déballage de la VMK : l'identité est prouvée par un tag
        # GCM valide (plus de hash bcrypt séparé) — Lot 4/H2.3, décision 1.
        try:
            vmk = EncryptionService.unlock_vault(
                user.kdf_salt, user.wrapped_vault_key, password)
        except ValueError:
            # Mauvais master password → échec d'auth : compteur + verrouillage
            try:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
                db.session.commit()
            except Exception:
                db.session.rollback()
            log_audit_event(
                user_id=user.id,
                action='LOGIN_FAILED',
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                error_message='Invalid password'
            )
            return jsonify({'error': 'Invalid credentials'}), 401

        # Succès : réinitialiser les compteurs
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        # Créer la session stable + ancrer la VMK (jamais recopiée)
        session_id = str(uuid.uuid4())
        current_app.session_key_store.store_session(
            session_id, vmk,
            current_app.config['VAULT_SESSION_IDLE_TTL_SECONDS'],
            current_app.config['VAULT_SESSION_ABSOLUTE_TTL_SECONDS'])
        tokens, refresh_jti = JWTService.generate_tokens(user, session_id)
        current_app.refresh_registry.register(
            refresh_jti, session_id,
            current_app.config['VAULT_SESSION_ABSOLUTE_TTL_SECONDS'])
        
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
@rate_limit_middleware
@token_required
def logout(current_user_id):
    """Route de déconnexion"""
    try:
        # Révoquer la session : supprime session:{sid} → VMK évincée + famille morte
        current_app.session_key_store.evict(g.session_id)
        
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
@rate_limit_middleware
def refresh():
    """Route de rafraîchissement de token"""
    try:
        data = request.get_json(silent=True) or {}   # Bug B : corps vide/malformé → 400

        refresh_token = data.get('refresh_token')
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400

        payload, decode_err = JWTService.decode_token(refresh_token)
        if decode_err:
            return jsonify({'error': decode_err}), 401       # token invalide → 401
        if payload.get('type') != 'refresh':
            return jsonify({'error': 'Invalid token type'}), 401

        sid = payload.get('sid')
        old_jti = payload.get('jti')
        store = current_app.session_key_store
        if not sid or not store.session_exists(sid):
            return jsonify({'error': 'Session expired or revoked'}), 401

        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 401

        # Nouveau couple de tokens (même session, VMK inchangée)
        tokens, new_jti = JWTService.generate_tokens(user, sid)

        # Rotation ATOMIQUE : consomme old_jti et publie new_jti (RENAME)
        if current_app.refresh_registry.rotate(old_jti, new_jti):
            return jsonify({'message': 'Token refreshed successfully', 'tokens': tokens}), 200

        # old_jti déjà consommé → REJEU (vol présumé) → révoquer toute la session
        store.evict(sid)
        return jsonify({'error': 'Refresh token reuse detected; session revoked'}), 401
        
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