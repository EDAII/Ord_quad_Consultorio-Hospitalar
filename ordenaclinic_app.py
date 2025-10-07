# ordenaclinic_app.py
# ------------------------------------------------------------
# OrdenaClinic · Fila de triagem com Merge Sort (estável)
# Interface em Dash (100% local)
# ------------------------------------------------------------

import time
from dataclasses import dataclass, asdict
from typing import List, Tuple, Callable
from datetime import datetime

import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, no_update, dash_table

# ============================
# Modelo e utilidades
# ============================

@dataclass(frozen=True)
class Paciente:
    id: int
    nome: str
    chegada: int
    idade: int
    triagem: int  # 0=Vermelho (mais crítico) ... 4=Azul

TRIAGEM_LABELS = {
    0: "Vermelho (crítico)",
    1: "Amarelo (urgente)",
    2: "Verde (pouco urgente)",
    3: "Azul (não urgente)",
    4: "Branco (administrativo)",
}
TRIAGEM_CORES = {
    0: "#d32f2f",
    1: "#f9a825",
    2: "#388e3c",
    3: "#1976d2",
    4: "#757575",
}

def chave_padrao(p: Paciente) -> Tuple[int, int, int]:
    return (p.triagem, p.chegada, -p.idade)

# ============================
# Merge Sort estável com métricas
# ============================

class Medidor:
    def __init__(self, key: Callable[[Paciente], tuple]):
        self.keyf = key
        self.comparacoes = 0

    def cmp_le(self, a: Paciente, b: Paciente) -> bool:
        self.comparacoes += 1
        return self.keyf(a) <= self.keyf(b)

def merge_sort_estavel(arr: List[Paciente], key=chave_padrao):
    inicio = time.perf_counter()
    med = Medidor(key)

    def merge_sort(lst: List[Paciente]) -> List[Paciente]:
        if len(lst) <= 1:
            return lst
        mid = len(lst) // 2
        left = merge_sort(lst[:mid])
        right = merge_sort(lst[mid:])
        return merge(left, right)

    def merge(left: List[Paciente], right: List[Paciente]) -> List[Paciente]:
        i = j = 0
        res: List[Paciente] = []
        while i < len(left) and j < len(right):
            if med.cmp_le(left[i], right[j]):
                res.append(left[i]); i += 1
            else:
                res.append(right[j]); j += 1
        if i < len(left): res.extend(left[i:])
        if j < len(right): res.extend(right[j:])
        return res

    saida = merge_sort(arr[:])
    dur_ms = (time.perf_counter() - inicio) * 1000
    return saida, {
        "algoritmo": "Merge Sort (estável)",
        "comparacoes": med.comparacoes,
        "tempo_ms": round(dur_ms, 3),
        "estavel": True
    }

# ============================
# Helpers de UI
# ============================

def pacientes_para_df(pacientes: List[Paciente]) -> pd.DataFrame:
    df = pd.DataFrame([asdict(p) for p in pacientes])
    if df.empty:
        return pd.DataFrame(columns=["posição", "nome", "triagem", "chegada", "idade"])
    df = df.assign(
        triagem_label=df["triagem"].map(TRIAGEM_LABELS),
        triagem_cor=df["triagem"].map(TRIAGEM_CORES),
    )
    df = df[["nome", "triagem", "triagem_label", "triagem_cor", "chegada", "idade"]]
    df.insert(0, "posição", range(1, len(df) + 1))
    return df

def tabela_formatada(id_table: str):
    return dash_table.DataTable(
        id=id_table,
        columns=[
            {"name": "Posição", "id": "posição"},
            {"name": "Nome", "id": "nome"},
            {"name": "Triagem", "id": "triagem_label"},
            {"name": "Chegada", "id": "chegada"},
            {"name": "Idade", "id": "idade"},
        ],
        data=[],
        style_cell={"padding": "8px", "fontFamily": "Inter, system-ui, Arial", "fontSize": 14},
        style_header={"fontWeight": "700"},
        style_table={"overflowX": "auto", "maxHeight": "60vh", "overflowY": "auto"},
        page_action="none",
        fill_width=True,
        sort_action="none",
    )

def triagem_options():
    return [{"label": TRIAGEM_LABELS[t], "value": t} for t in sorted(TRIAGEM_LABELS.keys())]

def card_style():
    return {
        "border": "1px solid #eee",
        "borderRadius": "14px",
        "padding": "12px",
        "boxShadow": "0 2px 10px rgba(0,0,0,0.04)",
        "background": "white",
    }

def colorir_triagem(df: pd.DataFrame):
    if df.empty:
        return []
    return [
        {
            "if": {"filter_query": f'{{triagem}} = {t}', "column_id": "triagem_label"},
            "backgroundColor": cor, "color": "white", "fontWeight": "700",
        }
        for t, cor in TRIAGEM_CORES.items()
    ]

# ============================
# App
# ============================

app = Dash(__name__, title="OrdenaClinic · Triagem", suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div(
    style={
        "maxWidth": "1100px",
        "margin": "0 auto",
        "padding": "16px",
        "fontFamily": "Inter, system-ui, Arial",
    },
    children=[
        html.H1("🏥 OrdenaClinic", style={"marginBottom": "4px"}),
        html.Div("Fila de triagem com ordenação estável (Merge Sort)", style={"color": "#555", "marginBottom": "16px"}),

        dcc.Store(id="store-pacientes", data={"lista": [], "seq_chegada": 0}),
        dcc.Store(id="store-ordenado", data={"lista": [], "metrics": {}}),

        # ---- Formulário de cadastro ----
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1.3fr 0.6fr 1fr 1fr",
                "gap": "10px",
                "alignItems": "end",
                "marginBottom": "14px",
            },
            children=[
                html.Div([
                    html.Label("Nome do paciente"),
                    dcc.Input(id="in-nome", type="text", placeholder="Ex.: Ana Souza", style={"width": "100%"}),
                ]),
                html.Div([
                    html.Label("Idade"),
                    dcc.Input(id="in-idade", type="number", min=0, max=120, placeholder="Ex.: 64", style={"width": "100%"}),
                ]),
                html.Div([
                    html.Label("Triagem"),
                    dcc.Dropdown(id="in-triagem", options=triagem_options(), value=1, clearable=False),
                ]),
                html.Div([
                    html.Button("➕ Adicionar", id="btn-add", n_clicks=0, className="btn"),
                    html.Button("📦 Cenário exemplo", id="btn-exemplo", n_clicks=0, style={"marginLeft": "8px"}, className="btn"),
                ]),
            ],
        ),

        # ---- Ações ----
        html.Div(
            style={"display": "flex", "gap": "8px", "marginBottom": "8px", "flexWrap": "wrap"},
            children=[
                html.Button("🧹 Limpar fila", id="btn-limpar", n_clicks=0, className="btn"),
                html.Button("🧮 Ordenar (Merge Sort)", id="btn-ordenar", n_clicks=0, className="btn"),
                html.Div(id="metrics-box", style={"marginLeft": "auto", "fontSize": 14, "color": "#333"}),
            ],
        ),

        # ---- Painéis ----
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px"},
            children=[
                html.Div([
                    html.H3("Fila atual (antes)"),
                    tabela_formatada("tbl-antes"),
                ], style=card_style()),
                html.Div([
                    html.H3("Fila ordenada (depois)"),
                    tabela_formatada("tbl-depois"),
                ], style=card_style()),
            ],
        ),

        html.Footer(
            "Regra: triagem ASC → chegada ASC → idade DESC • Estabilidade garantida por Merge Sort",
            style={"marginTop": "16px", "color": "#666", "fontSize": 12},
        ),

        # CSS inline simples
        html.Div(
            style={"marginTop": "12px"},
            children=[
                html.P(" ", style={"display": "none"}),  # placeholder invisível
            ],
        ),
    ],
)

# ============================
# Callbacks
# ============================

@app.callback(
    Output("store-pacientes", "data"),
    Output("in-nome", "value"),
    Output("in-idade", "value"),
    Input("btn-add", "n_clicks"),
    State("in-nome", "value"),
    State("in-idade", "value"),
    State("in-triagem", "value"),
    State("store-pacientes", "data"),
    prevent_initial_call=True,
)
def add_paciente(n, nome, idade, triagem, store):
    if not n or not nome or idade is None:
        return no_update, no_update, no_update
    lista = [Paciente(**p) for p in store["lista"]]
    seq = int(store.get("seq_chegada", 0)) + 1
    novo = Paciente(
        id=int(datetime.utcnow().timestamp() * 1000000) % 10**9,
        nome=nome.strip(),
        chegada=seq,
        idade=int(idade),
        triagem=int(triagem),
    )
    lista.append(novo)
    return {"lista": [asdict(p) for p in lista], "seq_chegada": seq}, "", None

@app.callback(
    Output("store-pacientes", "data", allow_duplicate=True),
    Input("btn-exemplo", "n_clicks"),
    prevent_initial_call=True,
)
def exemplo(n):
    if not n:
        return no_update
    exemplo_dados = [
        Paciente(1, "Ana", 1, 70, 1),
        Paciente(2, "Beto", 2, 30, 1),
        Paciente(3, "Caio", 3, 50, 0),
        Paciente(4, "Duda", 4, 65, 1),
        Paciente(5, "Eva", 5, 22, 2),
        Paciente(6, "Fábio", 6, 80, 1),
        Paciente(7, "Gabi", 7, 18, 2),
    ]
    seq = max(p.chegada for p in exemplo_dados)
    return {"lista": [asdict(p) for p in exemplo_dados], "seq_chegada": seq}

@app.callback(
    Output("store-pacientes", "data", allow_duplicate=True),
    Output("store-ordenado", "data"),
    Input("btn-limpar", "n_clicks"),
    prevent_initial_call=True,
)
def limpar(n):
    if not n:
        return no_update, no_update
    return {"lista": [], "seq_chegada": 0}, {"lista": [], "metrics": {}}

@app.callback(
    Output("store-ordenado", "data", allow_duplicate=True),
    Output("metrics-box", "children"),
    Input("btn-ordenar", "n_clicks"),
    State("store-pacientes", "data"),
    prevent_initial_call=True,
)
def ordenar(n, store):
    pacientes = [Paciente(**p) for p in store["lista"]]
    if not pacientes:
        return {"lista": [], "metrics": {}}, html.Span("Fila vazia.", style={"color": "#999"})
    ordenado, metrics = merge_sort_estavel(pacientes)
    metrics_txt = f"Algoritmo: {metrics['algoritmo']} • Comparações: {metrics['comparacoes']} • Tempo: {metrics['tempo_ms']} ms • Estável: {metrics['estavel']}"
    return {"lista": [asdict(p) for p in ordenado], "metrics": metrics}, metrics_txt

@app.callback(
    Output("tbl-antes", "data"),
    Output("tbl-antes", "style_data_conditional"),
    Input("store-pacientes", "data"),
)
def render_antes(store):
    pacientes = [Paciente(**p) for p in store["lista"]]
    df = pacientes_para_df(pacientes)
    return df.to_dict("records"), colorir_triagem(df)

@app.callback(
    Output("tbl-depois", "data"),
    Output("tbl-depois", "style_data_conditional"),
    Input("store-ordenado", "data"),
)
def render_depois(store_ord):
    pacientes = [Paciente(**p) for p in store_ord["lista"]]
    df = pacientes_para_df(pacientes)
    return df.to_dict("records"), colorir_triagem(df)

# ============================
# Main
# ============================
if __name__ == "__main__":
    app.run(
        debug=False,           # desliga o modo debug
        dev_tools_ui=False,    # some a barra "Errors/Callbacks/v3.x"
        dev_tools_hot_reload=False,
        dev_tools_props_check=False,
    )