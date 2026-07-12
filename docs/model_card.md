# Model Card — Credit Risk Prediction Model

## Milestone 3 - Étape 7

Carte d'identité du modèle de prédiction du risque de crédit.

---

## Identité du modèle

| Champ | Valeur |
|---|---|
| **Nom** | Credit Risk Prediction Model |
| **Type** | Classification binaire |
| **Algorithme** | Random Forest Classifier (scikit-learn) |
| **Version** | 1.0 |
| **Date d'entraînement** | Voir `models/metrics.json` |
| **Fichier** | `models/model.pkl` |
| **Hash SHA-256** | Voir `models/model_hash.txt` |
| **Framework** | scikit-learn |

---

## Objectif

Prédire si un client est susceptible d'être un **bon payeur**
("Good Credit") ou un **mauvais payeur** ("Bad Credit") sur la base de
ses caractéristiques socio-démographiques et financières, afin
d'aider à la décision d'octroi de crédit.

⚠️ Ce modèle est un **prototype pédagogique** (Milestone 2/3 d'un
projet de sécurisation de pipeline ML) et n'est **pas destiné à une
mise en production réelle** en l'état — voir la section Limites.

---

## Utilisateurs prévus

- **Utilisateurs directs :** applications internes ou analystes
  crédit interrogeant l'API via une clé API pour obtenir une
  recommandation automatisée.
- **Utilisateurs indirects :** clients demandeurs de crédit, dont le
  dossier est évalué par ce modèle (sans accès direct à l'API).
- **Non destiné à :** une utilisation comme seul critère de décision
  finale. Le modèle doit être un outil d'aide à la décision, avec
  validation humaine, notamment compte tenu des limites décrites
  ci-dessous.

---

## Données utilisées

- **Source :** dataset `data_credit_risk.csv` (3 200 clients, 25
  colonnes brutes)
- **Traitement :** nettoyage, suppression des identifiants directs,
  anonymisation des données financières, pseudonymisation des
  quasi-identifiants (voir `docs/dataset_datasheet.md` pour le détail
  complet)
- **Dataset final d'entraînement :** `data/processed/credit_processed.csv`
  (3 200 lignes, 37 features numériques/booléennes après encodage)
- **Répartition Train/Test :** 80 % / 20 %, stratifiée
- **Distribution de la cible :** 1 744 "Good Credit" (54.5 %) / 1 456
  "Bad Credit" (45.5 %) — raisonnablement équilibrée

---

## Performances

Mesurées sur le jeu de test (640 clients, jamais vus pendant
l'entraînement) :

| Métrique | Test Set | Train Set |
|---|:---:|:---:|
| Accuracy | 67.81 % | 91.52 % |
| Precision | 65.92 % | 91.36 % |
| Recall | 60.48 % | 89.87 % |
| F1-score | 63.08 % | 90.61 % |

**Matrice de confusion (Test Set) :**

|  | Prédit Good | Prédit Bad |
|---|:---:|:---:|
| **Réel Good** | 258 (VN) | 91 (FP) |
| **Réel Bad** | 115 (FN) | 176 (VP) |

---

## Limites connues

1. **Sur-apprentissage (overfitting) significatif.** L'écart de 23.71
   points entre l'accuracy sur le Train (91.52 %) et sur le Test
   (67.81 %) indique que le modèle a mémorisé des particularités du
   jeu d'entraînement plutôt que d'apprendre des règles généralisables.
2. **Comportement contre-intuitif détecté.** Les tests de boundary
   probing (Phase B, Red Team) ont montré qu'un client avec *plus*
   d'incidents de paiement (`past_due_count`) obtient parfois une
   *meilleure* évaluation qu'un client sans aucun incident — signal
   clair que le modèle a appris une corrélation fallacieuse présente
   dans les données d'entraînement plutôt qu'une vraie relation
   causale.
3. **Frontières de décision instables.** Sur certaines variables
   (ex. `debt_ratio`), la prédiction bascule plusieurs fois sur un
   intervalle resserré, signe d'un modèle peu régularisé.
4. **Taille limitée du dataset.** 3 200 exemples est un volume modeste
   pour un Random Forest à 100 arbres ; davantage de données
   réduiraient probablement le sur-apprentissage.
5. **Performance modeste en absolu.** Une accuracy de 67.81 % reste
   proche d'un modèle naïf pour un problème à deux classes proches de
   l'équilibre — insuffisant pour une décision automatisée sans
   supervision humaine.

---

## Risques de sécurité

- **Extraction de modèle (model stealing) :** un modèle clone entraîné
  sur seulement 400 requêtes à l'API a atteint 83.3 % de fidélité avec
  l'original (voir `docs/attack_report.md`, étape 18). Ce risque est
  atténué mais pas éliminé par le rate limiting mis en place en Phase C.
- **Attaque d'évasion :** en Phase A (avant sécurisation), le score de
  confiance exposé permettait de localiser précisément la frontière de
  décision (12 requêtes suffisaient). Ce risque est corrigé en Phase C
  par le masquage du score exact.
- **Biais potentiel :** le comportement contre-intuitif sur
  `past_due_count` pourrait, s'il n'est pas corrigé, conduire à des
  décisions de crédit injustifiées pour certains profils — un audit de
  biais plus poussé (par catégorie démographique) serait nécessaire
  avant toute utilisation réelle.
- **Dépendance à l'intégrité du fichier modèle :** un hash SHA-256 est
  fourni (`models/model_hash.txt`) pour détecter toute altération non
  autorisée de `model.pkl`, mais aucune vérification automatique de ce
  hash n'est encore intégrée au démarrage de l'API (amélioration
  future, voir `docs/risks_and_improvements.md`).

---

## Recommandation d'usage

Ce modèle doit être utilisé **uniquement à des fins pédagogiques ou de
démonstration** dans son état actuel. Une mise en production réelle
nécessiterait au minimum : un ré-entraînement avec plus de données et
une meilleure régularisation, un audit de biais formel, et
l'intégration de la vérification automatique du hash du modèle au
démarrage de l'API.
