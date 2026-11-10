"""Armazenamento dos usuários em CSV (#59).

Os usuários ficam em bilbioteca_de_jogos/data/usuarios.csv (a pasta data/
está no .gitignore). O arquivo é criado no primeiro cadastro. A senha nunca
é salva em texto puro, só o hash gerado por werkzeug.security.
"""

import csv
from pathlib import Path

from werkzeug.security import generate_password_hash

CAMINHO_USUARIOS = Path(__file__).resolve().parent.parent / "data" / "usuarios.csv"

CAMPOS = ["id", "nome", "email", "senha_hash", "perfil", "token_sessao"]


class EmailJaCadastrado(ValueError):
    pass


def _normalizar_email(email):
    return email.strip().lower()


def carregar_usuarios():
    if not CAMINHO_USUARIOS.exists():
        return []
    with CAMINHO_USUARIOS.open(encoding="utf-8", newline="") as arquivo:
        usuarios = list(csv.DictReader(arquivo))
    for usuario in usuarios:
        usuario["id"] = int(usuario["id"])
    return usuarios


def _salvar_usuarios(usuarios):
    CAMINHO_USUARIOS.parent.mkdir(parents=True, exist_ok=True)
    with CAMINHO_USUARIOS.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(usuarios)


def buscar_usuario_por_email(email):
    email = _normalizar_email(email)
    for usuario in carregar_usuarios():
        if usuario["email"] == email:
            return usuario
    return None


def buscar_usuario_por_id(usuario_id):
    for usuario in carregar_usuarios():
        if usuario["id"] == usuario_id:
            return usuario
    return None

"""Perfil é apenas para teste unitário"""
 
def cadastrar_usuario(nome, email, senha, perfil="usuario"):
    """Salva um novo usuário com a senha protegida por hash e o retorna.

    A validação dos dados do formulário é feita na rota de cadastro (#58);
    aqui só se garante que o e-mail não se repita.
    """
    email = _normalizar_email(email)
    usuarios = carregar_usuarios()
    if any(usuario["email"] == email for usuario in usuarios):
        raise EmailJaCadastrado(email)

    novo = {
        "id": max((usuario["id"] for usuario in usuarios), default=0) + 1,
        "nome": nome.strip(),
        "email": email,
        "senha_hash": generate_password_hash(senha),
        "perfil": perfil,
        "token_sessao": "",
    }
    usuarios.append(novo)
    _salvar_usuarios(usuarios)
    return novo


def definir_token_sessao(usuario_id, token):
    """Grava o token da sessão ativa do usuário. Token vazio invalida a sessão."""
    usuarios = carregar_usuarios()
    for usuario in usuarios:
        if usuario["id"] == usuario_id:
            usuario["token_sessao"] = token
            _salvar_usuarios(usuarios)
            return
