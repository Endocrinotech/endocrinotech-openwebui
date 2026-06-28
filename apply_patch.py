"""Apply consent handler patch to Open Web UI's main.py"""

import re

MAIN_PY = "/app/backend/open_webui/main.py"

with open(MAIN_PY, "r") as f:
    code = f.read()

if "handle_oauth_consent" in code:
    print("Patch already present, skipping")
    exit(0)

patch = '''

# --- Supabase OAuth consent handler (injected) ---
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
'''

with open(MAIN_PY, "a") as f:
    f.write(patch)

print("Patch applied successfully")
