# Cycle de vie du modèle

## Milestone 3 - Étape 6

Ce document décrit le parcours complet du modèle de prédiction du
risque de crédit, depuis la donnée brute jusqu'à sa mise à disposition
via une API sécurisée.

---

## Schéma général

```
1. Dataset brut (data_credit_risk.csv)
        ↓
2. Analyse et identification des données sensibles
        ↓
3. Nettoyage (valeurs aberrantes, types de données)
        ↓
4. Protection des données personnelles
   (suppression identifiants, anonymisation, pseudonymisation, masquage)
        ↓
5. Dataset ML-ready (data/processed/credit_processed.csv)
        ↓
6. Hash SHA-256 du dataset (traçabilité / intégrité)
        ↓
7. Entraînement du modèle (Random Forest, scikit-learn)
        ↓
8. Évaluation (accuracy, precision, recall, F1-score)
        ↓
9. Modèle entraîné (models/model.pkl) + hash SHA-256 (model_hash.txt)
        ↓
10. API FastAPI (src/api.py) — chargement du modèle au démarrage
        ↓
11. Tests Red Team (attacks/) — recherche de vulnérabilités
        ↓
12. Corrections Blue Team (authentification, validation, logs,
    rate limiting, masquage de la confiance, erreurs génériques)
        ↓
13. Conteneurisation (Docker + docker-compose)
        ↓
14. API sécurisée disponible pour les utilisateurs autorisés
```

---

## Détail de chaque étape

### 1. Dataset brut
Fichier source `data_credit_risk.csv` : 3 200 lignes, 25 colonnes,
contenant des identifiants directs (nom, email, téléphone, numéro
d'identité nationale), des quasi-identifiants (âge, genre, région...)
et des données financières sensibles (revenu, épargne, prêt...).

### 2. Analyse et identification des données sensibles
Classification systématique des colonnes en trois catégories :
identifiants directs, quasi-identifiants, données financières
sensibles — étape préalable indispensable avant tout traitement
(voir `docs/dataset_datasheet.md` pour le détail complet).

### 3. Nettoyage des données
- Détection et correction des valeurs aberrantes (méthode IQR élargie,
  remplacement par la médiane)
- Conversion des types (dates, booléens, catégories)
- Encodage des variables catégorielles (Label Encoding pour les
  variables binaires et la cible, One-Hot Encoding pour les variables
  multi-catégories)

### 4. Protection des données personnelles
- **Suppression** des identifiants directs (`customer_id`, `full_name`,
  `email`, `phone`, `national_id`)
- **Anonymisation** des données financières par normalisation
  (StandardScaler : moyenne 0, écart-type 1)
- **Pseudonymisation** des quasi-identifiants (âge agrégé en tranches,
  revenu catégorisé en quartiles)
- **Masquage** : remplacement des identifiants par des références
  génériques (`USER0001`, `USER0002`, ...)

### 5. Dataset ML-ready
Dataset final sans aucune donnée directement identifiante, prêt pour
l'entraînement : `data/processed/credit_processed.csv` (3 200 lignes,
41 colonnes).

### 6. Hash du dataset
Un hash SHA-256 est calculé sur le dataset brut et sur le dataset
traité, pour garantir leur intégrité et permettre de détecter toute
modification ultérieure non tracée.

### 7. Entraînement du modèle
Modèle **Random Forest Classifier** (scikit-learn), entraîné sur
80 % des données (2 560 lignes), testé sur les 20 % restants
(640 lignes), avec stratification pour préserver l'équilibre des
classes.

### 8. Évaluation
Résultats obtenus sur le jeu de test :
- Accuracy : 67.81 %
- Precision : 65.92 %
- Recall : 60.48 %
- F1-score : 63.08 %

Écart notable avec les performances sur le jeu d'entraînement
(accuracy 91.52 %), révélant un sur-apprentissage (voir
`docs/model_card.md`, section Limites).

### 9. Modèle final et hash
Le modèle entraîné est sauvegardé (`models/model.pkl`, 3.4 Mo) et son
hash SHA-256 est calculé (`models/model_hash.txt`) afin de garantir
que le fichier chargé par l'API est bien celui qui a été validé et
évalué, sans altération.

### 10. API FastAPI
Le modèle est chargé au démarrage de l'API (`src/api.py`) et exposé
via l'endpoint `POST /predict`.

### 11. Tests Red Team
Une phase d'attaque volontaire (`attacks/`) a permis d'identifier six
vulnérabilités concrètes : absence d'authentification, validation
insuffisante, fuite d'information via le score de confiance, absence
de limitation de requêtes, possibilité d'extraction du modèle, et
messages d'erreur trop détaillés (voir `docs/attack_report.md`).

### 12. Corrections Blue Team
Chaque vulnérabilité identifiée a été corrigée : clé API, validation
stricte des plages de valeurs, masquage du score de confiance exact,
journalisation complète, limitation à 100 requêtes/minute, messages
d'erreur génériques (voir `docs/mitigation_report.md`).

### 13. Conteneurisation
L'application est packagée dans une image Docker (`Dockerfile`) et
orchestrée via `docker-compose.yml`, permettant un déploiement
reproductible en une seule commande.

### 14. Mise à disposition
L'API sécurisée est prête à être utilisée par des clients autorisés
(possédant une clé API valide), avec traçabilité complète de chaque
requête.
