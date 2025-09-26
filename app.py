import os, json
from flask import Flask, render_template, abort
app = Flask(__name__)


def load_therapists():
    data_path = os.path.join(app.root_path, "data", "therapists.json")
    with open(data_path, encoding="utf-8") as f:
        items = json.load(f)
    # dict by slug for O(1) lookup
    return {item["slug"]: item for item in items}

THERAPISTS = load_therapists()

@app.route("/terapeut/<slug>/")
def therapist_detail(slug):
    therapist = THERAPISTS.get(slug)
    if not therapist:
        abort(404)
    return render_template("therapist.html", therapist=therapist)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/terapeut/<name>")
def terapeut(name):

    return render_template("index.html", name=name)

if __name__ == "__main__":
    app.secret_key = "your_secret_key"
    app.run(debug=True)