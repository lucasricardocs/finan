import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import random

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
# FRASES MOTIVADORAS PARA O RODAPÉ
# -------------------------------
frases_motivadoras = [
    "O sucesso é a soma de pequenos esforços repetidos dia após dia.",
    "Acredite em você mesmo e tudo será possível.",
    "O futuro pertence àqueles que acreditam na beleza de seus sonhos.",
    "Não espere por oportunidades, crie-as.",
    "A persistência é o caminho do êxito.",
    "Grandes conquistas requerem grandes ambições.",
    "O único lugar onde o sucesso vem antes do trabalho é no dicionário.",
    "Seja a mudança que você quer ver no mundo.",
    "A jornada de mil milhas começa com um único passo.",
    "Você é mais forte do que imagina e mais capaz do que acredita.",
    "O fracasso é apenas uma oportunidade para começar de novo com mais inteligência.",
    "Sonhe grande e ouse falhar.",
    "A vida é 10% o que acontece com você e 90% como você reage a isso.",
    "Não deixe que o medo de perder seja maior que a vontade de ganhar.",
    "O sucesso não é final, o fracasso não é fatal: é a coragem de continuar que conta.",
    "Acredite que você pode e você já está no meio do caminho.",
    "A única maneira de fazer um excelente trabalho é amar o que você faz.",
    "Seja você mesmo; todos os outros já foram tomados.",
    "A vida começa no final da sua zona de conforto.",
    "O que não nos mata, nos fortalece.",
    "Transforme seus sonhos em planos e seus planos em realidade.",
    "A disciplina é a ponte entre objetivos e conquistas.",
    "Cada dia é uma nova oportunidade para ser melhor que ontem.",
    "O impossível é apenas uma opinião.",
    "Sua única limitação é você mesmo."
]

# Seleciona uma frase aleatória para o rodapé
frase_rodape = random.choice(frases_motivadoras)

# -------------------------------
# ESTILOS MELHORADOS
# -------------------------------
st.markdown("""
    <style>
    @import url("https://fonts.googleapis.com/css2?family=Livvic:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,900&display=swap");
    
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Livvic', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    }
    
    .section-title {
        font-size: 2rem;
        font-weight: 600;
        color: #212529;
        margin-bottom: 1rem;
        text-align: center;
        font-family: 'Livvic', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    }
    .param-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .param-box {
        padding: 1.5rem;
        border: 1px solid #dee2e6;
        border-radius: 12px;
        text-align: center;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .param-box:hover {
        transform: translateY(-8px) scale(1.03);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, #ffffff 0%, #e9ecef 100%);
        border-color: #0d6efd;
    }
    .param-label {
        font-size: 0.9rem;
        color: #6c757d;
        margin-bottom: 0.5rem;
        font-family: 'Livvic', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    }
    .param-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0d6efd;
        font-family: 'Livvic', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    }
    
    /* Container da tabela com borda fina */
    .metric-table-container {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        background-color: white;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-table {
        width: 100%;
        display: flex;
        flex-direction: column;
        position: relative;
    }
    
    /* Linha vertical separadora com gradiente */
    .metric-table::before {
        content: '';
        position: absolute;
        left: 50%;
        top: 10px;
        bottom: 10px;
        width: 2px;
        background: linear-gradient(to bottom, 
            transparent 0%, 
            #0d6efd 20%, 
            #EC0000 50%, 
            #6c757d 80%, 
            transparent 100%);
        transform: translateX(-50%);
    }
    
    .metric-row {
        display: flex;
        justify-content: space-between;
        padding: 0.75rem 0;
        border-bottom: 1px solid #dee2e6;
        transition: all 0.3s ease;
        position: relative;
    }
    
    .metric-row:last-child {
        border-bottom: none;
    }
    
    /* Animação de hover nos dados - REMOVIDO O INDICADOR AZUL */
    .metric-row:hover {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        transform: translateX(8px) scale(1.02);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-radius: 8px;
        /* border-left: 4px solid #0d6efd; */ /* REMOVIDO */
    }
    
    .metric-label {
        color: #6c757d;
        flex: 1;
        padding-right: 1rem;
        font-family: 'Livvic', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    }
    .metric-value {
        font-weight: 600;
        flex: 1;
        text-align: right;
        padding-left: 1rem;
        font-family: 'Livvic', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    }

    @keyframes gradient-animation {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Estilos do rodapé */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #0d6efd 0%, #6c757d 100%);
        color: white;
        text-align: center;
        padding: 1rem;
        font-size: 1.1rem;
        font-weight: 500;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
        animation: slideInUp 0.8s ease-out;
        font-family: 'Livvic', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    }
    
    @keyframes slideInUp {
        from {
            transform: translateY(100%);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    /* Adiciona espaço no final da página para não sobrepor o rodapé */
    .main-content {
        padding-bottom: 80px;
    }
    
    /* Aplicando fonte Livvic aos elementos específicos do Streamlit */
    .stSelectbox label, .stNumberInput label, .stDateInput label, .stRadio label,
    .stButton button, .stExpander .streamlit-expanderHeader,
    .stDataFrame, .stTable, h1, h2, h3, h4, h5, h6, p, span, div {
        font-family: 'Livvic', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
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
    
    # Calculando percentuais
    total = sum(values)
    percentuais = [f"{label}<br>{format_currency(value)}<br>{(value/total*100):.1f}%" for label, value in zip(labels, values)]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.5, 
        marker=dict(colors=colors, line=dict(color='white', width=4)),  # STROKEWIDTH 4 E COR BRANCA
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{value:,.0f}<br>%{percent}',
        hovertemplate="<b>%{label}</b><br>%{value:,.2f} reais<br>%{percent}<extra></extra>"
    )])
    
    fig.update_layout(
        title="Composição do Financiamento",
        title_x=0.5,  # TÍTULO CENTRALIZADO
        height=500,   # ALTURA 500
        showlegend=False, 
        margin=dict(l=20, r=20, t=60, b=20), 
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
        title="Evolução das Parcelas por Mês",
        title_x=0.5,  # TÍTULO CENTRALIZADO
        barmode='stack', 
        height=500,   # ALTURA 500
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=20, t=60, b=20), 
        xaxis=dict(title='Meses'), 
        yaxis=dict(title='Valor (R$)', tickprefix='R$ ', tickformat=',.2f'),
        hovermode='x unified'
    )
    
    return fig

def criar_grafico_linha(dataframe):
    if dataframe.empty: return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dataframe['Mês'], y=dataframe['Prestação_Total'], name='Parcela', mode='lines', 
                             line=dict(color='#0d6efd', width=2.5),
                             hovertemplate='<b>Mês %{x}</b><br>Parcela: R$ %{y:,.2f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=dataframe['Mês'], y=dataframe['Juros'], name='Juros', mode='lines', 
                             line=dict(color='#EC0000', width=2.5),
                             hovertemplate='<b>Mês %{x}</b><br>Juros: R$ %{y:,.2f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=dataframe['Mês'], y=dataframe['Amortização'], name='Amortização', mode='lines', 
                             line=dict(color='#6c757d', width=2.5),
                             hovertemplate='<b>Mês %{x}</b><br>Amortização: R$ %{y:,.2f}<extra></extra>'))
    
    fig.update_layout(
        title="Evolução de Juros, Amortização e Parcela",
        title_x=0.5,  # TÍTULO CENTRALIZADO
        height=500,   # ALTURA 500
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=20, t=60, b=20), 
        xaxis=dict(title='Meses'), 
        yaxis=dict(title='Valor (R$)', tickprefix='R$ ', tickformat=',.2f')
    )
    
    return fig

# -------------------------------
# PÁGINA PRINCIPAL
# -------------------------------
# Container principal com classe para espaçamento do rodapé
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Seção do título - sem CSS customizado, usando componentes nativos do Streamlit
col1, col2 = st.columns([1, 3])

with col1:
    st.image("https://github.com/lucasricardocs/finan/blob/main/casa.png?raw=true", width=200)

with col2:
    st.title("Simulação de Financiamento e Amortização")
    st.subheader("Transformando sonhos em realidade financeira")

# Seção de parâmetros
with st.expander("Configurar Parâmetros da Simulação", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        valor_imovel_input = st.number_input("💰 Valor do Imóvel", value=0.0, format="%.2f")
        entrada_input = st.number_input("💵 Valor da Entrada", value=0.0, format="%.2f")
        taxa_juros_input = st.number_input("📈 Taxa de Juros Anual (%)", value=0.0, format="%.2f")
    with col2:
        num_parcelas_input = st.number_input("📅 Nº de Parcelas", value=0, step=12)
        data_inicio_input = st.date_input("🗓️ Início do Financiamento", value=datetime.now().date())
    with col3:
        amortizacao_extra = st.number_input("💪 Valor Extra Mensal (R$)", value=0.0, format="%.2f")
        tipo_amortizacao = st.radio("🎯 Objetivo da Amortização:", ("Reduzir prazo", "Reduzir parcela"), horizontal=True)

    if st.button("🚀 **SIMULAR FINANCIAMENTO**", type="primary", use_container_width=True):
        if valor_imovel_input > 0 and entrada_input < (valor_imovel_input * 0.20):
            st.error("A entrada não pode ser menor que 20% do valor do imóvel.")
            st.session_state.simular = False
        else:
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
    <div class="param-box"><p class="param-label">Nº de parcelas</p><p class="param-value">{int(num_parcelas_input)}</p></div>
</div>
""", unsafe_allow_html=True)

# Seção de resultados
if not df_sem_extra.empty:
    st.markdown('<p class="section-title">📈 Resultados da Simulação</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="metric-table-container">', unsafe_allow_html=True)
        st.markdown('<h4 style="text-align: center; margin-bottom: 1rem;">💰 Financiamento Padrão</h4>', unsafe_allow_html=True)
        st.markdown('<div class="metric-table">', unsafe_allow_html=True)
        
        total_pago = df_sem_extra['Prestação_Total'].sum()
        total_juros = df_sem_extra['Juros'].sum()
        total_amortizacao = df_sem_extra['Amortização'].sum()
        total_taxas = df_sem_extra['Taxas/Seguro'].sum()
        primeira_parcela = df_sem_extra['Prestação_Total'].iloc[0] if len(df_sem_extra) > 0 else 0
        ultima_parcela = df_sem_extra['Prestação_Total'].iloc[-1] if len(df_sem_extra) > 0 else 0
        
        st.markdown(f"""
        <div class="metric-row"><span class="metric-label">Total Pago:</span><span class="metric-value">{format_currency(total_pago)}</span></div>
        <div class="metric-row"><span class="metric-label">Total Juros:</span><span class="metric-value">{format_currency(total_juros)}</span></div>
        <div class="metric-row"><span class="metric-label">Total Principal:</span><span class="metric-value">{format_currency(total_amortizacao)}</span></div>
        <div class="metric-row"><span class="metric-label">Total Taxas/Seguro:</span><span class="metric-value">{format_currency(total_taxas)}</span></div>
        <div class="metric-row"><span class="metric-label">Primeira Parcela:</span><span class="metric-value">{format_currency(primeira_parcela)}</span></div>
        <div class="metric-row"><span class="metric-label">Última Parcela:</span><span class="metric-value">{format_currency(ultima_parcela)}</span></div>
        <div class="metric-row"><span class="metric-label">Prazo Total:</span><span class="metric-value">{len(df_sem_extra)} meses</span></div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    with col2:
        if not df_com_extra.empty:
            st.markdown('<div class="metric-table-container">', unsafe_allow_html=True)
            st.markdown('<h4 style="text-align: center; margin-bottom: 1rem;">💪 Com Amortização Extra</h4>', unsafe_allow_html=True)
            st.markdown('<div class="metric-table">', unsafe_allow_html=True)
            
            total_pago_extra = df_com_extra['Prestação_Total'].sum()
            total_juros_extra = df_com_extra['Juros'].sum()
            total_amortizacao_extra = df_com_extra['Amortização'].sum()
            total_taxas_extra = df_com_extra['Taxas/Seguro'].sum()
            primeira_parcela_extra = df_com_extra['Prestação_Total'].iloc[0] if len(df_com_extra) > 0 else 0
            ultima_parcela_extra = df_com_extra['Prestação_Total'].iloc[-1] if len(df_com_extra) > 0 else 0
            
            economia_total = total_pago - total_pago_extra
            economia_juros = total_juros - total_juros_extra
            reducao_prazo = len(df_sem_extra) - len(df_com_extra)
            
            st.markdown(f"""
            <div class="metric-row"><span class="metric-label">Total Pago:</span><span class="metric-value">{format_currency(total_pago_extra)}</span></div>
            <div class="metric-row"><span class="metric-label">Total Juros:</span><span class="metric-value">{format_currency(total_juros_extra)}</span></div>
            <div class="metric-row"><span class="metric-label">Total Principal:</span><span class="metric-value">{format_currency(total_amortizacao_extra)}</span></div>
            <div class="metric-row"><span class="metric-label">Total Taxas/Seguro:</span><span class="metric-value">{format_currency(total_taxas_extra)}</span></div>
            <div class="metric-row"><span class="metric-label">Primeira Parcela:</span><span class="metric-value">{format_currency(primeira_parcela_extra)}</span></div>
            <div class="metric-row"><span class="metric-label">Última Parcela:</span><span class="metric-value">{format_currency(ultima_parcela_extra)}</span></div>
            <div class="metric-row"><span class="metric-label">Prazo Total:</span><span class="metric-value">{len(df_com_extra)} meses</span></div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div></div>', unsafe_allow_html=True)
            
            # Seção de economia
            st.markdown('<div class="metric-table-container" style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); border-color: #28a745;">', unsafe_allow_html=True)
            st.markdown('<h4 style="text-align: center; margin-bottom: 1rem; color: #155724;">💰 Economia Obtida</h4>', unsafe_allow_html=True)
            st.markdown('<div class="metric-table">', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-row"><span class="metric-label">Economia Total:</span><span class="metric-value" style="color: #28a745;">{format_currency(economia_total)}</span></div>
            <div class="metric-row"><span class="metric-label">Economia em Juros:</span><span class="metric-value" style="color: #28a745;">{format_currency(economia_juros)}</span></div>
            <div class="metric-row"><span class="metric-label">Redução de Prazo:</span><span class="metric-value" style="color: #28a745;">{reducao_prazo} meses</span></div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Gráficos
    st.markdown('<p class="section-title">📊 Análise Gráfica</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🥧 Composição", "📊 Evolução Mensal", "📈 Tendências"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(criar_grafico_pizza(df_sem_extra), use_container_width=True)
        with col2:
            if not df_com_extra.empty:
                st.plotly_chart(criar_grafico_pizza(df_com_extra), use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(criar_grafico_barras(df_sem_extra), use_container_width=True)
        with col2:
            if not df_com_extra.empty:
                st.plotly_chart(criar_grafico_barras(df_com_extra), use_container_width=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(criar_grafico_linha(df_sem_extra), use_container_width=True)
        with col2:
            if not df_com_extra.empty:
                st.plotly_chart(criar_grafico_linha(df_com_extra), use_container_width=True)
    
    # Tabela detalhada
    with st.expander("📋 Tabela Detalhada de Parcelas"):
        if not df_com_extra.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Financiamento Padrão")
                st.dataframe(df_sem_extra.style.format({
                    'Prestação_Total': 'R$ {:,.2f}',
                    'Juros': 'R$ {:,.2f}',
                    'Amortização': 'R$ {:,.2f}',
                    'Saldo_Devedor': 'R$ {:,.2f}',
                    'Taxas/Seguro': 'R$ {:,.2f}'
                }), use_container_width=True)
            with col2:
                st.subheader("Com Amortização Extra")
                st.dataframe(df_com_extra.style.format({
                    'Prestação_Total': 'R$ {:,.2f}',
                    'Juros': 'R$ {:,.2f}',
                    'Amortização': 'R$ {:,.2f}',
                    'Saldo_Devedor': 'R$ {:,.2f}',
                    'Taxas/Seguro': 'R$ {:,.2f}'
                }), use_container_width=True)
        else:
            st.dataframe(df_sem_extra.style.format({
                'Prestação_Total': 'R$ {:,.2f}',
                'Juros': 'R$ {:,.2f}',
                'Amortização': 'R$ {:,.2f}',
                'Saldo_Devedor': 'R$ {:,.2f}',
                'Taxas/Seguro': 'R$ {:,.2f}'
            }), use_container_width=True)

# Fechamento do container principal
st.markdown('</div>', unsafe_allow_html=True)

# Rodapé com frase motivadora
st.markdown(f"""
<div class="footer">
    {frase_rodape}
</div>
""", unsafe_allow_html=True)
