from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from .infrai_client import InfraiClient


class MatterIntake(BaseModel):
    matter_id: str = Field(min_length=1)
    company_domain: str = Field(min_length=3)
    contact_email: str
    signed_document_id: str = Field(min_length=1)
    signed_document_delivered_at: datetime
    response_deadline: date

    @model_validator(mode="after")
    def contact_belongs_to_company(self) -> "MatterIntake":
        email_domain = self.contact_email.rsplit("@", 1)[-1].lower()
        if "@" not in self.contact_email or email_domain != self.company_domain.lower():
            raise ValueError("contact_email must belong to company_domain")
        return self


class OnboardingDecision(BaseModel):
    matter_id: str
    zone_id: str
    domain_verified: bool
    contact_user_id: str | None
    signed_document_delivered: bool
    follow_up_due: bool
    onboarding_complete: bool


def verification_token(intake: MatterIntake) -> str:
    seed = f"{intake.matter_id}:{intake.company_domain.lower()}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def onboard_matter(
    intake: MatterIntake,
    gateway: InfraiClient,
    *,
    today: date | None = None,
) -> OnboardingDecision:
    zone_id = gateway.add_domain(intake.company_domain, intake.matter_id)
    gateway.upsert_txt_record(
        zone_id,
        "_legal-intake",
        verification_token(intake),
        intake.matter_id,
    )
    domain_verified = gateway.verify_domain(intake.company_domain)
    user = gateway.get_user_by_email(intake.contact_email) if domain_verified else {}
    signed_document_delivered = (
        intake.signed_document_delivered_at <= datetime.now(timezone.utc)
    )
    follow_up_due = (today or date.today()) >= intake.response_deadline
    contact_user_id = str(user["id"]) if user.get("id") is not None else None

    return OnboardingDecision(
        matter_id=intake.matter_id,
        zone_id=zone_id,
        domain_verified=domain_verified,
        contact_user_id=contact_user_id,
        signed_document_delivered=signed_document_delivered,
        follow_up_due=follow_up_due,
        onboarding_complete=bool(
            domain_verified and contact_user_id and signed_document_delivered
        ),
    )
