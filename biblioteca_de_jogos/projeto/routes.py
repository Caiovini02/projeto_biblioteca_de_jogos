from flask import flash, g, redirect, render_template, request, url_for

from projeto import app
from projeto.catalogo import carregar_jogos, filtrar_por_genero, listar_generos, localizar_genero
from projeto.autenticacao import encerrar_sessao, iniciar_sessao, verificar_credenciais
from projeto.forms import validar_cadastro
from projeto.models import EmailJaCadastrado, cadastrar_usuario



# Rota do catálogo (#26) com os jogos carregados da fonte de dados (#27)
# Disponibiliza os gêneros para o filtro (#50) e filtra os jogos pelo gênero
# escolhido na URL, ex.: /?genero=RPG (#51)
@app.route("/")
def homepage():
    todos = carregar_jogos()
    generos = listar_generos(todos)
    genero = request.args.get("genero", "").strip()
    return render_template(
        "homepage.html",
        jogos=filtrar_por_genero(todos, genero),
        generos=generos,
        genero_selecionado=localizar_genero(generos, genero),
    )


@app.route("/detalhes")
def detalhes():
    return render_template("detalhes.html")


# Rota de autenticação (#63)
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
            # Mesma mensagem para e-mail inexistente e senha errada
            flash("E-mail ou senha incorretos.", "erro")

    return render_template("login.html", email=email)


# Formulário de cadastro integrado com o back-end (#60)
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
                # O perfil nunca vem do formulário: todo cadastro é de usuário comum.
                cadastrar_usuario(nome, email, senha)
            except EmailJaCadastrado:
                erros.append("Este e-mail já está cadastrado.")
            else:
                flash("Cadastro realizado! Entre com seu e-mail e senha.", "sucesso")
                return redirect(url_for("login"))

        for erro in erros:
            flash(erro, "erro")

    return render_template("cadastro.html", nome=nome, email=email)


# Rota de encerramento de sessão (#73) com redirecionamento (#72)
@app.route("/logout", methods=["POST"])
def logout():
    encerrar_sessao()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("homepage"))
