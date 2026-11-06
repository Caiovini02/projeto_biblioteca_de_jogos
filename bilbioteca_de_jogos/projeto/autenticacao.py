from flask import g, session
from werkzeug.security import check_password_hash

from projeto import app
from projeto.models import buscar_usuario_por_email, buscar_usuario_por_id


# Verificação das credenciais (#64)

def verificar_credenciais(email, senha):
    """Retorna o usuário se o e-mail existir e a senha bater com o hash salvo."""
    usuario = buscar_usuario_por_email(email)
    if usuario is None:
        return None
    if not check_password_hash(usuario.get("senha_hash", ""), senha):
        return None
    return usuario


# Gerenciamento de sessão (#65)

def iniciar_sessao(usuario):
    # Limpa qualquer dado anterior para não reaproveitar uma sessão antiga.
    session.clear()
    session["usuario_id"] = usuario["id"]
    session.permanent = True


def encerrar_sessao():
    session.clear()


@app.before_request
def carregar_usuario_logado():
    usuario_id = session.get("usuario_id")
    g.usuario = buscar_usuario_por_id(usuario_id) if usuario_id is not None else None
    # Usuário removido depois do login: descarta a sessão órfã.
    if usuario_id is not None and g.usuario is None:
        session.clear()


@app.context_processor
def disponibilizar_usuario_nos_templates():
    return {"usuario_logado": g.get("usuario")}
