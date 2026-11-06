import os
from datetime import timedelta

from flask import Flask

app = Flask(__name__)

# A sessão do Flask é assinada com a SECRET_KEY. Em produção, defina a
# variável de ambiente SECRET_KEY com um valor aleatório.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-chave-insegura-troque-em-producao")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


from projeto import autenticacao, routes
