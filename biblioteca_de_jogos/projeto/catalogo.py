"""Catálogo de jogos.

Os jogos ficam em bilbioteca_de_jogos/data/jogos.csv. Diferente do
usuarios.csv, esse arquivo É versionado no git (regra "!data/jogos.csv" no
.gitignore): o catálogo é conteúdo compartilhado por todo o time.

Colunas do CSV:
- id: inteiro único
- titulo, genero: texto
- desenvolvedora: texto (opcional; se vazio, não aparece na página de detalhes)
- ano: ano de lançamento, ex.: 2026 (opcional; se vazio, não aparece)
- preco: valor cheio em reais, com ponto decimal (ex.: 199.90)
- desconto: percentual inteiro (0 = sem promoção)
- avaliacao: nota média de 0 a 5; avaliacoes: quantidade de avaliações
- capa: URL ou caminho da imagem (ex.: /static/img/capas/bloodborne.jpg); vazio mostra um placeholder com as iniciais
- descricao: texto livre

Ao carregar, cada jogo ganha duas chaves calculadas: preco_final (já com o
desconto aplicado) e em_promocao (desconto > 0).

buscar_jogo_por_id() é o ponto de entrada para a página de detalhes.
"""

import csv
import unicodedata
from pathlib import Path

from projeto import app

CAMINHO_JOGOS = Path(__file__).resolve().parent.parent / "data" / "jogos.csv"


def _converter(jogo):
    jogo["id"] = int(jogo["id"])
    jogo["preco"] = float(jogo["preco"])
    jogo["desconto"] = int(jogo.get("desconto") or 0)
    jogo["avaliacao"] = float(jogo.get("avaliacao") or 0)
    jogo["avaliacoes"] = int(jogo.get("avaliacoes") or 0)
    jogo["preco_final"] = round(jogo["preco"] * (100 - jogo["desconto"]) / 100, 2)
    jogo["em_promocao"] = jogo["desconto"] > 0
    return jogo


def carregar_jogos():
    if not CAMINHO_JOGOS.exists():
        return []
    with CAMINHO_JOGOS.open(encoding="utf-8", newline="") as arquivo:
        return [_converter(jogo) for jogo in csv.DictReader(arquivo)]


def buscar_jogo_por_id(jogo_id):
    for jogo in carregar_jogos():
        if jogo["id"] == jogo_id:
            return jogo
    return None



def _normalizar(texto):
    sem_acento = unicodedata.normalize("NFD", texto or "")
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.strip().casefold()


def listar_generos(jogos):
    generos = {jogo["genero"] for jogo in jogos if jogo["genero"].strip()}
    return sorted(generos, key=_normalizar)


def localizar_genero(generos, texto):
    for genero in generos:
        if _normalizar(genero) == _normalizar(texto):
            return genero
    return texto


def filtrar_por_genero(jogos, genero):
    if not _normalizar(genero):
        return jogos
    procurado = _normalizar(genero)
    return [jogo for jogo in jogos if _normalizar(jogo["genero"]) == procurado]


# Busca por título


def buscar_por_titulo(jogos, termo):
    procurado = _normalizar(termo)
    if not procurado:
        return jogos
    return [jogo for jogo in jogos if procurado in _normalizar(jogo["titulo"])]


# Filtros usados pelos templates


@app.template_filter("moeda")
def moeda(valor):
    texto = f"{valor:,.2f}" 
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


@app.template_filter("iniciais")
def iniciais(titulo):
    """Duas iniciais do título, para o placeholder de capa (ex.: 'Hollow Knight' -> 'HK')."""
    palavras = [p for p in titulo.replace(":", " ").split() if p[0].isalnum()]
    return "".join(p[0] for p in palavras[:2]).upper()


# Filtro por preço e ordenação

def verificar_preco_maximo(texto):
    try:
        valor = int(texto)
    except (TypeError, ValueError):
        return 0
    return max(valor, 0)


def filtrar_por_preco(jogos, preco_maximo):
    if preco_maximo <= 0:
        return jogos
    return [jogo for jogo in jogos if jogo["preco_final"] <= preco_maximo]

def filtrar_promocao(jogos, promocoes_on):
    if not promocoes_on:
        return jogos
    return [jogo for jogo in jogos if jogo["em_promocao"]]




ORDENACOES = {
    "rate": (lambda jogo: (jogo["avaliacao"], jogo["avaliacoes"]), True),
    "low": (lambda jogo: jogo["preco_final"], False),
    "high": (lambda jogo: jogo["preco_final"], True),
}
ORDENACAO_PADRAO = "rate"


def normalizar_ordenacao(criterio):
    return criterio if criterio in ORDENACOES else ORDENACAO_PADRAO


def ordenar_jogos(jogos, criterio):
    chave, decrescente = ORDENACOES[normalizar_ordenacao(criterio)]
    return sorted(jogos, key=chave, reverse=decrescente)
