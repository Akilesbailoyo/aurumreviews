import json
import os
import subprocess
from datetime import datetime
from html import escape
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SITE_NAME = os.getenv("SITE_NAME", "AURUM")
SITE_URL = os.getenv("SITE_URL", "https://example.github.io/aurum").rstrip("/")
GITHUB_REPO_PATH = Path(os.getenv("GITHUB_REPO_PATH", Path.cwd()))

DOCS_DIR = GITHUB_REPO_PATH / "docs"
ARTICLES_DIR = DOCS_DIR / "articles"
MANIFEST_PATH = ARTICLES_DIR / "_manifest.json"
STYLE_PATH = DOCS_DIR / "style.css"


def _ensure_paths():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)


def _updated_label():
    return datetime.now().strftime("%B %Y")


def _faq_schema(faq_items):
    entities = []
    for item in faq_items:
        entities.append(
            {
                "@type": "Question",
                "name": item.get("q", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item.get("a", ""),
                },
            }
        )
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}


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
        name = escape(item.get("name", ""))
        score = escape(item.get("score", ""))
        price = escape(item.get("price", ""))
        best_for = escape(item.get("best_for", ""))
        badge = " <span class='winner-badge'>TOP</span>" if item.get("name") == winner else ""
        rows.append(
            f"<tr><td>{name}{badge}</td><td>{score}</td><td>{price}</td><td>{best_for}</td></tr>"
        )
    return "\n".join(rows)


def _render_sections(sections):
    blocks = []
    for section in sections:
        h2 = escape(section.get("h2", ""))
        content = escape(section.get("content", ""))
        blocks.append(f"<section class='article-section'><h2>{h2}</h2><p>{content}</p></section>")
    return "\n".join(blocks)


def _render_faq(faq_items):
    blocks = []
    for item in faq_items:
        q = escape(item.get("q", ""))
        a = escape(item.get("a", ""))
        blocks.append(f"<details class='faq-item'><summary>{q}</summary><p>{a}</p></details>")
    return "\n".join(blocks)

def _render_product_cards(products, winner):
    if not products:
        return ""
    cards = []
    for p in products:
        name = escape(p.get("name", ""))
        price = escape(p.get("price", ""))
        best_for = escape(p.get("best_for", ""))
        score = escape(p.get("score", ""))
        link = escape(p.get("link", "#"))
        image = escape(p.get("image", ""))
        is_winner = p.get("name") == winner
        border = "border:2px solid var(--accent);" if is_winner else "border:1px solid var(--border);"
        bg = "background:#1a1610;" if is_winner else "background:var(--panel);"
        badge = "<span class='winner-badge'>MEJOR OPCIÓN</span>" if is_winner else ""
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
    disclaimer = "<p class='affiliate-disclaimer'>* Enlaces de afiliado Amazon.es. Si compras a través de ellos recibimos una pequeña comisión sin coste adicional para ti. Nunca afecta nuestras recomendaciones.</p>"
    return "<div class='product-cards'>" + "\n".join(cards) + "</div>" + disclaimer


def generate_html(article_data, markdown_content, products=None):
    _ensure_paths()
    verdict = article_data.get("verdict", {})
    winner = verdict.get("winner", "")
    score = verdict.get("score", "")
    best_for = verdict.get("best_for", "")
    weakness = verdict.get("weakness", "")
    why = verdict.get("why", "")
    slug = article_data.get("slug", "articulo")
    title = article_data.get("title", "AURUM Article")
    subtitle = article_data.get("subtitle", "")
    description = article_data.get("meta_description", "")
    faq_items = article_data.get("faq", [])
    article_url = f"{SITE_URL}/articles/{slug}.html"

    article_schema = json.dumps(_article_schema(article_data, article_url), ensure_ascii=False)
    faq_schema = json.dumps(_faq_schema(faq_items), ensure_ascii=False)
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
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;700&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../style.css" />
  <script type="application/ld+json">{article_schema}</script>
  <script type="application/ld+json">{faq_schema}</script>
</head>
<body>
  <header class="site-header">
    <a class="logo" href="../index.html">{escape(SITE_NAME)}</a>
  </header>
  <main class="article-wrap">
    <article class="article-card">
      <p class="eyebrow">Guía premium</p>
      <h1>{escape(title)}</h1>
      <p class="subtitle">{escape(subtitle)}</p>
      <section class="verdict-box">
        <h2>Veredicto Aurum</h2>
        <p class="winner">{escape(winner)} <span>{escape(score)}</span></p>
        <p class="why">{escape(why)}</p>
        <ul>
          <li><strong>Ideal para:</strong> {escape(best_for)}</li>
          <li><strong>Punto débil:</strong> {escape(weakness)}</li>
        </ul>
      </section>
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
      <section class="article-section">
        <h2>Dónde comprar</h2>
        {product_cards_html}
      </section>
      {_render_sections(article_data.get("sections", []))}
      <section class="article-section">
        <h2>Preguntas frecuentes</h2>
        {_render_faq(faq_items)}
      </section>
      <section class="article-section sr-only">
        <h2>Fuente markdown</h2>
        <pre>{escape(markdown_content)}</pre>
      </section>
    </article>
  </main>
  <footer class="site-footer">Actualizado: {_updated_label()}</footer>
</body>
</html>
"""


def update_index(all_articles):
    _ensure_paths()
    cards = []
    for article in sorted(all_articles, key=lambda x: x.get("updated_at", ""), reverse=True):
        title = escape(article.get("title", "Artículo"))
        nicho = escape(article.get("nicho", "general"))
        score = escape(article.get("winner_score", "-"))
        href = escape(article.get("url", "#"))
        cards.append(
            f"<a class='article-item' data-category='{nicho}' href='{href}'>"
            f"<p class='article-nicho'>{nicho}</p>"
            f"<h3>{title}</h3>"
            f"<p class='article-score'>Score ganador: {score}</p>"
            "</a>"
        )
    cards_html = "\n".join(cards) if cards else "<p>No hay artículos todavía.</p>"

    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(SITE_NAME)} | Recomendaciones premium</title>
  <meta name="description" content="Comparativas premium de {escape(SITE_NAME)}: finanzas, tecnología, bebés y bienestar." />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;700&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="./style.css" />
</head>
<body>
  <header class="site-header">
    <span class="logo">{escape(SITE_NAME)}</span>
  </header>
  <main class="index-wrap">
    <section class="hero">
      <p class="eyebrow">Análisis independiente</p>
      <h1>Decisiones de compra más inteligentes.</h1>
      <p>Comparativas y veredictos claros con enfoque editorial premium.</p>
    </section>
    <section class="filters">
      <button class="filter-btn active" data-filter="all">Todos</button>
      <button class="filter-btn" data-filter="finanzas">Finanzas</button>
      <button class="filter-btn" data-filter="tecnologia">Tecnología</button>
      <button class="filter-btn" data-filter="bebes_y_crianza">Bebés</button>
      <button class="filter-btn" data-filter="bienestar">Bienestar</button>
    </section>
    <section class="article-grid">
      {cards_html}
    </section>
  </main>
  <footer class="site-footer">Actualizado: {_updated_label()}</footer>
  <script>
    const buttons = document.querySelectorAll(".filter-btn");
    const cards = document.querySelectorAll(".article-item");
    buttons.forEach((btn) => {{
      btn.addEventListener("click", () => {{
        buttons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const filter = btn.dataset.filter;
        cards.forEach((card) => {{
          const show = filter === "all" || card.dataset.category === filter;
          card.style.display = show ? "block" : "none";
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
:root{
  --bg:#0c0c0c;
  --panel:#131313;
  --text:#f0ebe0;
  --muted:#c8bea8;
  --accent:#d4a853;
  --border:#2c2417;
}
*{box-sizing:border-box}
body{
  margin:0;
  font-family:'DM Sans',sans-serif;
  background:var(--bg);
  color:var(--text);
  line-height:1.65;
}
h1,h2,h3,.logo{
  font-family:'Cormorant Garamond',serif;
}
.site-header{
  position:sticky;
  top:0;
  z-index:10;
  background:rgba(12,12,12,.9);
  border-bottom:1px solid var(--border);
  backdrop-filter: blur(8px);
  padding:14px 24px;
}
.logo{
  color:var(--accent);
  font-size:34px;
  text-decoration:none;
}
.index-wrap,.article-wrap{
  max-width:1080px;
  margin:0 auto;
  padding:28px 20px 48px;
}
.hero{
  padding:36px;
  border:1px solid var(--border);
  background:linear-gradient(160deg,#15120d,#0f0f0f);
  border-radius:18px;
}
.hero h1{margin:.2rem 0 .4rem;font-size:56px;line-height:1.1}
.eyebrow{color:var(--accent);letter-spacing:.08em;text-transform:uppercase;font-size:.78rem}
.filters{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}
.filter-btn{
  border:1px solid var(--border);
  background:#171717;
  color:var(--text);
  padding:8px 14px;
  border-radius:999px;
  cursor:pointer;
}
.filter-btn.active{background:var(--accent);color:#111;font-weight:700}
.article-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
  gap:14px;
}
.article-item{
  display:block;
  border:1px solid var(--border);
  border-radius:14px;
  background:var(--panel);
  padding:16px;
  text-decoration:none;
  color:var(--text);
}
.article-item:hover{border-color:var(--accent)}
.article-item h3{margin:.25rem 0 .35rem;font-size:28px;line-height:1.15}
.article-nicho{color:var(--accent);font-size:.8rem;text-transform:uppercase}
.article-score{color:var(--muted)}
.article-card{
  border:1px solid var(--border);
  border-radius:16px;
  background:var(--panel);
  padding:26px;
}
.article-card h1{font-size:54px;line-height:1.1;margin:.2rem 0}
.subtitle{color:var(--muted);font-size:1.1rem}
.verdict-box{
  margin:24px 0;
  border:1px solid var(--accent);
  border-radius:14px;
  padding:18px;
  background:#1a1610;
}
.verdict-box h2{margin:0 0 .2rem;color:var(--accent)}
.winner{font-size:1.3rem}
.winner span{color:var(--accent);font-weight:700}
.article-section h2{color:var(--accent);font-size:36px;margin-top:2rem}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th,td{border:1px solid var(--border);padding:10px;text-align:left}
th{background:#18140f;color:var(--accent)}
.winner-badge{
  border:1px solid var(--accent);
  border-radius:999px;
  padding:2px 8px;
  font-size:.7rem;
  color:var(--accent);
}
.faq-item{
  border:1px solid var(--border);
  border-radius:10px;
  padding:10px 12px;
  margin-bottom:10px;
  background:#141414;
}
.faq-item summary{cursor:pointer;font-weight:700}
.site-footer{
  border-top:1px solid var(--border);
  color:var(--muted);
  text-align:center;
  padding:16px;
}
.sr-only{display:none}
@media (max-width: 768px){
  .hero h1,.article-card h1{font-size:40px}
}
.product-cards {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 16px 0;
}
.product-card {
  display: flex;
  gap: 16px;
  border-radius: 12px;
  padding: 16px;
  align-items: flex-start;
}
.product-img {
  width: 90px;
  height: 90px;
  object-fit: contain;
  background: #fff;
  border-radius: 6px;
  padding: 4px;
  flex-shrink: 0;
}
.product-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.product-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.product-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--muted);
}
.product-score { color: var(--accent); font-weight: 700; }
.amazon-btn {
  display: inline-block;
  background: var(--accent);
  color: #0c0c0c;
  padding: 8px 18px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  text-decoration: none;
  width: fit-content;
}
.amazon-btn:hover { opacity: 0.85; }
.affiliate-disclaimer {
  font-size: 11px;
  color: var(--muted);
  font-style: italic;
  margin-top: 8px;
}
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
    target = str(Path(filepath))
    subprocess.run(["git", "-C", repo_path, "add", target], check=True)
    commit = subprocess.run(
        ["git", "-C", repo_path, "commit", "-m", commit_message],
        capture_output=True,
        text=True,
    )
    if commit.returncode != 0:
        output = (commit.stdout + commit.stderr).lower()
        if "nothing to commit" in output:
            return
        raise RuntimeError(commit.stdout + commit.stderr)
    subprocess.run(["git", "-C", repo_path, "push"], check=True)
