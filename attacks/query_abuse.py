"""
============================================
MILESTONE 2 - PHASE B (RED TEAM)
ÉTAPE 17 : Tester beaucoup de requêtes (query abuse / DoS léger)
============================================
On envoie un grand nombre de requêtes rapidement, en série puis en
parallèle, pour voir si l'API :
- résiste sans planter ;
- applique une limite de débit (rate limiting) ;
- répond de plus en plus lentement (signe de saturation).

⚠️ À utiliser uniquement sur TON PROPRE serveur local, jamais sur
une API en production qui ne t'appartient pas.
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor
from base_payload import BASE_URL, VALID_PAYLOAD

URL = f"{BASE_URL}/predict"

NB_REQUESTS_SEQUENTIAL = 50
NB_REQUESTS_PARALLEL = 100
NB_THREADS = 20


def one_request(i):
    start = time.time()
    try:
        response = requests.post(URL, json=VALID_PAYLOAD, timeout=5)
        elapsed = time.time() - start
        return response.status_code, elapsed
    except Exception as e:
        elapsed = time.time() - start
        return f"ERROR: {e}", elapsed


def test_sequential():
    print(f"\n--- Test séquentiel : {NB_REQUESTS_SEQUENTIAL} requêtes, une par une ---")
    codes = {}
    start_total = time.time()
    for i in range(NB_REQUESTS_SEQUENTIAL):
        code, elapsed = one_request(i)
        codes[code] = codes.get(code, 0) + 1
    total_time = time.time() - start_total

    print(f"Temps total : {total_time:.2f}s pour {NB_REQUESTS_SEQUENTIAL} requêtes")
    print(f"Débit moyen : {NB_REQUESTS_SEQUENTIAL / total_time:.1f} requêtes/seconde")
    print(f"Codes de retour observés : {codes}")

    if 429 in codes:
        print("✅ L'API applique une limite de débit (code 429 détecté).")
    else:
        print("⚠️ Aucune limite de débit détectée : l'API accepte toutes les requêtes.")


def test_parallel():
    print(f"\n--- Test parallèle : {NB_REQUESTS_PARALLEL} requêtes envoyées avec {NB_THREADS} threads simultanés ---")
    codes = {}
    start_total = time.time()

    with ThreadPoolExecutor(max_workers=NB_THREADS) as executor:
        results = list(executor.map(one_request, range(NB_REQUESTS_PARALLEL)))

    total_time = time.time() - start_total

    for code, elapsed in results:
        codes[code] = codes.get(code, 0) + 1

    print(f"Temps total : {total_time:.2f}s pour {NB_REQUESTS_PARALLEL} requêtes")
    print(f"Débit moyen : {NB_REQUESTS_PARALLEL / total_time:.1f} requêtes/seconde")
    print(f"Codes de retour observés : {codes}")

    if 429 in codes:
        print("✅ L'API applique une limite de débit sous charge.")
    elif any(isinstance(c, str) and "ERROR" in c for c in codes):
        print("❌ L'API a planté / timeout sous charge parallèle : vulnérable au DoS.")
    else:
        print("⚠️ L'API a encaissé toutes les requêtes sans aucune limite : vulnérable")
        print("   à un abus (extraction de modèle massive, saturation serveur).")


def main():
    print("=" * 60)
    print("ÉTAPE 17 : Test de résistance à de nombreuses requêtes")
    print("=" * 60)
    test_sequential()
    test_parallel()


if __name__ == "__main__":
    main()
