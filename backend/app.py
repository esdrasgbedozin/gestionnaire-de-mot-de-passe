"""
Application principale Flask
"""

import os
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config
from extensions import db, bcrypt
from rate_limiter import setup_rate_limiting
from security_headers import setup_security_headers

# Initialisation des extensions
migrate = Migrate()
jwt = JWTManager()


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
    CORS(app, 
         origins=app.config['CORS_ORIGINS'], 
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Import des modèles (nécessaire pour les migrations)
    from app.models import User, Password, AuditLog
    
    # Enregistrement des blueprints
    from app.routes.auth import auth_bp
    from app.routes.passwords import passwords_bp
    from app.routes.users import users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(passwords_bp, url_prefix='/api/passwords')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # Route de santé pour Docker
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
    
    # Configurer le rate limiting
    app = setup_rate_limiting(app)
    
    # Configurer les headers de sécurité
    app = setup_security_headers(app)
    
    # Health check endpoints
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check complet pour la production"""
        start_time = time.time()
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'services': {},
            'response_time_ms': 0
        }
        
        try:
            # Test de la base de données
            db_start = time.time()
            try:
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                db_time = (time.time() - db_start) * 1000
                health_status['services']['database'] = {
                    'status': 'ok',
                    'response_time_ms': round(db_time, 2)
                }
            except Exception as e:
                health_status['services']['database'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_status['status'] = 'unhealthy'
                logger.error(f"Database health check failed: {e}")
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['error'] = str(e)
            logger.error(f"Health check failed: {e}")
        
        # Temps de réponse total
        health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        # Statut HTTP approprié
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code

    return app


if __name__ == '__main__':
    import time
    import logging
    
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Démarrage de l'application Password Manager...")
    
    app = create_app()
    
    # Attendre que la base de données soit disponible
    max_retries = 30
    for attempt in range(max_retries):
        try:
            with app.app_context():
                db.session.execute(db.text("SELECT 1"))
                db.session.commit()
                logger.info("✅ Connexion à la base de données réussie")
                break
        except Exception as e:
            logger.warning(f"⏳ Tentative {attempt + 1}/{max_retries}: Base de données non disponible - {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logger.error("❌ Impossible de se connecter à la base de données")
                exit(1)
    
    # Initialiser la base de données
    try:
        with app.app_context():
            db.create_all()
            logger.info("✅ Tables de base de données initialisées")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        exit(1)
    
    logger.info("🎉 Application prête à démarrer!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)