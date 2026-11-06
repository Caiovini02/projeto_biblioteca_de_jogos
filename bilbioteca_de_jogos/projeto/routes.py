from flask import flash, g, redirect, render_template, request, url_for

from projeto import app
from projeto.autenticacao import encerrar_sessao, iniciar_sessao, verificar_credenciais



@app.route("/")
def homepage():
    return render_template("homepage.html")


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
                return redirect(url_for("homepage"))
            # Mesma mensagem para e-mail inexistente e senha errada, para não
            # revelar quais e-mails estão cadastrados.
            flash("E-mail ou senha incorretos.", "erro")

    return render_template("login.html", email=email)


# Rota de encerramento de sessão (#73) com redirecionamento (#72)
@app.route("/logout", methods=["POST"])
def logout():
    encerrar_sessao()
    return redirect(url_for("homepage"))
