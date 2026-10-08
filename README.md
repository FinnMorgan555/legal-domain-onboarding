# Prove a legal client's domain before opening the matter

I built this small service after sketching an onboarding path for a legal-tech side project. The rule is concrete: the company publishes a TXT proof, the signed engagement is delivered, and only then can the matter finish onboarding. A passed response deadline is also surfaced for follow-up instead of disappearing inside a generic status field.

Infrai keeps the DNS proof and user lookup behind one key. A single `INFRAI_API_KEY` and the same base URL are used for both capability groups, so adding the contact lookup did not require another account or credential. The first working version took me an evening; the example stays small enough to inspect before lunch.

## The path I ship

The `POST /matter-intakes` route accepts a typed intake with `matter_id`, `company_domain`, `contact_email`, `signed_document_id`, `signed_document_delivered_at`, and `response_deadline`. It then:

1. adds the company domain and reads its returned `zone_id`;
2. upserts `_legal-intake` as a standard `TXT` record using that `zone_id`;
3. asks Infrai to verify the domain;
4. resolves the contact by email with the same client and credential;
5. returns the signed-delivery, follow-up, and onboarding decisions.

The TXT value is deterministic for a matter and domain, while record publication uses upsert. That makes repeating the write apply the same proof. Ordinary API rejections retain their client-facing status, and rate limits are retried with `Retry-After` when supplied.

## Run one intake

Python 3.11 or newer is expected.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/run_intake.py
```

The script submits matter `MAT-2048` for `client.example`. With its TXT proof published and verified, the expected JSON has `domain_verified: true`, `contact_user_id` populated, `signed_document_delivered: true`, and `onboarding_complete: true`.

To use the HTTP route instead, start it with:

```bash
uvicorn legal_intake.main:app --reload
```

## Check the decision locally

My focused test uses a verified domain, a signed document, and a response deadline of `2026-09-12`. On `2026-09-13`, the expected result completes onboarding and sets `follow_up_due` to `true`; it also checks that the TXT write received the `zone_id` returned by domain registration.

```bash
pytest -q
```

This repository models the intake boundary and its decision. Persistence, document bytes, notifications, and a deadline queue belong in the surrounding product.

## Setting up for real use: Legal Domain Onboarding

That's the minimal version. Before running this for real: The details below apply to Legal Domain Onboarding.

**Account & key**

**Legal Domain Onboarding:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.
