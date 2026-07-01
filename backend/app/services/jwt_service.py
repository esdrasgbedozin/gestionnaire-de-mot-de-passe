"""
Service de gestion des tokens JWT
"""

import uuid
import jwt
from datetime import datetime, timedelta
from flask import current_app, request, jsonify, g
from functools import wraps


class JWTService:
    """Service pour gérer les tokens JWT"""

    @staticmethod
    def generate_tokens(user, session_id):
        """Générer (tokens, refresh_jti) rattachés à une session stable (sid)."""
        now = datetime.utcnow()

        access_payload = {
            "user_id": str(user.id),
            "email": user.email,
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "type": "access",
            "sid": session_id,
            "jti": str(uuid.uuid4()),
        }

        refresh_jti = str(uuid.uuid4())
        refresh_payload = {
            "user_id": str(user.id),
            "email": user.email,
            "iat": now,
            "exp": now + timedelta(days=7),
            "type": "refresh",
            "sid": session_id,
            "jti": refresh_jti,
        }

        access_token = jwt.encode(
            access_payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256"
        )
        refresh_token = jwt.encode(
            refresh_payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256"
        )

        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 900,  # 15 minutes
            "expires_at": (now + timedelta(minutes=15)).isoformat(),
        }
        return tokens, refresh_jti

    @staticmethod
    def decode_token(token):
        """Décoder et valider un token (algorithme épinglé HS256)."""
        try:
            payload = jwt.decode(
                token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
            return payload, None
        except jwt.ExpiredSignatureError:
            return None, "Token expired"
        except jwt.InvalidTokenError as e:
            return None, f"Invalid token: {str(e)}"



def token_required(f):
    """Décorateur protégeant les routes : token valide ET session encore active.

    À CHAQUE requête authentifiée, on vérifie que `session:{sid}` existe encore
    dans Redis (révocation par session). Un token JWT non expiré dont la session
    a été supprimée est donc refusé (401). C'est ce qui rend toute blacklist de
    tokens superflue.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header:
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"error": "Invalid authorization header format"}), 401
        if not token:
            return jsonify({"error": "Token is missing"}), 401

        payload, error = JWTService.decode_token(token)
        if error:
            return jsonify({"error": error}), 401
        if payload.get("type") != "access":
            return jsonify({"error": "Invalid token type"}), 401

        # Pivot du modèle de révocation : la session doit encore exister.
        sid = payload.get("sid")
        store = current_app.session_key_store
        if not sid or not store.session_exists(sid):
            return jsonify({"error": "Session expired or revoked"}), 401
        # Inactivité glissante : ré-armer le TTL à chaque requête.
        store.touch(sid, current_app.config["VAULT_SESSION_IDLE_TTL_SECONDS"])
        g.session_id = sid

        from app.models import User

        current_user = User.query.get(payload["user_id"])
        if not current_user:
            return jsonify({"error": "User not found"}), 401

        return f(current_user, *args, **kwargs)

    return decorated
