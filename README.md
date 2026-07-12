# Secure Credit Risk Project

Pipeline de machine learning sécurisé pour la prédiction du risque de
crédit : préparation des données respectueuse de la vie privée,
entraînement d'un modèle, API FastAPI, tests d'attaque (Red Team) et
protections (Blue Team), conteneurisation Docker.

---

## Structure du projet

```
secure-credit-risk-project/
├── data/
│   └── processed/
│       └── credit_processed.csv     # dataset ML-ready (généré)
├── models/
│   ├── model.pkl                    # modèle entraîné (généré)
│   ├── metrics.json                 # métriques (généré)
│   └── model_hash.txt               # hash SHA-256 du modèle (généré)
├── src/
│   ├── api.py                       # API FastAPI sécurisée
│   └── logging_config.py            # configuration des logs
├── attacks/                         # scripts Red Team
├── tests/
│   └── test_api_security.py         # tests Blue Team automatisés
├── scripts/
│   └── calculate_model_hash.py      # calcul du hash du modèle
├── docs/                            # rapports et gouvernance
├── logs/                            # logs générés à l'exécution
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 1. Installer les dépendances

Nécessite **Python 3.11+**.

```bash
pip install -r requirements.txt
```

Pour lancer les tests, installer en plus :
```bash
pip install pytest httpx
```

Pour rejouer les scripts Red Team :
```bash
pip install requests scikit-learn numpy
```

---

## 2. Obtenir / générer le dataset

Le dataset ML-ready (`data/processed/credit_processed.csv`) est produit
à partir du dataset brut (`data_credit_risk.csv`) via le notebook de
préparation des données (nettoyage, anonymisation, pseudonymisation,
encodage — voir `docs/dataset_datasheet.md` pour le détail complet des
transformations).

Si le fichier `data/processed/credit_processed.csv` n'existe pas
encore :
1. Placer `data_credit_risk.csv` à la racine du projet.
2. Exécuter le notebook/script de préparation des données (Milestone 1).
3. Le fichier `data/processed/credit_processed.csv` est généré
   automatiquement.

---

## 3. Entraîner le modèle

```bash
python src/train.py
```

Cela génère :
- `models/model.pkl` — le modèle entraîné (Random Forest)
- `models/metrics.json` — les métriques de performance (accuracy,
  precision, recall, F1-score)

Puis calculer le hash d'intégrité du modèle :
```bash
python scripts/calculate_model_hash.py
```
Cela génère `models/model_hash.txt`, utilisé pour vérifier que le
fichier `model.pkl` n'a pas été altéré.

---

## 4. Lancer l'API

### En local (sans Docker)

```bash
uvicorn src.api:app --port 8080
```

L'API est accessible sur `http://127.0.0.1:8080`.
Documentation interactive (Swagger) : `http://127.0.0.1:8080/docs`

**Authentification requise** : toutes les requêtes vers `/predict`
doivent inclure l'en-tête `X-API-Key`. Dans Swagger, cliquer sur le
bouton **"Authorize"** en haut à droite et entrer la clé (par défaut :
`demo-key-milestone2-2026`, définie via la variable d'environnement
`API_KEY`).

Exemple avec curl :
```bash
curl -X POST "http://127.0.0.1:8080/predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-milestone2-2026" \
  -d @exemple_client.json
```

### Avec Docker (recommandé pour un déploiement reproductible)

```bash
docker compose up --build
```

L'API est accessible sur `http://localhost:8080`. Les logs générés
dans le conteneur sont automatiquement synchronisés dans `./logs` sur
la machine hôte.

Pour arrêter :
```bash
docker compose down
```

---

## 5. Lancer les tests

### Tests de sécurité automatisés (Blue Team)

Depuis la racine du projet (le modèle doit être présent dans
`models/model.pkl`) :

```bash
pytest tests/test_api_security.py -v
```

Ces 12 tests vérifient : l'authentification par clé API, la validation
stricte des données, le masquage du score de confiance, les messages
d'erreur génériques, et la limitation du nombre de requêtes.

### Scripts d'attaque (Red Team)

Nécessite l'API lancée dans un terminal séparé (`uvicorn src.api:app
--port 8080`).  Ces scripts ciblent l'API **baseline non sécurisée**
(Phase A) à des fins pédagogiques ; contre l'API sécurisée (Phase C),
la plupart échoueront désormais (c'est le but).

```bash
cd attacks
python malformed_inputs.py
python confidence_leakage.py
python query_abuse.py
python boundary_probing.py
python model_extraction.py   
```

---

## Documentation complète

| Document | Contenu |
|---|---|
| `docs/final_report.pdf` | **Rapport principal** — synthèse complète du projet |
| `docs/model_card.md` | Carte d'identité du modèle |
| `docs/dataset_datasheet.md` | Carte d'identité du dataset |
| `docs/model_lifecycle.md` | Cycle de vie complet du modèle |
| `docs/attack_report.md` | Détail des attaques Red Team |
| `docs/mitigation_report.md` | Détail des protections Blue Team |
| `docs/before_after_metrics.md` | Comparaison avant/après sécurisation |
| `docs/risk_register.md` | Registre des risques |
| `docs/security_checklist.md` | Liste de vérification de sécurité |
| `docs/risks_and_improvements.md` | Risques restants et pistes d'amélioration |

---

## Notes importantes

- La clé API par défaut (`demo-key-milestone2-2026`) est fournie
  uniquement pour la démonstration. **Ne jamais l'utiliser telle
  quelle en production** — la définir via une variable d'environnement
  ou un fichier `.env` non versionné.
- Ce projet est un prototype pédagogique. Ses limites (sur-apprentissage
  du modèle, absence de HTTPS, authentification statique, etc.) sont
  documentées explicitement dans `docs/risks_and_improvements.md`.
