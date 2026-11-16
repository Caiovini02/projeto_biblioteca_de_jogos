import secrets
from functools import wraps

from flask import flash, g, make_response, redirect, session, url_for
from werkzeug.security import check_password_hash

from projeto import app
from projeto.models import buscar_usuario_por_email, buscar_usuario_por_id, definir_token_sessao


def verificar_credenciais(email, senha):
    usuario = buscar_usuario_por_email(email)
    if usuario is None:
        return None
    if not check_password_hash(usuario.get("senha_hash", ""), senha):
        return None
    return usuario


def iniciar_sessao(usuario):
    session.clear()
    token = secrets.token_urlsafe(32)
    definir_token_sessao(usuario["id"], token)
    session["usuario_id"] = usuario["id"]
    session["token_sessao"] = token
    session.permanent = True


def encerrar_sessao():
    usuario_id = session.get("usuario_id")
    if usuario_id is not None:
        definir_token_sessao(usuario_id, "")
    session.clear()


def _sessao_valida(usuario, token):
    token_salvo = usuario.get("token_sessao") or ""
    return bool(token) and bool(token_salvo) and secrets.compare_digest(token, token_salvo)


@app.before_request
def carregar_usuario_logado():
    g.usuario = None
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        return
    usuario = buscar_usuario_por_id(usuario_id)
    if usuario is None or not _sessao_valida(usuario, session.get("token_sessao")):
        session.clear()
        return
    g.usuario = usuario


def login_obrigatorio(view):
    @wraps(view)
    def view_protegida(*args, **kwargs):
        if g.get("usuario") is None:
            flash("Entre na sua conta para continuar.", "erro")
            return redirect(url_for("login"))
        resposta = make_response(view(*args, **kwargs))
        resposta.headers["Cache-Control"] = "no-store"
        return resposta
    return view_protegida


@app.context_processor
def disponibilizar_usuario_nos_templates():
    return {"usuario_logado": g.get("usuario")}
