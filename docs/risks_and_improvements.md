# Risques restants et améliorations futures

## Milestone 3 - Étapes 11 et 12

---

## Étape 11 : Risques restants

Malgré les protections mises en place en Phase C (Blue Team), certains
problèmes persistent et doivent être connus et assumés explicitement.

### 1. Dataset de taille limitée
Avec seulement 3 200 lignes, le dataset reste modeste pour un modèle
Random Forest à 100 arbres. Cela contribue directement au
sur-apprentissage observé (accuracy 91.52 % en entraînement contre
67.81 % en test).

### 2. Le modèle peut être amélioré
- L'accuracy de 67.81 % sur le test reste modeste pour une décision de
  crédit.
- Le comportement contre-intuitif détecté sur `past_due_count` (plus
  d'incidents de paiement améliore parfois le score) montre que le
  modèle a appris des corrélations qui ne reflètent pas une vraie
  logique métier.
- Aucune technique de régularisation avancée (ajustement de
  `max_depth`, `min_samples_leaf`, validation croisée) n'a encore été
  appliquée pour réduire l'écart Train/Test.

### 3. L'API peut être protégée plus fortement dans le futur
- L'authentification actuelle repose sur une **clé API unique et
  statique**, partagée par tous les utilisateurs. Une évolution
  naturelle serait d'implémenter **OAuth2 / JWT**, avec des jetons
  individuels, une expiration automatique, et des rôles différenciés
  (lecture seule, administration, etc.).
- Aucun **HTTPS/TLS** n'est configuré : les échanges actuels (en local)
  circulent en clair. En production, un reverse proxy (ex. Nginx,
  Traefik) avec certificat TLS serait indispensable.

### 4. Consentement non vérifié
Le dataset contient une colonne `consent_flag`, mais elle n'a pas été
utilisée pour filtrer les données avant l'entraînement. Rien ne garantit
aujourd'hui que seuls les clients ayant consenti figurent dans le
modèle entraîné.

### 5. Secrets encore mal gérés
La clé API (`API_KEY`) est actuellement définie directement dans
`docker-compose.yml` plutôt que dans un fichier `.env` séparé et
non versionné — un secret ne devrait jamais apparaître en clair dans
un fichier suivi par Git.

### 6. Absence de surveillance active
Les logs sont bien générés (`logs/api.log`), mais rien ne surveille
ces logs en temps réel : aucune alerte n'est déclenchée en cas
d'activité suspecte (ex. rafale de requêtes en 429, tentatives
répétées avec une mauvaise clé API).

### 7. Intégrité du modèle non vérifiée automatiquement
Le hash SHA-256 du modèle (`models/model_hash.txt`) existe, mais l'API
ne le recalcule pas et ne le compare pas automatiquement au démarrage :
un `model.pkl` corrompu ou substitué ne serait pas détecté
automatiquement à ce stade.

---

## Étape 12 : Améliorations futures proposées

### Modèle
- **Ré-entraînement avec régularisation renforcée** : limiter la
  profondeur des arbres, augmenter `min_samples_leaf`, utiliser une
  validation croisée (k-fold) pour mieux estimer la performance réelle
  et réduire le sur-apprentissage.
- **Explorer d'autres algorithmes** (Gradient Boosting, XGBoost,
  régression logistique régularisée) et comparer leurs performances de
  façon rigoureuse.
- **Plus de données** : collecter ou générer davantage d'exemples
  d'entraînement pour améliorer la capacité de généralisation.
- **Audit de biais** : vérifier que le modèle ne défavorise pas
  injustement certains groupes démographiques (région, genre, etc.).

### Infrastructure et données
- **Base de données** : remplacer le fichier CSV statique par une
  vraie base de données (PostgreSQL, par exemple), permettant une
  mise à jour continue des données et une meilleure traçabilité.
- **Pipeline automatisé (CI/CD)** : automatiser le ré-entraînement, les
  tests, et le déploiement à chaque mise à jour du dataset ou du code.

### Sécurité
- **Authentification plus forte** : migrer vers OAuth2/JWT avec des
  jetons par utilisateur, expiration automatique, et gestion de rôles.
- **HTTPS obligatoire** en production, via un reverse proxy avec
  certificat TLS (ex. Let's Encrypt).
- **Gestion des secrets** via un fichier `.env` non versionné, ou un
  gestionnaire de secrets dédié (ex. HashiCorp Vault, AWS Secrets
  Manager) pour un déploiement à plus grande échelle.
- **Vérification automatique du hash du modèle** au démarrage de
  l'API, avec refus de démarrer si le hash ne correspond pas à la
  valeur de référence.

### Surveillance
- **Surveillance en temps réel (monitoring)** : mettre en place des
  outils comme Prometheus + Grafana pour visualiser le trafic, les
  taux d'erreur, et déclencher des alertes automatiques en cas
  d'anomalie (ex. pic de requêtes 401/429).
- **Détection d'anomalies comportementales** : identifier
  automatiquement les patterns d'usage suspects (ex. beaucoup de
  requêtes similaires en peu de temps, signe possible d'une tentative
  d'extraction de modèle).

### Gouvernance
- **Vérification formelle du consentement** (`consent_flag`) avant
  toute utilisation des données en entraînement.
- **Vérification du k-anonymat** sur le dataset traité avant tout
  partage ou publication externe.
- **Politique de conservation des données** formalisée (durées
  précises pour le dataset brut, le dataset traité, et les logs).
