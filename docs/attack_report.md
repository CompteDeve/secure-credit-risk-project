# Rapport d'attaque — Phase B (Red Team)

## Milestone 2 - Étape 20

Ce document décrit les attaques menées contre l'API baseline (`src/api.py`,
Phase A), les résultats obtenus, et les problèmes de sécurité identifiés.
Ces résultats proviennent de tests réels exécutés contre l'API en local
(`http://127.0.0.1:8080`).

---

## Étape 15 — Entrées malformées (`attacks/malformed_inputs.py`)

### Attaque
Envoi de données invalides ou inattendues à `/predict` : texte à la place
d'un nombre, champ manquant, valeurs négatives, valeurs extrêmes, mauvais
type de donnée, champ non prévu, corps de requête vide.

### Résultats obtenus

| Test                                              | Code retour | Verdict |
|----------------------------------------------------|:-----------:|---------|
| Texte au lieu d'un nombre (`annual_income_normalized = "Bonjour"`) | 422 | ✅ Rejeté proprement |
| Champ manquant (`debt_ratio` absent)                | 422         | ✅ Rejeté proprement |
| Valeur négative (`loan_duration_months = -5`)       | 200         | ⚠️ Accepté |
| Valeur négative (`past_due_count = -100`)           | 200         | ⚠️ Accepté |
| Valeur extrême (`loan_amount_normalized = 999999999`) | 200       | ⚠️ Accepté |
| Mauvais type (`loan_purpose_car = "oui"`)           | 422         | ✅ Rejeté proprement |
| Champ inattendu ajouté (`is_admin = true`)          | 200         | ⚠️ Accepté (ignoré silencieusement) |
| Corps de requête vide                               | 422         | ✅ Rejeté proprement |

### Problèmes trouvés
- **Aucune validation de plage de valeurs.** FastAPI/Pydantic vérifie le
  *type* des champs (nombre, booléen, etc.) mais pas leur *plausibilité*.
  Une durée de prêt négative (`-5 mois`) ou un montant de prêt absurde
  (`999999999`) sont acceptés et transmis tels quels au modèle, qui
  retourne une prédiction sans se plaindre.
- **Les champs inattendus sont silencieusement ignorés.** Envoyer
  `is_admin: true` ne casse rien, mais montre que l'API n'a aucun
  contrôle strict sur la forme exacte des requêtes reçues.
- **Conséquence :** un client (ou un attaquant) peut obtenir une
  prédiction sur un profil totalement irréaliste, ce qui peut être
  exploité pour tester massivement le modèle sans être bloqué (voir
  aussi étape 18, extraction de modèle).

---

## Étape 16 — Fuite de confiance (`attacks/confidence_leakage.py`)

### Attaque
Interrogation de l'API en faisant varier une seule variable (`debt_ratio`)
par petits paliers, en observant à la fois la classe prédite et le score
de confiance retourné. Puis recherche automatique (dichotomie) du point
exact de bascule entre "Bad Credit" et "Good Credit".

### Résultats obtenus

```
debt_ratio |   prediction | confidence
------------------------------------------
      0.00 |   Bad Credit |     55.11%
      0.10 |   Bad Credit |     55.11%
      0.20 |   Bad Credit |     53.80%
      0.30 |   Bad Credit |     52.15%
      0.40 |   Bad Credit |     50.36%
      0.50 |  Good Credit |     51.28%   <-- bascule entre 0.40 et 0.50
      0.60 |  Good Credit |     56.38%
      ...
      1.00 |  Good Credit |     63.34%
```

Recherche automatique par dichotomie : **point de bascule localisé avec
précision à `debt_ratio ≈ 0.3126`, en seulement 12 requêtes.**

### Problèmes trouvés
- **Le score de confiance et la distribution complète des probabilités
  sont exposés**, ce qui transforme l'API en un véritable "oracle" pour
  un attaquant.
- **Une frontière de décision précise a été localisée en 12 requêtes
  seulement.** Sans cette information de confiance (juste la classe
  finale Good/Bad), le même travail aurait nécessité beaucoup plus de
  requêtes et donné une précision bien moindre.
- **Risque concret (attaque d'évasion) :** un attaquant peut ajuster
  un dossier de crédit "à la marge" (ex. `debt_ratio` juste en dessous du
  seuil) pour maximiser ses chances d'obtenir "Good Credit", sans avoir
  un dossier réellement solide.

---

## Étape 17 — Abus de requêtes (`attacks/query_abuse.py`)

### Attaque
Envoi de 50 requêtes séquentielles puis 100 requêtes en parallèle
(20 threads simultanés) pour observer si l'API applique une limite de
débit (rate limiting) ou montre des signes de saturation.

### Résultats obtenus

| Test | Requêtes | Temps total | Débit | Codes observés |
|---|---|---|---|---|
| Séquentiel | 50 | 3.16 s | 15.8 req/s | `{200: 50}` |
| Parallèle (20 threads) | 100 | 4.00 s | 25.0 req/s | `{200: 100}` |

**Aucun code `429 Too Many Requests` observé, dans aucun des deux tests.**

### Problèmes trouvés
- **Aucune limite de débit (rate limiting) n'est en place.** L'API a
  encaissé toutes les requêtes, séquentielles comme parallèles, sans
  jamais refuser ou ralentir le trafic.
- **Conséquences :**
  - Un attaquant peut envoyer un volume de requêtes illimité, ouvrant la
    porte à un déni de service (DoS) si le volume est poussé plus loin.
  - Ce même manque de limite est ce qui rend possible, à grande échelle,
    l'attaque d'extraction de modèle (étape 18) : rien n'empêche
    d'envoyer des milliers de requêtes pour reconstruire le comportement
    du modèle.

---

## Étape 18 — Extraction de modèle (`attacks/model_extraction.py`, optionnelle)

### Attaque
Collecte de 400 exemples aléatoires interrogés directement sur l'API
(sans jamais accéder à `model.pkl`), puis entraînement d'un modèle
"clone" (Decision Tree) sur ces paires (entrée, sortie). La fidélité du
clone est ensuite mesurée sur 60 nouveaux exemples jamais vus.

### Résultats obtenus

```
Données collectées : 400 lignes, 34 colonnes
Distribution des classes récupérées : Good=354, Bad=46

Fidélité du clone par rapport à l'API originale : 83.3%
```

❌ **Le clone reproduit fidèlement le modèle original avec seulement
400 requêtes**, sans jamais avoir eu accès au fichier `model.pkl`.

### Problèmes trouvés
- **Le modèle peut être "volé" (cloné) rien qu'en interrogeant l'API.**
  Une fidélité de 83.3 % avec seulement 400 requêtes est un score élevé :
  avec plus de requêtes et un modèle clone plus sophistiqué (ex. Random
  Forest au lieu d'un simple arbre), la fidélité serait probablement
  encore meilleure.
- **Cette attaque est directement facilitée par deux failles déjà
  identifiées :** l'absence de rate limiting (étape 17, qui permet de
  générer rapidement un grand nombre d'exemples) et l'exposition des
  probabilités complètes (étape 16, qui rend le clone plus précis qu'un
  clone entraîné seulement sur des classes 0/1).
- **Conséquence business :** le modèle représente un investissement
  (temps de collecte de données, entraînement, tuning). L'exposer ainsi
  permet à un concurrent ou un attaquant de le répliquer sans effort
  comparable.
- **Observation additionnelle :** la distribution des classes générées
  par des profils aléatoires est très déséquilibrée (Good=354, Bad=46),
  ce qui suggère que le modèle a tendance à prédire "Good Credit" pour
  la majorité des profils aléatoires — signe supplémentaire du
  sur-apprentissage déjà observé lors de l'entraînement (écart
  Train/Test de 23.71 points sur l'accuracy).

---

## Étape 19 — Boundary Probing (`attacks/boundary_probing.py`)

### Attaque
Variation systématique d'une seule variable à la fois (`annual_income_normalized`,
`debt_ratio`, `past_due_count`) pour localiser les seuils exacts où la
prédiction change, et test d'une micro-variation infime pour évaluer la
stabilité du modèle.

### Résultats obtenus (extraits)

**Revenu annuel normalisé :** bascule de "Good Credit" à "Bad Credit"
entre `-0.3` et `-0.2`.

**Ratio d'endettement (`debt_ratio`) :** comportement instable, avec
plusieurs bascules successives entre `0.30` et `0.45` (Bad → Good → Bad →
Good), avant de se stabiliser en "Good Credit" au-delà de `0.5`.

**Nombre d'incidents de paiement (`past_due_count`) :** résultat le plus
préoccupant — la prédiction bascule de **"Bad Credit" à "Good Credit"
dès qu'on passe de 0 à 1 incident**, et reste "Good Credit" jusqu'à
10 incidents.

### Problèmes trouvés
- **Comportement illogique du modèle sur `past_due_count`.** Un client
  avec *plus* d'incidents de paiement obtient une *meilleure* évaluation
  qu'un client sans aucun incident. C'est contre-intuitif d'un point de
  vue métier et constitue un signal fort de sur-apprentissage (le
  modèle a appris une corrélation présente dans les données
  d'entraînement qui ne reflète pas une vraie relation de cause à effet).
- **Instabilité locale sur `debt_ratio`.** Plusieurs bascules successives
  sur un intervalle resserré (`0.30`–`0.45`) indiquent une frontière de
  décision peu lisse, potentiellement due au nombre limité d'arbres/
  profondeur du Random Forest ou à un manque de données d'entraînement
  dans cette zone.
- **Risque d'évasion combiné avec l'étape 16 :** un attaquant qui
  combine le sondage de frontière avec le score de confiance peut
  construire un profil "juste assez bon" pour obtenir "Good Credit" sans
  avoir un dossier réellement solide — par exemple, ajouter un incident
  de paiement au lieu de zéro améliore paradoxalement le score.

---

## Résumé global des vulnérabilités identifiées

| # | Faille | Preuve concrète | Sévérité |
|---|---|---|:---:|
| 1 | Pas de validation de plage de valeurs | Valeurs négatives / extrêmes acceptées (étape 15) | Moyenne |
| 2 | Score de confiance et probabilités exposés | Frontière localisée en 12 requêtes (étape 16) | **Élevée** |
| 3 | Pas de rate limiting | 100 requêtes parallèles encaissées sans code 429 (étape 17) | **Élevée** |
| 4 | Modèle clonable via l'API | Clone fidèle à 83.3 % avec 400 requêtes (étape 18) | **Élevée** |
| 5 | Comportement instable / illogique du modèle | Bascules multiples et incohérence sur `past_due_count` (étape 19) | Moyenne |
| 6 | Aucune authentification | Toutes les requêtes ci-dessus ont été acceptées sans clé API | **Élevée** |

---

## Prochaine étape : Phase C (Blue Team)

Ces résultats concrets serviront de base à la phase de correction :
- Ajouter une authentification (clé API / token)
- Mettre en place un rate limiting (ex. `slowapi`)
- Ne plus exposer la confiance détaillée (ou l'arrondir/la masquer)
- Valider strictement les plages de valeurs acceptables (ex. `Field(ge=0)`
  dans Pydantic)
- Envisager un ré-entraînement du modèle avec un jeu de données plus
  équilibré et une régularisation plus forte pour réduire le
  sur-apprentissage observé
