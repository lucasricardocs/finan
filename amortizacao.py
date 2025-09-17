import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -------------------------------
# CONFIGURAÇÃO GERAL
# -------------------------------
st.set_page_config(
    page_title="Simulação de Financiamento & Amortização",
    page_icon="🏦",
    layout="wide",
)

# -------------------------------
# FUNÇÃO DE FORMATAÇÃO DE MOEDA BRASILEIRA
# -------------------------------
def format_currency(value):
    """Formata valores como moeda brasileira (R$ 1.234,56)"""
    if pd.isna(value) or value == 0:
        return "R$ 0,00"
    try:
        value = float(value)
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# -------------------------------
# ESTILOS SIMPLIFICADOS
# -------------------------------
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-title {
        font-size: 6rem;
        font-weight: 700;
        color: #0d6efd;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-title {
        font-size: 6rem;
        font-weight: 600;
        color: #212529;
        margin-bottom: 1rem;
    }
    .param-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .param-box {
        padding: 1rem;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        text-align: center;
        background-color: white;
    }
    .param-label {
        font-size: 0.9rem;
        color: #6c757d;
        margin-bottom: 0.5rem;
    }
    .param-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0d6efd;
    }
    .metric-table {
        width: 100%;
        margin-bottom: 2rem;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        padding: 0.75rem 0;
        border-bottom: 1px solid #dee2e6;
    }
    .metric-row:last-child {
        border-bottom: none;
    }
    .metric-label {
        color: #6c757d;
    }
    .metric-value {
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

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
# FUNÇÕES DE CRIAÇÃO DE GRÁFICOS
# -------------------------------
def criar_grafico_pizza(dataframe):
    if dataframe.empty: return go.Figure()
    
    labels = ['Principal', 'Juros', 'Taxas/Seguro']
    values = [dataframe['Amortização'].sum(), dataframe['Juros'].sum(), dataframe['Taxas/Seguro'].sum()]
    colors = ['#0d6efd', '#EC0000', '#6c757d']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.5, 
        marker=dict(colors=colors),
        hovertemplate="<b>%{label}</b><br>%{value:,.2f} reais<br>%{percent}<extra></extra>"
    )])
    
    fig.update_layout(
        height=400,
        showlegend=True, 
        margin=dict(l=20, r=20, t=20, b=20), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def criar_grafico_barras(dataframe):
    if dataframe.empty: return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Amortização', x=dataframe['Mês'], y=dataframe['Amortização'], marker_color='#0d6efd',
                         hovertemplate='<b>Mês %{x}</b><br>Amortização: R$ %{y:,.2f}<extra></extra>'))
    fig.add_trace(go.Bar(name='Juros', x=dataframe['Mês'], y=dataframe['Juros'], marker_color='#EC0000',
                         hovertemplate='<b>Mês %{x}</b><br>Juros: R$ %{y:,.2f}<extra></extra>'))
    fig.add_trace(go.Bar(name='Taxas/Seguro', x=dataframe['Mês'], y=dataframe['Taxas/Seguro'], marker_color='#6c757d',
                         hovertemplate='<b>Mês %{x}</b><br>Taxas/Seguro: R$ %{y:,.2f}<extra></extra>'))
    
    fig.update_layout(
        barmode='stack', 
        height=400,
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=20, t=20, b=20), 
        xaxis=dict(title='Meses'), 
        yaxis=dict(title='Valor (R$)'),
        hovermode='x unified'
    )
    
    fig.update_yaxes(tickprefix='R$ ', tickformat=',.2f')
    
    return fig

def criar_grafico_linha(dataframe):
    if dataframe.empty: return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dataframe['Mês'], y=dataframe['Prestação_Total'], name='Parcela', mode='lines', 
                             line=dict(color='#0d6efd', width=2.5),
                             hovertemplate='<b>Mês %{x}</b><br>Parcela: R$ %{y:,.2f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=dataframe['Mês'], y=dataframe['Amortização'], name='Amortização', mode='lines', 
                             line=dict(color='#EC0000', width=2.5),
                             hovertemplate='<b>Mês %{x}</b><br>Amortização: R$ %{y:,.2f}<extra></extra>'))
    
    fig.update_layout(
        height=400,
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=20, t=20, b=20), 
        xaxis=dict(title='Meses'), 
        yaxis=dict(title='Valor (R$)')
    )
    
    fig.update_yaxes(tickprefix='R$ ', tickformat=',.2f')
    
    return fig

# -------------------------------
# PÁGINA PRINCIPAL
# -------------------------------
st.markdown('<p class="main-title">🏦 Simulação de Financiamento e Amortização</p>', unsafe_allow_html=True)

# Seção de parâmetros
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

    if st.button("🚀 **SIMULAR FINANCIAMENTO**", type="primary", use_container_width=True):
        st.session_state.simular = True

# Cálculos
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

# Seção de parâmetros de financiamento
st.markdown('<p class="section-title">📊 Parâmetros de Financiamento</p>', unsafe_allow_html=True)
st.markdown(f"""
<div class="param-grid">
    <div class="param-box"><p class="param-label">Empréstimo</p><p class="param-value">{format_currency(valor_financiado_input)}</p></div>
    <div class="param-box"><p class="param-label">Início</p><p class="param-value">{data_inicio_input.strftime('%B de %Y')}</p></div>
    <div class="param-box"><p class="param-label">Tabela</p><p class="param-value">SAC</p></div>
    <div class="param-box"><p class="param-label">Taxa de juros</p><p class="param-value">{taxa_juros_input:.2f}%</p></div>
    <div class="param-box"><p class="param-label">Juros</p><p class="param-value">a.a</p></div>
    <div class="param-box"><p class="param-label">Nº de parcelas</p><p class="param-value">{num_parcelas_input}</p></div>
</div>
""", unsafe_allow_html=True)

st.divider()

# Seção de resultados
if 'simular' in st.session_state and st.session_state.simular:
    col_sem, col_com = st.columns(2)

    def gerar_tabela_html(dataframe, valor_financiado, taxa_juros, data_inicio):
        total_pagar, total_juros, total_taxas = dataframe["Prestação_Total"].sum(), dataframe["Juros"].sum(), dataframe["Taxas/Seguro"].sum()
        data_ultima = data_inicio + timedelta(days=30.4375 * len(dataframe))
        total_amortizado = dataframe["Amortização"].sum()
        
        dados = [
            ("Valor financiado", format_currency(valor_financiado)), 
            ("Total a ser pago", format_currency(total_pagar)),
            ("Total amortizado", format_currency(total_amortizado)),
            ("Total de juros", format_currency(total_juros)),
            ("Total de taxas/seguros", format_currency(total_taxas)),
            ("Taxa de juros", f"{taxa_juros:.2f}% (a.a)"),
            ("Quantidade de parcelas", len(dataframe)),
            ("Valor da primeira parcela", format_currency(dataframe.iloc[0]['Prestação_Total'])),
            ("Valor da última parcela", format_currency(dataframe.iloc[-1]['Prestação_Total'])),
            ("Data da última parcela", data_ultima.strftime('%B de %Y')),
            ("Sistema de amortização", "SAC")
        ]
        html = "".join([f"<div class='metric-row'><span class='metric-label'>{l}</span><span class='metric-value'>{v}</span></div>" for l,v in dados])
        return f"<div class='metric-table'>{html}</div>"

    with col_sem:
        st.markdown('<p class="section-title">📋 Sem Amortização Extra</p>', unsafe_allow_html=True)
        if not df_sem_extra.empty:
            st.markdown(gerar_tabela_html(df_sem_extra, valor_financiado_input, taxa_juros_input, data_inicio_input), unsafe_allow_html=True)
            st.plotly_chart(criar_grafico_pizza(df_sem_extra), use_container_width=True)
            st.divider()
            st.plotly_chart(criar_grafico_barras(df_sem_extra), use_container_width=True)
            st.plotly_chart(criar_grafico_linha(df_sem_extra), use_container_width=True)

    with col_com:
        st.markdown('<p class="section-title">🚀 Com Amortização Extra</p>', unsafe_allow_html=True)
        if not df_com_extra.empty:
            st.markdown(gerar_tabela_html(df_com_extra, valor_financiado_input, taxa_juros_input, data_inicio_input), unsafe_allow_html=True)
            st.plotly_chart(criar_grafico_pizza(df_com_extra), use_container_width=True)
            st.divider()
            st.plotly_chart(criar_grafico_barras(df_com_extra), use_container_width=True)
            st.plotly_chart(criar_grafico_linha(df_com_extra), use_container_width=True)
        else:
            st.info("💡 Insira um valor de amortização extra para ver a comparação detalhada!")
