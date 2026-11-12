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


class TesteFiltroPorGenero(TesteComCatalogo):
    """#51: buscar os jogos e retornar os do gênero selecionado."""

    def setUp(self):
        super().setUp()
        self.escrever_csv(
            "1,Jogo Zeta,Ação,10,0,4,1,,",
            "2,Jogo Alfa,RPG,10,0,4,1,,",
            "3,Jogo Beta,Aventura,10,0,4,1,,",
            "4,Jogo Gama,RPG,10,0,4,1,,",
        )

    def titulos(self, jogos):
        return [jogo["titulo"] for jogo in jogos]

    def test_retorna_so_os_jogos_do_genero_na_ordem_do_arquivo(self):
        jogos = catalogo.filtrar_por_genero(catalogo.carregar_jogos(), "RPG")
        self.assertEqual(self.titulos(jogos), ["Jogo Alfa", "Jogo Gama"])

    def test_sem_genero_retorna_todos(self):
        todos = catalogo.carregar_jogos()
        self.assertEqual(catalogo.filtrar_por_genero(todos, ""), todos)
        self.assertEqual(catalogo.filtrar_por_genero(todos, None), todos)

    def test_genero_inexistente_retorna_lista_vazia(self):
        self.assertEqual(catalogo.filtrar_por_genero(catalogo.carregar_jogos(), "Terror"), [])

    def test_ignora_maiusculas_e_acentos(self):
        todos = catalogo.carregar_jogos()
        self.assertEqual(self.titulos(catalogo.filtrar_por_genero(todos, "acao")), ["Jogo Zeta"])
        self.assertEqual(self.titulos(catalogo.filtrar_por_genero(todos, "  rpg ")), ["Jogo Alfa", "Jogo Gama"])

    def test_lista_generos_sem_repeticao_e_em_ordem_alfabetica(self):
        generos = catalogo.listar_generos(catalogo.carregar_jogos())
        self.assertEqual(generos, ["Ação", "Aventura", "RPG"])

    def test_localizar_genero_devolve_o_nome_cadastrado(self):
        generos = ["Ação", "Aventura", "RPG"]
        self.assertEqual(catalogo.localizar_genero(generos, "rpg"), "RPG")
        self.assertEqual(catalogo.localizar_genero(generos, "acao"), "Ação")
        self.assertEqual(catalogo.localizar_genero(generos, "Terror"), "Terror")

    # Rota "/" com ?genero=...

    def test_homepage_sem_filtro_mostra_todos(self):
        html = self.cliente.get("/").text
        self.assertEqual(html.count('class="card-jogo"'), 4)

    def test_homepage_filtra_pelo_genero_da_url(self):
        html = self.cliente.get("/?genero=RPG").text
        self.assertEqual(html.count('class="card-jogo"'), 2)
        self.assertIn("Jogo Alfa", html)
        self.assertIn("Jogo Gama", html)
        self.assertNotIn("Jogo Zeta", html)
        self.assertNotIn("Jogo Beta", html)

    def test_select_lista_os_generos_do_catalogo_e_marca_o_escolhido(self):
        html = self.cliente.get("/?genero=Aventura").text
        self.assertIn('<option value="">Qualquer gênero</option>', html)
        self.assertIn('<option value="Ação">Ação</option>', html)
        self.assertIn('<option value="Aventura" selected>Aventura</option>', html)
        self.assertIn('<option value="RPG">RPG</option>', html)

    def test_genero_digitado_em_minusculo_marca_a_opcao_correta(self):
        html = self.cliente.get("/?genero=rpg").text
        self.assertEqual(html.count('class="card-jogo"'), 2)
        self.assertIn('<option value="RPG" selected>RPG</option>', html)

    def test_filtro_envia_por_get_sem_javascript(self):
        html = self.cliente.get("/").text
        self.assertIn('method="get"', html)
        self.assertIn('name="genero"', html)
        self.assertNotIn("<script", html)

    def test_genero_sem_jogos_mostra_mensagem_propria(self):
        html = self.cliente.get("/?genero=Terror").text
        self.assertNotIn('class="card-jogo"', html)
        self.assertIn("Nenhum jogo encontrado no gênero", html)
        self.assertIn("Terror", html)
        self.assertNotIn("Nenhum jogo cadastrado", html)


class TesteBuscaPorTitulo(TesteComCatalogo):
    """#45: pesquisar os jogos e retornar os cujo título corresponde ao termo."""

    def setUp(self):
        super().setUp()
        self.escrever_csv(
            "1,Hollow Knight,Aventura,10,0,4,1,,",
            "2,Dark Souls,RPG,10,0,4,1,,",
            "3,Darkest Dungeon,RPG,10,0,4,1,,",
            "4,Ação Total,Ação,10,0,4,1,,",
        )

    def titulos(self, jogos):
        return [jogo["titulo"] for jogo in jogos]

    def test_retorna_jogos_cujo_titulo_contem_o_termo_na_ordem_do_arquivo(self):
        jogos = catalogo.buscar_por_titulo(catalogo.carregar_jogos(), "dark")
        self.assertEqual(self.titulos(jogos), ["Dark Souls", "Darkest Dungeon"])

    def test_encontra_termo_no_meio_do_titulo(self):
        jogos = catalogo.buscar_por_titulo(catalogo.carregar_jogos(), "knight")
        self.assertEqual(self.titulos(jogos), ["Hollow Knight"])

    def test_ignora_maiusculas_acentos_e_espacos_nas_pontas(self):
        todos = catalogo.carregar_jogos()
        self.assertEqual(self.titulos(catalogo.buscar_por_titulo(todos, "  HOLLOW  ")), ["Hollow Knight"])
        self.assertEqual(self.titulos(catalogo.buscar_por_titulo(todos, "acao")), ["Ação Total"])

    def test_termo_vazio_retorna_todos(self):
        todos = catalogo.carregar_jogos()
        self.assertEqual(catalogo.buscar_por_titulo(todos, ""), todos)
        self.assertEqual(catalogo.buscar_por_titulo(todos, "   "), todos)
        self.assertEqual(catalogo.buscar_por_titulo(todos, None), todos)

    def test_sem_correspondencia_retorna_lista_vazia(self):
        self.assertEqual(catalogo.buscar_por_titulo(catalogo.carregar_jogos(), "zelda"), [])

    def test_busca_so_no_titulo_e_nao_no_genero(self):
        # "RPG" é gênero de dois jogos, mas não aparece em nenhum título
        self.assertEqual(catalogo.buscar_por_titulo(catalogo.carregar_jogos(), "rpg"), [])

    # Rota "/" com ?busca=...

    def test_homepage_busca_pelo_titulo_da_url(self):
        html = self.cliente.get("/?busca=dark").text
        self.assertEqual(html.count('class="card-jogo"'), 2)
        self.assertIn("Dark Souls", html)
        self.assertIn("Darkest Dungeon", html)
        self.assertNotIn("Hollow Knight", html)

    def test_homepage_combina_busca_e_genero(self):
        html = self.cliente.get("/?busca=dark&genero=Aventura").text
        self.assertNotIn('class="card-jogo"', html)

        html = self.cliente.get("/?busca=souls&genero=RPG").text
        self.assertEqual(html.count('class="card-jogo"'), 1)
        self.assertIn("Dark Souls", html)

    def test_homepage_sem_busca_mostra_todos(self):
        html = self.cliente.get("/").text
        self.assertEqual(html.count('class="card-jogo"'), 4)


class TesteBuscaNaHomepage(TesteComCatalogo):
    """#46: o campo de pesquisa da homepage conectado à busca do back-end."""

    def setUp(self):
        super().setUp()
        self.escrever_csv(
            "1,Hollow Knight,Aventura,10,0,4,1,,",
            "2,Dark Souls,RPG,10,0,4,1,,",
            "3,Darkest Dungeon,RPG,10,0,4,1,,",
        )

    def partes(self, html):
        """Separa a página no formulário de gênero: (navbar e antes, filtro e depois)."""
        antes, depois = html.split('<form class="filtro-genero"', 1)
        return antes, depois

    def test_campo_de_busca_e_um_formulario_get_que_volta_ao_catalogo(self):
        navbar, _ = self.partes(self.cliente.get("/").text)
        self.assertIn('<form class="busca-jogos" method="get" action="/#catalog">', navbar)
        self.assertIn('name="busca"', navbar)
        self.assertIn('type="search"', navbar)
        self.assertIn(">Buscar</button>", navbar)

    def test_campo_mantem_o_termo_buscado(self):
        navbar, _ = self.partes(self.cliente.get("/?busca=dark").text)
        self.assertIn('value="dark"', navbar)

    def test_termo_com_html_e_escapado_no_campo(self):
        html = self.cliente.get('/?busca="><script>alert(1)</script>').text
        self.assertNotIn("<script", html)

    def test_busca_repassa_o_genero_escolhido_em_campo_oculto(self):
        navbar, _ = self.partes(self.cliente.get("/?genero=RPG").text)
        self.assertIn('<input type="hidden" name="genero" value="RPG" />', navbar)

    def test_filtro_de_genero_repassa_a_busca_em_campo_oculto(self):
        _, filtro = self.partes(self.cliente.get("/?busca=dark").text)
        self.assertIn('<input type="hidden" name="busca" value="dark" />', filtro)

    def test_sem_busca_nem_genero_os_campos_ocultos_vao_vazios(self):
        navbar, filtro = self.partes(self.cliente.get("/").text)
        self.assertIn('<input type="hidden" name="genero" value="" />', navbar)
        self.assertIn('<input type="hidden" name="busca" value="" />', filtro)

    def test_busca_sem_resultado_mostra_mensagem_com_o_termo(self):
        html = self.cliente.get("/?busca=zelda").text
        self.assertNotIn('class="card-jogo"', html)
        self.assertIn('Nenhum jogo encontrado para "zelda".', html)
        self.assertNotIn("Nenhum jogo cadastrado", html)

    def test_busca_com_genero_sem_resultado_cita_os_dois(self):
        html = self.cliente.get("/?busca=knight&genero=RPG").text
        self.assertNotIn('class="card-jogo"', html)
        self.assertIn('Nenhum jogo encontrado para "knight" no gênero "RPG".', html)

    def test_genero_sem_busca_mantem_a_mensagem_do_genero(self):
        html = self.cliente.get("/?genero=Terror").text
        self.assertIn('Nenhum jogo encontrado no gênero "Terror".', html)

    def test_titulo_da_secao_continua_catalogo(self):
        html = self.cliente.get("/?busca=dark").text
        self.assertIn('<h2 id="ctitle">Catálogo</h2>', html)

    def test_busca_nao_usa_javascript(self):
        self.assertNotIn("<script", self.cliente.get("/?busca=dark").text)
