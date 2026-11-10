from flask import redirect, render_template, url_for

from projeto import app
from projeto.catalogo import carregar_jogos



# Rota do catálogo (#26) com os jogos carregados da fonte de dados (#27)
@app.route("/")
def homepage():
    return render_template("homepage.html", jogos=carregar_jogos())

@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

@app.route("/detalhes")
def detalhes():
    return render_template("detalhes.html")
