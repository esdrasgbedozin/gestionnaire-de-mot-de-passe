#!/usr/bin/env python3
"""
Script d'initialisation de la base de données
"""

import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

# Création d'une app Flask simple pour l'initialisation
app = Flask(__name__)
app.config.from_object(config['development'])

# Initialiser SQLAlchemy
db = SQLAlchemy()
db.init_app(app)

# Importer tous les modèles
from app.models import User, Password, AuditLog

def init_database():
    """Initialiser la base de données"""
    with app.app_context():
        try:
            # Créer toutes les tables
            db.create_all()
            print("✅ Base de données initialisée avec succès!")
            print("✅ Tables créées: users, passwords, audit_logs")
            
            # Vérifier les tables créées
            result = db.engine.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            tables = [row[0] for row in result]
            print(f"✅ Tables existantes: {', '.join(tables)}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    return True

if __name__ == "__main__":
    init_database()