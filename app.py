# app.py
import os
import json
from flask import Flask, render_template, abort, g, request, url_for

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
    return render_template("index.html")

@app.route("/en/")
def home_en():
    return render_template("index.html")

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

# Other localized pages (reuse same templates; switch content via current_lang in templates)
@app.route("/kontakt")
def contact():
    return render_template("contact.html")

@app.route("/en/contact")
def contact_en():
    return render_template("contact.html")

@app.route("/cene")
def pricing():
    return render_template("pricing.html")

@app.route("/en/pricing")
def pricing_en():
    return render_template("pricing.html")

@app.route("/usluge")
def services():
    return render_template("services.html")

@app.route("/en/services")
def services_en():
    return render_template("services.html")

if __name__ == "__main__":
    app.run(debug=True)
