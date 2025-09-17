# simulador_financiamento_animado.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -------------------------------
# CONFIGURAÇÃO GERAL
# -------------------------------
st.set_page_config(
    page_title="Simulação de Financiamento",
    page_icon="🏦",
    layout="wide",
)

# -------------------------------
# ESTILOS E CORES
# -------------------------------
SANTANDER_RED = "#EC0000"
PRIMARY_BLUE = "#004481"
TEXT_COLOR = "#212529"
SUBTLE_TEXT_COLOR = "#6c757d"
BACKGROUND_COLOR = "#f8f9fa"
BORDER_COLOR = "#dee2e6"
COMPONENT_BACKGROUND = "#ffffff"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');
    
    html, body, [class*="st-"] {{ font-family: 'Open Sans', sans-serif; }}
    .stApp {{ background-color: {BACKGROUND_COLOR}; color: {TEXT_COLOR}; }}

    /* --- Cards de Resultado com Animação --- */
    .result-card {{
        background-color: {COMPONENT_BACKGROUND};
        border-radius: 0.5rem;
        padding: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        border-top: 4px solid {SANTANDER_RED}; /* Borda vermelha de destaque */
        height: 100%;
    }}
    .card-title {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {TEXT_COLOR};
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        position: relative;
    }}
    /* --- Animação da Linha no Título --- */
    .card-title::after {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 0%;
        height: 3px;
        background-color: {SANTANDER_RED};
        transition: width 0.4s ease-in-out;
    }}
    .result-card:hover .card-title::after {{
        width: 100%;
    }}
    
    /* --- Tabela de Métricas --- */
    .metric-table {{ width: 100%; }}
    .metric-row {{ display: flex; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid #f0f0f0; }}
    .metric-label {{ color: {SUBTLE_TEXT_COLOR}; font-size: 0.9rem; }}
    .metric-value {{ font-weight: 600; color: {TEXT_COLOR}; font-size: 0.95rem; }}
    </style>
    """, unsafe_allow_html=True)

# -------------------------------
# FUNÇÕES DE CÁLCULO (Inalteradas)
# -------------------------------
@st.cache_data
def calcular_financiamento(tipo_calculo, valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra_mensal=0.0):
    if valor_financiado <= 0 or prazo_meses <= 0: return pd.DataFrame()
    saldo_devedor, amortizacao_base = valor_financiado, valor_financiado / prazo_meses
    dados, prazo_restante = [], prazo_meses
    for mes in range(1, prazo_meses * 2):
        if saldo_devedor < 0.01 or prazo_restante <= 0: break
        amortizacao = amortizacao_base if tipo_calculo == 'prazo' else saldo_devedor / prazo_restante
        juros, seguro, taxa_admin = saldo_devedor * taxa_juros_mes, saldo_devedor * 0.0004, 25.0
        amortizacao_total = amortizacao + amortizacao_extra_mensal
        prestacao_total = juros + amortizacao_total + seguro + taxa_admin
        saldo_devedor -= amortizacao_total
        if saldo_devedor < 0:
            amortizacao_total += saldo_devedor; prestacao_total += saldo_devedor; saldo_devedor = 0
        dados.append({"Mês": mes, "Prestação_Total": prestacao_total, "Juros": juros, "Amortização": amortizacao_total, "Saldo_Devedor": saldo_devedor, "Taxas/Seguro": seguro + taxa_admin})
        prazo_restante -= 1
        if tipo_calculo == 'prazo' and amortizacao_extra_mensal > 0 and saldo_devedor < 0.01: break
    return pd.DataFrame(dados)

# -------------------------------
# PÁGINA PRINCIPAL
# -------------------------------
st.title("Simulação de Financiamento")

# --- Seção de Parâmetros (Sempre Visível) ---
param_col1, param_col2, param_col3 = st.columns(3)
with param_col1:
    valor_financiado_input = st.number_input("Valor do Empréstimo", value=500000.0, format="%.2f")
    taxa_juros_input = st.number_input("Taxa de Juros Anual (%)", value=9.93, format="%.2f")
with param_col2:
    num_parcelas_input = st.number_input("Nº de Parcelas", value=360, step=12)
    data_inicio_input = st.date_input("Início do Financiamento", value=datetime(2025, 9, 16))
with param_col3:
    amortizacao_extra = st.number_input("Valor Extra Mensal (R$)", value=0.0, format="%.2f")
    tipo_amortizacao = st.radio("Objetivo da Amortização:", ("Reduzir prazo", "Reduzir parcela"), horizontal=True)

# --- Cálculos ---
prazo_meses, taxa_juros_mes = int(num_parcelas_input), (1 + taxa_juros_input / 100) ** (1/12) - 1
df_sem_extra = calcular_financiamento('prazo', valor_financiado_input, taxa_juros_mes, prazo_meses, 0.0)
df_com_extra = pd.DataFrame()
if amortizacao_extra > 0:
    tipo = 'prazo' if tipo_amortizacao == "Reduzir prazo" else 'parcela'
    df_com_extra = calcular_financiamento(tipo, valor_financiado_input, taxa_juros_mes, prazo_meses, amortizacao_extra)

# --- Seção de Resultados ---
st.markdown("---")
col_sem, col_com = st.columns(2)

def gerar_tabela_html(dataframe, valor_financiado, taxa_juros, data_inicio):
    total_pagar, total_juros = dataframe["Prestação_Total"].sum(), dataframe["Juros"].sum()
    data_ultima = data_inicio + timedelta(days=30.4375 * len(dataframe))
    dados = [("Valor financiado", f"R$ {valor_financiado:,.2f}"), ("Total a ser pago", f"R$ {total_pagar:,.2f}"),
             ("Total de juros", f"R$ {total_juros:,.2f}"), ("Taxa de juros", f"{taxa_juros:.2f}% (a.a)"),
             ("Quantidade de parcelas", len(dataframe)), ("Primeira parcela", f"R$ {dataframe.iloc[0]['Prestação_Total']:,.2f}"),
             ("Última parcela", f"R$ {dataframe.iloc[-1]['Prestação_Total']:,.2f}"), ("Data da última parcela", data_ultima.strftime('%B de %Y'))]
    html = "".join([f"<div class='metric-row'><span class='metric-label'>{l}</span><span class='metric-value'>{v}</span></div>" for l, v in dados])
    return f"<div class='metric-table'>{html}</div>"

def criar_grafico_pizza(dataframe):
    if dataframe.empty: return go.Figure()
    labels = ['Principal', 'Juros', 'Taxas/Seguro']; values = [dataframe['Amortização'].sum(), dataframe['Juros'].sum(), dataframe['Taxas/Seguro'].sum()]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker_colors=[PRIMARY_BLUE, SANTANDER_RED, BORDER_COLOR])])
    fig.update_layout(height=300, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)')
    return fig

with col_sem:
    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
    st.markdown("<p class='card-title'>Cenário Padrão</p>", unsafe_allow_html=True)
    if not df_sem_extra.empty:
        st.markdown(gerar_tabela_html(df_sem_extra, valor_financiado_input, taxa_juros_input, data_inicio_input), unsafe_allow_html=True)
        with st.container():
             st.plotly_chart(criar_grafico_pizza(df_sem_extra), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_com:
    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
    st.markdown("<p class='card-title'>Cenário com Amortização Extra</p>", unsafe_allow_html=True)
    if not df_com_extra.empty:
        st.markdown(gerar_tabela_html(df_com_extra, valor_financiado_input, taxa_juros_input, data_inicio_input), unsafe_allow_html=True)
        with st.container():
            st.plotly_chart(criar_grafico_pizza(df_com_extra), use_container_width=True)
    else:
        st.info("Insira um valor de amortização extra para ver a comparação.")
    st.markdown("</div>", unsafe_allow_html=True)
