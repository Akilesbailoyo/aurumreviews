import json
import os
import subprocess
from datetime import datetime
from html import escape
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SITE_NAME        = os.getenv("SITE_NAME", "AURUM")
SITE_URL         = os.getenv("SITE_URL", "https://example.github.io/aurum").rstrip("/")
GITHUB_REPO_PATH = Path(os.getenv("GITHUB_REPO_PATH", Path.cwd()))

DOCS_DIR      = GITHUB_REPO_PATH / "docs"
ARTICLES_DIR  = DOCS_DIR / "articles"
MANIFEST_PATH = ARTICLES_DIR / "_manifest.json"
STYLE_PATH    = DOCS_DIR / "style.css"


def _ensure_paths():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)


def _updated_label():
    return datetime.now().strftime("%B %Y")


def _faq_schema(faq_items):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item.get("q", ""),
                "acceptedAnswer": {"@type": "Answer", "text": item.get("a", "")},
            }
            for item in faq_items
        ],
    }


def _article_schema(article_data, article_url):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article_data.get("title", ""),
        "description": article_data.get("meta_description", ""),
        "datePublished": datetime.utcnow().isoformat() + "Z",
        "dateModified": datetime.utcnow().isoformat() + "Z",
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
        "mainEntityOfPage": article_url,
        "image": f"{SITE_URL}/og-default.jpg",
    }


def _render_comparison_rows(comparison, winner):
    rows = []
    for item in comparison:
        name     = escape(item.get("name", ""))
        score    = escape(item.get("score", ""))
        price    = escape(item.get("price", ""))
        best_for = escape(item.get("best_for", ""))
        badge    = " <span class='winner-badge'>TOP</span>" if item.get("name") == winner else ""
        rows.append(
            f"<tr><td>{name}{badge}</td><td>{score}</td><td>{price}</td><td>{best_for}</td></tr>"
        )
    return "\n".join(rows)


def _render_sections(sections):
    blocks = []
    for section in sections:
        h2      = escape(section.get("h2", ""))
        content = escape(section.get("content", ""))
        blocks.append(
            f"<section class='article-section'><h2>{h2}</h2><p>{content}</p></section>"
        )
    return "\n".join(blocks)


def _render_faq(faq_items):
    blocks = []
    for item in faq_items:
        q = escape(item.get("q", ""))
        a = escape(item.get("a", ""))
        blocks.append(
            f"<details class='faq-item'><summary>{q}</summary><p>{a}</p></details>"
        )
    return "\n".join(blocks)


def _render_product_cards(products, winner):
    if not products:
        return ""
    cards = []
    for p in products:
        name     = escape(p.get("name", ""))
        price    = escape(p.get("price", ""))
        best_for = escape(p.get("best_for", ""))
        score    = escape(p.get("score", ""))
        link     = escape(p.get("link", "#"))
        image    = escape(p.get("image", ""))
        is_winner = p.get("name") == winner
        border   = "border:2px solid var(--accent);" if is_winner else "border:1px solid var(--border);"
        bg       = "background:#1a1610;" if is_winner else "background:var(--panel);"
        badge    = "<span class='winner-badge'>MEJOR OPCIÓN</span>" if is_winner else ""
        cards.append(f"""
<div class='product-card' style='{border}{bg}'>
  <img src='{image}' alt='{name}' class='product-img' onerror='this.style.display="none"'>
  <div class='product-info'>
    <div class='product-name'>{name} {badge}</div>
    <div class='product-meta'>
      <span class='product-score'>{score}</span>
      <span class='product-price'>{price}</span>
      <span class='product-best'>Ideal para: {best_for}</span>
    </div>
    <a href='{link}' class='amazon-btn' target='_blank' rel='noopener sponsored'>
      Ver en Amazon →
    </a>
  </div>
</div>""")
    disclaimer = (
        "<p class='affiliate-disclaimer'>* Enlaces de afiliado Amazon.es. "
        "Si compras a través de ellos recibimos una pequeña comisión sin coste adicional para ti. "
        "Nunca afecta nuestras recomendaciones.</p>"
    )
    return "<div class='product-cards'>" + "\n".join(cards) + "</div>" + disclaimer


def generate_html(article_data, markdown_content, products=None):
    _ensure_paths()
    verdict     = article_data.get("verdict", {})
    winner      = verdict.get("winner", "")
    score       = verdict.get("score", "")
    best_for    = verdict.get("best_for", "")
    weakness    = verdict.get("weakness", "")
    why         = verdict.get("why", "")
    slug        = article_data.get("slug", "articulo")
    title       = article_data.get("title", "AURUM Article")
    subtitle    = article_data.get("subtitle", "")
    intro       = article_data.get("intro", "")
    description = article_data.get("meta_description", "")
    nicho_raw   = article_data.get("nicho", "")
    nicho_label = nicho_raw.replace("_", " ").upper()
    faq_items   = article_data.get("faq", [])
    article_url = f"{SITE_URL}/articles/{slug}.html"

    article_schema    = json.dumps(_article_schema(article_data, article_url), ensure_ascii=False)
    faq_schema        = json.dumps(_faq_schema(faq_items), ensure_ascii=False)
    product_cards_html = _render_product_cards(products or [], winner)

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)} | {escape(SITE_NAME)}</title>
  <meta name="description" content="{escape(description)}" />
  <meta property="og:title" content="{escape(title)}" />
  <meta property="og:description" content="{escape(description)}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{escape(article_url)}" />
  <meta property="og:image" content="{escape(SITE_URL)}/og-default.jpg" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../style.css" />
  <script type="application/ld+json">{article_schema}</script>
  <script type="application/ld+json">{faq_schema}</script>
</head>
<body>
  <header class="site-header">
    <a class="logo" href="../index.html">{escape(SITE_NAME)}</a>
    <span class="header-right">{escape(nicho_label)}</span>
  </header>

  <main class="article-wrap">
    <div class="breadcrumb">
      <a href="../index.html">AURUM</a>
      <span>›</span>
      <span>{escape(nicho_label)}</span>
    </div>

    <article class="article-card">
      <p class="eyebrow">◈ Guía experta</p>
      <h1>{escape(title)}</h1>
      <p class="subtitle">{escape(subtitle)}</p>

      <!-- VEREDICTO -->
      <div class="verdict-box">
        <div class="verdict-label">🏆 Veredicto — Nuestra recomendación</div>
        <div class="winner">{escape(winner)} <span>{escape(score)}</span></div>
        <div class="why">{escape(why)}</div>
        <div class="verdict-pills">
          <span class="pill-good">✅ {escape(best_for)}</span>
          <span class="pill-bad">⚠️ {escape(weakness)}</span>
        </div>
      </div>

      <!-- INTRO -->
      <p class="intro-block">{escape(intro)}</p>

      <!-- COMPARATIVA -->
      <section class="article-section">
        <h2>Comparativa rápida</h2>
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Producto</th><th>Score</th><th>Precio</th><th>Ideal para</th></tr>
            </thead>
            <tbody>
              {_render_comparison_rows(article_data.get("comparison", []), winner)}
            </tbody>
          </table>
        </div>
      </section>

      <!-- PRODUCTOS AMAZON -->
      <section class="article-section">
        <h2>Dónde comprar</h2>
        {product_cards_html}
      </section>

      <!-- SECCIONES -->
      {_render_sections(article_data.get("sections", []))}

      <!-- FAQ -->
      <div class="faq-section">
        <h2>Preguntas frecuentes</h2>
        {_render_faq(faq_items)}
      </div>

      <!-- FECHA -->
      <div class="updated-note">
        📅 Actualizado: {_updated_label()} · AURUM revisa sus análisis mensualmente.
      </div>

    </article>
  </main>

  <footer class="site-footer">
    <div class="footer-logo">{escape(SITE_NAME)}</div>
    Curated for those who choose wisely · {_updated_label()}
  </footer>
</body>
</html>
"""


def update_index(all_articles):
    _ensure_paths()
    n = len(all_articles)
    cards = []
    for article in sorted(all_articles, key=lambda x: x.get("updated_at", ""), reverse=True):
        title    = escape(article.get("title", "Artículo"))
        nicho    = escape(article.get("nicho", "general"))
        score    = escape(article.get("winner_score", "-"))
        href     = escape(article.get("url", "#"))
        cards.append(
            f"<a class='article-item' data-category='{nicho}' href='{href}'>"
            f"<p class='article-nicho'>{nicho}</p>"
            f"<h3>{title}</h3>"
            f"<span class='article-score'>{score}</span>"
            f"</a>"
        )
    cards_html = "\n".join(cards) if cards else "<p style='color:var(--muted);padding:40px 0;'>No hay artículos todavía.</p>"

    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(SITE_NAME)} | Recomendaciones de expertos</title>
  <meta name="description" content="Análisis independientes de {escape(SITE_NAME)}: finanzas, tecnología, bebés y bienestar. La mejor opción, siempre en la primera frase." />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="./style.css" />
</head>
<body>
  <header class="site-header">
    <span class="logo">{escape(SITE_NAME)}</span>
    <span class="header-right">Análisis independientes</span>
  </header>

  <main class="index-wrap">

    <!-- HERO -->
    <section class="hero">
      <p class="eyebrow">◈ Editorial Intelligence</p>
      <h1>La respuesta,<br><em>siempre primero.</em></h1>
      <p>Analizamos cientos de productos para darte la mejor opción en la primera frase. Sin publicidad pagada. Sin sesgos.</p>
    </section>

    <!-- STATS -->
    <div class="stats">
      <div class="stat">
        <div class="stat-number">{n}+</div>
        <div class="stat-label">Análisis publicados</div>
      </div>
      <div class="stat">
        <div class="stat-number">4</div>
        <div class="stat-label">Categorías</div>
      </div>
      <div class="stat">
        <div class="stat-number">0</div>
        <div class="stat-label">Contenido pagado</div>
      </div>
    </div>

    <!-- FILTROS -->
    <div class="section-header">
      <h2>Últimos análisis</h2>
      <div class="section-line"></div>
    </div>
    <section class="filters">
      <button class="filter-btn active" data-filter="all">Todos</button>
      <button class="filter-btn" data-filter="finanzas">Finanzas</button>
      <button class="filter-btn" data-filter="tecnologia">Tecnología</button>
      <button class="filter-btn" data-filter="bebes_y_crianza">Bebés</button>
      <button class="filter-btn" data-filter="bienestar">Bienestar</button>
    </section>

    <!-- ARTÍCULOS -->
    <section class="article-grid">
      {cards_html}
    </section>

  </main>

  <footer class="site-footer">
    <div class="footer-logo">{escape(SITE_NAME)}</div>
    Curated for those who choose wisely · {_updated_label()}
  </footer>

  <script>
    const buttons = document.querySelectorAll(".filter-btn");
    const items   = document.querySelectorAll(".article-item");
    buttons.forEach((btn) => {{
      btn.addEventListener("click", () => {{
        buttons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const filter = btn.dataset.filter;
        items.forEach((card) => {{
          card.style.display = (filter === "all" || card.dataset.category === filter) ? "" : "none";
        }});
      }});
    }});
  </script>
</body>
</html>
"""
    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
    return html


def ensure_style():
    _ensure_paths()
    css = """
:root {
  --bg: #0c0c0c;
  --panel: #141414;
  --panel2: #1a1a1a;
  --text: #f0ebe0;
  --muted: #7a7060;
  --muted2: #b0a890;
  --accent: #d4a853;
  --border: rgba(255,255,255,0.06);
  --border-accent: rgba(212,168,83,0.25);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'DM Sans', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.7;
}
h1, h2, h3, .logo { font-family: 'Cormorant Garamond', Georgia, serif; }
a { color: var(--accent); text-decoration: none; }

/* ── HEADER ── */
.site-header {
  position: sticky; top: 0; z-index: 100;
  background: rgba(12,12,12,0.96);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
  padding: 0 40px;
  height: 62px;
  display: flex; align-items: center; justify-content: space-between;
}
.logo { font-size: 26px; color: var(--accent); letter-spacing: 5px; font-weight: 700; }
.header-right { font-size: 11px; color: var(--muted); letter-spacing: 2px; text-transform: uppercase; }

/* ── INDEX ── */
.index-wrap { max-width: 1020px; margin: 0 auto; padding: 0 24px 80px; }

.hero {
  padding: 80px 0 56px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0;
}
.eyebrow {
  font-size: 11px; color: var(--accent);
  letter-spacing: 3px; text-transform: uppercase;
  margin-bottom: 18px; font-family: 'DM Sans', sans-serif;
}
.hero h1 {
  font-size: clamp(44px, 7vw, 82px);
  font-weight: 300; line-height: 1.05; margin-bottom: 18px;
}
.hero h1 em { color: var(--accent); font-style: italic; }
.hero p { font-size: 16px; color: var(--muted); max-width: 460px; line-height: 1.7; }

/* ── STATS ── */
.stats {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1px; background: var(--border);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  margin-bottom: 48px;
}
.stat { background: var(--bg); padding: 28px 24px; }
.stat-number {
  font-family: 'Cormorant Garamond', serif;
  font-size: 38px; color: var(--accent);
  font-weight: 600; margin-bottom: 4px;
}
.stat-label { font-size: 11px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; }

/* ── SECTION HEADER ── */
.section-header {
  display: flex; align-items: center; gap: 16px;
  margin: 40px 0 16px;
}
.section-header h2 { font-size: 28px; font-weight: 400; white-space: nowrap; color: var(--text); }
.section-line { flex: 1; height: 1px; background: var(--border); }

/* ── FILTERS ── */
.filters { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px; }
.filter-btn {
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--muted2);
  padding: 7px 16px; border-radius: 100px;
  cursor: pointer; font-size: 12px; font-weight: 500;
  letter-spacing: 0.5px; transition: all 0.2s;
  font-family: 'DM Sans', sans-serif;
}
.filter-btn:hover { border-color: var(--border-accent); color: var(--accent); }
.filter-btn.active { background: var(--accent); color: #0c0c0c; border-color: var(--accent); font-weight: 700; }

/* ── ARTICLE GRID ── */
.article-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 2px; background: var(--border);
  border: 1px solid var(--border);
}
.article-item {
  display: block; background: var(--panel);
  padding: 24px 20px; color: var(--text);
  transition: background 0.2s;
}
.article-item:hover { background: var(--panel2); }
.article-nicho {
  font-size: 10px; color: var(--accent);
  letter-spacing: 2px; text-transform: uppercase;
  margin-bottom: 10px; font-family: 'DM Sans', sans-serif;
}
.article-item h3 {
  font-size: 19px; font-weight: 400;
  line-height: 1.3; margin-bottom: 12px;
  color: var(--muted2); transition: color 0.2s;
}
.article-item:hover h3 { color: var(--text); }
.article-score {
  display: inline-block;
  background: var(--accent); color: #0c0c0c;
  font-size: 12px; font-weight: 700;
  padding: 2px 10px; border-radius: 2px;
}

/* ── ARTICLE PAGE ── */
.article-wrap { max-width: 860px; margin: 0 auto; padding: 36px 24px 80px; }
.breadcrumb {
  font-size: 12px; color: var(--muted);
  margin-bottom: 28px; letter-spacing: 0.5px;
  font-family: 'DM Sans', sans-serif;
}
.breadcrumb a { color: var(--muted); }
.breadcrumb a:hover { color: var(--accent); }
.breadcrumb span { margin: 0 8px; }
.article-card h1 {
  font-size: clamp(30px, 5vw, 50px);
  font-weight: 300; line-height: 1.1; margin-bottom: 10px;
}
.subtitle { font-size: 17px; color: var(--muted); font-style: italic; margin-bottom: 32px; }

/* ── VERDICT BOX ── */
.verdict-box {
  background: linear-gradient(135deg, #1a1208 0%, #231808 100%);
  border: 2px solid var(--accent);
  border-radius: 12px; padding: 28px; margin-bottom: 32px;
}
.verdict-label {
  font-size: 10px; color: var(--accent);
  letter-spacing: 3px; text-transform: uppercase;
  font-family: 'DM Sans', sans-serif; margin-bottom: 14px;
}
.winner {
  font-family: 'Cormorant Garamond', serif;
  font-size: 30px; font-weight: 600;
  color: var(--text); margin-bottom: 6px;
}
.winner span { color: var(--accent); font-size: 22px; margin-left: 10px; }
.why { color: var(--muted2); font-style: italic; margin-bottom: 14px; font-size: 15px; }
.verdict-pills { display: flex; gap: 20px; flex-wrap: wrap; font-size: 13px; }
.pill-good { color: #86efac; }
.pill-bad  { color: #fca5a5; }

/* ── INTRO BLOCK ── */
.intro-block {
  font-size: 17px; line-height: 1.85; color: var(--muted2);
  border-left: 3px solid var(--accent);
  padding-left: 18px; margin-bottom: 40px;
}

/* ── SECTIONS ── */
.article-section { margin-bottom: 36px; }
.article-section h2 {
  font-size: clamp(22px, 3vw, 30px);
  color: var(--accent); font-weight: 400;
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border-accent);
}
.article-section p { color: var(--muted2); font-size: 15px; line-height: 1.8; }

/* ── TABLE ── */
.table-wrap { overflow-x: auto; margin: 16px 0; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th {
  background: #18140f; color: var(--accent);
  padding: 10px 14px; text-align: left;
  font-weight: 600; letter-spacing: 0.5px;
  border-bottom: 2px solid var(--border-accent);
}
td { padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--muted2); }
tr:hover td { color: var(--text); background: rgba(255,255,255,0.02); }
.winner-badge {
  display: inline-block;
  border: 1px solid var(--accent); color: var(--accent);
  border-radius: 100px; padding: 1px 8px;
  font-size: 10px; font-weight: 700; letter-spacing: 1px;
  margin-left: 6px; vertical-align: middle;
}

/* ── PRODUCT CARDS ── */
.product-cards { display: flex; flex-direction: column; gap: 12px; margin: 16px 0; }
.product-card {
  display: flex; gap: 16px;
  border-radius: 8px; padding: 18px;
  align-items: flex-start; transition: opacity 0.2s;
}
.product-card:hover { opacity: 0.92; }
.product-img {
  width: 88px; height: 88px; object-fit: contain;
  background: #fff; border-radius: 6px; padding: 4px; flex-shrink: 0;
}
.product-info { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.product-name {
  font-size: 15px; font-weight: 700; color: var(--text);
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.product-meta { display: flex; gap: 14px; flex-wrap: wrap; font-size: 13px; color: var(--muted); }
.product-score { color: var(--accent); font-weight: 700; }
.amazon-btn {
  display: inline-block;
  background: var(--accent); color: #0c0c0c;
  padding: 9px 20px; border-radius: 2px;
  font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
  text-decoration: none; width: fit-content; transition: opacity 0.15s;
  font-family: 'DM Sans', sans-serif;
}
.amazon-btn:hover { opacity: 0.85; }
.affiliate-disclaimer {
  font-size: 11px; color: var(--muted); font-style: italic;
  margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border);
}

/* ── FAQ ── */
.faq-section { background: var(--panel); border-radius: 10px; padding: 24px; margin: 36px 0; }
.faq-section h2 { font-size: 26px; margin-bottom: 20px; color: var(--text); font-weight: 400; }
.faq-item {
  border-bottom: 1px solid var(--border); padding: 14px 0;
}
.faq-item:last-child { border-bottom: none; }
.faq-item summary {
  font-weight: 600; font-size: 14px; color: var(--text);
  list-style: none; display: flex; justify-content: space-between;
  cursor: pointer; gap: 12px;
}
.faq-item summary::-webkit-details-marker { display: none; }
.faq-item summary::after { content: '+'; color: var(--accent); font-size: 20px; flex-shrink: 0; }
.faq-item[open] summary::after { content: '−'; }
.faq-item p { color: var(--muted2); font-size: 14px; margin-top: 10px; line-height: 1.7; }

/* ── UPDATED NOTE ── */
.updated-note {
  margin-top: 32px; padding: 14px 16px;
  border: 1px solid var(--border); border-radius: 4px;
  font-size: 12px; color: var(--muted); line-height: 1.6;
}

/* ── FOOTER ── */
.site-footer {
  border-top: 1px solid var(--border);
  padding: 32px 40px; text-align: center;
  font-size: 12px; color: var(--muted); letter-spacing: 0.5px;
}
.footer-logo {
  font-family: 'Cormorant Garamond', serif;
  font-size: 22px; color: var(--accent);
  letter-spacing: 5px; margin-bottom: 6px;
}

/* ── RESPONSIVE ── */
@media (max-width: 640px) {
  .site-header { padding: 0 16px; }
  .hero { padding: 48px 0 36px; }
  .hero h1 { font-size: 38px; }
  .article-card h1 { font-size: 28px; }
  .product-card { flex-direction: column; }
  .product-img { width: 100%; height: 140px; }
  .stats { grid-template-columns: 1fr; }
  .verdict-pills { flex-direction: column; gap: 8px; }
}
.sr-only { display: none; }
"""
    STYLE_PATH.write_text(css.strip() + "\n", encoding="utf-8")


def read_manifest():
    _ensure_paths()
    if not MANIFEST_PATH.exists():
        return []
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def upsert_article_metadata(article_meta):
    all_articles = [a for a in read_manifest() if a.get("slug") != article_meta.get("slug")]
    all_articles.append(article_meta)
    MANIFEST_PATH.write_text(
        json.dumps(all_articles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return all_articles


def git_publish(filepath, commit_message):
    repo_path = str(GITHUB_REPO_PATH)
    target    = str(Path(filepath))
    subprocess.run(["git", "-C", repo_path, "add", target], check=True)
    commit = subprocess.run(
        ["git", "-C", repo_path, "commit", "-m", commit_message],
        capture_output=True, text=True,
    )
    if commit.returncode != 0:
        output = (commit.stdout + commit.stderr).lower()
        if "nothing to commit" in output:
            return
        raise RuntimeError(commit.stdout + commit.stderr)
    subprocess.run(["git", "-C", repo_path, "push"], check=True)