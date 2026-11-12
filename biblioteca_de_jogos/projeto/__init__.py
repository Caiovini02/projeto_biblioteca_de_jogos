import os
from datetime import timedelta

from flask import Flask

app = Flask(__name__)

# SECRET_KEY DEVE  SER ALTERADA EM PRODUÇÃO
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-chave-insegura-troque-em-producao")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Respostas JSON com acentos legíveis (ex.: "Ação" em vez de "Ação").
app.json.ensure_ascii = False


from projeto import autenticacao, routes
