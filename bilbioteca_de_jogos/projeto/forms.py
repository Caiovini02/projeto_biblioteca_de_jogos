"""Validação dos formulários.

validar_cadastro é uma versão mínima, feita para integrar o formulário de
cadastro (#60). A validação completa é a task #58 e pode substituir esta
função, desde que continue retornando a lista de mensagens de erro.
"""

import re

TAMANHO_MINIMO_SENHA = 8
_FORMATO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_cadastro(nome, email, senha, confirmacao):
    """Retorna a lista de erros do formulário de cadastro (vazia se estiver ok)."""
    erros = []
    if not nome or not email or not senha or not confirmacao:
        erros.append("Preencha todos os campos.")
        return erros
    if not _FORMATO_EMAIL.match(email):
        erros.append("Informe um e-mail válido.")
    if len(senha) < TAMANHO_MINIMO_SENHA:
        erros.append(f"A senha deve ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres.")
    if senha != confirmacao:
        erros.append("As senhas não conferem.")
    return erros
