#!/usr/bin/env python3
"""
Migration pour ajouter la colonne username à la table users
"""

import sys
import os
from flask import Flask
from sqlalchemy import text
from extensions import db

def create_app():
    """Créer l'application Flask pour la migration"""
    app = Flask(__name__)
    
    # Configuration de base pour la migration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://password_manager:password123@db:5432/password_manager')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialiser les extensions
    db.init_app(app)
    
    return app

def add_username_column():
    """Ajouter la colonne username à la table users si elle n'existe pas déjà"""
    app = create_app()
    
    with app.app_context():
        try:
            # Vérifier si la colonne existe déjà
            result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='username'"))
            if result.fetchone():
                print("✅ La colonne 'username' existe déjà.")
                return True
            
            # Ajouter la colonne username
            db.session.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(100)"))
            db.session.commit()
            print("✅ Colonne 'username' ajoutée avec succès à la table 'users'.")
            
            # Créer un index sur username pour les performances
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"))
            db.session.commit()
            print("✅ Index sur 'username' créé avec succès.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la migration: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🔄 Début de la migration pour ajouter la colonne username...")
    success = add_username_column()
    if success:
        print("✅ Migration terminée avec succès.")
    else:
        print("❌ La migration a échoué.")
        sys.exit(1)