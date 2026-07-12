"""
============================================
MILESTONE 2 - PHASE C : API SECURISEE (BLUE TEAM)
============================================
Version corrigée de l'API baseline. Corrige les faiblesses identifiées
en Phase B (Red Team) :

- Etape 21 : Authentification par cle API
- Etape 22 : Validation stricte des donnees (plages de valeurs)
- Etape 23 : Le score de confiance exact n'est plus expose
- Etape 24 : Journalisation (logs) de chaque requete
- Etape 25 : Limite du nombre de requetes (rate limiting)
- Etape 26 : Messages d'erreur generiques, sans details internes
"""

import os
import time

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
import joblib
import pandas as pd

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

try:
    from src.logging_config import logger
except ImportError:
    from logging_config import logger

# ============================================
# ETAPE 21 : Authentification par cle API
# ============================================
# En production, definir la variable d'environnement API_KEY.
# Une valeur par defaut est fournie ici uniquement pour la demo/le test.
VALID_API_KEYS = {
    os.environ.get("API_KEY", "demo-key-milestone2-2026")
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key is None or api_key not in VALID_API_KEYS:
        logger.warning(f"Acces refuse : cle API invalide ou absente ({api_key!r})")
        raise HTTPException(status_code=401, detail="Cle API invalide ou manquante.")
    return api_key


# ============================================
# ETAPE 25 : Limite du nombre de requetes
# ============================================
limiter = Limiter(key_func=get_remote_address)

MODEL_PATH = "models/model.pkl"
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Modele introuvable : {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    logger.info(f"Modele charge depuis {MODEL_PATH}")
    yield
    logger.info("Arret de l'API.")


app = FastAPI(
    title="Credit Risk Prediction API (Securisee)",
    description="API de prediction du risque de credit - Phase C (Blue Team)",
    version="2.0.0",
    lifespan=lifespan
)
app.state.limiter = limiter


# ============================================
# ETAPE 26 : Gestion generique des erreurs
# ============================================
# On intercepte les erreurs de validation Pydantic et les erreurs
# inattendues pour ne JAMAIS renvoyer de details techniques au client,
# tout en gardant le detail complet dans les logs serveur.

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Requete invalide sur {request.url.path} : {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Entree invalide."}
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"Limite de requetes depassee pour {get_remote_address(request)}")
    return JSONResponse(
        status_code=429,
        content={"detail": "Trop de requetes. Veuillez reessayer plus tard."}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur interne sur {request.url.path} : {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue."}
    )


# ============================================
# ETAPE 22 : Validation stricte des donnees
# ============================================
# Chaque champ a maintenant des bornes plausibles (Field(ge=..., le=...)).
# Une valeur hors de ces bornes (ex. Age = -20) est automatiquement
# rejetee par Pydantic avec un code 422 -- gere par notre handler
# generique (etape 26), qui repond "Entree invalide." sans plus de detail.
class CreditApplication(BaseModel):
    gender_encoded: int = Field(..., ge=0, le=1, description="0 ou 1")
    marital_status_encoded: int = Field(..., ge=0, le=3)
    housing_status_encoded: int = Field(..., ge=0, le=3)
    annual_income_normalized: float = Field(..., ge=-5, le=5)
    savings_balance_normalized: float = Field(..., ge=-5, le=5)
    checking_balance_normalized: float = Field(..., ge=-5, le=5)
    loan_amount_normalized: float = Field(..., ge=-5, le=5)
    loan_duration_months: float = Field(..., gt=0, le=120)
    existing_credits: int = Field(..., ge=0, le=20)
    past_due_count: int = Field(..., ge=0, le=50)
    credit_history_score: float = Field(..., ge=0, le=1)
    debt_ratio: float = Field(..., ge=0, le=1)
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

    model_config = ConfigDict(extra="forbid")  # rejette tout champ non prevu (ex. is_admin)


FIELD_TO_COLUMN = {
    "region_Hodh_Ech_Chargui": "region_Hodh Ech Chargui",
    "region_Hodh_El_Gharbi": "region_Hodh El Gharbi",
}


# ============================================
# ETAPE 23 : Confiance qualitative (plus de score exact)
# ============================================
def confidence_to_level(confidence: float) -> str:
    """
    Convertit un score de confiance numerique (0-100) en categorie
    qualitative. Cela empeche un attaquant d'exploiter la valeur
    exacte pour sonder la frontiere de decision (voir attack_report.md,
    etape 16).
    """
    if confidence >= 70:
        return "Elevee"
    elif confidence >= 55:
        return "Moyenne"
    else:
        return "Faible"


# ============================================
# Route racine (pas besoin de cle API, juste un statut)
# ============================================
@app.get("/")
def root():
    return {"message": "Credit Risk Prediction API - Phase C (Securisee)", "status": "online"}


# ============================================
# Endpoint /predict protege
# ============================================
@app.post("/predict")
@limiter.limit("100/minute")
def predict(
    request: Request,
    application: CreditApplication,
    api_key: str = Depends(verify_api_key),
):
    start = time.time()
    try:
        data_dict = application.model_dump()
        renamed = {}
        for key, value in data_dict.items():
            column_name = FIELD_TO_COLUMN.get(key, key)
            renamed[column_name] = value

        input_df = pd.DataFrame([renamed])[list(model.feature_names_in_)]

        prediction = model.predict(input_df)[0]
        probabilities = model.predict_proba(input_df)[0]

        label = "Bad Credit" if prediction == 1 else "Good Credit"
        confidence = float(max(probabilities)) * 100
        confidence_level = confidence_to_level(confidence)

        elapsed = round((time.time() - start) * 1000, 2)
        logger.info(
            f"POST /predict OK | client={get_remote_address(request)} | "
            f"prediction={label} | confiance={confidence_level} | temps={elapsed}ms"
        )

        return {
            "prediction": label,
            "confidence_level": confidence_level
        }

    except Exception as e:
        # Toute exception inattendue ici est aussi remontee au handler
        # generique (etape 26), qui masque les details au client.
        logger.error(f"Erreur pendant la prediction : {e}")
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
