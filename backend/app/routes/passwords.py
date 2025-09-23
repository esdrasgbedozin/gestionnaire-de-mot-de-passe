"""
Routes pour la gestion des mots de passe - Version corrigée avec JWT personnalisé
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
import re

from app.models import Password, User, AuditLog, db
from app.services.encryption_service import EncryptionService
from app.services.password_generator import PasswordGenerator
from app.services.jwt_service import token_required

# Créer le blueprint
passwords_bp = Blueprint('passwords', __name__)


def log_audit_event(action, success=True, error_message=None, resource_id=None, user_id=None):
    """Enregistrer un événement d'audit"""
    try:
        if not user_id:
            # Essayer d'obtenir user_id du contexte de la requête si disponible
            user_id = getattr(request, 'current_user_id', None)
        
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Créer une nouvelle session pour l'audit
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type='PASSWORD',
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            timestamp=datetime.now(timezone.utc)
        )
        
        db.session.add(audit_entry)
        db.session.commit()
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'audit logging: {e}")


def validate_password_data(data, is_update=False):
    """Valider les données d'un mot de passe"""
    errors = []
    
    if not is_update or 'site_name' in data:
        if not data.get('site_name') or not data['site_name'].strip():
            errors.append("Le nom du site est obligatoire")
        elif len(data['site_name'].strip()) > 255:
            errors.append("Le nom du site ne peut pas dépasser 255 caractères")
    
    if not is_update or 'username' in data:
        if not data.get('username') or not data['username'].strip():
            errors.append("Le nom d'utilisateur est obligatoire")
        elif len(data['username'].strip()) > 255:
            errors.append("Le nom d'utilisateur ne peut pas dépasser 255 caractères")
    
    if not is_update or 'password' in data:
        if not data.get('password'):
            errors.append("Le mot de passe est obligatoire")
        elif len(data['password']) > 1000:  # Limite raisonnable pour un mot de passe
            errors.append("Le mot de passe est trop long")
    
    # Validation optionnelle
    if 'site_url' in data and data['site_url']:
        url_pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')
        if not url_pattern.match(data['site_url']):
            errors.append("L'URL du site n'est pas valide")
        elif len(data['site_url']) > 500:
            errors.append("L'URL ne peut pas dépasser 500 caractères")
    
    if 'email' in data and data['email']:
        email_pattern = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
        if not email_pattern.match(data['email']):
            errors.append("L'adresse email n'est pas valide")
        elif len(data['email']) > 255:
            errors.append("L'email ne peut pas dépasser 255 caractères")
    
    if 'category' in data and data['category'] and len(data['category']) > 100:
        errors.append("La catégorie ne peut pas dépasser 100 caractères")
    
    if 'notes' in data and data['notes'] and len(data['notes']) > 5000:
        errors.append("Les notes ne peuvent pas dépasser 5000 caractères")
    
    return errors


@passwords_bp.route('/', methods=['GET'])
@token_required
def get_passwords(current_user):
    """Récupérer la liste des mots de passe de l'utilisateur"""
    try:
        user_id = current_user.id
        
        # Paramètres de requête
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 par page
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        favorites_only = request.args.get('favorites', 'false').lower() == 'true'
        sort_by = request.args.get('sort', 'updated_at')
        sort_order = request.args.get('order', 'desc')
        
        # Construire la requête
        query = Password.query.filter(Password.user_id == user_id)
        
        # Filtres
        if search:
            search_filter = or_(
                Password.site_name.ilike(f'%{search}%'),
                Password.username.ilike(f'%{search}%'),
                Password.site_url.ilike(f'%{search}%'),
                Password.notes.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        if category:
            query = query.filter(Password.category == category)
        
        if favorites_only:
            query = query.filter(Password.is_favorite == True)
        
        # Tri
        if sort_by in ['site_name', 'username', 'category', 'created_at', 'updated_at', 'last_used']:
            order_column = getattr(Password, sort_by)
            if sort_order.lower() == 'desc':
                order_column = order_column.desc()
            query = query.order_by(order_column)
        
        # Pagination
        passwords_paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Convertir en dictionnaires (sans les mots de passe déchiffrés)
        passwords_data = [password.to_dict() for password in passwords_paginated.items]
        
        log_audit_event('LIST_PASSWORDS', user_id=user_id)
        
        return jsonify({
            'passwords': passwords_data,
            'pagination': {
                'page': passwords_paginated.page,
                'pages': passwords_paginated.pages,
                'per_page': passwords_paginated.per_page,
                'total': passwords_paginated.total,
                'has_next': passwords_paginated.has_next,
                'has_prev': passwords_paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        log_audit_event('LIST_PASSWORDS', success=False, error_message=str(e), user_id=user_id)
        current_app.logger.error(f"Erreur lors de la récupération des mots de passe: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@passwords_bp.route('/<string:password_id>', methods=['GET'])
@token_required
def get_password(current_user, password_id):
    """Récupérer un mot de passe spécifique (déchiffré)"""
    try:
        user_id = current_user.id
        
        # Récupérer le mot de passe
        password_entry = Password.query.filter(
            and_(Password.id == password_id, Password.user_id == user_id)
        ).first()
        
        if not password_entry:
            log_audit_event('VIEW_PASSWORD', success=False, error_message="Mot de passe non trouvé", resource_id=password_id, user_id=user_id)
            return jsonify({'error': 'Mot de passe non trouvé'}), 404
        
        # Déchiffrer le mot de passe
        try:
            user_key = EncryptionService.generate_user_key(user_id, "temp_key")  # À améliorer
            decrypted_password = EncryptionService.decrypt_password(
                password_entry.encrypted_password, 
                user_key
            )
        except Exception as decrypt_error:
            log_audit_event('VIEW_PASSWORD', success=False, error_message=f"Erreur déchiffrement: {str(decrypt_error)}", resource_id=password_id, user_id=user_id)
            return jsonify({'error': 'Impossible de déchiffrer le mot de passe'}), 500
        
        # Mettre à jour la date de dernière utilisation
        password_entry.last_used = datetime.now(timezone.utc)
        db.session.commit()
        
        # Retourner les données avec le mot de passe déchiffré
        password_data = password_entry.to_dict()
        password_data['password'] = decrypted_password
        
        log_audit_event('VIEW_PASSWORD', resource_id=password_id, user_id=user_id)
        
        return jsonify(password_data), 200
        
    except Exception as e:
        log_audit_event('VIEW_PASSWORD', success=False, error_message=str(e), resource_id=password_id, user_id=user_id)
        current_app.logger.error(f"Erreur lors de la récupération du mot de passe: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@passwords_bp.route('/', methods=['POST'])
@token_required
def create_password(current_user):
    """Créer un nouveau mot de passe"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        # Validation
        errors = validate_password_data(data)
        if errors:
            log_audit_event('CREATE_PASSWORD', success=False, error_message=f"Validation: {'; '.join(errors)}", user_id=user_id)
            return jsonify({'error': 'Données invalides', 'details': errors}), 400
        
        # Chiffrer le mot de passe
        try:
            user_key = EncryptionService.generate_user_key(user_id, "temp_key")  # À améliorer
            encrypted_password = EncryptionService.encrypt_password(data['password'], user_key)
        except Exception as encrypt_error:
            log_audit_event('CREATE_PASSWORD', success=False, error_message=f"Erreur chiffrement: {str(encrypt_error)}", user_id=user_id)
            return jsonify({'error': 'Erreur lors du chiffrement'}), 500
        
        # Évaluer la force du mot de passe
        strength_info = PasswordGenerator.evaluate_strength(data['password'])
        
        # Créer l'entrée
        password_entry = Password(
            user_id=user_id,
            site_name=data['site_name'].strip(),
            site_url=data.get('site_url', '').strip() or None,
            username=data['username'].strip(),
            email=data.get('email', '').strip() or None,
            encrypted_password=encrypted_password,
            category=data.get('category', '').strip() or None,
            notes=data.get('notes', '').strip() or None,
            is_favorite=data.get('is_favorite', False),
            priority=data.get('priority', 0),
            password_strength=strength_info['strength'],
            requires_2fa=data.get('requires_2fa', False),
            password_changed_at=datetime.now(timezone.utc)
        )
        
        # Gérer les tags
        if 'tags' in data:
            password_entry.set_tags(data['tags'])
        
        db.session.add(password_entry)
        db.session.commit()
        
        log_audit_event('CREATE_PASSWORD', resource_id=password_entry.id, user_id=user_id)
        
        return jsonify({
            'message': 'Mot de passe créé avec succès',
            'password': password_entry.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        log_audit_event('CREATE_PASSWORD', success=False, error_message="Violation contrainte base de données", user_id=user_id)
        return jsonify({'error': 'Erreur de contrainte de base de données'}), 400
    except Exception as e:
        db.session.rollback()
        log_audit_event('CREATE_PASSWORD', success=False, error_message=str(e), user_id=user_id)
        current_app.logger.error(f"Erreur lors de la création du mot de passe: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@passwords_bp.route('/generate', methods=['POST'])
@token_required
def generate_password(current_user):
    """Générer un nouveau mot de passe"""
    try:
        user_id = current_user.id
        data = request.get_json() or {}
        
        # Paramètres par défaut
        length = data.get('length', 16)
        include_uppercase = data.get('include_uppercase', True)
        include_lowercase = data.get('include_lowercase', True)
        include_digits = data.get('include_digits', True)
        include_special = data.get('include_special', True)
        
        # Générer le mot de passe
        result = PasswordGenerator.generate(
            length=length,
            include_uppercase=include_uppercase,
            include_lowercase=include_lowercase,
            include_digits=include_digits,
            include_special=include_special
        )
        
        log_audit_event('GENERATE_PASSWORD', user_id=user_id)
        
        return jsonify(result), 200
        
    except ValueError as e:
        log_audit_event('GENERATE_PASSWORD', success=False, error_message=str(e), user_id=user_id)
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        log_audit_event('GENERATE_PASSWORD', success=False, error_message=str(e), user_id=user_id)
        current_app.logger.error(f"Erreur lors de la génération de mot de passe: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@passwords_bp.route('/categories', methods=['GET'])
@token_required
def get_categories(current_user):
    """Récupérer les catégories avec statistiques"""
    try:
        user_id = current_user.id
        
        # Requête pour compter les mots de passe par catégorie
        categories_query = db.session.query(
            Password.category,
            db.func.count(Password.id).label('count')
        ).filter(
            Password.user_id == user_id,
            Password.category.isnot(None),
            Password.category != ''
        ).group_by(Password.category).order_by(Password.category).all()
        
        categories = [
            {'category': cat.category, 'count': cat.count}
            for cat in categories_query
        ]
        
        log_audit_event('LIST_CATEGORIES', user_id=user_id)
        
        return jsonify({'categories': categories}), 200
        
    except Exception as e:
        log_audit_event('LIST_CATEGORIES', success=False, error_message=str(e), user_id=user_id)
        current_app.logger.error(f"Erreur lors de la récupération des catégories: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@passwords_bp.route('/presets', methods=['GET'])
@token_required
def get_presets(current_user):
    """Récupérer les presets de génération de mots de passe"""
    try:
        user_id = current_user.id
        presets = PasswordGenerator.get_presets()
        
        log_audit_event('GET_PRESETS', user_id=user_id)
        
        return jsonify({'presets': presets}), 200
        
    except Exception as e:
        log_audit_event('GET_PRESETS', success=False, error_message=str(e), user_id=user_id)
        current_app.logger.error(f"Erreur lors de la récupération des presets: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@passwords_bp.route('/strength', methods=['POST'])
@token_required
def evaluate_password_strength(current_user):
    """Évaluer la force d'un mot de passe"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        if not data or 'password' not in data:
            return jsonify({'error': 'Mot de passe requis'}), 400
        
        result = PasswordGenerator.evaluate_strength(data['password'])
        
        log_audit_event('EVALUATE_STRENGTH', user_id=user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        log_audit_event('EVALUATE_STRENGTH', success=False, error_message=str(e), user_id=user_id)
        current_app.logger.error(f"Erreur lors de l'évaluation de la force: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@passwords_bp.route('/<string:password_id>', methods=['PUT'])
@token_required
def update_password(current_user, password_id):
    """Mettre à jour un mot de passe existant"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        # Valider les données (mise à jour partielle autorisée)
        validation_error = validate_password_data(data, is_update=True)
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        # Vérifier que le mot de passe appartient à l'utilisateur
        password_obj = Password.query.filter_by(
            id=password_id,
            user_id=user_id
        ).first()
        
        if not password_obj:
            log_audit_event('UPDATE_PASSWORD', success=False, 
                          error_message='Mot de passe non trouvé', 
                          resource_id=password_id, user_id=user_id)
            return jsonify({'error': 'Mot de passe non trouvé'}), 404
        
        # Mettre à jour les champs fournis
        if 'site_name' in data:
            password_obj.site_name = data['site_name']
        if 'username' in data:
            password_obj.username = data['username']
        if 'site_url' in data:
            password_obj.site_url = data.get('site_url', '')
        if 'category' in data:
            password_obj.category = data.get('category', 'personal')
        if 'notes' in data:
            password_obj.notes = data.get('notes', '')
        if 'email' in data:
            password_obj.email = data.get('email', '')
        if 'requires_2fa' in data:
            password_obj.requires_2fa = data.get('requires_2fa', False)
        if 'is_favorite' in data:
            password_obj.is_favorite = data.get('is_favorite', False)
        
        # Si le mot de passe est modifié, le chiffrer et calculer la force
        if 'password' in data:
            try:
                user_key = EncryptionService.generate_user_key(str(user_id), "temp_key")  # À améliorer
                encrypted_password = EncryptionService.encrypt_password(data['password'], user_key)
                password_obj.encrypted_password = encrypted_password
                
                strength_info = PasswordGenerator.evaluate_strength(data['password'])
                password_obj.password_strength = strength_info['strength']
                password_obj.password_changed_at = datetime.now(timezone.utc)
            except Exception as encrypt_error:
                log_audit_event('UPDATE_PASSWORD', success=False, error_message=f"Erreur chiffrement: {str(encrypt_error)}", 
                               resource_id=password_id, user_id=user_id)
                return jsonify({'error': 'Erreur lors du chiffrement'}), 500
        
        password_obj.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        log_audit_event('UPDATE_PASSWORD', resource_id=password_id, user_id=user_id)
        
        # Retourner le mot de passe mis à jour (sans le déchiffrer pour la sécurité)
        password_dict = {
            'id': password_obj.id,
            'site_name': password_obj.site_name,
            'username': password_obj.username,
            'site_url': password_obj.site_url,
            'category': password_obj.category,
            'notes': password_obj.notes,
            'email': password_obj.email,
            'password_strength': password_obj.password_strength,
            'requires_2fa': password_obj.requires_2fa,
            'is_favorite': password_obj.is_favorite,
            'created_at': password_obj.created_at.isoformat(),
            'updated_at': password_obj.updated_at.isoformat(),
            'password_changed_at': password_obj.password_changed_at.isoformat() if password_obj.password_changed_at else None,
            'last_used': password_obj.last_used.isoformat() if password_obj.last_used else None,
        }
        
        return jsonify({
            'message': 'Mot de passe mis à jour avec succès',
            'password': password_dict
        }), 200
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('UPDATE_PASSWORD', success=False, error_message=str(e), 
                       resource_id=password_id, user_id=user_id)
        current_app.logger.error(f"Erreur lors de la mise à jour du mot de passe: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@passwords_bp.route('/<string:password_id>', methods=['DELETE'])
@token_required
def delete_password(current_user, password_id):
    """Supprimer un mot de passe"""
    try:
        user_id = current_user.id
        
        # Vérifier que le mot de passe appartient à l'utilisateur
        password_obj = Password.query.filter_by(
            id=password_id,
            user_id=user_id
        ).first()
        
        if not password_obj:
            log_audit_event('DELETE_PASSWORD', success=False, 
                          error_message='Mot de passe non trouvé', 
                          resource_id=password_id, user_id=user_id)
            return jsonify({'error': 'Mot de passe non trouvé'}), 404
        
        db.session.delete(password_obj)
        db.session.commit()
        
        log_audit_event('DELETE_PASSWORD', resource_id=password_id, user_id=user_id)
        
        return jsonify({'message': 'Mot de passe supprimé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('DELETE_PASSWORD', success=False, error_message=str(e), 
                       resource_id=password_id, user_id=user_id)
        current_app.logger.error(f"Erreur lors de la suppression du mot de passe: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500