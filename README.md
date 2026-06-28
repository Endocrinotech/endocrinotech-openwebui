# Open Web UI + Supabase OAuth Consent Handler

Imagen Docker de Open Web UI con soporte para el OAuth 2.1 Server de Supabase.

## ¿Por qué?

Supabase redirige a `/oauth/consent?authorization_id=xxx` para que el usuario apruebe el
consentimiento OAuth. Open Web UI no tiene esta página, causando un bucle infinito.

Esta imagen añade un handler que auto-aprueba el consentimiento automáticamente usando
la **service_role key** de Supabase.

## Cómo usar

### 1. Crear el repo en GitHub

```bash
# Crea un repo nuevo en GitHub y clónalo
# Copia estos archivos:
#   Dockerfile, consent_handler.py,
#   .github/workflows/docker-build.yml,
#   docker-compose.yml
git push origin main
```

GitHub Actions buildca la imagen automáticamente y la publica en
`ghcr.io/tuusuario/tu-repo:latest`.

### 2. Variables de entorno

Además de las variables normales de Open Web UI, añade:

| Variable | Valor | Ejemplo |
|---|---|---|
| `SUPABASE_PROJECT` | Tu project ref de Supabase | `dlmrkcyszgidpxvqzmzb` |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key de Supabase | `eyJ...` |

### 3. Configurar Open Web UI

Las variables OIDC (cámbialas como hicimos antes):

| Variable | Valor |
|---|---|
| `OAUTH_CLIENT_ID` | Client ID de tu OAuth App en Supabase |
| `OAUTH_CLIENT_SECRET` | Client Secret de tu OAuth App |
| `OPENID_PROVIDER_URL` | `https://{PROJECT}.supabase.co/auth/v1/.well-known/openid-configuration` |
| `OPENID_REDIRECT_URI` | `https://tu-dominio/oauth/oidc/callback` |
| `ENABLE_LOGIN_FORM` | `false` |
| `OAUTH_AUTO_REDIRECT` | `true` |
| `OAUTH_PROVIDER_NAME` | `Supabase` |

### 4. Configurar Supabase

- **Authentication > Settings > Site URL**: `https://tu-dominio`
- **Authentication > Settings > OAuth Apps**: Añade `https://tu-dominio/oauth/oidc/callback`
  como redirect URL
- **Authentication > Settings > Redirect URLs**: opcional (para flujos nativos)

### 5. Desplegar

```bash
docker run -d \
  --name open-webui \
  -p 8080:8080 \
  -e SUPABASE_PROJECT=tu-project-ref \
  -e SUPABASE_SERVICE_ROLE_KEY=eyJ... \
  -e OAUTH_CLIENT_ID=... \
  -e OAUTH_CLIENT_SECRET=... \
  -e OPENID_PROVIDER_URL=... \
  -e OPENID_REDIRECT_URI=... \
  -e ENABLE_LOGIN_FORM=false \
  -e OAUTH_AUTO_REDIRECT=true \
  -e OAUTH_PROVIDER_NAME=Supabase \
  ghcr.io/tuusuario/tu-repo:latest
```

O en Coolify: usa la imagen `ghcr.io/tuusuario/tu-repo:latest` y añade las
variables de entorno en el panel.
