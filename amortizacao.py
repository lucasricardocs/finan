import streamlit as st
import pandas as pd
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
TEXT_COLOR = "#212529"
SUBTLE_TEXT_COLOR = "#6c757d"
BACKGROUND_COLOR = "#f8f9fa"
BORDER_COLOR = "#dee2e6"

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
    
    /* --- CORREÇÃO DO ÍCONE DO EXPANSÍVEL --- */
    [data-testid="stExpander"] summary {{
      position: relative; /* Necessário para posicionar nosso ícone customizado */
      padding-left: 2rem; /* Espaço para o novo ícone */
    }}
    /* Esconde o ícone quebrado original do Streamlit */
    [data-testid="stExpander"] summary .st-emotion-cache-1282ie9, 
    [data-testid="stExpander"] summary .st-emotion-cache-g85b5l {{
        display: none;
    }}
    /* Cria nosso próprio ícone de seta (▶) */
    [data-testid="stExpander"] summary::before {{
        content: '▶';
        font-size: 14px;
        color: {SUBTLE_TEXT_COLOR};
        position: absolute;
        left: 0.5rem;
        top: 50%;
        transform: translateY(-50%) rotate(0deg);
        transition: transform 0.2s ease-in-out;
    }}
    /* Gira nosso ícone (▼) quando o expansível está aberto */
    [data-testid="stExpander"][open] > summary::before {{
        transform: translateY(-50%) rotate(90deg);
    }}
    
    /* --- Tabela de Métricas de Resultado --- */
    .metric-table {{
        width: 100%;
        margin-top: 1.5rem;
    }}
    .metric-row {{
        display: flex;
        justify-content: space-between;
        padding: 0.85rem 0.5rem;
        border-bottom: 1px solid {BORDER_COLOR};
    }}
    .metric-row:nth-child(even) {{
        background-color: #fdfdfd;
    }}
    .metric-label {{
        color: {SUBTLE_TEXT_COLOR};
        font-size: 0.95rem;
    }}
    .metric-value {{
        font-weight: 600;
        color: {TEXT_COLOR};
        font-size: 0.95rem;
    }}
    </style>
    """, unsafe_allow_html=True)

# -------------------------------
# FUNÇÕES DE CÁLCULO
# -------------------------------
@st.cache_data
def calcular_sac(valor_financiado, taxa_juros_anual, prazo_meses):
    if valor_financiado <= 0 or prazo_meses <= 0: 
        return pd.DataFrame(), {}

    taxa_juros_mes = (1 + taxa_juros_anual / 100) ** (1/12) - 1
    
    saldo_devedor = valor_financiado
    amortizacao_mensal = valor_financiado / prazo_meses
    dados_parcelas = []
    
    for mes in range(1, prazo_meses + 1):
        juros = saldo_devedor * taxa_juros_mes
        prestacao = amortizacao_mensal + juros
        saldo_devedor -= amortizacao_mensal
        
        # Garante que o último saldo devedor seja exatamente zero
        if mes == prazo_meses:
            saldo_devedor = 0

        dados_parcelas.append({
            "Mês": mes,
            "Prestação": prestacao,
            "Juros": juros,
            "Amortização": amortizacao_mensal,
            "Saldo_Devedor": saldo_devedor,
        })
        
    df = pd.DataFrame(dados_parcelas)
    
    # Calcular totais e outras métricas
    resumo = {
        "valor_financiado": valor_financiado,
        "total_pago": df["Prestação"].sum(),
        "total_juros": df["Juros"].sum(),
        "taxa_juros_aa": f"{taxa_juros_anual:.2f}% (a.a)",
        "quantidade_parcelas": len(df),
        "primeira_parcela": df.iloc[0]["Prestação"],
        "ultima_parcela": df.iloc[-1]["Prestação"],
    }
    
    return df, resumo

# -------------------------------
# PÁGINA PRINCIPAL
# -------------------------------

st.title("Resultado da Simulação de Amortização")

# --- Parâmetros fixos para gerar os dados da imagem ---
VALOR_FINANCIADO = 500000.00
TAXA_JUROS_AA = 9.93
PRAZO_MESES = 360
DATA_INICIO = datetime(2025, 9, 1)

# --- Cálculo ---
df_resultado, resumo = calcular_sac(VALOR_FINANCIADO, TAXA_JUROS_AA, PRAZO_MESES)

# --- Exibição com Expansível ---
with st.expander("Sem amortização extra", expanded=True):
    if not df_resultado.empty:
        data_ultima = DATA_INICIO + timedelta(days=30.4375 * PRAZO_MESES)

        # Monta a lista de dados para a tabela
        dados_tabela = [
            ("Valor financiado", f"R$ {resumo['valor_financiado']:,.2f}"),
            ("Total a ser pago", f"R$ {resumo['total_pago']:,.2f}"),
            ("Total amortizado", "--"),
            ("Total de juros", f"R$ {resumo['total_juros']:,.2f}"),
            ("Total de taxas/seguros", "R$ 0,00"),
            ("Correção", "R$ 0,00"),
            ("Taxa de juros", resumo['taxa_juros_aa']),
            ("Quantidade de parcelas", resumo['quantidade_parcelas']),
            ("Valor da primeira parcela", f"R$ {resumo['primeira_parcela']:,.2f}"),
            ("Valor da última parcela", f"R$ {resumo['ultima_parcela']:,.2f}"),
            ("Data da última parcela", data_ultima.strftime('%B de %Y')),
            ("Sistema de amortização", "SAC"),
        ]

        # Gera o HTML da tabela a partir da lista de dados
        tabela_html = "".join([
            f"<div class='metric-row'>"
            f"<span class='metric-label'>{label}</span>"
            f"<span class='metric-value'>{value}</span>"
            f"</div>"
            for label, value in dados_tabela
        ])
        
        st.markdown(f"<div class='metric-table'>{tabela_html}</div>", unsafe_allow_html=True)

    else:
        st.error("Não foi possível calcular os dados com os parâmetros fornecidos.")
