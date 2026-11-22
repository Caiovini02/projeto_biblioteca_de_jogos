import csv

from werkzeug.security import check_password_hash

from projeto import models
from tests.base import TesteComUsuarios


class TesteArmazenamentoUsuarios(TesteComUsuarios):
    """#59: armazenamento dos usuários em CSV com senha protegida por hash."""

    def test_sem_arquivo_nao_ha_usuarios(self):
        self.assertEqual(models.carregar_usuarios(), [])
        self.assertIsNone(models.buscar_usuario_por_email("ana@exemplo.com"))

    def test_cadastro_cria_csv_com_cabecalho(self):
        self.cadastrar_ana()

        with self.caminho_csv.open(encoding="utf-8", newline="") as arquivo:
            linhas = list(csv.reader(arquivo))
        self.assertEqual(linhas[0], models.CAMPOS)
        self.assertEqual(len(linhas), 2)

    def test_senha_salva_apenas_como_hash(self):
        usuario = self.cadastrar_ana()

        conteudo = self.caminho_csv.read_text(encoding="utf-8")
        self.assertNotIn("segredo123", conteudo)
        self.assertTrue(check_password_hash(usuario["senha_hash"], "segredo123"))

    def test_ids_sao_sequenciais(self):
        ana = self.cadastrar_ana()
        bruno = models.cadastrar_usuario("Bruno", "bruno@exemplo.com", "outrasenha")

        self.assertEqual((ana["id"], bruno["id"]), (1, 2))

    def test_email_normalizado_na_gravacao_e_na_busca(self):
        models.cadastrar_usuario("Ana", "  ANA@Exemplo.com ", "segredo123")

        usuario = models.buscar_usuario_por_email("ana@EXEMPLO.com")
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario["email"], "ana@exemplo.com")

    def test_email_repetido_e_recusado(self):
        self.cadastrar_ana()

        with self.assertRaises(models.EmailJaCadastrado):
            models.cadastrar_usuario("Outra Ana", "ANA@exemplo.com", "abc12345")
        self.assertEqual(len(models.carregar_usuarios()), 1)

    def test_busca_por_id_retorna_id_inteiro(self):
        self.cadastrar_ana()

        usuario = models.buscar_usuario_por_id(1)
        self.assertEqual(usuario["nome"], "Ana")
        self.assertIsInstance(usuario["id"], int)
        self.assertIsNone(models.buscar_usuario_por_id(99))

    def test_definir_token_sessao(self):
        self.cadastrar_ana()

        models.definir_token_sessao(1, "abc")
        self.assertEqual(models.buscar_usuario_por_id(1)["token_sessao"], "abc")
        models.definir_token_sessao(1, "")
        self.assertEqual(models.buscar_usuario_por_id(1)["token_sessao"], "")
