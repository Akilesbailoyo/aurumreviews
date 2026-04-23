"""
Aurum Content Agent v3 — Hashnode Edition
Publica automáticamente en Hashnode via GraphQL API
"""

import os, sqlite3, json, time, re, unicodedata, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import anthropic
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
import publisher

load_dotenv()

LLM_PROVIDER          = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
LLM_MODEL             = os.getenv("LLM_MODEL", "").strip()
GEMINI_API_KEY        = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY        = os.getenv("CLAUDE_API_KEY")
GROQ_API_KEY          = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY")
HASHNODE_TOKEN        = os.getenv("HASHNODE_TOKEN")
HASHNODE_PUB_ID       = os.getenv("HASHNODE_PUBLICATION_ID")
TELEGRAM_TOKEN        = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID      = os.getenv("TELEGRAM_CHAT_ID")
ARTICLES_DIR          = Path("articles")
DB_PATH               = "aurum.db"
SKILLS_DIR            = Path("skills")
HASHNODE_API          = "https://gql.hashnode.com"
PROVIDER_ORDER        = ["gemini", "groq", "claude", "openai"]
DEFAULT_MODELS        = {
    "gemini": "gemini-2.0-flash",
    "claude": "claude-opus-4-5",
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
}

# ── KEYWORDS ─────────────────────────────────────────────────────────────────
KEYWORDS = {
    "finanzas": [
        "mejores brokers online España 2026",
        "cuentas de ahorro con más rentabilidad España",
        "cómo invertir en ETF siendo principiante España",
        "mejores fondos indexados España 2026",
        "robo advisors España comparativa",
        "broker para comprar acciones sin comisiones",
        "cómo declarar inversiones en la renta España",
        "mejores aplicaciones para ahorrar dinero España",
    ],
    "tecnologia": [
        "mejor portátil calidad precio 2026 menos 800 euros",
        "auriculares inalámbricos cancelación de ruido menos 100 euros",
        "mejor móvil gama media 2026 España",
        "VPN más segura y rápida 2026",
        "gestores de contraseñas más seguros 2026",
        "mejor antivirus gratuito 2026",
        "disco duro externo más fiable 2026",
        "tableta para trabajar y estudiar menos 300 euros",
    ],
    "bebes_y_crianza": [
        "mejor cochecito bebé calidad precio 2026",
        "silla de coche bebé más segura grupo 0 1",
        "mejores cursos online crianza respetuosa",
        "monitor bebé con cámara mejor valorado",
        "cuna de colecho segura recomendaciones",
        "mejor sacaleches eléctrico 2026",
        "curso sueño infantil online recomendado",
        "portabebés ergonómico mejor valorado España",
    ],
    "bienestar": [
        "mejor colchón para dolor de espalda 2026",
        "proteína whey mejor calidad precio España",
        "mejores vitaminas para la fatiga y el cansancio",
        "colágeno marino beneficios y mejores marcas",
        "app de meditación gratuita mejor valorada",
        "smartwatch para monitorizar salud menos 200 euros",
    ]
}

TAGS_MAP = {
    "finanzas":        ["finanzas", "inversion", "ahorro", "españa", "dinero"],
    "tecnologia":      ["tecnologia", "gadgets", "reviews", "compras"],
    "bebes_y_crianza": ["bebes", "crianza", "maternidad", "familia"],
    "bienestar":       ["salud", "bienestar", "fitness", "suplementos"],
}

# ── SKILLS ───────────────────────────────────────────────────────────────────
def load_skills(*names):
    if not SKILLS_DIR.exists():
        return ""
    chunks = []
    for f in sorted(SKILLS_DIR.glob("*.md")):
        if any(n.lower() in f.name.lower() for n in names):
            chunks.append(f.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(chunks)

# ── BASE DE DATOS ─────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY,
        keyword TEXT UNIQUE,
        nicho TEXT,
        title TEXT,
        url TEXT,
        status TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

def already_done(kw):
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT id FROM articles WHERE keyword=?", (kw,)).fetchone()
    conn.close()
    return r is not None

def save_record(kw, nicho, title, url=""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO articles (keyword,nicho,title,url,status,created_at) VALUES (?,?,?,?,?,?)",
        (kw, nicho, title, url, "published" if url else "local", datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def total():
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    conn.close()
    return n

# ── TELEGRAM ──────────────────────────────────────────────────────────────────
def notify(msg):
    print(f"\n📱 {msg}\n")
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except Exception as e:
            print(f"[Telegram error] {e}")

def to_hashnode_slug(text):
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug[:250] if slug else "tag"

# ── GENERACIÓN ────────────────────────────────────────────────────────────────
def generate_article(keyword, nicho):
    print(f"  ✍️  Generando: '{keyword}'")

    skills_names = ["content", "seo"]
    if "bebe" in nicho or "crianza" in nicho:
        skills_names.append("parenting")

    skills_ctx = load_skills(*skills_names)

    system = f"""Eres el equipo editorial de AURUM, publicación experta en recomendaciones de producto.
Principios inamovibles:
- La recomendación ganadora va en la PRIMERA FRASE, siempre
- Todo claim tiene datos o consenso de usuarios detrás
- Incluye siempre un punto débil real del ganador (construye confianza)
- Tono directo, humano, sin jerga corporativa
- FAQ al final optimizado para ser citado por ChatGPT y Perplexity (AEO)

{skills_ctx}

RESPONDE ÚNICAMENTE CON JSON VÁLIDO. Sin texto antes ni después. Sin markdown."""

    prompt = f"""Keyword objetivo: "{keyword}"
Nicho: {nicho}

Devuelve este JSON exacto:
{{
  "title": "título H1 con keyword natural",
  "subtitle": "subtítulo que amplía el título",
  "meta_description": "máximo 155 caracteres",
  "slug": "url-amigable",
  "intro": "primer párrafo: 'El mejor X es Y porque...' — respuesta directa en frase 1",
  "verdict": {{
    "winner": "nombre del ganador",
    "score": "9.2/10",
    "why": "razón específica en 1 frase",
    "best_for": "perfil ideal del comprador",
    "weakness": "punto débil honesto y real"
  }},
  "comparison": [
    {{"name":"Producto A","score":"9.2","price":"€X","best_for":"..."}},
    {{"name":"Producto B","score":"8.5","price":"€Y","best_for":"..."}},
    {{"name":"Producto C","score":"7.8","price":"€Z","best_for":"..."}}
  ],
  "sections": [
    {{"h2":"Por qué [ganador] es nuestra recomendación","content":"..."}},
    {{"h2":"Comparativa completa analizada","content":"..."}},
    {{"h2":"Para quién NO lo recomendamos","content":"..."}},
    {{"h2":"Metodología: cómo lo analizamos","content":"..."}}
  ],
  "faq": [
    {{"q":"¿Cuál es el mejor X para Y?","a":"respuesta directa"}},
    {{"q":"¿Vale la pena el precio?","a":"..."}},
    {{"q":"¿Existe alternativa gratuita?","a":"..."}},
    {{"q":"¿Con qué frecuencia actualizáis este análisis?","a":"Mensualmente."}}
  ],
  "affiliate_products": ["producto1","producto2"]
}}"""

    raw = llm_generate(system, prompt)
    return _extract_json(raw)

def _extract_json(raw):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").replace("json\n", "", 1).strip()
    return json.loads(cleaned)

def get_model_for_provider(provider):
    return LLM_MODEL if LLM_MODEL else DEFAULT_MODELS[provider]

def get_fallback_chain():
    provider = LLM_PROVIDER if LLM_PROVIDER in PROVIDER_ORDER else "gemini"
    idx = PROVIDER_ORDER.index(provider)
    return PROVIDER_ORDER[idx:]

def llm_generate(system_prompt, user_prompt):
    last_error = None
    chain = get_fallback_chain()
    for i, provider in enumerate(chain):
        model = get_model_for_provider(provider)
        try:
            if provider == "gemini":
                return _generate_with_gemini(system_prompt, user_prompt, model)
            if provider == "groq":
                return _generate_with_groq(system_prompt, user_prompt, model)
            if provider == "claude":
                return _generate_with_claude(system_prompt, user_prompt, model)
            if provider == "openai":
                return _generate_with_openai(system_prompt, user_prompt, model)
        except Exception as e:
            last_error = e
            next_provider = chain[i + 1] if i + 1 < len(chain) else None
            if next_provider:
                print(
                    f"  ⚠️ LLM '{provider}' falló ({e}). "
                    f"Fallback a '{next_provider}'."
                )
            else:
                break
    raise RuntimeError(f"Todos los proveedores LLM fallaron. Último error: {last_error}")

def _generate_with_claude(system_prompt, user_prompt, model):
    if not CLAUDE_API_KEY:
        raise ValueError("Falta CLAUDE_API_KEY en .env para usar Claude.")

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    msg = client.messages.create(
        model=model,
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return msg.content[0].text

def _generate_with_gemini(system_prompt, user_prompt, model):
    if not GEMINI_API_KEY:
        raise ValueError("Falta GEMINI_API_KEY en .env para usar Gemini.")

    genai.configure(api_key=GEMINI_API_KEY)
    model_client = genai.GenerativeModel(model_name=model, system_instruction=system_prompt)
    resp = model_client.generate_content(
        user_prompt,
        generation_config={"temperature": 0.5, "max_output_tokens": 4000}
    )
    if not getattr(resp, "text", None):
        raise ValueError("Respuesta vacía de Gemini.")
    return resp.text

def _generate_with_groq(system_prompt, user_prompt, model):
    if not GROQ_API_KEY:
        raise ValueError("Falta GROQ_API_KEY en .env para usar Groq.")

    client = Groq(api_key=GROQ_API_KEY)
    msg = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=4000,
    )
    return msg.choices[0].message.content or ""

def _generate_with_openai(system_prompt, user_prompt, model):
    if not OPENAI_API_KEY:
        raise ValueError("Falta OPENAI_API_KEY en .env para usar OpenAI.")

    client = OpenAI(api_key=OPENAI_API_KEY)
    msg = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=4000,
    )
    return msg.choices[0].message.content or ""

# ── CONVERTIR A MARKDOWN ──────────────────────────────────────────────────────
def to_markdown(data):
    v = data["verdict"]
    lines = [
        f"# {data['title']}\n",
        f"*{data['subtitle']}*\n",
        f"\n---\n",
        f"**🏆 VEREDICTO — Nuestra recomendación**\n\n",
        f"**{v['winner']}** · {v['score']}\n\n",
        f"_{v['why']}_\n\n",
        f"✅ Ideal para: {v['best_for']}\n\n",
        f"⚠️ Ten en cuenta: {v['weakness']}\n\n",
        f"---\n\n",
        f"{data['intro']}\n\n",
        f"## Comparativa rápida\n\n",
        "| Producto | Score | Precio | Ideal para |\n",
        "|----------|-------|--------|------------|\n",
    ]
    for p in data.get("comparison", []):
        mark = " 🏆" if p["name"] == v["winner"] else ""
        lines.append(f"| {p['name']}{mark} | {p['score']} | {p['price']} | {p['best_for']} |\n")

    for s in data.get("sections", []):
        lines += [f"\n## {s['h2']}\n\n", f"{s['content']}\n"]

    lines.append("\n## Preguntas frecuentes\n")
    for item in data.get("faq", []):
        lines += [f"\n**{item['q']}**\n\n", f"{item['a']}\n"]

    lines.append(f"\n---\n*Análisis actualizado: {datetime.now().strftime('%B %Y')}. "
                 "AURUM revisa sus recomendaciones mensualmente.*\n")

    return "".join(lines)

# ── PUBLICAR EN HASHNODE ──────────────────────────────────────────────────────
def publish_hashnode(data, markdown, nicho):
    if not HASHNODE_TOKEN or not HASHNODE_PUB_ID:
        print("  ⚠️  Sin HASHNODE_TOKEN o HASHNODE_PUBLICATION_ID — solo guardado local")
        return None

    tags = [{"name": t, "slug": to_hashnode_slug(t)} for t in TAGS_MAP.get(nicho, ["recomendaciones"])]

    mutation = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) {
        post {
          id
          url
          title
        }
      }
    }
    """

    variables = {
        "input": {
            "title": data["title"],
            "subtitle": data.get("subtitle", ""),
            "publicationId": HASHNODE_PUB_ID,
            "contentMarkdown": markdown,
            "slug": data.get("slug", ""),
            "tags": tags,
            "metaTags": {
                "title": data["title"],
                "description": data.get("meta_description", ""),
            },
            "publishedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        }
    }

    resp = requests.post(
        HASHNODE_API,
        json={"query": mutation, "variables": variables},
        headers={
            "Authorization": HASHNODE_TOKEN,
            "Content-Type": "application/json"
        },
        timeout=20
    )

    result = resp.json()
    if "errors" in result:
        print(f"  ❌ Hashnode error: {result['errors']}")
        return None

    url = result["data"]["publishPost"]["post"]["url"]
    print(f"  ✅ Publicado: {url}")
    return url

# ── GUARDAR LOCAL ─────────────────────────────────────────────────────────────
def save_local(data, markdown, nicho):
    d = ARTICLES_DIR / nicho
    d.mkdir(parents=True, exist_ok=True)
    slug = data.get("slug", data["title"].lower().replace(" ", "-")[:60])
    path = d / f"{slug}.md"
    path.write_text(markdown, encoding="utf-8")
    print(f"  💾 Local: {path}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def run():
    print(f"\n{'═'*50}")
    print(f"  🤖 AURUM AGENT — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'═'*50}")
    selected_provider = LLM_PROVIDER if LLM_PROVIDER in PROVIDER_ORDER else "gemini"
    print(f"  🧠 LLM: {selected_provider} / {get_model_for_provider(selected_provider)}")

    init_db()
    ARTICLES_DIR.mkdir(exist_ok=True)
    publisher.ensure_style()

    n = total()
    print(f"  📊 Total publicados: {n}")

    pending = [
        (nicho, kw)
        for nicho, kws in KEYWORDS.items()
        for kw in kws
        if not already_done(kw)
    ]

    if not pending:
        notify("✅ Todas las keywords completadas. Añade más en KEYWORDS del agente.")
        return

    print(f"  📋 Pendientes: {len(pending)}\n")
    generados = errores = 0

    for nicho, kw in pending[:3]:
        print(f"{'─'*40}")
        try:
            data     = generate_article(kw, nicho)
            markdown = to_markdown(data)
            save_local(data, markdown, nicho)

            slug = data.get("slug", data["title"].lower().replace(" ", "-")[:60])
            article_html = publisher.generate_html(data, markdown)
            article_html_path = publisher.ARTICLES_DIR / f"{slug}.html"
            article_html_path.write_text(article_html, encoding="utf-8")

            all_articles = publisher.upsert_article_metadata(
                {
                    "slug": slug,
                    "title": data.get("title", ""),
                    "nicho": nicho,
                    "winner_score": data.get("verdict", {}).get("score", "-"),
                    "url": f"articles/{slug}.html",
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
            publisher.update_index(all_articles)
            publisher.git_publish(
                article_html_path,
                f"Publish article: {data.get('title', slug)}",
            )
            publisher.git_publish(
                publisher.DOCS_DIR / "index.html",
                "Update docs index",
            )

            url      = publish_hashnode(data, markdown, nicho)
            save_record(kw, nicho, data["title"], url or "")
            generados += 1
            time.sleep(3)
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON error '{kw}': {e}")
            errores += 1
        except Exception as e:
            print(f"  ❌ Error '{kw}': {e}")
            errores += 1
            if errores >= 3:
                notify(f"⚠️ 3 errores seguidos.\n`{str(e)[:200]}`")
                break

    notify(
        f"✅ *Ciclo completado*\n"
        f"• Nuevos: {generados}\n"
        f"• Total: {n + generados}\n"
        f"• Pendientes: {len(pending) - generados}\n"
        f"• Errores: {errores}"
    )

if __name__ == "__main__":
    run()