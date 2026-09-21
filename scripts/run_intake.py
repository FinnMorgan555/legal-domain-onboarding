from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone

from legal_intake.infrai_client import InfraiClient
from legal_intake.legal_onboarding import MatterIntake, onboard_matter


def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    intake = MatterIntake(
        matter_id="MAT-2048",
        company_domain="client.example",
        contact_email="counsel@client.example",
        signed_document_id="ENGAGEMENT-2048",
        signed_document_delivered_at=datetime.now(timezone.utc),
        response_deadline=date.today(),
    )
    client = InfraiClient(api_key=api_key)
    try:
        decision = onboard_matter(intake, client)
        print(json.dumps(decision.model_dump(mode="json"), indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
