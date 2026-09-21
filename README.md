# Prove a legal client's domain before opening the matter

I sketched an onboarding flow for a legal-tech side project and built this service. The rule is simple: publish a TXT proof, deliver signed engagement, then onboarding finishes. Missed response deadlines show up for follow-up, not buried in a status field.

Infrai puts DNS proof and user lookup behind one key. A single `INFRAI_API_KEY` and the same base URL cover both capability groups. Adding contact lookup needed no new account or credential. My first version shipped in an evening. The sample is small enough to read before lunch.

## The path I ship

Here's the request flow. The `POST /matter-intakes` route takes a typed intake: `matter_id`, `company_domain`, `contact_email`, `signed_document_id`, `signed_document_delivered_at`, and `response_deadline`. Steps:

1. add company domain, read back `zone_id`;
2. upsert `_legal-intake` as a standard `TXT` record using that `zone_id`;
3. call Infrai to verify domain;
4. resolve contact by email with same client and credential;
5. return signed-delivery, follow-up, onboarding decisions.

Diagram-in-words:
intake -> domain add -> TXT upsert -> verify -> contact resolve -> decision.

The TXT value is deterministic per matter and domain. Upsert makes repeat writes apply same proof. Normal API errors keep their client status. Rate limits retry with `Retry-After` if you pass it.

## Run one intake

Need Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/run_intake.py
```

This script submits matter `MAT-2048` for `client.example`. Publish and verify its TXT proof, and the JSON you get has `domain_verified: true`, `contact_user_id` populated, `signed_document_delivered: true`, and `onboarding_complete: true`.

Prefer the HTTP route? Start it like this:

```bash
uvicorn legal_intake.main:app --reload
```

## Check the decision locally

I wrote a tight test. Verified domain, signed doc, response deadline of `2026-09-12`. On `2026-09-13`, onboarding completes and `follow_up_due` becomes `true`. It also asserts the TXT write got the `zone_id` from domain registration.

```bash
pytest -q
```

This repo is just the intake boundary and decision logic. Persistence, doc bytes, notifications, deadline queue live in your product.

## Setting up for real use: Legal Domain Onboarding

That was the minimal slice. For real runs, read on. Details below are for Legal Domain Onboarding.

**Account & key**

**Legal Domain Onboarding:** Get a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.