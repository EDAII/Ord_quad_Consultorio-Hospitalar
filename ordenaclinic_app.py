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
    meses: int = 0
    # Prioridade legal (Lei de atendimento prioritário)
    deficiencia: bool = False
    gestante: bool = False
    lactante: bool = False
    crianca_colo: bool = False
    obesidade: bool = False

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

def chave_padrao(p: Paciente) -> Tuple[int, int, int, int]:
    """
    Chave de ordenação padrão (usada pelo Merge Sort).

    Ordem (importante):
      1) triagem (ASC) - prioridades clínicas (0=Vermelho, 1=Amarelo) sempre vêm primeiro
      2) prioridade legal (ASC) - em triagens não urgentes, grupos prioritários vêm antes (0=prioritário, 1=não)
      3) chegada (ASC) - quem chegou primeiro
      4) idade (DESC) - desempate por idade (pessoas mais velhas primeiro)

    Observação: a prioridade legal não sobrescreve casos de emergência/urgência porque triagem tem precedência.
    """
    # determina se o paciente pertence a grupo prioritário pela legislação
    total_months = (p.idade * 12) + int(getattr(p, "meses", 0))
    possui_prioridade = (
        p.deficiencia or p.gestante or p.lactante or p.crianca_colo or p.obesidade or (p.idade >= 60)
    )
    # prioridade_flag: 0 para prioritário (vem antes), 1 para não prioritário
    prioridade_flag = 0 if possui_prioridade else 1

    # Em qualquer caso, triagem continua sendo o primeiro critério. A prioridade legal só afeta
    # a ordenação entre pacientes com a mesma triagem (em especial, triagens não urgentes).
    # desempate por idade mais preciso: usar total de meses (maiores primeiro)
    return (p.triagem, prioridade_flag, p.chegada, -total_months)

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
        return pd.DataFrame(columns=["posição", "nome", "prioridade", "triagem_label", "chegada", "idade_label"])
    df = df.assign(
        triagem_label=df["triagem"].map(TRIAGEM_LABELS),
        triagem_cor=df["triagem"].map(TRIAGEM_CORES),
    )
    # construir rótulo de prioridade legal (concatena grupos quando presentes)
    def prioridade_label_row(row):
        labels = []
        if row.get("deficiencia"):
            labels.append("Deficiência")
        if row.get("gestante"):
            labels.append("Gestante")
        if row.get("lactante"):
            labels.append("Lactante")
        if row.get("crianca_colo"):
            labels.append("Criança de colo")
        if row.get("obesidade"):
            labels.append("Obesidade")
        # idoso é calculado a partir da idade (>=60)
        if row.get("idade") is not None and int(row.get("idade")) >= 60:
            labels.append("Idoso (60+)")
        return ", ".join(labels)

    df = df.assign(prioridade=df.apply(prioridade_label_row, axis=1))
    # formatar idade como "X anos Y meses"
    def idade_label_row(row):
        anos = int(row.get("idade", 0))
        meses = int(row.get("meses", 0) or 0)
        if anos <= 0 and meses > 0:
            return f"{meses} meses"
        if meses <= 0:
            return f"{anos} anos"
        return f"{anos} anos {meses} meses"
    df = df.assign(idade_label=df.apply(idade_label_row, axis=1))
    # organizar colunas: manter triagem numérica (para regras de estilo), mostrar triagem_label e prioridade
    df = df[["nome", "prioridade", "triagem", "triagem_label", "triagem_cor", "chegada", "idade_label"]]
    df.insert(0, "posição", range(1, len(df) + 1))
    return df

def tabela_formatada(id_table: str):
    return dash_table.DataTable(
        id=id_table,
        columns=[
            {"name": "Posição", "id": "posição"},
            {"name": "Nome", "id": "nome"},
            {"name": "Prioridade", "id": "prioridade"},
            {"name": "Triagem", "id": "triagem_label"},
            {"name": "Chegada", "id": "chegada"},
            {"name": "Idade", "id": "idade_label"},
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
                    html.Label("Idade (anos / meses)"),
                    html.Div([
                        dcc.Input(id="in-idade-anos", type="number", min=0, max=120, placeholder="Anos", style={"width": "48%", "marginRight": "4%"}),
                        dcc.Input(id="in-idade-meses", type="number", min=0, max=11, placeholder="Meses", style={"width": "48%"}),
                    ], style={"display": "flex"}),
                ]),
                html.Div([
                    html.Label("Triagem"),
                    dcc.Dropdown(id="in-triagem", options=triagem_options(), value=1, clearable=False),
                ]),
                html.Div([
                    html.Button("➕ Adicionar", id="btn-add", n_clicks=0, className="btn"),
                    html.Button("📦 Cenário exemplo", id="btn-exemplo", n_clicks=0, style={"marginLeft": "8px"}, className="btn"),
                    html.Span("", id="add-msg", style={"marginLeft": "12px", "color": "#c00"}),
                ]),
            ],
        ),

        # ---- Prioridades legais (checkboxes) ----
        html.Div(
            style={"display": "flex", "gap": "8px", "marginBottom": "14px", "flexWrap": "wrap"},
            children=[
                dcc.Checklist(
                    id="in-prioridades",
                    options=[
                        {"label": "Deficiência", "value": "deficiencia"},
                        {"label": "Gestante", "value": "gestante"},
                        {"label": "Lactante", "value": "lactante"},
                        {"label": "Criança de colo", "value": "crianca_colo"},
                        {"label": "Obesidade", "value": "obesidade"},
                    ],
                    value=[],
                    labelStyle={"marginRight": "12px"},
                )
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
    Output("in-idade-anos", "value"),
    Output("in-idade-meses", "value"),
    Input("btn-add", "n_clicks"),
    State("in-nome", "value"),
    State("in-idade-anos", "value"),
    State("in-idade-meses", "value"),
    State("in-triagem", "value"),
    State("in-prioridades", "value"),
    State("store-pacientes", "data"),
    prevent_initial_call=True,
)
def add_paciente(n, nome, idade_anos, idade_meses, triagem, prioridades, store):
    if not n or not nome or idade_anos is None:
        return no_update, no_update, no_update
    lista = [Paciente(**p) for p in store["lista"]]
    seq = int(store.get("seq_chegada", 0)) + 1
    flags = set(prioridades or [])
    idade_int = int(idade_anos)
    meses_int = int(idade_meses or 0)
    # regra: não permitir gestante e lactante se idade >= 60 (idoso)
    if idade_int >= 60 and "gestante" in flags:
        flags.discard("gestante")
    if idade_int >= 60 and "lactante" in flags:
        flags.discard("lactante")
    # regra: se for criança de colo, não pode ser gestante nem lactante
    if "crianca_colo" in flags:
        flags.discard("gestante")
        flags.discard("lactante")
    # regra: criança de colo permitida até 3 anos (<= 36 meses)
    if (idade_int * 12 + meses_int) > 36 and "crianca_colo" in flags:
        flags.discard("crianca_colo")

    novo = Paciente(
        id=int(datetime.utcnow().timestamp() * 1000000) % 10**9,
        nome=nome.strip(),
        chegada=seq,
        idade=idade_int,
        meses=meses_int,
        triagem=int(triagem),
        deficiencia="deficiencia" in flags,
        gestante="gestante" in flags,
        lactante="lactante" in flags,
        crianca_colo="crianca_colo" in flags,
        obesidade="obesidade" in flags,
    )
    lista.append(novo)
    return {"lista": [asdict(p) for p in lista], "seq_chegada": seq}, "", None, None

@app.callback(
    Output("store-pacientes", "data", allow_duplicate=True),
    Input("btn-exemplo", "n_clicks"),
    prevent_initial_call=True,
)
def exemplo(n):
    if not n:
        return no_update
    exemplo_dados = [
        Paciente(1, "Ana", 1, 70, 1, 0, deficiencia=False, gestante=False, lactante=False, crianca_colo=False, obesidade=False),
        Paciente(2, "Beto", 2, 30, 1, 0, deficiencia=False, gestante=False, lactante=False, crianca_colo=False, obesidade=True),
        Paciente(3, "Caio", 3, 50, 0, 0, deficiencia=False, gestante=False, lactante=False, crianca_colo=False, obesidade=False),
        Paciente(4, "Duda", 4, 65, 1, 0, deficiencia=False, gestante=False, lactante=False, crianca_colo=False, obesidade=False),
        Paciente(5, "Eva", 5, 22, 2, 0, deficiencia=False, gestante=False, lactante=True, crianca_colo=False, obesidade=False),
        Paciente(6, "Fábio", 6, 80, 1, 0, deficiencia=False, gestante=False, lactante=False, crianca_colo=False, obesidade=False),
        Paciente(7, "Gabi", 7, 1, 2, 0, deficiencia=False, gestante=False, lactante=False, crianca_colo=True, obesidade=False),
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


@app.callback(
    Output("in-prioridades", "options"),
    Output("in-prioridades", "value"),
    Input("in-idade-anos", "value"),
    Input("in-idade-meses", "value"),
    Input("in-prioridades", "value"),
)
def ajustar_prioridades_por_idade(idade_anos, idade_meses, current_vals):
    """Desabilita e desmarca opções inválidas conforme idade em anos/meses e seleção de prioridades.

    Regras adicionais:
    - Se 'crianca_colo' estiver marcada, então 'gestante' e 'lactante' são inválidas e serão removidas.
    """
    base = [
        {"label": "Deficiência", "value": "deficiencia"},
        {"label": "Gestante", "value": "gestante"},
        {"label": "Lactante", "value": "lactante"},
        {"label": "Criança de colo", "value": "crianca_colo"},
        {"label": "Obesidade", "value": "obesidade"},
    ]
    try:
        anos = int(idade_anos) if idade_anos is not None else None
        meses = int(idade_meses) if idade_meses is not None else 0
    except Exception:
        return base, current_vals or []

    if anos is None:
        return base, current_vals or []

    total_months = anos * 12 + meses

    # lógica para gestante/lactante/creche
    opts = []
    for o in base:
        val = o["value"]
        disabled = False
        # desabilitar gestante/lactante para idosos (>=60 anos)
        if anos >= 60 and val in ("gestante", "lactante"):
            disabled = True
        # desabilitar crianca_colo se total_months > 36 (permitimos até 36 meses)
        if val == "crianca_colo" and total_months > 36:
            disabled = True
        # se crianca_colo estiver marcada, gestante/lactante são inválidas
        if "crianca_colo" in (current_vals or []) and val in ("gestante", "lactante"):
            disabled = True
        opts.append({**o, "disabled": disabled} if disabled else o)
    vals = list(current_vals or [])
    # remover gestante/lactante se idosos ou se crianca_colo estiver selecionada
    if anos >= 60 or "crianca_colo" in (current_vals or []):
        vals = [v for v in vals if v not in ("gestante", "lactante")]
    # remover crianca_colo se > 36 meses
    if total_months > 36:
        vals = [v for v in vals if v != "crianca_colo"]
    return opts, vals


@app.callback(
    Output("btn-add", "disabled"),
    Output("add-msg", "children"),
    Input("in-nome", "value"),
    Input("in-idade-anos", "value"),
    Input("in-idade-meses", "value"),
)
def validar_form(nome, anos, meses):
    # Nome obrigatório
    if not nome or not str(nome).strip():
        return True, "Informe o nome do paciente"
    # anos must be integer >= 0
    try:
        anos_int = int(anos)
        if anos_int < 0:
            return True, "Idade inválida"
    except Exception:
        return True, "Informe a idade (anos)"
    # meses must be between 0 and 11
    if meses is None:
        meses_int = 0
    else:
        try:
            meses_int = int(meses)
        except Exception:
            return True, "Meses inválidos"
    if meses_int < 0 or meses_int > 11:
        return True, "Meses deve estar entre 0 e 11"
    # all good
    return False, ""

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