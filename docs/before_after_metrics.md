# Comparaison Avant / Après — Sécurisation de l'API

## Milestone 2 - Étape 28

Ce document compare l'API baseline (Phase A, vulnérable) à l'API
sécurisée (Phase C, Blue Team), point par point, avec des preuves
concrètes issues des tests réalisés en Phase B (Red Team).

---

## Tableau comparatif

| Aspect | ❌ Avant (Phase A) | ✅ Après (Phase C) |
|---|---|---|
| **Authentification** | Aucune. N'importe qui peut appeler `/predict`. | Clé API obligatoire (en-tête `X-API-Key`). Toute requête sans clé valide reçoit un `401 Unauthorized`. |
| **Score de confiance** | Exposé en clair, avec les probabilités complètes (ex. `"confidence": 52.15, "probabilities": {...}`). | Remplacé par un niveau qualitatif uniquement (`"confidence_level": "Faible"` / `"Moyenne"` / `"Elevee"`). |
| **Validation des données** | Seulement le *type* est vérifié (nombre, texte, booléen). Les valeurs négatives ou extrêmes sont acceptées. | Chaque champ a des bornes plausibles (`Field(ge=..., le=...)`). Les champs inattendus sont rejetés (`extra="forbid"`). |
| **Journalisation (logs)** | Aucune trace des requêtes, résultats ou erreurs. | Chaque requête (date, heure, résultat, erreur) est enregistrée dans `logs/api.log`. |
| **Limitation des requêtes** | Aucune. Testé : 100 requêtes en parallèle toutes acceptées (`{200: 100}`). | Limite de 100 requêtes/minute. Testé : sur 110 requêtes envoyées, 100 acceptées et 10 rejetées avec `429`. |
| **Messages d'erreur** | FastAPI renvoie par défaut des messages détaillés (noms de colonnes, types Pydantic attendus, etc.). | Messages génériques uniquement (`"Entree invalide."`, `"Cle API invalide ou manquante."`), sans détail technique exposé au client. |

---

## Preuves concrètes (avant / après)

### Authentification

**Avant :**
```json
POST /predict  (sans en-tête)
→ 200 OK
{"prediction": "Bad Credit", "confidence": 52.15, ...}
```

**Après :**
```json
POST /predict  (sans en-tête X-API-Key)
→ 401 Unauthorized
{"detail": "Cle API invalide ou manquante."}
```

### Score de confiance

**Avant :**
```json
{
  "prediction": "Bad Credit",
  "prediction_encoded": 1,
  "confidence": 52.15,
  "probabilities": {"good_credit": 47.85, "bad_credit": 52.15}
}
```
👉 Cette précision a permis de localiser la frontière de décision du
modèle (`debt_ratio ≈ 0.3126`) en seulement 12 requêtes (voir
`attack_report.md`, étape 16).

**Après :**
```json
{
  "prediction": "Bad Credit",
  "confidence_level": "Faible"
}
```
👉 Impossible de reconstruire une frontière de décision précise avec
une simple étiquette qualitative.

### Validation

**Avant :**
```json
{"loan_duration_months": -5, ...}
→ 200 OK  (accepté sans broncher)
```

**Après :**
```json
{"loan_duration_months": -5, ...}
→ 422 Unprocessable Entity
{"detail": "Entree invalide."}
```

### Limitation des requêtes

**Avant :** 100 requêtes parallèles → 100 acceptées, débit ~25-45 req/s,
aucune limite observée.

**Après :** 110 requêtes envoyées → 100 acceptées (`200`), 10 rejetées
(`429 Too Many Requests`) dès que la limite de 100/minute est atteinte.

### Messages d'erreur

**Avant (exemple réel obtenu en Phase A) :**
```json
{
  "detail": [
    {
      "type": "float_parsing",
      "loc": ["body", "annual_income_normalized"],
      "msg": "Input should be a valid number, unable to parse string as a number",
      "input": "Bonjour"
    }
  ]
}
```
👉 Révèle le nom exact du champ, son type attendu, et la structure
interne du modèle de données.

**Après :**
```json
{"detail": "Entree invalide."}
```
👉 Le client sait que sa requête est invalide, sans qu'aucun détail sur
la structure interne de l'API ne soit exposé (le détail complet reste
cependant consultable côté serveur dans `logs/api.log`, pour le
débogage).

---

## Ce qui reste à améliorer (limites connues)

- La clé API est actuellement unique et partagée (`demo-key-milestone2-2026`).
  En production, il faudrait une clé par client, stockée de façon
  sécurisée (hashée, avec rotation possible).
- La validation Pydantic vérifie les plages de valeurs par champ, mais
  pas encore la cohérence logique entre champs liés (ex. s'assurer
  qu'une seule région parmi `region_*` est à `true`).
- Le modèle lui-même montre des signes de sur-apprentissage (voir
  `attack_report.md`, étape 19) — un ré-entraînement serait nécessaire
  pour une mise en production réelle, indépendamment des protections de
  l'API.
