# Risk Register — Registre des risques

## Milestone 3 - Étape 9

Registre synthétique de tous les risques identifiés au cours du
projet (données, modèle, API, infrastructure), leur probabilité,
impact, et statut de traitement.

---

## Légende

- **Probabilité :** Faible / Moyenne / Élevée
- **Impact :** Faible / Moyen / Élevé / Critique
- **Statut :** 🔴 Non traité — 🟡 Partiellement traité — 🟢 Traité

---

## Tableau des risques

| # | Risque | Catégorie | Probabilité | Impact | Statut | Mitigation |
|---|---|---|:---:|:---:|:---:|---|
| 1 | Réidentification par combinaison de quasi-identifiants | Données | Faible | Élevé | 🟡 | Pseudonymisation appliquée (tranches d'âge, catégories de revenu) ; k-anonymat non vérifié formellement |
| 2 | Consentement des clients non vérifié avant entraînement | Données | Moyenne | Élevé | 🔴 | `consent_flag` présent mais non utilisé comme filtre |
| 3 | Fuite de données financières sensibles | Données | Faible | Élevé | 🟢 | Anonymisation par normalisation (StandardScaler) |
| 4 | Sur-apprentissage du modèle (écart Train/Test de 23.71 pts) | Modèle | Élevée | Moyen | 🔴 | Identifié, non corrigé (nécessite ré-entraînement) |
| 5 | Comportement contre-intuitif (`past_due_count`) | Modèle | Moyenne | Élevé | 🔴 | Identifié via boundary probing, non corrigé |
| 6 | Absence d'authentification sur l'API | API | Élevée | Critique | 🟢 | Clé API obligatoire (`X-API-Key`) |
| 7 | Fuite du score de confiance exact (attaque d'évasion) | API | Élevée | Élevé | 🟢 | Confiance remplacée par un niveau qualitatif |
| 8 | Absence de validation des plages de valeurs | API | Élevée | Moyen | 🟢 | Bornes Pydantic (`Field(ge=..., le=...)`) |
| 9 | Absence de limitation de requêtes (DoS, extraction de modèle) | API | Élevée | Élevé | 🟢 | Rate limiting 100 requêtes/minute (slowapi) |
| 10 | Extraction de modèle via requêtes massives | API / Modèle | Moyenne | Élevé | 🟡 | Rate limiting réduit le risque, ne l'élimine pas totalement |
| 11 | Messages d'erreur révélant la structure interne | API | Élevée | Faible | 🟢 | Messages génériques, détails uniquement en logs serveur |
| 12 | Absence de traçabilité des requêtes | API | Élevée | Moyen | 🟢 | Logging complet (`logs/api.log`) |
| 13 | Altération non détectée du fichier `model.pkl` | Intégrité | Faible | Élevé | 🟡 | Hash SHA-256 généré, mais pas vérifié automatiquement au démarrage |
| 14 | Clé API unique partagée entre tous les utilisateurs | API | Moyenne | Moyen | 🔴 | Une seule clé statique, pas de gestion par utilisateur |
| 15 | Secrets (clé API) codés en dur dans le code / docker-compose | Infrastructure | Moyenne | Moyen | 🔴 | Devrait être déplacé vers un fichier `.env` non versionné |
| 16 | Absence de chiffrement HTTPS en local/démo | Infrastructure | Moyenne | Moyen | 🔴 | API testée en HTTP local uniquement, pas de TLS configuré |
| 17 | Dataset de taille limitée (3 200 lignes) | Données / Modèle | Moyenne | Moyen | 🔴 | Non traité, nécessiterait plus de données |
| 18 | Absence de surveillance en temps réel (monitoring) | Infrastructure | Moyenne | Moyen | 🔴 | Logs disponibles mais pas d'alerting automatique |

---

## Synthèse par statut

| Statut | Nombre de risques |
|---|:---:|
| 🟢 Traité | 6 |
| 🟡 Partiellement traité | 3 |
| 🔴 Non traité | 9 |

---

## Priorités recommandées pour la suite

1. **Priorité haute :** filtrer les données d'entraînement selon
   `consent_flag` (#2), déplacer les secrets vers `.env` (#15),
   corriger le sur-apprentissage du modèle (#4).
2. **Priorité moyenne :** vérifier automatiquement le hash du modèle
   au démarrage de l'API (#13), passer à une gestion de clés API par
   utilisateur (#14), mettre en place HTTPS (#16).
3. **Priorité basse (amélioration continue) :** vérification formelle
   du k-anonymat (#1), monitoring temps réel (#18), agrandissement du
   dataset (#17).
