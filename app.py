# app.py
import os
import json
from flask import Flask, render_template, abort, g, request, url_for
from datetime import date, datetime
from flask import Response, redirect



app = Flask(__name__)

LANGS = {"sr", "en"}
DEFAULT_LANG = "sr"

# ---------- Data ----------
def load_therapists():
    data_path = os.path.join(app.root_path, "data", "therapists.json")
    with open(data_path, encoding="utf-8") as f:
        items = json.load(f)
    by_slug = {it["slug"]: it for it in items}
    return by_slug, items

THERAPISTS_BY_SLUG, THERAPISTS_LIST = load_therapists()

# ---------- Language from path ----------
@app.before_request
def set_lang_from_path():
    # English for /en/... ; Serbian (default) for everything else
    g.lang = "en" if request.path.startswith("/en/") else "sr"

# ---------- Helpers available in templates ----------


@app.context_processor
def inject_current_year():
    return dict(current_year=date.today().year)
@app.context_processor
def inject_helpers():
    def tfield(obj, key, lang):
        """Return localized field with SR fallback, e.g. titles_en → titles."""
        if lang == "en":
            return obj.get(f"{key}_en") or obj.get(key)
        return obj.get(key)

    def url_for_therapist(slug):
        ep = 'therapist_detail_en' if g.get('lang', 'sr') == 'en' else 'therapist_detail_sr'
        return url_for(ep, slug=slug)

    return dict(tfield=tfield, url_for_therapist=url_for_therapist)

# ---------- Lang context: <html lang>, alternate URLs, language switcher ----------
@app.context_processor
def inject_lang_context():
    # Map endpoints between SR (default) and EN variants
    endpoint_map = {
        # home
        "home": {"sr": "home", "en": "home_en"},
        "home_en": {"sr": "home", "en": "home_en"},
        # therapist detail
        "therapist_detail_sr": {"sr": "therapist_detail_sr", "en": "therapist_detail_en"},
        "therapist_detail_en": {"sr": "therapist_detail_sr", "en": "therapist_detail_en"},
        # contact
        "contact": {"sr": "contact", "en": "contact_en"},
        "contact_en": {"sr": "contact", "en": "contact_en"},
        # pricing
        "pricing": {"sr": "pricing", "en": "pricing_en"},
        "pricing_en": {"sr": "pricing", "en": "pricing_en"},
        # services
        "services": {"sr": "services", "en": "services_en"},
        "services_en": {"sr": "services", "en": "services_en"},
    }

    def other_lang_url():
        cur_ep = request.endpoint
        other = "en" if g.lang == "sr" else "sr"
        args = dict(request.view_args or {})
        target_ep = endpoint_map.get(cur_ep, {}).get(other, cur_ep)
        return url_for(target_ep, **args)

    def absolute(u: str) -> str:
        return request.url_root.rstrip("/") + u

    cur_ep = request.endpoint
    args = dict(request.view_args or {})
    ep_sr = endpoint_map.get(cur_ep, {}).get("sr", cur_ep)
    ep_en = endpoint_map.get(cur_ep, {}).get("en", cur_ep)
    sr_url = absolute(url_for(ep_sr, **args))
    en_url = absolute(url_for(ep_en, **args))

    lang_code = "sr-RS" if g.lang == "sr" else "en"

    return dict(
        lang_code=lang_code,
        current_lang=g.lang,
        other_lang_url=other_lang_url(),
        alt_urls={"sr": sr_url, "en": en_url},
    )

# ---------- Routes (SR default, EN under /en) ----------
# Home (both languages use the same template)
@app.route("/")
def home():
    return render_template("index.html", therapists=THERAPISTS_LIST)

@app.route("/en/")
def home_en():
    return render_template("index.html", therapists=THERAPISTS_LIST)


# Therapist detail (localized path segment; same template for both)
@app.route("/terapeut/<slug>/")
def therapist_detail_sr(slug):
    t = THERAPISTS_BY_SLUG.get(slug)
    if not t:
        abort(404)
    return render_template("therapist.html", therapist=t)

@app.route("/en/therapist/<slug>/")
def therapist_detail_en(slug):
    t = THERAPISTS_BY_SLUG.get(slug)
    if not t:
        abort(404)
    return render_template("therapist.html", therapist=t)


# ========= 301 canonicalizers (normalize slashes / language) =========

# /en  -> /en/
@app.route("/en")
def en_no_slash():
    return redirect(url_for("home_en"), code=301)

# Accidental /sr/ -> root /
@app.route("/sr/")
def sr_prefix_canonical():
    return redirect(url_for("home"), code=301)

# Normalize therapist detail slashes
@app.route("/terapeut/<slug>")
def therapist_detail_sr_no_slash(slug):
    return redirect(url_for("therapist_detail_sr", slug=slug), code=301)

@app.route("/en/therapist/<slug>")
def therapist_detail_en_no_slash(slug):
    return redirect(url_for("therapist_detail_en", slug=slug), code=301)


# ========= robots.txt =========
@app.route("/robots.txt")
def robots_txt():
    root = request.url_root.rstrip("/")
    content = f"""User-agent: *
Allow: /

Sitemap: {root}/sitemap.xml
"""
    return Response(content, mimetype="text/plain")


# ========= sitemap.xml =========
# Only include the pages you actually have:
# - Home (SR: "/", EN: "/en/")
# - Therapist details (SR + EN variants)
def _abs(u: str) -> str:
    return request.url_root.rstrip("/") + u

def _url(loc: str, alternates=None, changefreq="weekly", priority="0.8", lastmod=None) -> str:
    alt_links = ""
    if alternates:
        for href, lang in alternates:
            alt_links += f'\n    <xhtml:link rel="alternate" hreflang="{lang}" href="{href}"/>'
    lm = lastmod or datetime.utcnow().date().isoformat()
    return f"""  <url>
    <loc>{loc}</loc>{alt_links}
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
    <lastmod>{lm}</lastmod>
  </url>"""

@app.route("/sitemap.xml")
def sitemap_xml():
    items = []

    # Home (bilingual)
    sr_home = _abs(url_for("home"))
    en_home = _abs(url_for("home_en"))
    items.append(_url(sr_home, alternates=[(sr_home, "sr-RS"), (en_home, "en")], priority="1.0"))
    items.append(_url(en_home, alternates=[(sr_home, "sr-RS"), (en_home, "en")], priority="1.0"))

    # Therapist details (bilingual paths)
    for slug in THERAPISTS_BY_SLUG.keys():
        sr_url = _abs(url_for("therapist_detail_sr", slug=slug))
        en_url = _abs(url_for("therapist_detail_en", slug=slug))
        items.append(_url(sr_url, alternates=[(sr_url, "sr-RS"), (en_url, "en")], changefreq="monthly"))
        items.append(_url(en_url, alternates=[(sr_url, "sr-RS"), (en_url, "en")], changefreq="monthly"))

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xhtml="http://www.w3.org/1999/xhtml">
{chr(10).join(items)}
</urlset>
"""
    return Response(xml, mimetype="application/xml")




if __name__ == "__main__":
    app.run(debug=True)
