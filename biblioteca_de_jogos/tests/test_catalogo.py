import tempfile
import unittest
from pathlib import Path
from unittest import mock

from projeto import app, catalogo

CABECALHO = "id,titulo,genero,preco,desconto,avaliacao,avaliacoes,capa,descricao\n"


class TesteComCatalogo(unittest.TestCase):
    """Usa um jogos.csv temporário, sem tocar no data/jogos.csv do projeto."""

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.caminho_csv = Path(pasta.name) / "jogos.csv"

        trocar_caminho = mock.patch.object(catalogo, "CAMINHO_JOGOS", self.caminho_csv)
        trocar_caminho.start()
        self.addCleanup(trocar_caminho.stop)

        app.config["TESTING"] = True
        self.cliente = app.test_client()

    def escrever_csv(self, *linhas):
        self.caminho_csv.write_text(CABECALHO + "".join(f"{linha}\n" for linha in linhas), encoding="utf-8")


class TesteCarregamentoDoCatalogo(TesteComCatalogo):
    """#27: carregar os jogos da fonte de dados."""

    def test_sem_arquivo_retorna_lista_vazia(self):
        self.assertEqual(catalogo.carregar_jogos(), [])
        self.assertIsNone(catalogo.buscar_jogo_por_id(1))

    def test_converte_tipos_e_calcula_preco_final(self):
        self.escrever_csv('1,Jogo A,Ação,200.00,30,4.5,120,,"Descrição, com vírgula"')

        (jogo,) = catalogo.carregar_jogos()
        self.assertEqual(jogo["id"], 1)
        self.assertEqual(jogo["preco"], 200.0)
        self.assertEqual(jogo["desconto"], 30)
        self.assertEqual(jogo["preco_final"], 140.0)
        self.assertTrue(jogo["em_promocao"])
        self.assertEqual(jogo["avaliacao"], 4.5)
        self.assertEqual(jogo["avaliacoes"], 120)
        self.assertEqual(jogo["descricao"], "Descrição, com vírgula")

    def test_sem_desconto(self):
        self.escrever_csv("1,Jogo A,Ação,59.90,0,4.0,10,,Sem promoção")

        (jogo,) = catalogo.carregar_jogos()
        self.assertEqual(jogo["preco_final"], 59.9)
        self.assertFalse(jogo["em_promocao"])

    def test_mantem_a_ordem_do_arquivo(self):
        self.escrever_csv("2,Zeta,Ação,10,0,4,1,,", "1,Alfa,RPG,10,0,4,1,,")

        self.assertEqual([j["titulo"] for j in catalogo.carregar_jogos()], ["Zeta", "Alfa"])

    def test_buscar_jogo_por_id(self):
        self.escrever_csv("1,Alfa,RPG,10,0,4,1,,", "2,Beta,Ação,10,0,4,1,,")

        self.assertEqual(catalogo.buscar_jogo_por_id(2)["titulo"], "Beta")
        self.assertIsNone(catalogo.buscar_jogo_por_id(99))

    def test_filtro_moeda(self):
        self.assertEqual(catalogo.moeda(24.99), "R$ 24,99")
        self.assertEqual(catalogo.moeda(1234.5), "R$ 1.234,50")
        self.assertEqual(catalogo.moeda(0), "R$ 0,00")

    def test_filtro_iniciais(self):
        self.assertEqual(catalogo.iniciais("Hollow Knight"), "HK")
        self.assertEqual(catalogo.iniciais("Hollow Knight: Silksong"), "HK")
        self.assertEqual(catalogo.iniciais("Bloodborne"), "B")


class TesteListagemNaHomepage(TesteComCatalogo):
    """#28: a homepage mostra os jogos do catálogo (UC 05)."""

    def test_lista_os_jogos_com_preco_e_desconto(self):
        self.escrever_csv(
            "1,Jogo A,Ação,200.00,30,4.5,120,,Um jogo",
            "2,Jogo B,RPG,59.90,0,4.0,10,,Outro jogo",
        )

        html = self.cliente.get("/").text
        self.assertIn("Jogo A", html)
        self.assertIn("Jogo B", html)
        self.assertEqual(html.count('class="card-jogo"'), 2)
        self.assertIn("-30%", html)
        self.assertIn("R$ 200,00", html)  # preço antigo riscado
        self.assertIn("R$ 140,00", html)  # preço com desconto
        self.assertIn("R$ 59,90", html)
        self.assertNotIn("Nenhum jogo cadastrado", html)

    def test_sem_capa_mostra_iniciais(self):
        self.escrever_csv("1,Hollow Knight,Aventura,46.99,0,4.9,4800,,Um jogo")

        html = self.cliente.get("/").text
        self.assertIn("capa-vazia", html)
        self.assertIn(">HK<", html)

    def test_com_capa_mostra_imagem(self):
        self.escrever_csv("1,Jogo A,Ação,10,0,4,1,/static/img/a.png,Um jogo")

        html = self.cliente.get("/").text
        self.assertIn('src="/static/img/a.png"', html)
        self.assertNotIn("capa-vazia", html)

    def test_catalogo_vazio_mostra_mensagem(self):
        self.escrever_csv()  # só o cabeçalho

        html = self.cliente.get("/").text
        self.assertIn("Nenhum jogo cadastrado no catálogo ainda.", html)
        self.assertNotIn('class="card-jogo"', html)

    def test_sem_arquivo_tambem_mostra_mensagem(self):
        html = self.cliente.get("/").text
        self.assertIn("Nenhum jogo cadastrado no catálogo ainda.", html)


class TesteArquivoDoRepositorio(unittest.TestCase):
    """Garante que o data/jogos.csv versionado está bem formado."""

    def test_csv_do_projeto_carrega(self):
        jogos = catalogo.carregar_jogos()
        self.assertGreaterEqual(len(jogos), 1)
        ids = [j["id"] for j in jogos]
        self.assertEqual(len(ids), len(set(ids)), "ids repetidos no jogos.csv")
        for jogo in jogos:
            self.assertTrue(jogo["titulo"].strip(), f"título vazio no id {jogo['id']}")
            self.assertGreaterEqual(jogo["preco"], 0)
            self.assertTrue(0 <= jogo["desconto"] <= 100)
            self.assertTrue(0 <= jogo["avaliacao"] <= 5)
