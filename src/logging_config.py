"""
============================================
MILESTONE 2 - PHASE C (BLUE TEAM)
ÉTAPE 24 : Configuration des logs
============================================
Ce module configure un logger réutilisable par toute l'application.
Chaque entrée de log contient automatiquement la date et l'heure
(grâce au formatter), et on y enregistre :
- la requête reçue (endpoint, résumé des données)
- le résultat (prédiction obtenue)
- les erreurs éventuelles (validation, exception interne, etc.)

Les logs sont écrits à la fois :
- dans la console (utile en développement)
- dans un fichier logs/api.log (utile pour l'audit / la traçabilité)
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "api.log")

os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name: str = "credit_api") -> logging.Logger:
    """
    Retourne un logger configuré. Peut être appelé plusieurs fois
    (ex. depuis différents modules) sans dupliquer les handlers.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Déjà configuré (évite les doublons de logs si get_logger()
        # est appelé plusieurs fois, ex. au rechargement --reload)
        return logger

    logger.setLevel(logging.INFO)

    # Format : date + heure + niveau + message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler fichier (avec rotation pour éviter un fichier illimité)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Logger prêt à l'emploi, importable directement : `from logging_config import logger`
logger = get_logger()
