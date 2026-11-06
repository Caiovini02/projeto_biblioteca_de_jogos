from flask import g

from projeto import models
from projeto.autenticacao import login_obrigatorio, verificar_credenciais
from tests.base import TesteComUsuarios


class TesteVerificacaoCredenciais(TesteComUsuarios):
    """#64: compara a senha informada com o hash salvo."""

    def setUp(self):
        super().setUp()
        self.cadastrar_ana()

    def test_credenciais_corretas(self):
        self.assertEqual(verificar_credenciais("ana@exemplo.com", "segredo123")["id"], 1)

    def test_senha_errada(self):
        self.assertIsNone(verificar_credenciais("ana@exemplo.com", "errada"))

    def test_email_inexistente(self):
        self.assertIsNone(verificar_credenciais("ninguem@exemplo.com", "segredo123"))


class TesteLogin(TesteComUsuarios):
    """#63, #65 e #66: rota de login, sessão e mensagens de sucesso/erro."""

    def setUp(self):
        super().setUp()
        self.cadastrar_ana()

    def test_homepage_tem_link_para_login(self):
        resposta = self.cliente.get("/")
        self.assertIn('href="/login"', resposta.text)

    def test_pagina_de_login(self):
        resposta = self.cliente.get("/login")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('action="/login"', resposta.text)

    def test_campos_vazios_mostram_erro(self):
        resposta = self.entrar(email="", senha="")
        self.assertIn("Preencha o e-mail e a senha.", resposta.text)

    def test_senha_errada_mostra_erro_e_mantem_email(self):
        resposta = self.entrar(senha="errada")
        self.assertIn("E-mail ou senha incorretos.", resposta.text)
        self.assertIn('value="ana@exemplo.com"', resposta.text)
        with self.cliente.session_transaction() as sessao:
            self.assertNotIn("usuario_id", sessao)

    def test_email_inexistente_mostra_mesma_mensagem(self):
        resposta = self.entrar(email="ninguem@exemplo.com")
        self.assertIn("E-mail ou senha incorretos.", resposta.text)

    def test_login_valido_mostra_sucesso_na_homepage(self):
        resposta = self.entrar()
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.headers["Location"], "/")

        homepage = self.cliente.get("/")
        self.assertIn("Bem-vindo(a), Ana!", homepage.text)
        self.assertNotIn('href="/login"', homepage.text)

    def test_login_inicia_sessao_com_token(self):
        self.entrar()

        with self.cliente.session_transaction() as sessao:
            self.assertEqual(sessao["usuario_id"], 1)
            self.assertTrue(sessao.permanent)
            token = sessao["token_sessao"]
        self.assertEqual(models.buscar_usuario_por_id(1)["token_sessao"], token)

    def test_usuario_logado_em_login_vai_para_homepage(self):
        self.entrar()
        resposta = self.cliente.get("/login")
        self.assertEqual(resposta.status_code, 302)


class TesteInvalidacaoSessao(TesteComUsuarios):
    """#73, #72 e #74: logout, redirecionamento e sessão inválida depois de sair."""

    def setUp(self):
        super().setUp()
        self.cadastrar_ana()

    def cookie_de_sessao(self):
        return self.cliente.get_cookie("session").value

    def esta_logado(self, cliente):
        with cliente:
            cliente.get("/")
            return g.usuario is not None

    def test_logout_so_por_post(self):
        self.assertEqual(self.cliente.get("/logout").status_code, 405)

    def test_logout_redireciona_e_mostra_mensagem(self):
        self.entrar()
        resposta = self.cliente.post("/logout")
        self.assertEqual(resposta.headers["Location"], "/")
        self.assertIn("Você saiu da sua conta.", self.cliente.get("/").text)

    def test_logout_apaga_token_salvo(self):
        self.entrar()
        self.cliente.post("/logout")

        self.assertEqual(models.buscar_usuario_por_id(1)["token_sessao"], "")
        with self.cliente.session_transaction() as sessao:
            self.assertNotIn("usuario_id", sessao)

    def test_cookie_antigo_nao_vale_depois_do_logout(self):
        self.entrar()
        cookie_antigo = self.cookie_de_sessao()
        self.cliente.post("/logout")

        outro_cliente = self.app.test_client()
        outro_cliente.set_cookie("session", cookie_antigo)
        self.assertFalse(self.esta_logado(outro_cliente))

    def test_novo_login_invalida_sessao_anterior(self):
        self.entrar()
        cookie_antigo = self.cookie_de_sessao()

        self.entrar(cliente=self.app.test_client())

        outro_cliente = self.app.test_client()
        outro_cliente.set_cookie("session", cookie_antigo)
        self.assertFalse(self.esta_logado(outro_cliente))

    def test_usuario_removido_perde_a_sessao(self):
        self.entrar()
        self.caminho_csv.unlink()
        self.assertFalse(self.esta_logado(self.cliente))

    def test_rota_restrita_sem_login_vai_para_login(self):
        @login_obrigatorio
        def restrita():
            return "conteúdo restrito"

        with self.app.test_request_context("/restrita"):
            g.usuario = None
            resposta = restrita()
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.headers["Location"], "/login")

    def test_rota_restrita_com_login_nao_fica_em_cache(self):
        @login_obrigatorio
        def restrita():
            return "conteúdo restrito"

        with self.app.test_request_context("/restrita"):
            g.usuario = models.buscar_usuario_por_id(1)
            resposta = restrita()
        self.assertEqual(resposta.get_data(as_text=True), "conteúdo restrito")
        self.assertEqual(resposta.headers["Cache-Control"], "no-store")
