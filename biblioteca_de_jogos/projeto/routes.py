from flask import abort, flash, g, redirect, render_template, request, url_for

from projeto import app

from projeto.catalogo import (
    buscar_jogo_por_id,
    buscar_por_titulo,
    carregar_jogos,
    filtrar_por_genero,
    filtrar_por_preco,
    filtrar_promocao,
    verificar_preco_maximo,
    listar_generos,
    localizar_genero,
    normalizar_ordenacao,
    ordenar_jogos,
)

from projeto.autenticacao import encerrar_sessao, iniciar_sessao, verificar_credenciais
from projeto.forms import validar_cadastro
from projeto.models import EmailJaCadastrado, cadastrar_usuario


# /-------------------------Routes na homepage-------------------------\ 

@app.route("/")
def homepage():
    todos = carregar_jogos()
    generos = listar_generos(todos)
    genero = request.args.get("genero", "").strip()
    busca = request.args.get("busca", "").strip()
    preco = verificar_preco_maximo(request.args.get("preco"))
    ordem = normalizar_ordenacao(request.args.get("ordem"))
    promocoes_on = request.args.get("promo") == "1"
    
    jogos = filtrar_por_genero(todos, genero)
    jogos = buscar_por_titulo(jogos, busca)
    jogos = filtrar_por_preco(jogos, preco)
    jogos = filtrar_promocao(jogos, promocoes_on)
    jogos = ordenar_jogos(jogos, ordem)
    filtrando = bool(genero or busca or preco or promocoes_on)

    return render_template(
        "homepage.html",
        jogos=jogos,
        generos=generos,
        genero_selecionado=localizar_genero(generos, genero),
        busca=busca,
        preco_selecionado=preco,
        ordem_selecionada=ordem,
        promocoes_on=promocoes_on,
        destaques=[] if filtrando else ordenar_jogos(todos, "rate")[:4],
        promocoes=[] if filtrando else sorted(filtrar_promocao(todos, True), key=lambda jogo: jogo["desconto"], reverse=True),
        em_alta=[] if filtrando else sorted(todos, key=lambda jogo: jogo["avaliacoes"], reverse=True)[:5],
    )


@app.route("/jogo/<int:jogo_id>")
def detalhes(jogo_id):
    jogo = buscar_jogo_por_id(jogo_id)
    if jogo is None:
        abort(404)
    return render_template("detalhes.html", jogo=jogo)


# /-------------------------Route de autenticação-------------------------\ 

@app.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario is not None:
        return redirect(url_for("homepage"))

    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")

        if not email or not senha:
            flash("Preencha o e-mail e a senha.", "erro")
        else:
            usuario = verificar_credenciais(email, senha)
            if usuario is not None:
                iniciar_sessao(usuario)
                flash(f"Bem-vindo(a), {usuario['nome']}!", "sucesso")
                return redirect(url_for("homepage"))
            flash("E-mail ou senha incorretos.", "erro")

    return render_template("login.html", email=email)


# /-------------------------Formulário de cadastro-------------------------\ 

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if g.usuario is not None:
        return redirect(url_for("homepage"))

    nome = email = ""
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        confirmacao = request.form.get("confirmacao", "")

        erros = validar_cadastro(nome, email, senha, confirmacao)
        if not erros:
            try:
                cadastrar_usuario(nome, email, senha)
            except EmailJaCadastrado:
                erros.append("Este e-mail já está cadastrado.")
            else:
                flash("Cadastro realizado! Entre com seu e-mail e senha.", "sucesso")
                return redirect(url_for("login"))

        for erro in erros:
            flash(erro, "erro")

    return render_template("cadastro.html", nome=nome, email=email)


# /-------------------------Route de encerramento de sessão com redirecionamento-------------------------\ 

@app.route("/logout", methods=["POST"])
def logout():
    encerrar_sessao()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("homepage"))
