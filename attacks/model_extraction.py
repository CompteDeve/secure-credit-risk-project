"""
============================================
MILESTONE 2 - PHASE B (RED TEAM)
ÉTAPE 18 (OPTIONNELLE) : Extraction de modèle (model extraction)
============================================
Idée : sans jamais avoir accès à model.pkl, on interroge l'API des
centaines de fois avec des entrées aléatoires, puis on entraîne un
NOUVEAU modèle ("modèle clone") sur ces paires (entrée, sortie).

Si le clone reproduit fidèlement le comportement de l'API originale,
cela prouve que l'API a "fuité" son modèle : un attaquant peut voler
le savoir-faire du modèle (souvent une propriété intellectuelle
coûteuse à développer) rien qu'en l'interrogeant.

⚠️ Ce script est plus lourd : il nécessite scikit-learn côté attaquant
(pip install scikit-learn) et peut prendre 1-2 minutes.
"""

import requests
import random
import copy
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from base_payload import BASE_URL, VALID_PAYLOAD

URL = f"{BASE_URL}/predict"

NB_SAMPLES = 400  # nombre de requêtes envoyées à l'API cible pour construire le clone

# Colonnes numériques CONTINUES (float) qu'on va faire varier aléatoirement
FLOAT_FIELDS = [
    "annual_income_normalized", "savings_balance_normalized",
    "checking_balance_normalized", "loan_amount_normalized",
    "loan_duration_months", "credit_history_score", "debt_ratio"
]

# Colonnes numériques ENTIÈRES (int) — doivent rester des entiers, sinon FastAPI renvoie 422
INT_FIELDS = ["existing_credits", "past_due_count"]

NUMERIC_FIELDS = FLOAT_FIELDS + INT_FIELDS  # ordre utilisé pour construire le clone

BOOL_FIELDS = [k for k, v in VALID_PAYLOAD.items() if isinstance(v, bool)]


def random_payload():
    """Génère un client aléatoire mais plausible."""
    payload = copy.deepcopy(VALID_PAYLOAD)
    for field in FLOAT_FIELDS:
        payload[field] = round(random.uniform(-2, 2), 3)
    for field in INT_FIELDS:
        payload[field] = random.randint(0, 5)
    for field in BOOL_FIELDS:
        payload[field] = random.choice([True, False])
    return payload


def main():
    print("=" * 60)
    print("ÉTAPE 18 : Extraction de modèle (attaque de clonage)")
    print("=" * 60)

    print(f"\n--- Étape 1 : collecte de {NB_SAMPLES} exemples via l'API cible ---")
    X, y = [], []
    feature_order = NUMERIC_FIELDS + BOOL_FIELDS  # ordre fixe pour le clone

    for i in range(NB_SAMPLES):
        payload = random_payload()
        response = requests.post(URL, json=payload, timeout=5)
        result = response.json()

        row = [payload[f] for f in NUMERIC_FIELDS] + [int(payload[f]) for f in BOOL_FIELDS]
        X.append(row)
        y.append(result["prediction_encoded"])

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{NB_SAMPLES} requêtes envoyées...")

    X = np.array(X)
    y = np.array(y)

    print(f"\nDonnées collectées : {X.shape[0]} lignes, {X.shape[1]} colonnes")
    print(f"Distribution des classes récupérées : Good={sum(y == 0)}, Bad={sum(y == 1)}")

    # ------------------------------------------------------
    # Étape 2 : entraîner un modèle clone sur ces données
    # ------------------------------------------------------
    print("\n--- Étape 2 : entraînement du modèle clone (Decision Tree) ---")
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    clone = DecisionTreeClassifier(max_depth=8, random_state=42)
    clone.fit(X_train, y_train)

    # ------------------------------------------------------
    # Étape 3 : évaluer la fidélité du clone
    # ------------------------------------------------------
    print("\n--- Étape 3 : évaluer la fidélité du clone face à l'API originale ---")

    # On envoie des NOUVEAUX exemples aléatoires à l'API originale ET au clone
    nb_eval = 60
    fidelity_matches = 0

    for _ in range(nb_eval):
        payload = random_payload()
        real_result = requests.post(URL, json=payload, timeout=5).json()
        real_pred = real_result["prediction_encoded"]

        row = np.array([[payload[f] for f in NUMERIC_FIELDS] + [int(payload[f]) for f in BOOL_FIELDS]])
        clone_pred = clone.predict(row)[0]

        if clone_pred == real_pred:
            fidelity_matches += 1

    fidelity = fidelity_matches / nb_eval * 100
    print(f"\nFidélité du clone par rapport à l'API originale : {fidelity:.1f}%")
    print(f"(sur {nb_eval} nouveaux exemples jamais vus pendant l'entraînement du clone)")

    if fidelity > 80:
        print("\n❌ ALERTE : le clone reproduit fidèlement le modèle original.")
        print("   Un attaquant peut voler le comportement du modèle sans jamais")
        print(f"   accéder à model.pkl, avec seulement {NB_SAMPLES} requêtes API.")
    else:
        print("\n✅ Le clone reste peu fidèle avec ce volume de requêtes ")
        print("   (mais un attaquant patient avec plus de requêtes ferait mieux).")


if __name__ == "__main__":
    main()
