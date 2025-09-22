"""
Extensions Flask partagées
"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Instances partagées
db = SQLAlchemy()
bcrypt = Bcrypt()