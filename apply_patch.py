"""Apply patches to Open Web UI for Supabase integration.

Patches applied:
1. Insert /oauth/consent route BEFORE the SPA catch-all mount in main.py
2. Add supabase_logout call to the signout handler in auths.py
"""

import re

# ──────────────────────────────────────────
# Patch 1: /oauth/consent route in main.py
# ──────────────────────────────────────────
MAIN_PY = "/app/backend/open_webui/main.py"

with open(MAIN_PY, "r") as f:
    code = f.read()

if "handle_oauth_consent" not in code:
    # Find the SPA mount section and insert before it
    spa_mount_pattern = r"(\nif os\.path\.exists\(FRONTEND_BUILD_DIR\):.*?app\.mount\(.*?SPAStaticFiles.*?\).*?\))"

    patch = """

# --- Supabase OAuth consent handler ---
try:
    from open_webui.consent_handler import handle_oauth_consent
except Exception:
    import logging
    logging.getLogger(__name__).warning(
        "consent_handler not available, /oauth/consent will 404"
    )
else:
    @app.get("/oauth/consent")
    async def oauth_consent(authorization_id: str = ""):
        return await handle_oauth_consent(authorization_id)
"""

    replacement = patch + r"\1"
    new_code = re.sub(spa_mount_pattern, replacement, code, count=1, flags=re.DOTALL)

    if new_code == code:
        print("ERROR: Could not find SPA mount section in main.py")
        exit(1)

    with open(MAIN_PY, "w") as f:
        f.write(new_code)
    print("Patch 1/2: /oauth/consent route inserted before SPA mount")
else:
    print("Patch 1/2: /oauth/consent route already present, skipping")

# ──────────────────────────────────────────
# Patch 2: supabase_logout in auths.py
# ──────────────────────────────────────────
AUTHS_PY = "/app/backend/open_webui/routers/auths.py"

with open(AUTHS_PY, "r") as f:
    auths_code = f.read()

if "supabase_logout" not in auths_code:
    # Add import after OAuthSessions import
    old_import = "from open_webui.models.oauth_sessions import OAuthSessions"
    if old_import not in auths_code:
        print("ERROR: Could not find OAuthSessions import in auths.py")
        exit(1)
    new_import = old_import + "\nfrom open_webui.consent_handler import supabase_logout"
    auths_code = auths_code.replace(old_import, new_import, 1)

    # Add supabase_logout call after getting session
    old_logout_section = """        session = await OAuthSessions.get_session_by_id(oauth_session_id, db=db)

        # If a custom end_session_endpoint is configured (e.g. AWS Cognito), redirect
        # there directly instead of attempting OIDC discovery."""

    if old_logout_section not in auths_code:
        print("ERROR: Could not find logout section in auths.py")
        exit(1)

    new_logout_section = """        session = await OAuthSessions.get_session_by_id(oauth_session_id, db=db)

        # --- Supabase session logout ---
        if session and session.token.get('access_token'):
            try:
                supabase_access_token = session.token.get('access_token')
                await supabase_logout(supabase_access_token)
            except Exception as e:
                log.warning(f'Signout: supabase_logout error: {e}')

        # If a custom end_session_endpoint is configured (e.g. AWS Cognito), redirect
        # there directly instead of attempting OIDC discovery."""

    auths_code = auths_code.replace(old_logout_section, new_logout_section, 1)

    with open(AUTHS_PY, "w") as f:
        f.write(auths_code)
    print("Patch 2/2: supabase_logout added to signout handler")
else:
    print("Patch 2/2: supabase_logout already present in auths.py, skipping")

print("All patches applied successfully!")
