"""
Configuration pytest partagée.

Le dossier backend/ contient à la fois le module entrypoint `app.py` ET le
package `app/`. En cas de collision de nom, Python privilégie le package, si
bien que `from app import create_app` échoue (le package n'expose pas la
factory). Pour garder le code de production intact, on charge ici `app.py`
sous un nom distinct `app_entry` et on l'enregistre dans sys.modules, afin que
les tests puissent faire `from app_entry import create_app, db`.
"""

import importlib.util
import os
import sys

# Paramètres Argon2id RÉDUITS pour la vitesse des tests UNIQUEMENT.
# Cloisonnement : ces valeurs ne sont posées que par ce conftest (chargé par
# pytest seulement) via setdefault. La production ne définit JAMAIS ces variables
# (cf. docker-compose*.yml) → EncryptionService retombe sur ses défauts 192 MiB.
os.environ.setdefault("ARGON2_MEMORY_KIB", "8192")
os.environ.setdefault("ARGON2_TIME_COST", "1")
os.environ.setdefault("ARGON2_PARALLELISM", "1")

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

_spec = importlib.util.spec_from_file_location(
    "app_entry", os.path.join(_BACKEND_DIR, "app.py")
)
app_entry = importlib.util.module_from_spec(_spec)
sys.modules["app_entry"] = app_entry
_spec.loader.exec_module(app_entry)
