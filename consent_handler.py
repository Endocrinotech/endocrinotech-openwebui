"""
Supabase OAuth Consent Handler for Open Web UI

Handles the /oauth/consent redirect from Supabase's OAuth 2.1 Server
by auto-approving the consent using the service_role key.

Environment variables:
  SUPABASE_PROJECT        - your Supabase project ref (e.g. dlmrkcyszgidpxvqzmzb)
  SUPABASE_SERVICE_ROLE_KEY - your Supabase service_role key
"""

import logging
import os

import httpx
from fastapi import Request
from starlette.responses import RedirectResponse

log = logging.getLogger(__name__)


def get_config() -> tuple[str, str]:
    project = os.environ.get("SUPABASE_PROJECT", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    return project, key


async def handle_oauth_consent(authorization_id: str = "") -> RedirectResponse:
    """Auto-approve Supabase OAuth consent and redirect to the callback flow."""

    if not authorization_id:
        return RedirectResponse(url="/auth?error=no_auth_id")

    project, api_key = get_config()
    if not project or not api_key:
        log.error("SUPABASE_PROJECT or SUPABASE_SERVICE_ROLE_KEY not configured")
        return RedirectResponse(url="/auth?error=supabase_not_configured")

    base_url = f"https://{project}.supabase.co/auth/v1/oauth/authorizations"
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        # Step 1: GET authorization details.
        # This also auto-approves if the user already has an active consent.
        get_resp = await client.get(
            f"{base_url}/{authorization_id}",
            headers=headers,
        )

        if get_resp.status_code == 200:
            data = get_resp.json()
            redirect_url = data.get("redirect_url")
            if redirect_url:
                return RedirectResponse(url=redirect_url)
            log.warning(
                "GET authorization returned 200 but no redirect_url, "
                "falling through to explicit approve"
            )

        # Step 2: Explicitly approve the consent.
        post_resp = await client.post(
            f"{base_url}/{authorization_id}/consent",
            json={"action": "approve"},
            headers=headers,
        )

        if post_resp.status_code == 200:
            data = post_resp.json()
            redirect_url = data.get("redirect_url", "/auth")
            return RedirectResponse(url=redirect_url)
        else:
            body = await post_resp.aread()
            log.error(
                "Consent approval failed: %s - %s",
                post_resp.status_code,
                body.decode(errors="replace"),
            )
            return RedirectResponse(
                url=f"/auth?error=consent_failed&code={post_resp.status_code}"
            )
