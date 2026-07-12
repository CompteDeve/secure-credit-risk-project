# ============================================
# MILESTONE 3 - ETAPE 2 : Dockerfile
# ============================================
# Ce fichier explique a Docker comment construire une image contenant
# notre API FastAPI (Credit Risk Prediction API - Phase C securisee).

# ------------------------------------------------
# 1. Quelle image Python utiliser
# ------------------------------------------------
# Image officielle Python, version "slim" : plus legere que l'image
# complete, tout en gardant tout ce qu'il faut pour installer pandas/
# scikit-learn (contrairement a "alpine", qui pose souvent des soucis
# de compilation avec ces bibliotheques).
FROM python:3.11-slim

# ------------------------------------------------
# 2. Dossier de travail dans le conteneur
# ------------------------------------------------
WORKDIR /app

# ------------------------------------------------
# 3. Installer les bibliotheques
# ------------------------------------------------
# On copie d'abord UNIQUEMENT requirements.txt (et pas tout le projet)
# pour profiter du cache Docker : si le code change mais pas les
# dependances, Docker reutilise cette etape sans tout reinstaller.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------
# 4. Copier le projet dans le conteneur
# ------------------------------------------------
# On copie le code source, le modele entraine et les metriques.
# (Le dossier logs/ sera cree automatiquement au demarrage par
# src/logging_config.py -- inutile de le copier.)
COPY src/ ./src/
COPY models/ ./models/

# ------------------------------------------------
# 5. Variables d'environnement
# ------------------------------------------------
# La cle API par defaut peut etre surchargee au lancement du conteneur
# (voir docker-compose.yml) sans jamais modifier le code.
ENV API_KEY=demo-key-milestone2-2026
ENV PYTHONUNBUFFERED=1

# ------------------------------------------------
# 6. Port expose
# ------------------------------------------------
EXPOSE 8080

# ------------------------------------------------
# 7. Commande de lancement de l'API
# ------------------------------------------------
# Pas de --reload ici : le rechargement automatique est utile en
# developpement seulement, jamais en production/conteneur.
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]