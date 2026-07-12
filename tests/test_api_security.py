"""
============================================
MILESTONE 2 - PHASE C (BLUE TEAM)
ÉTAPE 27 : Tester la sécurité (tests/test_api_security.py)
============================================
Tests automatisés qui vérifient que toutes les corrections de la
Phase C fonctionnent réellement :
- Étape 21 : API Key obligatoire
- Étape 22 : Validation stricte des données
- Étape 23 : Confiance qualitative uniquement (pas de score exact)
- Étape 26 : Messages d'erreur génériques (pas de détails internes)
- Étape 25 : Limite de requêtes (rate limiting)

Lancer avec : pytest tests/test_api_security.py -v
(depuis la racine du projet, pour que "models/model.pkl" soit trouvé)
"""

import copy
import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.api import app

VALID_KEY = os.environ.get("API_KEY", "demo-key-milestone2-2026")
INVALID_KEY = "cle-totalement-invalide"

VALID_PAYLOAD = {
    "gender_encoded": 1,
    "marital_status_encoded": 2,
    "housing_status_encoded": 2,
    "annual_income_normalized": 0.17,
    "savings_balance_normalized": 1.04,
    "checking_balance_normalized": 0.13,
    "loan_amount_normalized": 0.63,
    "loan_duration_months": 24,
    "existing_credits": 1,
    "past_due_count": 0,
    "credit_history_score": 0.5,
    "debt_ratio": 0.3,
    "loan_purpose_car": True,
    "loan_purpose_education": False,
    "loan_purpose_health": False,
    "loan_purpose_housing": False,
    "loan_purpose_other": False,
    "region_Assaba": False,
    "region_Brakna": False,
    "region_Gorgol": False,
    "region_Guidimakha": False,
    "region_Hodh_Ech_Chargui": False,
    "region_Hodh_El_Gharbi": False,
    "region_Inchiri": False,
    "region_Nouadhibou": False,
    "region_Nouakchott": True,
    "region_Tagant": False,
    "region_Trarza": False,
    "education_level_master": False,
    "education_level_phd": False,
    "education_level_primary": False,
    "education_level_secondary": True,
    "employment_status_public_sector": True,
    "employment_status_retired": False,
    "employment_status_self_employed": False,
    "employment_status_student": False,
    "employment_status_unemployed": False
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ============================================
# ÉTAPE 21 : Tests de l'authentification par API Key
# ============================================
class TestApiKey:

    def test_predict_sans_cle_est_refuse(self, client):
        response = client.post("/predict", json=VALID_PAYLOAD)
        assert response.status_code == 401

    def test_predict_avec_mauvaise_cle_est_refuse(self, client):
        response = client.post(
            "/predict",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": INVALID_KEY}
        )
        assert response.status_code == 401

    def test_predict_avec_bonne_cle_fonctionne(self, client):
        response = client.post(
            "/predict",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": VALID_KEY}
        )
        assert response.status_code == 200


# ============================================
# ÉTAPE 22 : Tests de la validation des données
# ============================================
class TestValidation:

    def test_valeur_negative_est_refusee(self, client):
        payload = copy.deepcopy(VALID_PAYLOAD)
        payload["existing_credits"] = -5
        response = client.post(
            "/predict", json=payload, headers={"X-API-Key": VALID_KEY}
        )
        assert response.status_code == 422

    def test_texte_au_lieu_dun_nombre_est_refuse(self, client):
        payload = copy.deepcopy(VALID_PAYLOAD)
        payload["annual_income_normalized"] = "abc"
        response = client.post(
            "/predict", json=payload, headers={"X-API-Key": VALID_KEY}
        )
        assert response.status_code == 422

    def test_valeur_hors_plage_est_refusee(self, client):
        payload = copy.deepcopy(VALID_PAYLOAD)
        payload["debt_ratio"] = 999  # hors de la plage [0, 1]
        response = client.post(
            "/predict", json=payload, headers={"X-API-Key": VALID_KEY}
        )
        assert response.status_code == 422

    def test_champ_manquant_est_refuse(self, client):
        payload = copy.deepcopy(VALID_PAYLOAD)
        del payload["debt_ratio"]
        response = client.post(
            "/predict", json=payload, headers={"X-API-Key": VALID_KEY}
        )
        assert response.status_code == 422

    def test_champ_inattendu_est_refuse(self, client):
        payload = copy.deepcopy(VALID_PAYLOAD)
        payload["is_admin"] = True
        response = client.post(
            "/predict", json=payload, headers={"X-API-Key": VALID_KEY}
        )
        assert response.status_code == 422


# ============================================
# ÉTAPE 23 : Test que la confiance exacte n'est plus exposée
# ============================================
class TestConfidenceMasking:

    def test_reponse_ne_contient_pas_de_score_numerique(self, client):
        response = client.post(
            "/predict", json=VALID_PAYLOAD, headers={"X-API-Key": VALID_KEY}
        )
        assert response.status_code == 200
        body = response.json()

        # Les anciens champs de la version vulnérable ne doivent plus exister
        assert "confidence" not in body
        assert "probabilities" not in body
        assert "prediction_encoded" not in body

        # Le nouveau champ doit être qualitatif
        assert "confidence_level" in body
        assert body["confidence_level"] in ["Faible", "Moyenne", "Elevee"]


# ============================================
# ÉTAPE 26 : Tests des messages d'erreur génériques
# ============================================
class TestGenericErrors:

    def test_erreur_validation_ne_revele_pas_de_details_techniques(self, client):
        payload = copy.deepcopy(VALID_PAYLOAD)
        payload["existing_credits"] = -5
        response = client.post(
            "/predict", json=payload, headers={"X-API-Key": VALID_KEY}
        )
        body = response.json()

        assert body == {"detail": "Entree invalide."}
        # On vérifie explicitement l'ABSENCE de détails internes
        # (noms de colonnes, types Pydantic, stack trace, etc.)
        body_str = str(body)
        assert "pydantic" not in body_str.lower()
        assert "traceback" not in body_str.lower()
        assert "ge=0" not in body_str

    def test_cle_invalide_ne_revele_pas_de_details_techniques(self, client):
        response = client.post(
            "/predict",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": INVALID_KEY}
        )
        body = response.json()
        assert body == {"detail": "Cle API invalide ou manquante."}


# ============================================
# ÉTAPE 25 : Test de la limite de requêtes (rate limiting)
# ============================================
class TestRateLimiting:

    def test_depassement_de_la_limite_declenche_un_429(self, client):
        """
        La limite est fixée à 100 requêtes/minute (voir src/api.py).
        On envoie volontairement plus de requêtes que la limite pour
        vérifier qu'au moins une reçoit bien un code 429.
        """
        status_codes = []
        for _ in range(110):
            response = client.post(
                "/predict", json=VALID_PAYLOAD, headers={"X-API-Key": VALID_KEY}
            )
            status_codes.append(response.status_code)

        assert 429 in status_codes, (
            "Aucune requête n'a été bloquée par le rate limiting "
            "alors que la limite (100/min) a été dépassée."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
