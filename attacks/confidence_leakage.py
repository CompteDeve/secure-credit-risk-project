"""
============================================
ÉTAPE 16 : Tester la fuite de confiance (confidence leakage)
============================================
Ce script montre POURQUOI exposer le score de confiance / les
probabilités complètes est dangereux : en faisant varier une seule
variable à la fois, on observe comment la confiance évolue, ce qui
permet de "sentir" la frontière de décision du modèle sans jamais
voir son code ni ses poids (attaque d'évasion / model inversion).
"""

import requests
import copy
from base_payload import BASE_URL, VALID_PAYLOAD

URL = f"{BASE_URL}/predict"


def query(payload):
    response = requests.post(URL, json=payload, timeout=5)
    return response.json()


def main():
    print("=" * 60)
    print("ÉTAPE 16 : Fuite de confiance")
    print("=" * 60)

    # ------------------------------------------------------
    # Partie 1 : observer une confiance très élevée
    # ------------------------------------------------------
    print("\n--- Partie 1 : requête de base ---")
    result = query(VALID_PAYLOAD)
    print(f"Prediction : {result['prediction']}")
    print(f"Confidence : {result['confidence']} %")
    print(f"Probabilities : {result['probabilities']}")
    print("\n On voit ici bien plus qu'une simple décision Good/Bad : on voit")
    print("   à quel point le modèle est 'sûr' de lui, sur une échelle continue.")

    # ------------------------------------------------------
    # Partie 2 : sonder la frontière de décision (evasion attack)
    # ------------------------------------------------------
    print("\n--- Partie 2 : recherche de la frontière de décision ---")
    print("On fait varier UNE SEULE variable (debt_ratio) petit à petit")
    print("et on regarde comment la confiance évolue.\n")

    print(f"{'debt_ratio':>12} | {'prediction':>12} | {'confidence':>10}")
    print("-" * 42)

    for debt_ratio in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        payload = copy.deepcopy(VALID_PAYLOAD)
        payload["debt_ratio"] = debt_ratio
        result = query(payload)
        print(f"{debt_ratio:>12.2f} | {result['prediction']:>12} | {result['confidence']:>9.2f}%")

    print("\n Un attaquant peut repérer précisément la valeur de debt_ratio")
    print("   où la décision bascule de 'Bad Credit' à 'Good Credit'.")
    print("   Sans le score de confiance affiché en clair (juste la classe),")
    print("   cette recherche serait beaucoup plus difficile et beaucoup plus lente.")

    # ------------------------------------------------------
    # Partie 3 : dichotomie automatique pour trouver la frontière exacte
    # ------------------------------------------------------
    print("\n--- Partie 3 : recherche automatique du point de bascule ---")
    low, high = 0.0, 1.0
    payload_low = copy.deepcopy(VALID_PAYLOAD)
    payload_low["debt_ratio"] = low
    pred_low = query(payload_low)["prediction"]

    for _ in range(12):  # 12 itérations -> précision ~1/4096
        mid = (low + high) / 2
        payload = copy.deepcopy(VALID_PAYLOAD)
        payload["debt_ratio"] = mid
        result = query(payload)
        if result["prediction"] == pred_low:
            low = mid
        else:
            high = mid

    print(f"Point de bascule approximatif trouvé : debt_ratio ≈ { (low + high) / 2:.4f}")
    print(" En 12 requêtes seulement, un attaquant localise précisément")
    print("   la frontière de décision du modèle sur cette variable.")
    print("   C'est exactement le genre d'information qu'un score de confiance")
    print("   détaillé permet d'extraire très rapidement.")


if __name__ == "__main__":
    main()
