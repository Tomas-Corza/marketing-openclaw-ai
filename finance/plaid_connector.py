"""Optional, read-only Plaid bank data adapter. Standard-library HTTP client.

Plaid Link's user-facing authentication must happen in an authorized frontend.
Never collect bank credentials, log tokens, or expose this module in a public demo.
"""
from __future__ import annotations
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError

HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}


class PlaidError(RuntimeError):
    pass


class PlaidBankClient:
    def __init__(self, client_id=None, secret=None, environment=None):
        self.client_id = client_id or os.environ.get("PLAID_CLIENT_ID")
        self.secret = secret or os.environ.get("PLAID_SECRET")
        self.environment = environment or os.environ.get("PLAID_ENV", "sandbox")
        if self.environment not in HOSTS:
            raise ValueError("PLAID_ENV must be sandbox, development or production")
        if not self.client_id or not self.secret:
            raise ValueError("Plaid client ID and secret must be configured server-side")

    def _post(self, endpoint, payload):
        body = json.dumps({"client_id": self.client_id, "secret": self.secret, **payload}).encode()
        request = Request(HOSTS[self.environment] + endpoint, data=body,
                          headers={"Content-Type": "application/json",
                                   "Plaid-Version": "2020-09-14"}, method="POST")
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as exc:
            # Plaid error bodies can contain sensitive request context. Do not expose them.
            raise PlaidError(f"Plaid request failed: HTTP {exc.code} for {endpoint}") from None

    def create_link_token(self, user_id: str):
        """Server-side initialization for a separately implemented Plaid Link UI."""
        if not user_id or not user_id.strip():
            raise ValueError("Stable authenticated user identifier is required")
        result = self._post("/link/token/create", {
            "user": {"client_user_id": user_id},
            "client_name": "OpenClaw Finance Automation",
            "products": ["transactions"],
            "country_codes": ["US"],
            "language": "en",
        })
        return result["link_token"]

    def exchange_public_token(self, public_token):
        """Server-only exchange after user completes Plaid Link.

        Caller must store the returned access token in an encrypted secrets manager;
        this module intentionally does not persist it.
        """
        if not public_token:
            raise ValueError("A Plaid Link public token is required")
        result = self._post("/item/public_token/exchange", {"public_token": public_token})
        return {"access_token": result["access_token"], "item_id": result["item_id"]}

    def sync_transactions(self, access_token, cursor=None, max_pages=50):
        """Return a complete change batch; never persist a partially paged cursor.

        The caller must atomically apply added/modified/removed updates before
        saving next_cursor. On mutation-during-pagination restart at old cursor.
        """
        if not access_token:
            raise ValueError("Access token required")
        original_cursor = cursor
        for attempt in range(2):
            adds, modifies, removes = [], [], []
            next_cursor = original_cursor
            try:
                for _ in range(max_pages):
                    payload = {"access_token": access_token, "count": 500}
                    if next_cursor is not None:
                        payload["cursor"] = next_cursor
                    result = self._post("/transactions/sync", payload)
                    adds.extend(result.get("added", []))
                    modifies.extend(result.get("modified", []))
                    removes.extend(result.get("removed", []))
                    next_cursor = result["next_cursor"]
                    if not result.get("has_more", False):
                        return {"added": adds, "modified": modifies,
                                "removed": removes, "next_cursor": next_cursor}
                raise PlaidError("Plaid sync exceeded maximum pages; no cursor committed")
            except PlaidError as exc:
                if "mutation" not in str(exc).lower() or attempt:
                    raise
        raise PlaidError("Plaid transaction sync failed")
