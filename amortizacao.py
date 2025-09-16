# simulador_financiamento_pro_ui.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

# -------------------------------
# CONFIGURAÇÃO GERAL
# -------------------------------
st.set_page_config(
    page_title="Simulador de Financiamento Santander",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# ESTILOS E CORES
# -------------------------------
SANTANDER_RED = "#EC0000"
SANTANDER_BLUE = "#004481"
SANTANDER_GRAY = "#6c757d"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');
    
    html, body, [class*="st-"] {{
        font-family: 'Open Sans', sans-serif;
    }}
    .stApp {{
        background-color: #f0f2f6;
    }}
    /* Barra Lateral */
    [data-testid="stSidebar"] {{
        background-color: #ffffff;
        border-right: 1px solid #e6e6e6;
    }}
    [data-testid="stSidebar"] h2 {{
        font-weight: 700;
        color: {SANTANDER_RED};
    }}
    /* Títulos da Página Principal */
    .main-title {{
        font-size: 28px;
        font-weight: 700;
        color: #1e293b;
        padding-bottom: 8px;
        border-bottom: 4px solid {SANTANDER_RED};
        margin-bottom: 30px;
    }}
    .section-header {{
        font-size: 20px;
        font-weight: 600;
        color: #334155;
        margin-top: 20px;
        margin-bottom: 20px;
    }}
    /* Métricas */
    [data-testid="stMetric"] {{
        background-color: #FFFFFF;
        border-left: 5px solid {SANTANDER_RED};
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 15px;
        color: {SANTANDER_GRAY};
    }}
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
# BARRA LATERAL (CONTROLES)
# -------------------------------
with st.sidebar:
    st.markdown("## 🏦 Simulador")
    st.markdown("Use os campos abaixo para configurar sua simulação de financiamento.")
    
    with st.expander("💵 **Valores do Imóvel**", expanded=True):
        valor_imovel = st.number_input("Valor Total do Imóvel (R$)", value=600000.0, format="%.2f", key="valor_imovel", min_value=0.0)
        min_entrada = valor_imovel * 0.20
        entrada = st.number_input("Valor da Entrada (R$)", value=max(min_entrada, 120000.0), format="%.2f", key="entrada", min_value=0.0)
        st.caption(f"Entrada mínima (20%): R$ {min_entrada:,.2f}")
        
    with st.expander("⚙️ **Condições do Contrato**", expanded=True):
        data_inicio = st.date_input("Data de Início", value=datetime.now().date(), key="inicio")
        taxa_juros = st.number_input("Taxa de Juros Anual (%)", value=10.5, format="%.2f", key="taxa")
        num_parcelas = st.number_input("Prazo (meses)", value=360, step=12, key="parcelas")
        
    with st.expander("🚀 **Amortização Extra**"):
        amortizacao_extra = st.number_input("Valor Extra Mensal (R$)", value=500.0, format="%.2f", key="extra", min_value=0.0)
        tipo_amortizacao = st.radio("Objetivo:", ("Reduzir prazo", "Reduzir parcela"), key="tipo_amortizacao", horizontal=True)

# -------------------------------
# PÁGINA PRINCIPAL (RESULTADOS)
# -------------------------------
st.markdown("<p class='main-title'>Análise Comparativa de Financiamento</p>", unsafe_allow_html=True)

valor_financiado = valor_imovel - entrada
if valor_financiado <= 0:
    st.error("O 'Valor a ser Financiado' deve ser maior que zero. Ajuste o valor do imóvel ou da entrada.")
else:
    # --- Cálculos ---
    prazo_meses, taxa_juros_mes = int(num_parcelas), (1 + taxa_juros / 100) ** (1/12) - 1
    df_sem_extra = calcular_financiamento('prazo', valor_financiado, taxa_juros_mes, prazo_meses, 0.0)
    df_com_extra = pd.DataFrame()
    if amortizacao_extra > 0:
        tipo = 'prazo' if tipo_amortizacao == "Reduzir prazo" else 'parcela'
        df_com_extra = calcular_financiamento(tipo, valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra)

    # --- Resumo e Gráficos de Pizza ---
    col_sem, col_com = st.columns(2)
    with col_sem:
        st.markdown("<p class='section-header'>Cenário Padrão</p>", unsafe_allow_html=True)
        if not df_sem_extra.empty:
            total_pagar, total_juros = df_sem_extra["Prestação_Total"].sum(), df_sem_extra["Juros"].sum()
            st.metric("Custo Total do Financiamento", f"R$ {total_pagar:,.2f}")
            st.metric("Total de Juros Pagos", f"R$ {total_juros:,.2f}")
            st.metric("Prazo Final do Contrato", f"{len(df_sem_extra)} meses")
    
    with col_com:
        st.markdown("<p class='section-header'>Cenário com Amortização Extra</p>", unsafe_allow_html=True)
        if not df_com_extra.empty:
            total_pagar_extra, total_juros_extra = df_com_extra["Prestação_Total"].sum(), df_com_extra["Juros"].sum()
            economia = total_pagar - total_pagar_extra
            st.metric("Custo Total do Financiamento", f"R$ {total_pagar_extra:,.2f}", f"- R$ {economia:,.2f}")
            st.metric("Total de Juros Pagos", f"R$ {total_juros_extra:,.2f}")
            st.metric("Prazo Final do Contrato", f"{len(df_com_extra)} meses")

    # --- Análise Detalhada ---
    st.markdown("<p class='main-title'>Análise Detalhada da Evolução</p>", unsafe_allow_html=True)
    
    # Preparação de dados para gráficos detalhados
    df_sem_extra_plot = df_sem_extra.copy()
    df_sem_extra_plot['Cenário'] = 'Padrão'
    df_plot = df_sem_extra_plot
    if not df_com_extra.empty:
        df_com_extra_plot = df_com_extra.copy()
        df_com_extra_plot['Cenário'] = 'Com Amortização'
        df_plot = pd.concat([df_sem_extra_plot, df_com_extra_plot])

    # Abas com gráficos
    tab_saldo, tab_comp, tab_acum, tab_tabela = st.tabs(["📉 Saldo Devedor", "📊 Composição Mensal", "📈 Pagamento Acumulado", "📋 Tabela Detalhada"])
    with tab_saldo:
        chart = alt.Chart(df_plot).mark_line().encode(
            x=alt.X('Mês:Q', title='Meses'),
            y=alt.Y('Saldo_Devedor:Q', title='Saldo Devedor (R$)'),
            color=alt.Color('Cenário:N', legend=alt.Legend(orient="top", title=None), scale=alt.Scale(domain=['Padrão', 'Com Amortização'], range=[SANTANDER_GRAY, SANTANDER_RED])),
            tooltip=['Mês', 'Saldo_Devedor', 'Cenário']
        ).properties(height=400).configure_view(fill='transparent')
        st.altair_chart(chart, use_container_width=True)
    with tab_comp:
        df_melted = df_plot.melt(id_vars=['Mês', 'Cenário'], value_vars=['Juros', 'Amortização'], var_name='Componente', value_name='Valor')
        chart = alt.Chart(df_melted[df_melted['Mês'] <= 72]).mark_bar().encode(
            x=alt.X('Mês:O', title='Meses (primeiros 6 anos)', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Valor:Q', title='Valor da Parcela (R$)', stack='zero'),
            color=alt.Color('Componente:N', scale=alt.Scale(domain=['Juros', 'Amortização'], range=[SANTANDER_RED, SANTANDER_BLUE]), legend=alt.Legend(orient="top", title="Componente")),
            tooltip=['Mês', 'Cenário', 'Componente', 'Valor']
        ).properties(height=400).configure_view(fill='transparent')
        st.altair_chart(chart, use_container_width=True)
    with tab_acum:
        df_plot_acum = df_plot.copy()
        df_plot_acum[['Juros Acumulados', 'Principal Pago']] = df_plot_acum.groupby('Cenário')[['Juros', 'Amortização']].cumsum()
        df_melted_acum = df_plot_acum.melt(id_vars=['Mês', 'Cenário'], value_vars=['Juros Acumulados', 'Principal Pago'], var_name='Componente', value_name='Valor Acumulado')
        chart = alt.Chart(df_melted_acum).mark_area(opacity=0.8).encode(
            x=alt.X('Mês:Q', title='Meses'),
            y=alt.Y('Valor Acumulado:Q', stack='zero', title='Valor Acumulado (R$)'),
            color=alt.Color('Componente:N', scale=alt.Scale(domain=['Juros Acumulados', 'Principal Pago'], range=[SANTANDER_RED, SANTANDER_BLUE]), legend=alt.Legend(orient="top", title="Componente")),
            tooltip=['Mês', 'Cenário', 'Componente', 'Valor Acumulado']
        ).properties(height=400).configure_view(fill='transparent')
        st.altair_chart(chart, use_container_width=True)
    with tab_tabela:
        st.markdown("<p class='section-header'>Tabela de Amortização Completa</p>", unsafe_allow_html=True)
        if not df_com_extra.empty:
            with st.expander("Cenário com Amortização Extra"):
                st.dataframe(df_com_extra.style.format("R$ {:,.2f}", subset=["Prestação_Total", "Juros", "Amortização", "Saldo_Devedor", "Taxas/Seguro"]), use_container_width=True)
        with st.expander("Cenário Padrão", expanded=True):
            st.dataframe(df_sem_extra.style.format("R$ {:,.2f}", subset=["Prestação_Total", "Juros", "Amortização", "Saldo_Devedor", "Taxas/Seguro"]), use_container_width=True)
