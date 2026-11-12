"""Validação dos formulários.

validar_cadastro foi criada para integrar o formulário de cadastro (#60) e
hoje também verifica os campos obrigatórios (#56). A validação completa é a
task #58 e pode estender esta função, desde que continue retornando a lista
de mensagens de erro.
"""

import re

TAMANHO_MINIMO_SENHA = 8
_FORMATO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _vazio(valor):
    """True se o campo não foi enviado ou só tem espaços."""
    return not valor or not valor.strip()


def validar_cadastro(nome, email, senha, confirmacao):
    """Retorna a lista de erros do formulário de cadastro (vazia se estiver ok).

    Cada campo obrigatório vazio gera a sua própria mensagem. As demais regras
    só são checadas nos campos preenchidos, para não repetir erros do mesmo campo.
    """
    erros = []

    if _vazio(nome):
        erros.append("Informe o nome.")

    if _vazio(email):
        erros.append("Informe o e-mail.")
    elif not _FORMATO_EMAIL.match(email):
        erros.append("Informe um e-mail válido.")

    if not senha:
        erros.append("Informe a senha.")
    elif len(senha) < TAMANHO_MINIMO_SENHA:
        erros.append(f"A senha deve ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres.")

    if not confirmacao:
        erros.append("Confirme a senha.")
    elif senha and senha != confirmacao:
        erros.append("As senhas não conferem.")

    return erros
