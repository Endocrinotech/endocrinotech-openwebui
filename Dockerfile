FROM ghcr.io/open-webui/open-webui:main

# ============================================================
# Supabase OAuth Consent Handler
# Adds auto-approval for Supabase's OAuth 2.1 consent page.
# ============================================================

# Install httpx (usually already present, explicit for safety)
RUN pip install --no-cache-dir httpx

# Copy the handler and patch script
COPY consent_handler.py /app/backend/open_webui/
COPY apply_patch.py /tmp/

# Apply the patch to register the /oauth/consent route
RUN python3 /tmp/apply_patch.py && rm /tmp/apply_patch.py
