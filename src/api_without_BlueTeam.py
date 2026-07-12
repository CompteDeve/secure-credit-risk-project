# ============================================
# ÉTAPE 10 : Créer src/api.py
# ============================================
from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import os

app = FastAPI(
    title="Credit Risk Prediction API",
    description="API de prédiction du risque de crédit (Milestone 2 - Phase A - Baseline)",
    version="1.0.0"
)

# ============================================
# ÉTAPE 11 : Charger le modèle au démarrage
# ============================================
MODEL_PATH = "models/model.pkl"

model = None

@app.on_event("startup")
def load_model():
    global model
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Modèle introuvable : {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    print(f"Modèle chargé depuis {MODEL_PATH}")


# ============================================
# Schéma des données d'entrée
# ============================================
# Ces champs correspondent EXACTEMENT aux 37 colonnes utilisées
# lors de l'entraînement (model.feature_names_in_), dans le même ordre.
class CreditApplication(BaseModel):
    gender_encoded: int
    marital_status_encoded: int
    housing_status_encoded: int
    annual_income_normalized: float
    savings_balance_normalized: float
    checking_balance_normalized: float
    loan_amount_normalized: float
    loan_duration_months: float
    existing_credits: int
    past_due_count: int
    credit_history_score: float
    debt_ratio: float
    loan_purpose_car: bool
    loan_purpose_education: bool
    loan_purpose_health: bool
    loan_purpose_housing: bool
    loan_purpose_other: bool
    region_Assaba: bool
    region_Brakna: bool
    region_Gorgol: bool
    region_Guidimakha: bool
    region_Hodh_Ech_Chargui: bool
    region_Hodh_El_Gharbi: bool
    region_Inchiri: bool
    region_Nouadhibou: bool
    region_Nouakchott: bool
    region_Tagant: bool
    region_Trarza: bool
    education_level_master: bool
    education_level_phd: bool
    education_level_primary: bool
    education_level_secondary: bool
    employment_status_public_sector: bool
    employment_status_retired: bool
    employment_status_self_employed: bool
    employment_status_student: bool
    employment_status_unemployed: bool

    class Config:
        # Exemple pré-rempli visible dans /docs (Swagger UI)
        json_schema_extra = {
            "example": {
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
        }


# Correspondance nom du champ Pydantic -> nom exact de colonne attendu par le modèle
# (nécessaire car les noms de régions contiennent des espaces, incompatibles
# avec les noms de champs Python)
FIELD_TO_COLUMN = {
    "region_Hodh_Ech_Chargui": "region_Hodh Ech Chargui",
    "region_Hodh_El_Gharbi": "region_Hodh El Gharbi",
}


# ============================================
# Route racine (santé de l'API)
# ============================================
@app.get("/")
def root():
    return {"message": "Credit Risk Prediction API - Phase A (Baseline)", "status": "online"}


# ============================================
# ÉTAPE 12 & 13 : Endpoint /predict
# ============================================
@app.post("/predict")
def predict(application: CreditApplication):
    # Convertir les données reçues en DataFrame dans le bon ordre de colonnes
    data_dict = application.dict()

    # Renommer les champs vers les noms exacts de colonnes du modèle
    renamed = {}
    for key, value in data_dict.items():
        column_name = FIELD_TO_COLUMN.get(key, key)
        renamed[column_name] = value

    # Respecter l'ordre exact des colonnes utilisé à l'entraînement
    input_df = pd.DataFrame([renamed])[list(model.feature_names_in_)]

    # Prédiction
    prediction = model.predict(input_df)[0]
    probabilities = model.predict_proba(input_df)[0]

    label = "Bad Credit" if prediction == 1 else "Good Credit"
    confidence = float(max(probabilities))

    #  FAIBLESSE VOLONTAIRE (Étape 13) :
    # On retourne la confiance exacte du modèle ainsi que la distribution
    # complète des probabilités. Cette information sera exploitée durant
    # la phase Red Team (voir docs/attack_report.md).
    return {
        "prediction": label,
        "prediction_encoded": int(prediction),
        "confidence": round(confidence * 100, 2),
        "probabilities": {
            "good_credit": round(float(probabilities[0]) * 100, 2),
            "bad_credit": round(float(probabilities[1]) * 100, 2)
        }
    }


# ============================================
# Lancement local : uvicorn src.api:app --reload
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)