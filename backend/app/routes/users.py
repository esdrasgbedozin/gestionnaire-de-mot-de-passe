"""
Routes de gestion des utilisateurs
"""

from flask import Blueprint, jsonify, request, g, current_app
from app.services.jwt_service import token_required
from app.services.encryption_service import EncryptionService
from app.models import User, db
from sqlalchemy.exc import SQLAlchemyError
from validators import validate_user_data as xss_validate_user, SecurityValidator
from rate_limiter import rate_limit_middleware
import logging

# Créer le blueprint de gestion des utilisateurs
users_bp = Blueprint("users", __name__)


@users_bp.route("/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    """Obtenir le profil utilisateur"""
    try:
        return jsonify(
            {
                "user": {
                    "id": current_user.id,
                    "email": current_user.email,
                    "username": current_user.username,  # Ajouter le username
                    "created_at": current_user.created_at.isoformat(),
                    "updated_at": current_user.updated_at.isoformat()
                    if current_user.updated_at
                    else None,
                    "failed_login_attempts": current_user.failed_login_attempts,
                    "is_active": current_user.is_active,
                    "last_login": current_user.last_login.isoformat()
                    if current_user.last_login
                    else None,
                },
                "status": "success",
            }
        ), 200

    except Exception as e:
        logging.error(f"Erreur lors de récupération profil: {str(e)}")
        return jsonify(
            {
                "error": "Server error while retrieving profile",
            }
        ), 500


@users_bp.route("/profile", methods=["PUT"])
@rate_limit_middleware
@token_required
@xss_validate_user
def update_profile(current_user):
    """Modifier le profil utilisateur"""
    try:
        # Utiliser les données validées du décorateur XSS
        data = getattr(g, "validated_data", None)

        # Fallback vers request.get_json() si pas de données validées
        if data is None:
            data = request.get_json()

        if not data:
            return jsonify(
                {
                    "error": "JSON data required",
                }
            ), 400

        # Mise à jour des champs autorisés
        if "email" in data:
            # Vérifier unicité de l'email
            existing_user = User.query.filter(
                User.email == data["email"], User.id != current_user.id
            ).first()
            if existing_user:
                return jsonify(
                    {
                        "error": "Cette adresse email est déjà utilisée",
                        "status": "error",
                    }
                ), 409
            current_user.email = data["email"]

        # Mise à jour du username si fourni
        if "username" in data:
            username = data["username"].strip() if data["username"] else None
            if username and len(username) > 100:
                return jsonify(
                    {
                        "error": "Le nom d'utilisateur est trop long (max 100 caractères)",
                        "status": "error",
                    }
                ), 400
            current_user.username = username

        db.session.commit()

        return jsonify(
            {"message": "Profile updated successfully", "user": current_user.to_dict()}
        ), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Erreur base de données lors de mise à jour profil: {str(e)}")
        return jsonify({"error": "Server error during update", "status": "error"}), 500


@users_bp.route("/account", methods=["DELETE"])
@rate_limit_middleware
@token_required
def delete_account(current_user):
    """Supprimer le compte et TOUTES ses données (destruction irréversible).

    D2 : ré-auth FORTE avant toute destruction. Séquence critique
    prouver -> révoquer -> purger :
      (1) prouver l'identité par déballage de la VMK (ressaisie du master
          password, même mécanisme que le login H2.3 — identité prouvée
          FRAÎCHEMENT, pas via le token de session) + confirmation littérale
          "DELETE" (garde-fou anti-accident) ;
      (2) évincer la session courante ;
      (3) purger.
    On ne révoque/purge JAMAIS avant d'avoir prouvé, sinon on déconnecterait un
    utilisateur légitime dont la ré-auth échoue. Un token volé seul ne suffit
    plus. Le master password et le corps de la requête ne sont JAMAIS journalisés.
    """
    data = request.get_json(silent=True) or {}
    master_password = data.get("master_password")
    confirm = data.get("confirm")

    if not master_password:
        return jsonify(
            {"error": "Master password is required to delete the account"}
        ), 400

    # (1) Prouver l'identité : déballage VMK. unlock_vault paie Argon2id dans
    # TOUS les cas (dérivation KEK) avant l'échec GCM -> anti-timing (cf. D1/M2).
    try:
        EncryptionService.unlock_vault(
            current_user.kdf_salt, current_user.wrapped_vault_key, master_password
        )
    except ValueError:
        # Ne jamais logguer le master password / le corps de la requête.
        logging.warning(
            "Account deletion refused: re-auth failed (user_id=%s)", current_user.id
        )
        return jsonify({"error": "Invalid credentials"}), 401

    # Confirmation explicite APRÈS preuve d'identité (bloque l'accident, pas le vol).
    if confirm != "DELETE":
        return jsonify(
            {"error": 'Missing or invalid confirmation (expected "DELETE")'}
        ), 400

    try:
        # (2) Révoquer la session courante ; les autres sessions meurent avec la
        # suppression de la ligne User (token_required -> User introuvable -> 401).
        current_app.session_key_store.evict(g.session_id)
        # (3) Purger (passwords et audit_logs supprimés en cascade).
        db.session.delete(current_user)
        db.session.commit()

        return jsonify({"message": "Account deleted successfully"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Erreur base de données lors de suppression compte: {str(e)}")
        return jsonify(
            {"error": "Server error during deletion", "status": "error"}
        ), 500
