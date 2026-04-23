"""
Aurum Content Agent v3 — Hashnode Edition
Publica automáticamente en Hashnode via GraphQL API
"""

import os, sqlite3, json, time, requests
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
TELEGRAM_TOKEN        = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID      = os.getenv("TELEGRAM_CHAT_ID")
ARTICLES_DIR          = Path("articles")
DB_PATH               = "aurum.db"
AMAZON_TAG = os.getenv("AMAZON_TAG", "aurum099-21")

PRODUCTS = {
    "mejores brokers online España 2026": [
        {"name": "El Inversor Inteligente", "asin": "8423426955", "price": "€18", "best_for": "inversión value", "score": "9.5"},
        {"name": "Padre Rico Padre Pobre", "asin": "8466329390", "price": "€14", "best_for": "mentalidad financiera", "score": "8.8"},
        {"name": "Un paso por delante de Wall Street", "asin": "8423413654", "price": "€16", "best_for": "bolsa principiantes", "score": "9.0"},
    ],
    "mejor portátil calidad precio 2026 menos 800 euros": [
        {"name": "Acer Aspire 5 A515", "asin": "B0CLWXB7JY", "price": "€549", "best_for": "uso general y estudiantes", "score": "9.0"},
        {"name": "Lenovo IdeaPad 3", "asin": "B09TQXHPZK", "price": "€479", "best_for": "presupuesto ajustado", "score": "8.5"},
        {"name": "HP 15s-fq5065ns", "asin": "B0BW3TTKGM", "price": "€599", "best_for": "ofimática y multimedia", "score": "8.7"},
    ],
    "auriculares inalámbricos cancelación de ruido menos 100 euros": [
        {"name": "Soundcore Q45", "asin": "B09BJKR2MH", "price": "€59", "best_for": "mejor calidad-precio", "score": "9.2"},
        {"name": "JBL Tune 770NC", "asin": "B0BZSCY3GZ", "price": "€79", "best_for": "bajos potentes", "score": "8.9"},
        {"name": "Edifier W820NB", "asin": "B09KC8FSJD", "price": "€69", "best_for": "diseño premium económico", "score": "8.7"},
    ],
    "mejor cochecito bebé calidad precio 2026": [
        {"name": "Chicco Miinimo4", "asin": "B09ZQMG6ZP", "price": "€199", "best_for": "presupuesto ajustado", "score": "8.4"},
        {"name": "Cybex Eezy S Twist+2", "asin": "B07WQHBMGK", "price": "€299", "best_for": "rotación 360°", "score": "8.8"},
        {"name": "Bugaboo Butterfly", "asin": "B0B1Z7QXPK", "price": "€599", "best_for": "calidad premium ciudad", "score": "9.2"},
    ],
    "proteína whey mejor calidad precio España": [
        {"name": "Myprotein Impact Whey 1kg", "asin": "B00INBGZGE", "price": "€34", "best_for": "mejor relación calidad-precio", "score": "9.3"},
        {"name": "Optimum Nutrition Gold Standard 908g", "asin": "B000QSNYGI", "price": "€54", "best_for": "calidad premium", "score": "9.0"},
        {"name": "Weider Premium Whey 500g", "asin": "B07X9QFKQZ", "price": "€22", "best_for": "iniciarse sin gastar mucho", "score": "8.5"},
    ],
    "mejor colchón para dolor de espalda 2026": [
        {"name": "Emma Original 150x200cm", "asin": "B076ZKQF83", "price": "€399", "best_for": "posición mixta y espalda", "score": "9.2"},
        {"name": "Pikolin New Vitalia 150x200", "asin": "B07RQGFXQB", "price": "€459", "best_for": "marca española clásica", "score": "8.9"},
        {"name": "Dreamea Sport 150x200", "asin": "B07CZ6NBTX", "price": "€279", "best_for": "presupuesto ajustado", "score": "8.7"},
    ],
    "VPN más segura y rápida 2026": [
        {"name": "NordVPN Tarjeta 1 año", "asin": "B07ZFQSV4K", "price": "€47", "best_for": "seguridad y velocidad", "score": "9.4"},
        {"name": "Surfshark Tarjeta 1 año", "asin": "B08K4VDXJL", "price": "€35", "best_for": "dispositivos ilimitados", "score": "9.1"},
    ],
    "gestores de contraseñas más seguros 2026": [
        {"name": "YubiKey 5 NFC", "asin": "B07HBD71HL", "price": "€54", "best_for": "máxima seguridad 2FA", "score": "9.5"},
        {"name": "YubiKey 5C NFC", "asin": "B08DHL1YDL", "price": "€58", "best_for": "USB-C + NFC", "score": "9.3"},
    ],
    "smartwatch para monitorizar salud menos 200 euros": [
        {"name": "Garmin Vívomove Sport", "asin": "B09SMQYVBK", "price": "€159", "best_for": "salud y estilo clásico", "score": "9.0"},
        {"name": "Samsung Galaxy Watch6 40mm", "asin": "B0C6BRGWKQ", "price": "€189", "best_for": "usuarios Android", "score": "8.8"},
        {"name": "Xiaomi Smart Band 8 Pro", "asin": "B0CJQQ3GGL", "price": "€59", "best_for": "presupuesto mínimo", "score": "8.4"},
    ],
}

def amazon_link(asin):
    return f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"

def amazon_image(asin):
    return f"https://images-na.ssl-images-amazon.com/images/I/{asin}._AC_SL300_.jpg"

def get_products_for_keyword(keyword):
    return [
        {**p, "link": amazon_link(p["asin"]), "image": amazon_image(p["asin"])}
        for p in PRODUCTS.get(keyword, [])
    ]

SKILLS_DIR            = Path("skills")

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

# ── GENERACIÓN ────────────────────────────────────────────────────────────────
def generate_article(keyword, nicho, products=None):
    print(f"  ✍️  Generando: '{keyword}'")

    skills_names = ["content", "seo"]
    if "bebe" in nicho or "crianza" in nicho:
        skills_names.append("parenting")

    skills_ctx = load_skills(*skills_names)

    products_info = ""
    if products:
        products_info = "\n\nPRODUCTOS REALES EN AMAZON.ES (inclúyelos en tu análisis):\n"
        products_info += "\n".join(
            f"- {p['name']} | {p['price']} | Ideal para: {p['best_for']} | Score: {p['score']}"
            for p in products
        )

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
}}{products_info}"""

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

    # Rotar entre categorías para más variedad
    # Agrupar pendientes por nicho
    nichos_pendientes = {}
    for nicho, kw in pending:
        if nicho not in nichos_pendientes:
            nichos_pendientes[nicho] = []
        nichos_pendientes[nicho].append((nicho, kw))
    
    # Procesar hasta 10 artículos por ciclo, rotando entre nichos
    max_articulos = 10
    procesados = 0
    nicho_index = 0
    nichos_list = list(nichos_pendientes.keys())
    
    while procesados < max_articulos and nicho_index < len(nichos_list):
        nicho_actual = nichos_list[nicho_index]
        if nichos_pendientes[nicho_actual]:
            nicho, kw = nichos_pendientes[nicho_actual].pop(0)
            print(f"{'─'*40}")
            try:
                products = get_products_for_keyword(kw)
                data     = generate_article(kw, nicho, products)
                markdown = to_markdown(data)
                save_local(data, markdown, nicho)

                slug = data.get("slug", data["title"].lower().replace(" ", "-")[:60])
                article_html = publisher.generate_html(data, markdown, products)
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

                url = f"{os.getenv('SITE_URL', '')}/articles/{slug}.html"
                save_record(kw, nicho, data["title"], url)
                generados += 1
                procesados += 1
                time.sleep(3)
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON error '{kw}': {e}")
                errores += 1
                procesados += 1
            except Exception as e:
                print(f"  ❌ Error '{kw}': {e}")
                errores += 1
                procesados += 1
                if errores >= 3:
                    notify(f"⚠️ 3 errores seguidos.\n`{str(e)[:200]}`")
                    break
        
        # Pasar al siguiente nicho (rotación)
        nicho_index = (nicho_index + 1) % len(nichos_list)
        
        # Si todos los nichos están vacíos, salir
        if all(not items for items in nichos_pendientes.values()):
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