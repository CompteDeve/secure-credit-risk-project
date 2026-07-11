# ACCESS CONTROL MATRIX

## INTRODUCTION

Cette matrice définit les droits d'accès aux différentes ressources du projet en fonction des rôles.

**Légende :**
- ✅ **Oui** : Accès autorisé
- ❌ **Non** : Accès interdit
- ⚠️ **Restreint** : Accès limité



## MATRICE DES ACCÈS

| Rôle | Raw Data | Processed Data | Model | API | Logs |
|------|----------|---------------|-------|-----|------|
| **Data Engineer** | ✅ Oui | ✅ Oui | ❌ Non | ❌ Non | ✅ Oui |
| **Data Scientist** | ❌ Non | ✅ Oui | ✅ Oui | ❌ Non | ❌ Non |
| **API Service** | ❌ Non | ❌ Non | ✅ Oui | ✅ Oui | ✅ Oui |
| **Auditor** | ❌ Non | ✅ Oui | ✅ Oui | ❌ Non | ✅ Oui |



## DÉTAIL DES ACCÈS PAR RÔLE

### 1. Data Engineer

| Ressource | Accès | Justification |
|-----------|-------|---------------|
| **Raw Data** | ✅ Oui | Pour construire et maintenir le pipeline de données |
| **Processed Data** | ✅ Oui | Pour valider le traitement des données |
| **Model** | ❌ Non | Pas besoin pour la gestion des données |
| **API** | ❌ Non | Pas besoin pour la gestion des données |
| **Logs** | ✅ Oui | Pour surveiller le pipeline et les erreurs système |

**Responsabilités :**
- Construction du pipeline ETL
- Maintenance de l'infrastructure
- Surveillance des logs système



### 2. Data Scientist

| Ressource | Accès | Justification |
|-----------|-------|---------------|
| **Raw Data** | ❌ Non | Protéger la vie privée des clients (PII) |
| **Processed Data** | ✅ Oui | Pour l'analyse et la modélisation |
| **Model** | ✅ Oui | Pour entraîner et améliorer le modèle |
| **API** | ❌ Non | Pas besoin pour la recherche |
| **Logs** | ❌ Non | Pas besoin pour la recherche |

**Responsabilités :**
- Analyse exploratoire des données
- Développement du modèle ML
- Optimisation des performances
- Feature engineering



### 3. API Service

| Ressource | Accès | Justification |
|-----------|-------|---------------|
| **Raw Data** | ❌ Non | Protéger les données brutes |
| **Processed Data** | ❌ Non | Pas besoin pour les prédictions |
| **Model** | ✅ Oui | Pour faire des prédictions |
| **API** | ✅ Oui | Pour servir les requêtes |
| **Logs** | ✅ Oui | Pour tracer les appels API |

**Responsabilités :**
- Servir le modèle via l'API
- Gérer les requêtes utilisateur
- Journaliser les appels API


### 4. Auditor

| Ressource | Accès | Justification |
|-----------|-------|---------------|
| **Raw Data** | ❌ Non | Protéger la vie privée (PII) |
| **Processed Data** | ✅ Oui | Pour vérifier la qualité des données |
| **Model** | ✅ Oui | Pour auditer les performances |
| **API** | ❌ Non | Pas besoin pour l'audit |
| **Logs** | ✅ Oui | Pour vérifier la conformité |

**Responsabilités :**
- Auditer la qualité des données
- Vérifier la conformité RGPD
- Contrôler les performances du modèle
- Surveiller les accès


## PRINCIPES DE SÉCURITÉ

### Moindre Privilège

Chaque rôle n'a que les accès strictement nécessaires à ses fonctions.

### Séparation des Tâches

- Data Engineer : Gère l'infrastructure (Raw, Logs)
- Data Scientist : Gère la modélisation (Processed, Model)
- API Service : Gère la production (Model, API, Logs)
- Auditor : Vérifie la conformité (Processed, Model, Logs)

### Protection des Données

- Raw Data : Accès limité (Data Engineer uniquement)
- Processed Data : Accès contrôlé (Data Scientist, Data Engineer, Auditor)
- Model : Accès contrôlé (Data Scientist, API Service, Auditor)

### Journalisation

Tous les accès sont journalisés dans les logs pour permettre l'audit.



## RÉSUMÉ DES ACCÈS

| | Raw Data | Processed Data | Model | API | Logs |
|---|----------|---------------|-------|-----|------|
| **Data Engineer** | 🔴 | 🟡 | ⚪ | ⚪ | 🟡 |
| **Data Scientist** | ⚪ | 🟡 | 🟡 | ⚪ | ⚪ |
| **API Service** | ⚪ | ⚪ | 🟡 | 🟡 | 🟡 |
| **Auditor** | ⚪ | 🟡 | 🟡 | ⚪ | 🟡 |

**Légende :**
- 🔴 Accès strictement contrôlé (un seul rôle)
- 🟡 Accès contrôlé (plusieurs rôles)
- ⚪ Pas d'accès
