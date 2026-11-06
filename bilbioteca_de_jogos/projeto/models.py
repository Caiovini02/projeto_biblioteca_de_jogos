"""Acesso aos dados dos usuários.

O armazenamento definitivo dos usuários é a task #59. Até lá, eles são lidos
de um arquivo JSON em bilbioteca_de_jogos/data/usuarios.json (a pasta data/
está no .gitignore), no formato:

[
  {
    "id": 1,
    "nome": "Ana",
    "email": "ana@exemplo.com",
    "senha_hash": "<gerado com werkzeug.security.generate_password_hash>",
    "perfil": "usuario"
  }
]

Quando a #59 for implementada, basta manter as funções abaixo com a mesma
assinatura para que o login continue funcionando.
"""

import json
from pathlib import Path

CAMINHO_USUARIOS = Path(__file__).resolve().parent.parent / "data" / "usuarios.json"


def carregar_usuarios():
    if not CAMINHO_USUARIOS.exists():
        return []
    with CAMINHO_USUARIOS.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def buscar_usuario_por_email(email):
    email = email.strip().lower()
    for usuario in carregar_usuarios():
        if usuario.get("email", "").strip().lower() == email:
            return usuario
    return None


def buscar_usuario_por_id(usuario_id):
    for usuario in carregar_usuarios():
        if usuario.get("id") == usuario_id:
            return usuario
    return None
