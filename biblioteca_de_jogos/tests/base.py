import tempfile
import unittest
from pathlib import Path
from unittest import mock

from projeto import app, models


class TesteComUsuarios(unittest.TestCase):
    """Usa um usuarios.csv temporário, sem tocar na pasta data/ do projeto."""

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.caminho_csv = Path(pasta.name) / "usuarios.csv"

        trocar_caminho = mock.patch.object(models, "CAMINHO_USUARIOS", self.caminho_csv)
        trocar_caminho.start()
        self.addCleanup(trocar_caminho.stop)

        app.config["TESTING"] = True
        self.app = app
        self.cliente = app.test_client()

    def cadastrar_ana(self):
        return models.cadastrar_usuario("Ana", "ana@exemplo.com", "segredo123")

    def entrar(self, cliente=None, email="ana@exemplo.com", senha="segredo123"):
        return (cliente or self.cliente).post("/login", data={"email": email, "senha": senha})
