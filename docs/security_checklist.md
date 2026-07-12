# Security Checklist

## Milestone 3 - Étape 10

Liste de vérification permettant de confirmer, point par point, que
les protections attendues sont bien en place dans le projet. À
utiliser comme check finale avant toute démonstration ou mise en
production.

---

## API

- [x] **API protégée** — accès uniquement via clé API (`X-API-Key`)
- [x] **API Key activée** — vérifiée sur `POST /predict` (`src/api.py`, `verify_api_key`)
- [x] **Validation Pydantic** — bornes de valeurs (`Field(ge=..., le=...)`), types stricts, `extra="forbid"`
- [x] **Score de confiance masqué** — niveau qualitatif uniquement (`Faible` / `Moyenne` / `Elevee`)
- [x] **Rate limiting** — 100 requêtes/minute par IP (`slowapi`)
- [x] **Messages d'erreur génériques** — pas de détails techniques exposés au client (`"Entree invalide."`)
- [ ] **HTTPS / TLS activé** — non configuré (API testée en HTTP local uniquement)
- [ ] **Authentification forte (OAuth2 / JWT)** — non implémentée (clé API statique unique pour l'instant)
- [ ] **Gestion de clés API par utilisateur** — une seule clé partagée actuellement

## Journalisation et surveillance

- [x] **Logs activés** — date, heure, requête, résultat, erreurs (`src/logging_config.py` → `logs/api.log`)
- [x] **Rotation des logs** — 5 Mo max par fichier, 3 fichiers de sauvegarde
- [ ] **Monitoring temps réel / alerting** — non mis en place (logs disponibles mais pas d'alertes automatiques)

## Modèle et intégrité

- [x] **Hash du modèle calculé** — SHA-256 (`models/model_hash.txt`)
- [ ] **Vérification automatique du hash au démarrage de l'API** — non implémentée
- [x] **Métriques de performance documentées** — `models/metrics.json`, `docs/model_card.md`
- [x] **Limites du modèle documentées** — sur-apprentissage, comportement contre-intuitif (`docs/model_card.md`)

## Données

- [x] **Identifiants directs supprimés** — `customer_id`, `full_name`, `email`, `phone`, `national_id`
- [x] **Données financières anonymisées** — normalisation (StandardScaler)
- [x] **Quasi-identifiants pseudonymisés** — âge en tranches, revenu en quartiles
- [x] **Hash du dataset calculé** — brut et traité (`hashes/`)
- [ ] **Vérification du consentement (`consent_flag`) avant entraînement** — non appliquée
- [ ] **Vérification formelle du k-anonymat** — non réalisée

## Secrets et configuration

- [ ] **Secrets dans `.env`** — actuellement codés en dur / passés en variable d'environnement `API_KEY` dans `docker-compose.yml`, pas encore dans un fichier `.env` dédié et non versionné
- [x] **`.dockerignore` en place** — évite de copier des fichiers sensibles ou inutiles dans l'image

## Infrastructure

- [x] **Docker utilisé** — `Dockerfile` + `docker-compose.yml`
- [x] **`docker compose up` fonctionnel en une commande**
- [x] **Volume pour les logs** — persistance des logs hors du conteneur
- [ ] **Healthcheck testé en conditions réelles** — configuré dans `docker-compose.yml`, à valider en environnement de déploiement

## Tests

- [x] **Tests Red Team réalisés** — `attacks/` (entrées malformées, fuite de confiance, abus de requêtes, extraction de modèle, boundary probing)
- [x] **Tests Blue Team automatisés** — `tests/test_api_security.py` (12 tests, tous réussis)
- [x] **Rapport d'attaque documenté** — `docs/attack_report.md`
- [x] **Rapport de mitigation documenté** — `docs/mitigation_report.md`

---

## Score global (indicatif)

**22 / 29 points de contrôle validés (~76 %)**

Les points non cochés sont repris en détail dans
`docs/risks_and_improvements.md` (risques restants et améliorations
futures).
