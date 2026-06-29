"""
Supabase OAuth Consent Handler for Open Web UI

Handles the /oauth/consent redirect from Supabase's OAuth 2.1 Server
by creating a service user JWT and auto-approving the consent.
"""

import logging
import os

import httpx
from starlette.responses import RedirectResponse

log = logging.getLogger(__name__)

# Service user credentials (created via admin API at container startup)
CONSENT_EMAIL = "consent@endocrinotech.app"
CONSENT_PASSWORD = "ConsentPass789!"


async def _ensure_user_jwt(client: httpx.AsyncClient, base: str, key: str) -> str | None:
    """Get a JWT for the consent service user by signing in."""
    try:
        resp = await client.post(
            f"{base}/token?grant_type=password",
            json={"email": CONSENT_EMAIL, "password": CONSENT_PASSWORD},
            headers={"apikey": key, "Content-Type": "application/json"},
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("access_token")
        else:
            body = await resp.aread()
            log.error("sign-in failed: %s - %s", resp.status_code, body.decode(errors="replace"))
            return None
    except Exception as e:
        log.error("sign-in exception: %s", e)
        return None


async def supabase_logout(access_token: str) -> bool:
    """Call Supabase's logout API to revoke the user's session.

    Args:
        access_token: The user's Supabase access_token (Bearer token).

    Returns:
        True if logout was successful (or Supabase not configured), False on failure.
    """
    project = os.environ.get("SUPABASE_PROJECT", "")
    api_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not project or not api_key:
        log.warning("supabase_logout: SUPABASE_PROJECT or SUPABASE_SERVICE_ROLE_KEY not set")
        return False

    url = f"https://{project}.supabase.co/auth/v1/logout"
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {access_token}",
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers)
            if resp.status_code in (200, 204):
                log.info("supabase_logout: session revoked successfully")
                return True
            else:
                body = await resp.aread()
                log.warning("supabase_logout: failed (%s): %s", resp.status_code, body.decode(errors="replace"))
                return False
    except Exception as e:
        log.error("supabase_logout: exception: %s", e)
        return False


async def handle_oauth_consent(authorization_id: str = ""):
    """Auto-approve Supabase OAuth consent."""

    if not authorization_id:
        return RedirectResponse(url="/auth?error=no_auth_id")

    project = os.environ.get("SUPABASE_PROJECT", "")
    api_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not project or not api_key:
        log.error("SUPABASE_PROJECT or SUPABASE_SERVICE_ROLE_KEY not set")
        return RedirectResponse(url="/auth?error=supabase_not_configured")

    base = f"https://{project}.supabase.co/auth/v1"

    async with httpx.AsyncClient() as client:
        # 1. Get user JWT
        jwt = await _ensure_user_jwt(client, base, api_key)
        if not jwt:
            log.error("consent: could not obtain user JWT")
            return RedirectResponse(url="/auth?error=consent_jwt_failed")

        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
        }

        # 2. GET authorization details (auto-approves if consent already exists)
        get_resp = await client.get(
            f"{base}/oauth/authorizations/{authorization_id}",
            headers=headers,
        )

        if get_resp.status_code == 200:
            data = get_resp.json()
            redirect_url = data.get("redirect_url")
            if redirect_url:
                log.info("consent: auto-approved, redirecting to %s", redirect_url)
                return RedirectResponse(url=redirect_url)

        # 3. Approve consent explicitly
        post_resp = await client.post(
            f"{base}/oauth/authorizations/{authorization_id}/consent",
            json={"action": "approve"},
            headers=headers,
        )

        if post_resp.status_code == 200:
            data = post_resp.json()
            redirect_url = data.get("redirect_url", "/auth")
            log.info("consent: approved, redirecting to %s", redirect_url)
            return RedirectResponse(url=redirect_url)

        # 4. Failed
        body = await post_resp.aread()
        log.error(
            "consent: approval failed: %s - %s",
            post_resp.status_code,
            body.decode(errors="replace"),
        )
        return RedirectResponse(url=f"/auth?error=consent_failed&code={post_resp.status_code}")
