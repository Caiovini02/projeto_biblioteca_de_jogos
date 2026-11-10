"""Catálogo de jogos (#27).

Os jogos ficam em bilbioteca_de_jogos/data/jogos.csv. Diferente do
usuarios.csv, esse arquivo É versionado no git (regra "!data/jogos.csv" no
.gitignore): o catálogo é conteúdo compartilhado por todo o time.

Colunas do CSV:
- id: inteiro único
- titulo, genero: texto
- preco: valor cheio em reais, com ponto decimal (ex.: 199.90)
- desconto: percentual inteiro (0 = sem promoção)
- avaliacao: nota média de 0 a 5; avaliacoes: quantidade de avaliações
- capa: URL ou caminho da imagem; vazio mostra um placeholder com as iniciais
- descricao: texto livre

Ao carregar, cada jogo ganha duas chaves calculadas: preco_final (já com o
desconto aplicado) e em_promocao (desconto > 0).

buscar_jogo_por_id() é o ponto de entrada para a página de detalhes (#39).
"""

import csv
from pathlib import Path

from projeto import app

CAMINHO_JOGOS = Path(__file__).resolve().parent.parent / "data" / "jogos.csv"


def _converter(jogo):
    """Converte os textos do CSV para números e calcula os campos derivados."""
    jogo["id"] = int(jogo["id"])
    jogo["preco"] = float(jogo["preco"])
    jogo["desconto"] = int(jogo.get("desconto") or 0)
    jogo["avaliacao"] = float(jogo.get("avaliacao") or 0)
    jogo["avaliacoes"] = int(jogo.get("avaliacoes") or 0)
    jogo["preco_final"] = round(jogo["preco"] * (100 - jogo["desconto"]) / 100, 2)
    jogo["em_promocao"] = jogo["desconto"] > 0
    return jogo


def carregar_jogos():
    """Retorna todos os jogos do catálogo, na ordem do arquivo."""
    if not CAMINHO_JOGOS.exists():
        return []
    with CAMINHO_JOGOS.open(encoding="utf-8", newline="") as arquivo:
        return [_converter(jogo) for jogo in csv.DictReader(arquivo)]


def buscar_jogo_por_id(jogo_id):
    for jogo in carregar_jogos():
        if jogo["id"] == jogo_id:
            return jogo
    return None


# Filtros usados pelos templates


@app.template_filter("moeda")
def moeda(valor):
    """Formata 1234.5 como 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"  # 1,234.50 (padrão americano)
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


@app.template_filter("iniciais")
def iniciais(titulo):
    """Duas iniciais do título, para o placeholder de capa (ex.: 'Hollow Knight' -> 'HK')."""
    palavras = [p for p in titulo.replace(":", " ").split() if p[0].isalnum()]
    return "".join(p[0] for p in palavras[:2]).upper()
