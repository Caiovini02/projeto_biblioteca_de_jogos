import unittest

from werkzeug.security import check_password_hash

from projeto import models
from projeto.forms import validar_cadastro
from tests.base import TesteComUsuarios


class TesteValidacaoCadastro(unittest.TestCase):
    """Validação do cadastro: integração (#60) e campos obrigatórios (#56)."""

    def test_dados_validos(self):
        self.assertEqual(validar_cadastro("Ana", "ana@exemplo.com", "segredo123", "segredo123"), [])

    def test_nome_vazio(self):
        self.assertEqual(
            validar_cadastro("", "ana@exemplo.com", "segredo123", "segredo123"),
            ["Informe o nome."],
        )

    def test_email_vazio(self):
        self.assertEqual(
            validar_cadastro("Ana", "", "segredo123", "segredo123"),
            ["Informe o e-mail."],
        )

    def test_senha_vazia(self):
        self.assertEqual(
            validar_cadastro("Ana", "ana@exemplo.com", "", ""),
            ["Informe a senha.", "Confirme a senha."],
        )

    def test_confirmacao_vazia(self):
        self.assertEqual(
            validar_cadastro("Ana", "ana@exemplo.com", "segredo123", ""),
            ["Confirme a senha."],
        )

    def test_todos_os_campos_vazios_listam_um_erro_por_campo(self):
        self.assertEqual(
            validar_cadastro("", "", "", ""),
            ["Informe o nome.", "Informe o e-mail.", "Informe a senha.", "Confirme a senha."],
        )

    def test_nome_e_email_so_com_espacos_contam_como_vazios(self):
        erros = validar_cadastro("   ", "   ", "segredo123", "segredo123")
        self.assertEqual(erros, ["Informe o nome.", "Informe o e-mail."])

    def test_email_invalido(self):
        self.assertIn("Informe um e-mail válido.", validar_cadastro("Ana", "ana", "segredo123", "segredo123"))

    def test_senha_curta(self):
        erros = validar_cadastro("Ana", "ana@exemplo.com", "curta", "curta")
        self.assertIn("A senha deve ter pelo menos 8 caracteres.", erros)

    def test_senhas_diferentes(self):
        erros = validar_cadastro("Ana", "ana@exemplo.com", "segredo123", "segredo124")
        self.assertIn("As senhas não conferem.", erros)


class TesteRotaCadastro(TesteComUsuarios):
    """#60: formulário de cadastro conectado à rota, com mensagens de sucesso/erro."""

    def cadastrar(self, **campos):
        dados = {
            "nome": "Ana",
            "email": "ana@exemplo.com",
            "senha": "segredo123",
            "confirmacao": "segredo123",
        }
        dados.update(campos)
        return self.cliente.post("/cadastro", data=dados)

    def test_pagina_de_cadastro(self):
        resposta = self.cliente.get("/cadastro")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('action="/cadastro"', resposta.text)

    def test_homepage_deslogada_tem_link_para_a_pagina_de_cadastro(self):
        resposta = self.cliente.get("/")
        self.assertIn('href="/cadastro"', resposta.text)

    def test_login_e_cadastro_tem_links_entre_si(self):
        self.assertIn('href="/cadastro"', self.cliente.get("/login").text)
        self.assertIn('href="/login"', self.cliente.get("/cadastro").text)

    def test_cadastro_valido_salva_e_vai_para_login_com_mensagem(self):
        resposta = self.cadastrar()
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.headers["Location"], "/login")

        usuario = models.buscar_usuario_por_email("ana@exemplo.com")
        self.assertEqual(usuario["nome"], "Ana")
        self.assertTrue(check_password_hash(usuario["senha_hash"], "segredo123"))
        self.assertIn("Cadastro realizado!", self.cliente.get("/login").text)

    def test_depois_do_cadastro_consegue_entrar(self):
        self.cadastrar()
        resposta = self.entrar()
        self.assertEqual(resposta.headers["Location"], "/")

    def test_perfil_nao_vem_do_formulario(self):
        self.cadastrar(perfil="admin")
        self.assertEqual(models.buscar_usuario_por_email("ana@exemplo.com")["perfil"], "usuario")

    def test_email_repetido_mostra_erro(self):
        self.cadastrar()
        resposta = self.cadastrar(nome="Outra Ana")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Este e-mail já está cadastrado.", resposta.text)
        self.assertEqual(len(models.carregar_usuarios()), 1)

    def test_erro_mostra_mensagens_e_mantem_nome_e_email(self):
        resposta = self.cadastrar(senha="curta", confirmacao="outra")
        self.assertIn("A senha deve ter pelo menos 8 caracteres.", resposta.text)
        self.assertIn("As senhas não conferem.", resposta.text)
        self.assertIn('value="Ana"', resposta.text)
        self.assertIn('value="ana@exemplo.com"', resposta.text)
        self.assertNotIn("curta", resposta.text)
        self.assertEqual(models.carregar_usuarios(), [])

    def test_campos_vazios_mostram_uma_mensagem_por_campo(self):
        resposta = self.cadastrar(nome="", email="", senha="", confirmacao="")
        self.assertEqual(resposta.status_code, 200)
        for mensagem in ("Informe o nome.", "Informe o e-mail.", "Informe a senha.", "Confirme a senha."):
            self.assertIn(mensagem, resposta.text)
        self.assertEqual(models.carregar_usuarios(), [])

    def test_usuario_logado_em_cadastro_vai_para_homepage(self):
        self.cadastrar()
        self.entrar()
        resposta = self.cliente.get("/cadastro")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.headers["Location"], "/")
