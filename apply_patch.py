"""Apply consent handler patch to Open Web UI's main.py

Inserts the /oauth/consent route BEFORE the SPA catch-all mount.
"""

import re

MAIN_PY = "/app/backend/open_webui/main.py"

with open(MAIN_PY, "r") as f:
    code = f.read()

if "handle_oauth_consent" in code:
    print("Patch already present, skipping")
    exit(0)

# Find the SPA mount section and insert before it
# The mount looks like: if os.path.exists(FRONTEND_BUILD_DIR):
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

print("Patch applied successfully - route inserted before SPA mount")
