"""
Point d'entrée WSGI pour gunicorn (production).

Le dossier backend/ contient à la fois le module `app.py` et le package `app/`.
Python privilégiant le package lors de `import app`, la factory `create_app`
n'est pas accessible par `from app import create_app`. On charge donc `app.py`
sous le nom `app_entry` (via importlib) et on expose l'application WSGI `app` :

    gunicorn wsgi:app
"""

import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    "app_entry", os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
)
_app_entry = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_app_entry)

# Application WSGI servie par gunicorn. create_app() applique le fail-fast des
# secrets (Lot 1) : gunicorn refuse de démarrer si un secret requis est absent.
app = _app_entry.create_app()
