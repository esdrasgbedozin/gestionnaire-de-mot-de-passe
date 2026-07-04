FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# M4 : exécuter en utilisateur non-root (moindre privilège). Créé sans home ni
# shell de login ; propriétaire de /app pour pouvoir écrire le bytecode .pyc.
# gunicorn logue sur stdout (pas d'écriture disque) et bind sur 5000 (> 1024,
# accessible sans privilège).
RUN groupadd --system --gid 1001 appuser \
    && useradd --system --uid 1001 --gid appuser --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

# Exposer le port
EXPOSE 5000

# Variables d'environnement
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Commande de démarrage avec script plus robuste
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "--timeout", "120", "--access-logfile", "-", "wsgi:app"]