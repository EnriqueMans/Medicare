#!/usr/bin/env python3
"""
TriZetto Elements - Automated TC 76 (Member Residential Address Update) client.

What this does:
  1. Authenticates with the Identity Server using OAuth2 Client Credentials Grant
     to get a Bearer access token.
  2. Caches the token in memory and re-fetches it automatically once it expires.
  3. Submits one or more member address update records to the
     Member Information Update API (TC 76).
  4. (Optional) Polls the Transaction Status API until the update resolves.

Fill in the CONFIG section below (or set the equivalent environment variables),
then either import `update_address(...)` into your own code, or run this file
directly with a JSON file of records to update.

Environment variables (override the CONFIG values, useful for CI/secrets managers):
  TMS_HOSTNAME          e.g. mytenant.example.com
  TMS_TOKEN_PORT        e.g. 44335
  TMS_CLIENT_ID
  TMS_CLIENT_SECRET
  TMS_SCOPE             e.g. tms_gw_api
  TMS_REDIRECT_URI      e.g. https://mytenant.example.com/swagger/ui/index
  TMS_GATEWAY_BASE_URL  e.g. https://mytenant.example.com/apigateway/tms/api/v1
"""

import base64
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import requests

# ---------------------------------------------------------------------------
# CONFIG - replace with your real values, or export the env vars listed above.
# ---------------------------------------------------------------------------
CONFIG = {
    "hostname": os.environ.get("TMS_HOSTNAME", "your-tenant.example.com"),
    "token_port": os.environ.get("TMS_TOKEN_PORT", "44335"),
    "client_id": os.environ.get("TMS_CLIENT_ID", "REPLACE_ME"),
    "client_secret": os.environ.get("TMS_CLIENT_SECRET", "REPLACE_ME"),
    "scope": os.environ.get("TMS_SCOPE", "tms_gw_api"),
    "redirect_uri": os.environ.get(
        "TMS_REDIRECT_URI", "https://your-tenant.example.com/swagger/ui/index"
    ),
    # Base URL for the actual member-info / transaction endpoints.
    "gateway_base_url": os.environ.get(
        "TMS_GATEWAY_BASE_URL", "https://your-tenant.example.com/apigateway/tms/api/v1"
    ),
}

TOKEN_URL_TEMPLATE = "https://{hostname}:{port}/ids/connect/token"
# NOTE: Confirm this exact path against your Swagger UI - the guide gives the
# pattern https://[tenant].[domain]/apigateway/tms/api/v1/<API Name>. The
# Member Information Update (TC 76/72/92) API name may be "memberinfo",
# "member-information", etc. depending on your deployment. Update below once
# verified in Swagger.
MEMBER_INFO_UPDATE_PATH = "/memberinfo"
TRANSACTION_STATUS_PATH = "/transaction/status"


class TokenCache:
    """Fetches and caches the Bearer token, refreshing before it expires."""

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self._token: Optional[str] = None
        self._expires_at: float = 0.0

    def get_token(self) -> str:
        # Refresh 60s before actual expiry to avoid races.
        if self._token is None or time.time() >= (self._expires_at - 60):
            self._fetch_token()
        return self._token

    def _fetch_token(self) -> None:
        cfg = self.config
        url = TOKEN_URL_TEMPLATE.format(hostname=cfg["hostname"], port=cfg["token_port"])
        basic = base64.b64encode(
            f'{cfg["client_id"]}:{cfg["client_secret"]}'.encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/json",
        }
        body = {
            "grant_type": "client_credentials",
            "scope": cfg["scope"],
            "redirect_uri": cfg["redirect_uri"],
        }

        resp = requests.post(url, headers=headers, json=body, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Token request failed: HTTP {resp.status_code} - {resp.text}"
            )

        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + int(data.get("expires_in", 3600))


def _auth_headers(token_cache: TokenCache) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token_cache.get_token()}",
        "Content-Type": "application/json",
    }


def build_address_record(
    member_beneficiary_id: str,
    contract_id: str,
    pbp: str,
    effective_date: str,
    application_sign_date: str,
    address1: str,
    city: str,
    state: str,
    zip_code: str,
    address2: str = "",
    address3: str = "",
    county: str = "",
    **extra_fields: Any,
) -> Dict[str, Any]:
    """
    Build one TC 76 transaction record. Required fields per the guide:
    memberBeneficiaryId, contractId, pbp, effectiveDate, applicationSignDate,
    memberAddress1, memberCity, memberState, memberZip.

    To DELETE an address instead of updating it, leave address1/city/state/zip
    all blank (pass empty strings).
    """
    record = {
        "memberBeneficiaryId": member_beneficiary_id,
        "contractId": contract_id,
        "pbp": pbp,
        "effectiveDate": effective_date,
        "applicationSignDate": application_sign_date,
        "memberAddress1": address1,
        "memberAddress2": address2,
        "memberAddress3": address3,
        "memberCity": city,
        "memberState": state,
        "memberZip": zip_code,
        "memberCounty": county,
    }
    record.update(extra_fields)
    return record


def update_address(
    records: List[Dict[str, Any]],
    token_cache: Optional[TokenCache] = None,
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Submit one or more address-update records to the TC 76 endpoint.
    Returns the parsed JSON response (includes Activity ID(s) on success,
    or validation errors on failure).
    """
    cfg = config or CONFIG
    tc = token_cache or TokenCache(cfg)

    url = cfg["gateway_base_url"].rstrip("/") + MEMBER_INFO_UPDATE_PATH
    payload = {"transactionRecords": records}

    resp = requests.post(url, headers=_auth_headers(tc), json=payload, timeout=30)

    try:
        result = resp.json()
    except ValueError:
        result = {"raw_response": resp.text}

    result["_http_status"] = resp.status_code
    return result


def get_transaction_status(
    activity_id: str,
    token_cache: Optional[TokenCache] = None,
    config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Look up the status of a submitted transaction by Activity ID."""
    cfg = config or CONFIG
    tc = token_cache or TokenCache(cfg)

    url = cfg["gateway_base_url"].rstrip("/") + TRANSACTION_STATUS_PATH
    resp = requests.get(
        url, headers=_auth_headers(tc), params={"activityId": activity_id}, timeout=30
    )
    try:
        return resp.json()
    except ValueError:
        return {"raw_response": resp.text, "_http_status": resp.status_code}


def poll_until_resolved(
    activity_id: str,
    token_cache: Optional[TokenCache] = None,
    config: Optional[Dict[str, str]] = None,
    interval_seconds: int = 5,
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    """Poll Transaction Status until it's no longer 'Pending' or until timeout."""
    deadline = time.time() + timeout_seconds
    last = {}
    while time.time() < deadline:
        last = get_transaction_status(activity_id, token_cache, config)
        status = str(last.get("status", "")).lower()
        if status and status not in ("pending", "in progress", "processing"):
            return last
        time.sleep(interval_seconds)
    return last


# ---------------------------------------------------------------------------
# CLI entry point: python tc76_address_update.py records.json
# records.json should be a JSON array of objects with the fields expected by
# build_address_record's keyword args (member_beneficiary_id, contract_id, ...).
# ---------------------------------------------------------------------------
def _main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python tc76_address_update.py <records.json>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        raw_records = json.load(f)

    token_cache = TokenCache(CONFIG)
    built_records = [build_address_record(**r) for r in raw_records]

    result = update_address(built_records, token_cache=token_cache)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _main()
