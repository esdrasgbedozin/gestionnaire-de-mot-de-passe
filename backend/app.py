"""
Application principale Flask
"""

import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from config import config

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()


def create_app(config_name=None):
    """Factory pour créer l'application Flask"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    # Configuration CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Import des modèles (nécessaire pour les migrations)
    from app.models import User, Password
    
    # Enregistrement des blueprints
    from app.routes.auth import auth_bp
    from app.routes.passwords import passwords_bp
    from app.routes.users import users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(passwords_bp, url_prefix='/api/passwords')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # Route de santé pour Docker
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Password Manager API is running'})
    
    # Route de base
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Password Manager API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'passwords': '/api/passwords',
                'users': '/api/users',
                'health': '/health'
            }
        })
    
    # Gestionnaire d'erreurs JWT
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'message': 'Authorization token is required'}), 401
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)