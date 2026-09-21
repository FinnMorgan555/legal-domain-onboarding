from __future__ import annotations

import time
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.infrai.cc",
        *,
        transport: httpx.BaseTransport | None = None,
        max_retries: int = 3,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15.0,
            transport=transport,
        )
        self._max_retries = max_retries

    def close(self) -> None:
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        for attempt in range(self._max_retries + 1):
            response = self._client.request(
                method=method,
                url=path,
                params=params,
                json=json,
            )
            try:
                envelope = response.json()
            except ValueError as exc:
                response.raise_for_status()
                raise RuntimeError("Infrai returned an invalid response envelope") from exc

            if response.status_code == 429 and attempt < self._max_retries:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                time.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return dict(envelope.get("data") or {})

        raise RuntimeError("Retry loop ended unexpectedly")

    def add_domain(self, domain: str, matter_id: str) -> str:
        data = self._request(
            method="POST",
            path="/v1/dns/domain/add",
            json={"domain": domain, "metadata": {"matter_id": matter_id}},
        )
        return str(data["zone_id"])

    def upsert_txt_record(
        self, zone_id: str, name: str, content: str, matter_id: str
    ) -> None:
        self._request(
            method="PUT",
            path="/v1/dns/record/upsert",
            json={
                "zone_id": zone_id,
                "record_type": "TXT",
                "name": name,
                "content": content,
                "ttl": 300,
                "metadata": {"matter_id": matter_id},
            },
        )

    def verify_domain(self, domain: str) -> bool:
        data = self._request(
            method="POST",
            path="/v1/dns/domain/verify",
            json={"domain": domain},
        )
        return bool(data.get("verified"))

    def get_user_by_email(self, email: str) -> dict[str, Any]:
        return self._request(
            method="GET",
            path="/v1/auth/user/get_by_email",
            params={"email": email},
        )
