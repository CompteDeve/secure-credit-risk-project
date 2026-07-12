# Rapport des protections (Mitigation Report)

## Milestone 2 - Étape 29

Ce document explique chaque protection ajoutée en Phase C (Blue Team),
pourquoi elle était nécessaire, et quelle attaque précise (identifiée en
Phase B, Red Team) elle neutralise.

---

## 1. Authentification par clé API (Étape 21)

### Ce qui a été ajouté
Un en-tête `X-API-Key` obligatoire sur `/predict`. Toute requête sans
clé valide reçoit un code `401 Unauthorized`, avant même que la donnée
soit envoyée au modèle.

### Pourquoi c'est utile
En Phase A, n'importe qui connaissant l'URL de l'API pouvait l'utiliser
librement. Cela ouvrait la porte à :
- un usage non autorisé (intégration dans un produit tiers sans accord) ;
- une absence totale de traçabilité de qui utilise l'API ;
- un point d'entrée facile pour toutes les autres attaques (abus de
  requêtes, extraction de modèle), puisque rien ne filtrait qui pouvait
  appeler l'API.

Avec une clé API, seules les personnes/systèmes autorisés peuvent
utiliser le service, et chaque requête peut être rattachée à un client
identifié (utile pour la facturation, l'audit, ou révoquer un accès
compromis).

---

## 2. Validation stricte des données (Étape 22)

### Ce qui a été ajouté
Des bornes (`Field(ge=..., le=...)`) sur chaque champ numérique
(ex. `debt_ratio` entre 0 et 1, `existing_credits` entre 0 et 20), et
`extra="forbid"` pour rejeter tout champ non prévu dans le schéma.

### Pourquoi c'est utile
En Phase A (étape 15), des valeurs négatives (`past_due_count = -100`)
ou absurdes (`loan_amount_normalized = 999999999`) étaient acceptées
sans problème. Cela permettait :
- d'obtenir des prédictions sur des profils totalement irréalistes ;
- de faciliter le sondage systématique du modèle (boundary probing,
  étape 19) avec des valeurs qui n'ont aucun sens métier ;
- d'injecter des champs non prévus (`is_admin: true`) sans que l'API ne
  s'en aperçoive.

Rejeter ces requêtes en amont protège aussi le modèle : une prédiction
basée sur des données absurdes n'a aucune valeur et peut induire en
erreur un système qui consommerait cette API en aval.

---

## 3. Masquage du score de confiance exact (Étape 23)

### Ce qui a été ajouté
Le score de confiance numérique précis (ex. `52.15 %`) et la
distribution complète des probabilités ne sont plus renvoyés. Seul un
niveau qualitatif (`"Faible"`, `"Moyenne"`, `"Elevee"`) est exposé.

### Pourquoi c'est utile
C'était la faille la plus critique identifiée en Phase B (étape 16) :
en observant comment la confiance évoluait quand on faisait varier une
seule variable, un attaquant a pu localiser la frontière de décision du
modèle (`debt_ratio ≈ 0.3126`) en seulement **12 requêtes**.

En ne renvoyant qu'une catégorie large, cette recherche fine devient
beaucoup plus difficile : un attaquant ne peut plus utiliser la
confiance comme un "signal de gradient" pour ajuster précisément un
dossier de crédit et le faire basculer artificiellement vers
"Good Credit".

---

## 4. Journalisation (Étape 24)

### Ce qui a été ajouté
Un module `src/logging_config.py` qui enregistre, pour chaque
événement, la date, l'heure, le type de requête, le résultat obtenu, et
les erreurs rencontrées, dans `logs/api.log`.

### Pourquoi c'est utile
En Phase A, aucune trace n'existait : impossible de savoir a posteriori
qui avait interrogé l'API, combien de fois, ou si un comportement
suspect (ex. des centaines de requêtes similaires en quelques secondes)
s'était produit.

Avec les logs :
- une tentative d'accès non autorisée est tracée (`WARNING | Acces
  refuse`) ;
- une activité anormale (ex. beaucoup de requêtes similaires, signe
  possible d'une extraction de modèle en cours, étape 18) peut être
  détectée après coup ;
- en cas d'incident, il est possible de reconstituer précisément ce qui
  s'est passé, ce qui est indispensable pour tout système traitant des
  données sensibles (ici, des données de crédit).

---

## 5. Limitation du nombre de requêtes (Étape 25)

### Ce qui a été ajouté
Une limite de 100 requêtes par minute par adresse IP (librairie
`slowapi`). Au-delà, l'API répond `429 Too Many Requests`.

### Pourquoi c'est utile
En Phase A (étape 17), 100 requêtes envoyées en parallèle avaient
toutes été acceptées sans aucun ralentissement ni refus. Cette absence
de limite permettait :
- un risque de déni de service (DoS) si le volume était poussé plus
  loin ;
- surtout, elle facilitait directement l'extraction de modèle (étape
  18) : avec seulement 400 requêtes (largement en dessous de ce qu'un
  attaquant patient pourrait envoyer sans limite), un modèle clone
  avait atteint 83.3 % de fidélité avec l'original.

Avec la limite en place, un attaquant qui tenterait de collecter des
milliers d'exemples pour cloner le modèle serait automatiquement
ralenti, rendant l'attaque beaucoup plus longue et plus détectable
(chaque `429` étant lui-même enregistré dans les logs).

---

## 6. Messages d'erreur génériques (Étape 26)

### Ce qui a été ajouté
Des gestionnaires d'exception personnalisés qui remplacent les messages
d'erreur détaillés de FastAPI/Pydantic par des messages génériques
(`"Entree invalide."`, `"Une erreur interne est survenue."`), tout en
conservant le détail complet côté serveur dans les logs.

### Pourquoi c'est utile
Les messages d'erreur détaillés de la Phase A révélaient la structure
interne exacte attendue par l'API : noms de colonnes, types de données,
règles de validation. C'est une information précieuse pour un
attaquant qui cherche à comprendre comment l'API fonctionne en interne
("reconnaissance"), avant de préparer une attaque plus ciblée.

En renvoyant un message générique au client tout en gardant le détail
en interne (pour le débogage légitime), on applique le principe de
"defense in depth" : ne jamais donner à un attaquant plus d'information
que nécessaire, même en cas d'erreur.

---

## Synthèse : quelle protection neutralise quelle attaque ?

| Protection ajoutée | Attaque Red Team neutralisée |
|---|---|
| Clé API (21) | Usage non autorisé, absence de traçabilité |
| Validation stricte (22) | Entrées malformées, valeurs absurdes (étape 15) |
| Confiance masquée (23) | Fuite de confiance / recherche de frontière (étape 16) |
| Logs (24) | Absence de détection d'activité suspecte |
| Rate limiting (25) | Abus de requêtes (étape 17), facilite l'extraction de modèle (étape 18) |
| Erreurs génériques (26) | Reconnaissance de la structure interne via les messages d'erreur |

---

## Limite importante à souligner

Ces protections sécurisent l'**accès et l'usage** de l'API, mais ne
corrigent pas le **modèle lui-même**. Le sur-apprentissage observé dès
l'entraînement (écart Train/Test de 23.71 points) et le comportement
illogique détecté en boundary probing (étape 19 : plus d'incidents de
paiement améliore paradoxalement le score) restent présents. Une
sécurisation complète du système nécessiterait, en complément, un
ré-entraînement du modèle avec plus de données et une meilleure
régularisation.
