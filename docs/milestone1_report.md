# RAPPORT DE NETTOYAGE ET PRÉPARATION DES DONNÉES

**Projet :** Secure Credit Risk Project  

## INTRODUCTION

Ce rapport documente les transformations effectuées sur le dataset `credit.csv` pour le préparer à l'entraînement du modèle Machine Learning.

**Objectifs :**
- Nettoyer les données
- Protéger les données personnelles
- Préparer un dataset ML-ready

**Dataset final :** `credit_processed.csv`



## STRUCTURE INITIALE DU DATASET

| Attribut | Valeur |
|----------|--------|
| **Lignes** | 3 200 |
| **Colonnes** | 25 |
| **Valeurs manquantes** | 0 |
| **Variable cible** | `credit_risk` (good/bad) |



## 1. COLONNES SUPPRIMÉES

### Identifiants directs (PII)

| Colonne | Raison |
|---------|--------|
| `customer_id` | Identifiant unique du client |
| `full_name` | Nom complet du client |
| `email` | Adresse email du client |
| `phone` | Numéro de téléphone |
| `national_id` | Numéro d'identité nationale |

**Pourquoi ?** Ces colonnes permettent d'identifier directement une personne. Elles sont supprimées pour :
- Protéger la vie privée des clients
- Respecter le RGPD
- Ces colonnes ne sont pas utiles pour le modèle



## 2. TRANSFORMATIONS EFFECTUÉES

### 2.1 Traitement des valeurs incorrectes

**Action :** Détection et correction des valeurs aberrantes dans les colonnes numériques  
**Méthode :** Méthode IQR (remplacement par la médiane)  
**Colonnes concernées :** `age`, `annual_income`, `savings_balance`, `checking_balance`, `loan_amount`, `loan_duration_months`, `existing_credits`, `past_due_count`, `credit_history_score`, `debt_ratio`

**Pourquoi ?** Les valeurs aberrantes peuvent fausser les résultats du modèle.



### 2.2 Traitement des valeurs manquantes

**Action :** Remplissage des valeurs manquantes  
**Méthode :** 
- Colonnes numériques → remplacement par la médiane
- Colonnes catégorielles → remplacement par le mode

**Pourquoi ?** Éviter les erreurs et garder toutes les lignes pour l'entraînement.



### 2.3 Conversion des types de données

| Colonne | Avant | Après |
|---------|-------|-------|
| `application_date` | object | datetime |
| `gender`, `region`, `marital_status`, etc. | object | category |

**Pourquoi ?** Optimiser la mémoire et préparer l'encodage.



### 2.4 Encodage des variables catégorielles

**a) Label Encoding (variables binaires)**

| Colonne | Encodage |
|---------|----------|
| `gender` | Male → 0, Female → 1 |
| `marital_status` | Single → 0, Married → 1, Divorced → 2, Widowed → 3 |
| `housing_status` | Rent → 0, Own → 1, Other → 2 |

**Pourquoi ?** Les ordinateurs ne comprennent que les nombres.

**b) One-Hot Encoding (variables multicatégories)**

| Colonne | Colonnes créées |
|---------|-----------------|
| `region` | `region_Nouakchott`, `region_Nouadhibou`, etc. |
| `education_level` | `education_level_primary`, `education_level_secondary`, etc. |
| `employment_status` | `employment_status_employed`, `employment_status_unemployed`, etc. |
| `loan_purpose` | `loan_purpose_business`, `loan_purpose_car`, etc. |

**Pourquoi ?** Éviter de créer un faux ordre entre les catégories.

**c) Encodage de la variable cible**

| Colonne | Mapping |
|---------|---------|
| `credit_risk` | good → 0, bad → 1 |

**Pourquoi ?** Pour que le modèle puisse apprendre à prédire.



### 2.5 Anonymisation des données financières

| Colonne | Transformation |
|---------|---------------|
| `annual_income` | Normalisation (StandardScaler) |
| `savings_balance` | Normalisation (StandardScaler) |
| `checking_balance` | Normalisation (StandardScaler) |
| `loan_amount` | Normalisation (StandardScaler) |

**Pourquoi ?** Masquer les montants réels tout en gardant l'information relative.



### 2.6 Pseudonymisation des quasi-identifiants

| Colonne | Transformation |
|---------|---------------|
| `age` | Agrégation en tranches : 18-25, 26-35, 36-45, 46-55, 56+ |
| `annual_income_normalized` | Catégorisation : Très bas, Bas, Élevé, Très élevé |

**Pourquoi ?** Réduire le risque de ré-identification des clients.



### 2.7 Masquage des données

| Colonne | Transformation |
|---------|---------------|
| `customer_id` | → `customer_reference` (USER0001, USER0002, ...) |

**Pourquoi ?** Créer des références anonymes sans lien avec le client réel.



## 3. RÉSUMÉ DES TRANSFORMATIONS

| Étape | Actions | Résultat |
|-------|---------|----------|
| **Nettoyage** | Correction valeurs aberrantes, remplissage valeurs manquantes, conversion types, encodage | Dataset propre et numérique |
| **Protection** | Suppression PII, anonymisation financière, pseudonymisation, masquage | Dataset anonyme et conforme RGPD |



## 4. COMPOSITION DU DATASET FINAL

### Colonnes conservées

| Type | Colonnes |
|------|----------|
| **Quasi-identifiants** | `age_group`, `gender_encoded`, `marital_status_encoded`, `housing_status_encoded`, `income_category` |
| **Données financières** | `annual_income_normalized`, `savings_balance_normalized`, `checking_balance_normalized`, `loan_amount_normalized` |
| **Indicateurs de crédit** | `loan_duration_months`, `existing_credits`, `past_due_count`, `credit_history_score`, `debt_ratio` |
| **One-Hot encodées** | `region_*`, `education_level_*`, `employment_status_*`, `loan_purpose_*` |
| **Cible** | `credit_risk_encoded` |
