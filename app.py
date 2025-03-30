from flask import Flask, render_template

from flask import Flask, render_template, request, flash
app = Flask(__name__)




@app.route("/")
def home():
    return render_template("index.html")

@app.route("/terapeut/<name>")
def terapeut(name):

    return render_template("index.html", name=name)

if __name__ == "__main__":
    app.secret_key = "your_secret_key"
    app.run(debug=True)