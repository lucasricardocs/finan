# simulador_financiamento_final_corrigido.py
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
SUCCESS_GREEN = "#198754"
TEXT_COLOR = "#212529"
SUBTLE_TEXT_COLOR = "#6c757d"
BACKGROUND_COLOR = "#f8f9fa"
BORDER_COLOR = "#dee2e6"
COMPONENT_BACKGROUND = "#ffffff"
LIGHT_BLUE = "#e3f2fd"
SHADOW_COLOR = "rgba(0,0,0,0.08)"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="st-"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    .stApp {{
        background: linear-gradient(135deg, {BACKGROUND_COLOR} 0%, #e8f4fd 100%);
        color: {TEXT_COLOR};
    }}
    
    /* --- CORREÇÃO DO ÍCONE DO EXPANSÍVEL --- */
    [data-testid="stExpander"] {{
        border: 1px solid {BORDER_COLOR};
        border-radius: 12px;
        box-shadow: 0 2px 8px {SHADOW_COLOR};
        background: {COMPONENT_BACKGROUND};
        margin-bottom: 1.5rem;
    }}
    
    [data-testid="stExpander"] summary {{
        position: relative;
        padding: 1.5rem 2rem;
        background: linear-gradient(135deg, {PRIMARY_BLUE} 0%, #4dabf7 100%);
        color: white;
        font-weight: 600;
        font-size: 1.1rem;
        border-radius: 12px 12px 0 0;
        margin: -1px -1px 0 -1px;
    }}
    
    [data-testid="stExpander"][open] > summary {{
        border-radius: 12px 12px 0 0;
    }}
    
    /* Esconde todos os ícones padrão do Streamlit */
    [data-testid="stExpander"] summary svg {{
        display: none !important;
    }}
    
    [data-testid="stExpander"] summary span[data-testid] {{
        display: none !important;
    }}
    
    /* Remove classes específicas que causam problemas */
    [data-testid="stExpander"] summary .st-emotion-cache-1282ie9,
    [data-testid="stExpander"] summary .st-emotion-cache-g85b5l,
    [data-testid="stExpander"] summary [class*="st-emotion-cache"],
    [data-testid="stExpander"] summary [class*="keyboard_arrow"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    
    /* Cria nosso próprio ícone */
    [data-testid="stExpander"] summary::before {{
        content: '⚙️ ';
        font-size: 18px;
    }}
    
    [data-testid="stExpander"] summary::after {{
        content: '▼';
        font-size: 16px;
        position: absolute;
        right: 1.5rem;
        top: 50%;
        transform: translateY(-50%) rotate(-90deg);
        transition: transform 0.3s ease;
    }}
    
    [data-testid="stExpander"][open] > summary::after {{
        transform: translateY(-50%) rotate(0deg);
    }}

    /* --- Contêineres (Cards) --- */
    .card {{
        background: {COMPONENT_BACKGROUND};
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 8px 32px {SHADOW_COLOR};
        margin-bottom: 2rem;
        height: 100%;
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }}
    
    .card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, {PRIMARY_BLUE} 0%, {SUCCESS_GREEN} 50%, {SANTANDER_RED} 100%);
    }}
    
    .card-title {{
        font-size: 1.4rem;
        font-weight: 700;
        color: {TEXT_COLOR};
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid {LIGHT_BLUE};
        position: relative;
    }}
    
    .card-title::after {{
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 60px;
        height: 2px;
        background: {PRIMARY_BLUE};
    }}
    
    .param-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1.5rem;
        margin-top: 1rem;
    }}
    
    .param-box {{
        padding: 1.5rem;
        border: 1px solid {BORDER_COLOR};
        border-radius: 12px;
        text-align: center;
        background: linear-gradient(135deg, {COMPONENT_BACKGROUND} 0%, {LIGHT_BLUE} 100%);
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(13, 110, 253, 0.1);
    }}
    
    .param-box:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(13, 110, 253, 0.15);
    }}
    
    .param-label {{
        font-size: 0.9rem;
        color: {SUBTLE_TEXT_COLOR};
        font-weight: 500;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .param-value {{
        font-size: 1.2rem;
        font-weight: 700;
        color: {PRIMARY_BLUE};
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }}
    
    .metric-table {{
        width: 100%;
        margin-bottom: 2rem;
        background: {LIGHT_BLUE};
        border-radius: 12px;
        padding: 1.5rem;
    }}
    
    .metric-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid rgba(13, 110, 253, 0.1);
        transition: background-color 0.2s ease;
    }}
    
    .metric-row:hover {{
        background-color: rgba(13, 110, 253, 0.05);
        border-radius: 8px;
        margin: 0 -0.5rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }}
    
    .metric-row:last-child {{
        border-bottom: none;
    }}
    
    .metric-label {{
        color: {SUBTLE_TEXT_COLOR};
        font-size: 0.95rem;
        font-weight: 500;
    }}
    
    .metric-value {{
        font-weight: 700;
        color: {TEXT_COLOR};
        font-size: 1rem;
    }}
    
    /* Melhorando inputs do Streamlit */
    .stNumberInput > div > div > input {{
        border-radius: 8px;
        border: 2px solid {BORDER_COLOR};
        padding: 12px 16px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }}
    
    .stNumberInput > div > div > input:focus {{
        border-color: {PRIMARY_BLUE};
        box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.1);
    }}
    
    .stDateInput > div > div > input {{
        border-radius: 8px;
        border: 2px solid {BORDER_COLOR};
        padding: 12px 16px;
        transition: all 0.3s ease;
    }}
    
    .stDateInput > div > div > input:focus {{
        border-color: {PRIMARY_BLUE};
        box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.1);
    }}
    
    .stRadio > div {{
        background: {LIGHT_BLUE};
        border-radius: 12px;
        padding: 1rem;
    }}
    
    /* Título principal */
    h1 {{
        background: linear-gradient(135deg, {PRIMARY_BLUE} 0%, {SUCCESS_GREEN} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }}
    
    /* Melhorando as colunas */
    .stColumn > div {{
        padding: 0 0.75rem;
    }}
    
    /* Info box styling */
    .stInfo {{
        background: linear-gradient(135deg, {LIGHT_BLUE} 0%, rgba(13, 110, 253, 0.1) 100%);
        border: 1px solid {PRIMARY_BLUE};
        border-radius: 12px;
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
# FUNÇÕES DE CRIAÇÃO DE GRÁFICOS (PLOTLY) - MELHORADAS
# -------------------------------
def criar_grafico_pizza(dataframe):
    if dataframe.empty: return go.Figure()
    
    labels = ['Principal', 'Juros', 'Taxas/Seguro']
    values = [dataframe['Amortização'].sum(), dataframe['Juros'].sum(), dataframe['Taxas/Seguro'].sum()]
    colors = [PRIMARY_BLUE, SANTANDER_RED, '#aaaaaa']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.5, 
        marker=dict(
            colors=colors,
            line=dict(color='white', width=2)  # strokewidth=2
        ),
        hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>"
    )])
    
    fig.update_layout(
        height=300, 
        showlegend=True, 
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="center", 
            x=0.5,
            font=dict(size=12)
        ), 
        margin=dict(l=20, r=20, t=20, b=20), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def criar_grafico_barras(dataframe):
    if dataframe.empty: 
        return go.Figure()
    
    df_view = dataframe[dataframe['Mês'] <= 36]
    
    if df_view.empty:
        return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Amortização', x=df_view['Mês'], y=df_view['Amortização'], marker_color=PRIMARY_BLUE))
    fig.add_trace(go.Bar(name='Juros', x=df_view['Mês'], y=df_view['Juros'], marker_color=SANTANDER_RED))
    fig.add_trace(go.Bar(name='Taxas/Seguro', x=df_view['Mês'], y=df_view['Taxas/Seguro'], marker_color='#aaaaaa'))
    
    fig.update_layout(
        barmode='stack', 
        height=300, 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=20, t=20, b=20), 
        xaxis=dict(showgrid=False, title=''), 
        yaxis=dict(showgrid=False, title='')
    )
    return fig

def criar_grafico_linha(dataframe):
    if dataframe.empty: 
        return go.Figure()
    
    df_view = dataframe[dataframe['Mês'] <= 36]
    
    if df_view.empty:
        return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_view['Mês'], y=df_view['Prestação_Total'], name='Parcela', mode='lines', line=dict(color=PRIMARY_BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=df_view['Mês'], y=df_view['Amortização'], name='Amortização mensal', mode='lines', line=dict(color=SANTANDER_RED, width=2.5)))
    
    fig.update_layout(
        height=300, 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=20, t=20, b=20), 
        xaxis=dict(showgrid=False, title=''), 
        yaxis=dict(showgrid=False, title='')
    )
    return fig

# -------------------------------
# PÁGINA PRINCIPAL
# -------------------------------
st.title("🏦 Simulação de Financiamento")

with st.expander("Configurar Parâmetros da Simulação", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        valor_imovel_input = st.number_input("💰 Valor do Imóvel", value=625000.0, format="%.2f")
        entrada_input = st.number_input("💵 Valor da Entrada", value=125000.0, format="%.2f")
        taxa_juros_input = st.number_input("📈 Taxa de Juros Anual (%)", value=9.93, format="%.2f")
    with col2:
        num_parcelas_input = st.number_input("📅 Nº de Parcelas", value=360, step=12)
        data_inicio_input = st.date_input("🗓️ Início do Financiamento", value=datetime(2025, 9, 16))
    with col3:
        amortizacao_extra = st.number_input("💪 Valor Extra Mensal (R$)", value=500.0, format="%.2f")
        tipo_amortizacao = st.radio("🎯 Objetivo da Amortização:", ("Reduzir prazo", "Reduzir parcela"), horizontal=True)

    # Botão para executar simulação
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 **SIMULAR FINANCIAMENTO**", type="primary", use_container_width=True):
            st.session_state.simular = True

# --- Cálculos (só executa após clicar no botão) ---
if 'simular' in st.session_state and st.session_state.simular:
    valor_financiado_input = valor_imovel_input - entrada_input
    prazo_meses, taxa_juros_mes = int(num_parcelas_input), (1 + taxa_juros_input / 100) ** (1/12) - 1
    df_sem_extra = calcular_financiamento('prazo', valor_financiado_input, taxa_juros_mes, prazo_meses, 0.0)
    df_com_extra = pd.DataFrame()
    if amortizacao_extra > 0:
        tipo = 'prazo' if tipo_amortizacao == "Reduzir prazo" else 'parcela'
        df_com_extra = calcular_financiamento(tipo, valor_financiado_input, taxa_juros_mes, prazo_meses, amortizacao_extra)
else:
    df_sem_extra = pd.DataFrame()
    df_com_extra = pd.DataFrame()
    valor_financiado_input = valor_imovel_input - entrada_input

# --- Seção de Display dos Parâmetros ---
if 'simular' in st.session_state and st.session_state.simular:
    with styled_container("card"):
        st.markdown("<p class='card-title'>📊 Parâmetros de Financiamento</p>", unsafe_allow_html=True)
        st.markdown("<div class='param-grid'>"
                    f"<div class='param-box'><p class='param-label'>Empréstimo</p><p class='param-value'>R$ {valor_financiado_input:,.2f}</p></div>"
                    f"<div class='param-box'><p class='param-label'>Início</p><p class='param-value'>{data_inicio_input.strftime('%B de %Y')}</p></div>"
                    f"<div class='param-box'><p class='param-label'>Tabela</p><p class='param-value'>SAC</p></div>"
                    f"<div class='param-box'><p class='param-label'>Taxa de juros</p><p class='param-value'>{taxa_juros_input:.2f}%</p></div>"
                    f"<div class='param-box'><p class='param-label'>Juros</p><p class='param-value'>a.a</p></div>"
                    f"<div class='param-box'><p class='param-label'>Nº de parcelas</p><p class='param-value'>{num_parcelas_input}</p></div>"
                    "</div>", unsafe_allow_html=True)

# --- Seção de Resultados ---
if 'simular' in st.session_state and st.session_state.simular:
    col_sem, col_com = st.columns(2)

    def gerar_tabela_html(dataframe, valor_financiado, taxa_juros, data_inicio):
        total_pagar, total_juros, total_taxas = dataframe["Prestação_Total"].sum(), dataframe["Juros"].sum(), dataframe["Taxas/Seguro"].sum()
        data_ultima = data_inicio + timedelta(days=30.4375 * len(dataframe))
        dados = [
            ("Valor financiado", f"R$ {valor_financiado:,.2f}"), 
            ("Total a ser pago", f"R$ {total_pagar:,.2f}"),
            ("Total amortizado", "--"),
            ("Total de juros", f"R$ {total_juros:,.2f}"),
            ("Total de taxas/seguros", f"R$ {total_taxas:,.2f}"),
            ("Correção", "R$ 0,00"),
            ("Taxa de juros", f"{taxa_juros:.2f}% (a.a)"),
            ("Quantidade de parcelas", len(dataframe)),
            ("Valor da primeira parcela", f"R$ {dataframe.iloc[0]['Prestação_Total']:,.2f}"),
            ("Valor da última parcela", f"R$ {dataframe.iloc[-1]['Prestação_Total']:,.2f}"),
            ("Data da última parcela", data_ultima.strftime('%B de %Y')),
            ("Sistema de amortização", "SAC")
        ]
        html = "".join([f"<div class='metric-row'><span class='metric-label'>{l}</span><span class='metric-value'>{v}</span></div>" for l,v in dados])
        return f"<div class='metric-table'>{html}</div>"

    with col_sem:
        with styled_container("card"):
            st.markdown("<p class='card-title'>📋 Sem Amortização Extra</p>", unsafe_allow_html=True)
            if not df_sem_extra.empty:
                st.markdown(gerar_tabela_html(df_sem_extra, valor_financiado_input, taxa_juros_input, data_inicio_input), unsafe_allow_html=True)
                st.plotly_chart(criar_grafico_pizza(df_sem_extra), use_container_width=True)
                st.markdown("<p class='card-title' style='text-align:center; border:none; margin-top: 1rem;'>Composição das parcelas</p>", unsafe_allow_html=True)
                st.plotly_chart(criar_grafico_barras(df_sem_extra), use_container_width=True)
                st.plotly_chart(criar_grafico_linha(df_sem_extra), use_container_width=True)

    with col_com:
        with styled_container("card"):
            st.markdown("<p class='card-title'>🚀 Com Amortização Extra</p>", unsafe_allow_html=True)
            if not df_com_extra.empty:
                st.markdown(gerar_tabela_html(df_com_extra, valor_financiado_input, taxa_juros_input, data_inicio_input), unsafe_allow_html=True)
                st.plotly_chart(criar_grafico_pizza(df_com_extra), use_container_width=True)
                st.markdown("<p class='card-title' style='text-align:center; border:none; margin-top: 1rem;'>Composição das parcelas</p>", unsafe_allow_html=True)
                st.plotly_chart(criar_grafico_barras(df_com_extra), use_container_width=True)
                st.plotly_chart(criar_grafico_linha(df_com_extra), use_container_width=True)
            else:
                st.info("💡 Insira um valor de amortização extra para ver a comparação detalhada!")
