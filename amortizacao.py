# simulador_financiamento_final_no_sidebar.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from contextlib import contextmanager

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
PRIMARY_BLUE = "#0d6efd"
SANTANDER_RED = "#EC0000"
TEXT_COLOR = "#212529"
SUBTLE_TEXT_COLOR = "#6c757d"
BACKGROUND_COLOR = "#f8f9fa"
BORDER_COLOR = "#dee2e6"
COMPONENT_BACKGROUND = "#ffffff"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');
    
    html, body, [class*="st-"] {{
        font-family: 'Open Sans', sans-serif;
    }}
    .stApp {{
        background-color: {BACKGROUND_COLOR};
        color: {TEXT_COLOR};
    }}
    /* --- Contêineres (Cards) --- */
    .card {{
        background-color: {COMPONENT_BACKGROUND};
        border-radius: 0.5rem;
        padding: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
        height: 100%;
    }}
    .card-title {{
        font-size: 1.25rem;
        font-weight: 600;
        color: {TEXT_COLOR};
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid {BORDER_COLOR};
    }}
    /* --- Tabela de Métricas de Resultado --- */
    .metric-table {{
        width: 100%;
        margin-bottom: 2rem;
    }}
    .metric-row {{
        display: flex;
        justify-content: space-between;
        padding: 0.75rem 0;
        border-bottom: 1px solid #f0f0f0;
    }}
    .metric-label {{
        color: {SUBTLE_TEXT_COLOR};
        font-size: 0.9rem;
    }}
    .metric-value {{
        font-weight: 600;
        color: {TEXT_COLOR};
        font-size: 0.95rem;
    }}
    </style>
    """, unsafe_allow_html=True)

# -------------------------------
# FUNÇÃO AUXILIAR PARA CRIAR CONTAINERS ESTILIZADOS
@contextmanager
def styled_container(class_name: str):
    st.markdown(f"<div class='{class_name}'>", unsafe_allow_html=True)
    yield
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------
# FUNÇÕES DE CÁLCULO
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
# FUNÇÕES DE CRIAÇÃO DE GRÁFICOS (PLOTLY)
# -------------------------------
def criar_grafico_pizza(dataframe):
    if dataframe.empty: return go.Figure()
    labels = ['Principal', 'Juros', 'Taxas/Seguro']; values = [dataframe['Amortização'].sum(), dataframe['Juros'].sum(), dataframe['Taxas/Seguro'].sum()]
    colors = [PRIMARY_BLUE, SANTANDER_RED, '#6c757d']
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker_colors=colors, hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>")])
    fig.update_layout(height=300, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

def criar_grafico_barras(dataframe):
    if dataframe.empty: return go.Figure()
    df_view = dataframe[dataframe['Mês'] <= 36]
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Amortização', x=df_view['Mês'], y=df_view['Amortização'], marker_color=PRIMARY_BLUE))
    fig.add_trace(go.Bar(name='Juros', x=df_view['Mês'], y=df_view['Juros'], marker_color=SANTANDER_RED))
    fig.add_trace(go.Bar(name='Taxas/Seguro', x=df_view['Mês'], y=df_view['Taxas/Seguro'], marker_color='#6c757d'))
    fig.update_layout(barmode='stack', height=300, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20), xaxis=dict(showgrid=False, title=''), yaxis=dict(showgrid=False, title=''))
    return fig

def criar_grafico_linha(dataframe):
    if dataframe.empty: return go.Figure()
    df_view = dataframe[dataframe['Mês'] <= 36]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_view['Mês'], y=df_view['Prestação_Total'], name='Parcela', mode='lines+markers', line=dict(color=PRIMARY_BLUE)))
    fig.add_trace(go.Scatter(x=df_view['Mês'], y=df_view['Amortização'], name='Amortização mensal', mode='lines+markers', line=dict(color=SANTANDER_RED)))
    fig.update_layout(height=300, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20), xaxis=dict(showgrid=False, title=''), yaxis=dict(showgrid=False, title=''))
    return fig

# -------------------------------
# PÁGINA PRINCIPAL
# -------------------------------
st.title("Simulação de Financiamento")

if st.toggle("Mostrar/Ocultar Parâmetros de Simulação", value=True):
    with styled_container("card"):
        param_col1, param_col2, param_col3 = st.columns(3)
        with param_col1:
            valor_financiado_input = st.number_input("Valor do Empréstimo", value=500000.0, format="%.2f")
            taxa_juros_input = st.number_input("Taxa de Juros Anual (%)", value=9.93, format="%.2f")
        with param_col2:
            num_parcelas_input = st.number_input("Nº de Parcelas", value=360, step=12)
            data_inicio_input = st.date_input("Início do Financiamento", value=datetime(2025, 9, 1))
        with param_col3:
            amortizacao_extra = st.number_input("Valor Extra Mensal (R$)", value=0.0, format="%.2f")
            tipo_amortizacao = st.radio("Objetivo da Amortização:", ("Reduzir prazo", "Reduzir parcela"), horizontal=True)

prazo_meses, taxa_juros_mes = int(num_parcelas_input), (1 + taxa_juros_input / 100) ** (1/12) - 1
df_sem_extra = calcular_financiamento('prazo', valor_financiado_input, taxa_juros_mes, prazo_meses, 0.0)
df_com_extra = pd.DataFrame()
if amortizacao_extra > 0:
    tipo = 'prazo' if tipo_amortizacao == "Reduzir prazo" else 'parcela'
    df_com_extra = calcular_financiamento(tipo, valor_financiado_input, taxa_juros_mes, prazo_meses, amortizacao_extra)

st.markdown("---")
st.header("Análise Comparativa")

col_sem, col_com = st.columns(2)

def gerar_tabela_html(dataframe, valor_financiado, taxa_juros, data_inicio):
    total_pagar, total_juros, total_taxas = dataframe["Prestação_Total"].sum(), dataframe["Juros"].sum(), dataframe["Taxas/Seguro"].sum()
    data_ultima = data_inicio + timedelta(days=30.4375 * len(dataframe))
    dados = [
        ("Valor financiado", f"R$ {valor_financiado:,.2f}"), ("Total a ser pago", f"R$ {total_pagar:,.2f}"),
        ("Total amortizado", "--"), ("Total de juros", f"R$ {total_juros:,.2f}"),
        ("Total de taxas/seguros", f"R$ {total_taxas:,.2f}"), ("Correção", "R$ 0,00"),
        ("Taxa de juros", f"{taxa_juros:.2f}% (a.a)"), ("Quantidade de parcelas", len(dataframe)),
        ("Valor da primeira parcela", f"R$ {dataframe.iloc[0]['Prestação_Total']:,.2f}"),
        ("Valor da última parcela", f"R$ {dataframe.iloc[-1]['Prestação_Total']:,.2f}"),
        ("Data da última parcela", data_ultima.strftime('%B de %Y')), ("Sistema de amortização", "SAC")]
    html = "".join([f"<div class='metric-row'><span class='metric-label'>{l}</span><span class='metric-value'>{v}</span></div>" for l, v in dados])
    return f"<div class='metric-table'>{html}</div>"

with col_sem:
    with styled_container("card"):
        st.markdown("<p class='card-title'>Sem amortização extra</p>", unsafe_allow_html=True)
        if not df_sem_extra.empty:
            st.markdown(gerar_tabela_html(df_sem_extra, valor_financiado_input, taxa_juros_input, data_inicio_input), unsafe_allow_html=True)
            st.plotly_chart(criar_grafico_pizza(df_sem_extra), use_container_width=True)
            st.markdown("<p class='card-title' style='text-align:center; border:none; margin-top: 1rem;'>Composição das parcelas</p>", unsafe_allow_html=True)
            st.plotly_chart(criar_grafico_barras(df_sem_extra), use_container_width=True)
            st.plotly_chart(criar_grafico_linha(df_sem_extra), use_container_width=True)

with col_com:
    with styled_container("card"):
        st.markdown("<p class='card-title'>Com amortização extra</p>", unsafe_allow_html=True)
        if not df_com_extra.empty:
            st.markdown(gerar_tabela_html(df_com_extra, valor_financiado_input, taxa_juros_input, data_inicio_input), unsafe_allow_html=True)
            st.plotly_chart(criar_grafico_pizza(df_com_extra), use_container_width=True)
            st.markdown("<p class='card-title' style='text-align:center; border:none; margin-top: 1rem;'>Composição das parcelas</p>", unsafe_allow_html=True)
            st.plotly_chart(criar_grafico_barras(df_com_extra), use_container_width=True)
            st.plotly_chart(criar_grafico_linha(df_com_extra), use_container_width=True)
        else:
            st.info("Insira um valor de amortização extra para ver a comparação.")
