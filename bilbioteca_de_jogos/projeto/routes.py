from flask import redirect, render_template, url_for

from projeto import app



@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

@app.route("/detalhes")
def detalhes():
    return render_template("detalhes.html")
