# AURUM Reviews

Agente de contenido que genera artículos, los convierte a HTML premium y los publica en GitHub Pages desde `docs/`.

## Configuración rápida

1. Crea y activa entorno virtual:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
2. Instala dependencias:
   - `pip install -r requirements.txt`
3. Completa `.env` (mínimo):
   - `LLM_PROVIDER=gemini`
   - `GEMINI_API_KEY=...` (o la key del proveedor elegido)
   - `GITHUB_REPO_PATH=/Users/akiles/Desktop/dev/aurum` (ruta local real del repo)
   - `SITE_NAME=AURUM`
   - `SITE_URL=https://akilesbailoyo.github.io/aurumreviews`

## Ejecutar el agente

- `python agent.py`

Por cada artículo, el flujo hace:
- Genera markdown en `articles/...`
- Genera HTML en `docs/articles/<slug>.html`
- Regenera `docs/index.html`
- Intenta `git add/commit/push` automático mediante `publisher.py`

## Publicación en GitHub Pages

En GitHub:
1. Ve a `Settings -> Pages`
2. `Source`: **Deploy from a branch**
3. `Branch`: `main`
4. `Folder`: `/docs`

URL esperada del sitio:
- `https://akilesbailoyo.github.io/aurumreviews`

## Problemas comunes

- **No aparece el sitio**:
  - Revisa que `docs/index.html` exista y esté en `main`.
  - Espera 1-3 minutos tras push.
  - Revisa `Settings -> Pages` por estado de deploy.
- **`git push` rechazado (fetch first)**:
  - Ejecuta `git branch --set-upstream-to=origin/main main`
  - Luego `git pull --rebase --autostash`
  - Después `git push origin main`
- **`GITHUB_REPO_PATH` mal puesto**:
  - Debe ser ruta local del repo, no URL remota.