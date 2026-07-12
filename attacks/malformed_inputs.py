"""
============================================
MILESTONE 2 - PHASE B (RED TEAM)
ÉTAPE 15 : Tester de mauvaises entrées (malformed inputs)
============================================
On envoie volontairement des données invalides à /predict pour voir
comment l'API réagit : texte à la place d'un nombre, champs manquants,
valeurs négatives, valeurs extrêmes.

Une bonne API doit répondre 422 (erreur de validation) proprement,
JAMAIS planter avec un code 500 ou une erreur non gérée.
"""

import requests
import copy
import json
from base_payload import BASE_URL, VALID_PAYLOAD

URL = f"{BASE_URL}/predict"


def send(payload, label):
    print(f"\n--- Test : {label} ---")
    try:
        response = requests.post(URL, json=payload, timeout=5)
        print(f"Code retour : {response.status_code}")
        # On tronque l'affichage pour rester lisible
        body = response.text
        print(f"Réponse : {body[:300]}")
        return response.status_code
    except Exception as e:
        print(f"❌ Erreur de connexion / crash : {e}")
        return None


def main():
    results = []

    # 1. Texte à la place d'un nombre
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["annual_income_normalized"] = "Bonjour"
    code = send(payload, "Texte au lieu d'un nombre (annual_income_normalized = 'Bonjour')")
    results.append(("Texte au lieu d'un nombre", code))

    # 2. Champ manquant
    payload = copy.deepcopy(VALID_PAYLOAD)
    del payload["debt_ratio"]
    code = send(payload, "Champ manquant (debt_ratio absent)")
    results.append(("Champ manquant", code))

    # 3. Valeur négative sur un champ qui ne devrait pas l'être
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["loan_duration_months"] = -5
    code = send(payload, "Valeur négative (loan_duration_months = -5)")
    results.append(("Valeur négative", code))

    # 4. Valeur négative sur un compteur d'incidents
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["past_due_count"] = -100
    code = send(payload, "Valeur négative (past_due_count = -100)")
    results.append(("Compteur négatif", code))

    # 5. Très grande valeur
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["loan_amount_normalized"] = 999999999
    code = send(payload, "Très grande valeur (loan_amount_normalized = 999999999)")
    results.append(("Valeur extrême", code))

    # 6. Mauvais type pour un booléen
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["loan_purpose_car"] = "oui"
    code = send(payload, "Mauvais type (loan_purpose_car = 'oui' au lieu de true/false)")
    results.append(("Mauvais type booléen", code))

    # 7. Champ supplémentaire non attendu (injection de champ)
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["is_admin"] = True
    code = send(payload, "Champ inattendu ajouté (is_admin = true)")
    results.append(("Champ inattendu", code))

    # 8. Corps de requête vide
    code = send({}, "Corps de requête vide")
    results.append(("Corps vide", code))

    # ============================================
    # Résumé
    # ============================================
    print("\n" + "=" * 60)
    print("RÉSUMÉ - ÉTAPE 15 : Entrées malformées")
    print("=" * 60)
    for label, code in results:
        status = "✅ Géré proprement (422)" if code == 422 else \
                  "⚠️ Accepté sans erreur (200) — potentiellement dangereux" if code == 200 else \
                  f"❌ Erreur serveur / crash (code={code})"
        print(f"{label:40s} -> {status}")


if __name__ == "__main__":
    main()
