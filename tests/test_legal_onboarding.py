from datetime import date, datetime, timezone
from typing import Any

from legal_intake.legal_onboarding import MatterIntake, onboard_matter


class RecordingGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def add_domain(self, domain: str, matter_id: str) -> str:
        self.calls.append(("add_domain", domain))
        return "zone_legal_42"

    def upsert_txt_record(
        self, zone_id: str, name: str, content: str, matter_id: str
    ) -> None:
        self.calls.append(("upsert_txt", (zone_id, name, content)))

    def verify_domain(self, domain: str) -> bool:
        self.calls.append(("verify_domain", domain))
        return True

    def get_user_by_email(self, email: str) -> dict[str, Any]:
        self.calls.append(("get_user", email))
        return {"id": "user_86", "email": email}


def test_verified_signed_matter_completes_and_marks_deadline_follow_up() -> None:
    gateway = RecordingGateway()
    intake = MatterIntake(
        matter_id="MAT-2048",
        company_domain="client.example",
        contact_email="counsel@client.example",
        signed_document_id="ENGAGEMENT-2048",
        signed_document_delivered_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        response_deadline=date(2026, 9, 12),
    )

    result = onboard_matter(intake, gateway, today=date(2026, 9, 13))

    assert result.onboarding_complete is True
    assert result.signed_document_delivered is True
    assert result.follow_up_due is True
    assert result.contact_user_id == "user_86"
    assert gateway.calls[1][0] == "upsert_txt"
    assert gateway.calls[1][1][0] == "zone_legal_42"
    assert gateway.calls[-1] == ("get_user", "counsel@client.example")
