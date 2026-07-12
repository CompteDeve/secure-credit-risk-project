# Dataset Datasheet — Credit Risk Dataset

## Milestone 3 - Étape 8

Carte d'identité du dataset utilisé pour entraîner le modèle de
prédiction du risque de crédit.

---

## Origine du dataset

- **Fichier source :** `data_credit_risk.csv`
- **Volume :** 3 200 lignes (clients), 25 colonnes brutes
- **Qualité :** aucune valeur manquante détectée sur l'ensemble des
  colonnes
- **Nature :** données synthétiques/pédagogiques simulant un
  portefeuille de demandes de crédit (région : Mauritanie, à en juger
  par les régions présentes : Nouakchott, Trarza, Assaba, etc.)

---

## Description des colonnes (avant traitement)

| Type | Nombre | Colonnes |
|---|:---:|---|
| Numérique (int64) | 6 | `national_id`, `age`, `loan_duration_months`, `existing_credits`, `past_due_count`, `credit_history_score` |
| Numérique (float64) | 5 | `annual_income`, `savings_balance`, `checking_balance`, `loan_amount`, `debt_ratio` |
| Catégoriel/texte | 13 | `customer_id`, `full_name`, `email`, `phone`, `gender`, `region`, `marital_status`, `education_level`, `employment_status`, `housing_status`, `loan_purpose`, `application_date` |
| Booléen | 1 | `consent_flag` |
| **Variable cible** | 1 | `credit_risk` ("good" / "bad") |

**Statistiques principales (avant traitement) :**

| Variable | Min | Max | Moyenne | Médiane |
|---|---:|---:|---:|---:|
| Âge | 18 ans | 75 ans | 38.5 ans | 38 ans |
| Revenu annuel | 4 000 | 120 000 | 32 224 | 27 587 |
| Montant du prêt | 1 298 | 81 907 | 12 058 | 10 395 |
| Durée du prêt | 6 mois | 60 mois | 26.7 mois | 24 mois |
| Ratio d'endettement | 0.01 | 1.80 | 0.65 | 0.52 |

---

## Données sensibles identifiées

### A) Identifiants directs (5)
`customer_id`, `full_name`, `email`, `phone`, `national_id`

Ces colonnes permettent d'identifier directement et sans ambiguïté un
individu. **Toutes ont été supprimées** avant l'entraînement.

### B) Quasi-identifiants (7)
`age`, `gender`, `region`, `marital_status`, `education_level`,
`employment_status`, `housing_status`

Pris isolément, ces champs n'identifient pas un individu, mais leur
combinaison peut permettre une réidentification (ex. croiser âge +
région + statut marital pourrait suffire à isoler un individu dans une
petite population). **Toutes ont été pseudonymisées ou encodées**
(âge → tranches, autres → encodage numérique/One-Hot).

### C) Données financières sensibles (7)
`annual_income`, `savings_balance`, `checking_balance`, `loan_amount`,
`loan_duration_months`, `existing_credits`, `debt_ratio`

Données à caractère financier, sensibles au titre de la vie privée
économique. **Anonymisées par normalisation** (StandardScaler) pour
les quatre premières ; les autres sont conservées telles quelles car
moins directement identifiantes, mais restent utilisées uniquement à
des fins de calcul du modèle.

---

## Nettoyage appliqué

1. **Détection des valeurs aberrantes** : méthode IQR élargie
   (bornes = Q1 − 3×IQR / Q3 + 3×IQR) sur toutes les colonnes
   numériques, remplacement des valeurs aberrantes détectées par la
   médiane de la colonne.
2. **Conversion des types** : `application_date` en `datetime`,
   `consent_flag` en `bool`, colonnes catégorielles en type `category`.
3. **Vérification des valeurs catégorielles** : contrôle manuel des
   valeurs uniques de chaque colonne catégorielle pour détecter des
   incohérences (fautes de frappe, valeurs incohérentes).

---

## Transformations appliquées

| Transformation | Colonnes concernées | Méthode |
|---|---|---|
| Suppression | Identifiants directs (5 colonnes) | Suppression pure et simple |
| Anonymisation | Données financières (4 colonnes) | StandardScaler (moyenne 0, écart-type 1) |
| Pseudonymisation | Âge, revenu | Âge → 5 tranches (`18-25` à `56+`) ; revenu → 4 quartiles |
| Masquage | Identifiant client | Remplacement par référence générique (`USER0001`, ...) |
| Encodage binaire | `gender`, `marital_status`, `housing_status`, `consent_flag` | Label Encoding |
| Encodage multi-catégorie | `region`, `education_level`, `employment_status`, `loan_purpose` | One-Hot Encoding |
| Encodage cible | `credit_risk` | Label Encoding (good=0, bad=1) |

**Résultat final :** `data/processed/credit_processed.csv`,
3 200 lignes × 41 colonnes (dont 37 features utilisées pour
l'entraînement, après retrait des colonnes non numériques restantes).

---

## Risques de confidentialité résiduels

Même après suppression des identifiants directs, un risque de
**réidentification par combinaison de quasi-identifiants** subsiste
théoriquement (ex. croiser tranche d'âge + région + statut marital
dans un sous-groupe très restreint de la population). Ce risque est
réduit mais pas nul, car :
- les quasi-identifiants pseudonymisés (tranches d'âge, catégories de
  revenu) réduisent la granularité de l'information, mais ne
  l'éliminent pas complètement ;
- le dataset n'a pas fait l'objet d'une vérification formelle de
  k-anonymat (aucune garantie qu'au moins *k* individus partagent
  chaque combinaison de quasi-identifiants).

**Recommandation :** avant toute publication ou partage externe du
dataset traité, effectuer une vérification de k-anonymat (k ≥ 5
recommandé) et envisager un regroupement plus grossier des
quasi-identifiants si nécessaire.

---

## Hypothèses sur le consentement

Le dataset contient une colonne `consent_flag` (booléenne), supposée
indiquer si le client a consenti à l'utilisation de ses données pour
l'évaluation de son risque de crédit et/ou l'entraînement de modèles.

⚠️ **Hypothèse non vérifiée dans ce projet pédagogique :** on suppose
que ce indicateur reflète un consentement valide et éclairé recueilli
au moment de la demande de crédit. Dans un contexte réel de production,
il faudrait :
- vérifier que seuls les enregistrements avec `consent_flag = True`
  sont utilisés pour l'entraînement (ce filtrage n'a pas été appliqué
  dans la version actuelle du pipeline) ;
- documenter précisément la base légale du traitement (ex. consentement
  explicite, intérêt légitime, obligation contractuelle) conformément
  aux réglementations applicables sur la protection des données.

---

## Durée de conservation

Non définie formellement dans ce projet pédagogique. **Recommandation**
pour une mise en production réelle :
- **Dataset brut (contenant des identifiants) :** conservation limitée
  à la durée strictement nécessaire à la préparation du dataset
  ML-ready, puis suppression ou archivage sécurisé (chiffré, accès
  restreint).
- **Dataset ML-ready (anonymisé/pseudonymisé) :** conservation liée au
  cycle de vie du modèle (ex. tant que le modèle est en production +
  durée légale de traçabilité), avec réévaluation périodique de la
  nécessité de le conserver.
- **Logs de l'API (`logs/api.log`) :** rotation automatique déjà en
  place (5 Mo par fichier, 3 fichiers de sauvegarde maximum, voir
  `src/logging_config.py`), limitant la durée de rétention des traces
  d'usage.
