from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .legal_onboarding import MatterIntake, OnboardingDecision, onboard_matter

app = FastAPI(title="Legal domain onboarding")


@app.post("/matter-intakes", response_model=OnboardingDecision)
def create_matter_intake(intake: MatterIntake) -> OnboardingDecision:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    client = InfraiClient(api_key=api_key)
    try:
        return onboard_matter(intake, client)
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    finally:
        client.close()
