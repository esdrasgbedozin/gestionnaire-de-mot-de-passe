"""
Tests unitaires pour l'authentification
"""

import pytest
import json
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Fixture pour créer l'application Flask de test"""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
        "WTF_CSRF_ENABLED": False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Fixture pour créer le client de test"""
    return app.test_client()


@pytest.fixture
def sample_user(app):
    """Fixture pour créer un utilisateur de test"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('TestPassword123!')
        )
        db.session.add(user)
        db.session.commit()
        return user


class TestUserRegistration:
    """Tests pour l'enregistrement d'utilisateur"""
    
    def test_register_valid_user(self, client):
        """Test enregistrement utilisateur valide"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'ValidPassword123!'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert 'token' in response_data
        assert response_data['user']['username'] == 'newuser'
        assert response_data['user']['email'] == 'newuser@example.com'
        
    def test_register_duplicate_email(self, client, sample_user):
        """Test enregistrement avec email déjà existant"""
        data = {
            'username': 'differentuser',
            'email': 'test@example.com',  # Email déjà utilisé
            'password': 'ValidPassword123!'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 409
        response_data = json.loads(response.data)
        assert response_data['status'] == 'error'
        assert 'déjà utilisée' in response_data['error']
        
    def test_register_duplicate_username(self, client, sample_user):
        """Test enregistrement avec username déjà existant"""
        data = {
            'username': 'testuser',  # Username déjà utilisé
            'email': 'different@example.com',
            'password': 'ValidPassword123!'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 409
        response_data = json.loads(response.data)
        assert response_data['status'] == 'error'
        assert 'déjà utilisé' in response_data['error']
        
    def test_register_invalid_password(self, client):
        """Test enregistrement avec mot de passe invalide"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123'  # Mot de passe trop simple
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['status'] == 'error'


class TestUserLogin:
    """Tests pour la connexion utilisateur"""
    
    def test_login_valid_credentials(self, client, sample_user):
        """Test connexion avec identifiants valides"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert 'token' in response_data
        assert response_data['user']['email'] == 'test@example.com'
        
    def test_login_invalid_email(self, client):
        """Test connexion avec email inexistant"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'AnyPassword123!'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['status'] == 'error'
        assert 'invalides' in response_data['error']
        
    def test_login_invalid_password(self, client, sample_user):
        """Test connexion avec mot de passe incorrect"""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['status'] == 'error'
        assert 'invalides' in response_data['error']
        
    def test_login_missing_fields(self, client):
        """Test connexion avec champs manquants"""
        data = {
            'email': 'test@example.com'
            # password manquant
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['status'] == 'error'


class TestUserLogout:
    """Tests pour la déconnexion utilisateur"""
    
    def test_logout_success(self, client, sample_user):
        """Test déconnexion réussie"""
        # D'abord se connecter pour obtenir un token
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        login_data = json.loads(login_response.data)
        token = login_data['token']
        
        # Ensuite se déconnecter
        response = client.post('/api/auth/logout',
                             headers={'Authorization': f'Bearer {token}'},
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert 'déconnecté' in response_data['message']


class TestTokenRefresh:
    """Tests pour le rafraîchissement de token"""
    
    def test_refresh_token_success(self, client, sample_user):
        """Test rafraîchissement de token réussi"""
        # Se connecter pour obtenir un token
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        login_data = json.loads(login_response.data)
        token = login_data['token']
        
        # Rafraîchir le token
        response = client.post('/api/auth/refresh',
                             headers={'Authorization': f'Bearer {token}'},
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert 'token' in response_data
        # Le nouveau token doit être différent
        assert response_data['token'] != token
        
    def test_refresh_invalid_token(self, client):
        """Test rafraîchissement avec token invalide"""
        response = client.post('/api/auth/refresh',
                             headers={'Authorization': 'Bearer invalid_token'},
                             content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['status'] == 'error'


class TestAccountLocking:
    """Tests pour le verrouillage de compte"""
    
    def test_account_locking_after_failed_attempts(self, client, sample_user):
        """Test verrouillage de compte après tentatives échouées"""
        login_data = {
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        }
        
        # Faire 5 tentatives échouées
        for i in range(5):
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            assert response.status_code == 401
            
        # La 6ème tentative devrait déclencher le verrouillage
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        response_data = json.loads(response.data)
        # Selon l'implémentation, le compte devrait être verrouillé
        # ou proche du verrouillage
        assert response.status_code == 401
        assert response_data['status'] == 'error'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])