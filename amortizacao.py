# simulador_financiamento_final_v5.py
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
    initial_sidebar_state="collapsed"
)

# --- TEMA TRANSPARENTE PARA GRÁFICOS (SOLUÇÃO DEFINITIVA) ---
alt.themes.enable('none')

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
    h1 {{
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
        padding-bottom: 0.5rem;
    }}
    h2 {{
        font-size: 1.75rem;
        font-weight: 600;
        color: #334155;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }}
    h5 {{
        font-weight: 600;
        color: #475569;
        margin-bottom: 1rem;
    }}
    /* Linha Separadora Vermelha */
    .styled-hr {{
        border: none;
        border-top: 3px solid {SANTANDER_RED};
        margin: 2rem 0;
    }}
    /* Ajuste para as métricas sem contêiner */
    [data-testid="stMetric"] {{
        background-color: transparent;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 1rem;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 2rem;
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
# PÁGINA PRINCIPAL
# -------------------------------
st.title("Simulador de Financiamento e Amortização")

# --- Seção de Parâmetros ---
param_col1, param_col2, param_col3 = st.columns(3)
with param_col1:
    st.markdown("<h5>💵 Valores do Imóvel</h5>", unsafe_allow_html=True)
    valor_imovel = st.number_input("Valor Total (R$)", value=600000.0, format="%.2f", key="valor_imovel", min_value=0.0, label_visibility="collapsed")
    min_entrada = valor_imovel * 0.20
    entrada = st.number_input("Entrada (R$)", value=max(min_entrada, 120000.0), format="%.2f", key="entrada", min_value=0.0, label_visibility="collapsed")
    st.caption(f"Entrada mínima (20%): R$ {min_entrada:,.2f}")
with param_col2:
    st.markdown("<h5>⚙️ Condições do Contrato</h5>", unsafe_allow_html=True)
    taxa_juros = st.number_input("Taxa de Juros Anual (%)", value=10.5, format="%.2f", key="taxa", label_visibility="collapsed")
    num_parcelas = st.number_input("Prazo (meses)", value=360, step=12, key="parcelas", label_visibility="collapsed")
    data_inicio = st.date_input("Data de Início", value=datetime.now().date(), key="inicio", label_visibility="collapsed")
with param_col3:
    st.markdown("<h5>🚀 Amortização Extra</h5>", unsafe_allow_html=True)
    amortizacao_extra = st.number_input("Valor Extra Mensal (R$)", value=500.0, format="%.2f", key="extra", min_value=0.0, label_visibility="collapsed")
    tipo_amortizacao = st.radio("Objetivo:", ("Reduzir prazo", "Reduzir parcela"), key="tipo_amortizacao", horizontal=True)

valor_financiado = valor_imovel - entrada
if entrada < min_entrada: st.warning(f"Atenção: A entrada de R$ {entrada:,.2f} está abaixo do mínimo recomendado de R$ {min_entrada:,.2f}.")
st.info(f"**Valor a ser Financiado:** R$ {valor_financiado:,.2f}")

st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)

# --- Bloco Principal de Cálculos e Exibição ---
if valor_financiado > 0:
    prazo_meses, taxa_juros_mes = int(num_parcelas), (1 + taxa_juros / 100) ** (1/12) - 1
    df_sem_extra = calcular_financiamento('prazo', valor_financiado, taxa_juros_mes, prazo_meses, 0.0)
    df_com_extra = pd.DataFrame()
    if amortizacao_extra > 0:
        tipo = 'prazo' if tipo_amortizacao == "Reduzir prazo" else 'parcela'
        df_com_extra = calcular_financiamento(tipo, valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra)

    def criar_grafico_pizza_total(dataframe):
        if dataframe.empty: return None
        total_pago = dataframe[['Amortização', 'Juros', 'Taxas/Seguro']].sum().sum()
        pie_data_df = pd.DataFrame({'Componente': ['Principal', 'Juros', 'Taxas/Seguro'], 'Valor': [dataframe['Amortização'].sum(), dataframe['Juros'].sum(), dataframe['Taxas/Seguro'].sum()]})
        pie_data_df['Percentual'] = (pie_data_df['Valor'] / total_pago) * 100
        pie_data_df['Label'] = pie_data_df.apply(lambda row: f"{row['Componente']} {row['Percentual']:.1f}%", axis=1)
        chart_base = alt.Chart(pie_data_df).encode(theta=alt.Theta(field="Valor", type="quantitative", stack=True), color=alt.Color(field="Componente", type="nominal", scale=alt.Scale(domain=['Principal', 'Juros', 'Taxas/Seguro'], range=[SANTANDER_BLUE, SANTANDER_RED, SANTANDER_GRAY]), legend=None))
        chart_arc = chart_base.mark_arc(outerRadius=120, innerRadius=70)
        chart_text = chart_base.mark_text(radius=155, size=14).encode(text='Label:N')
        return (chart_arc + chart_text).properties(height=500).configure_view(strokeWidth=0, fill='transparent')

    st.header("Análise Comparativa")
    
    col_met_sem, col_met_com = st.columns(2)
    with col_met_sem:
        st.subheader("Cenário Padrão")
        if not df_sem_extra.empty:
            total_pagar, total_juros = df_sem_extra["Prestação_Total"].sum(), df_sem_extra["Juros"].sum()
            st.metric("Custo Total", f"R$ {total_pagar:,.2f}")
            st.metric("Total em Juros", f"R$ {total_juros:,.2f}")
            st.metric("Prazo Final", f"{len(df_sem_extra)} meses")
    with col_met_com:
        st.subheader("Cenário com Amortização Extra")
        if not df_com_extra.empty:
            total_pagar_extra, total_juros_extra = df_com_extra["Prestação_Total"].sum(), df_com_extra["Juros"].sum()
            economia = total_pagar - total_pagar_extra
            st.metric("Custo Total", f"R$ {total_pagar_extra:,.2f}", f"- R$ {economia:,.2f}")
            st.metric("Total em Juros", f"R$ {total_juros_extra:,.2f}")
            st.metric("Prazo Final", f"{len(df_com_extra)} meses")
        else:
            st.info("Nenhum cenário com amortização extra para comparar.")

    col_pizza_sem, col_pizza_com = st.columns(2)
    with col_pizza_sem:
        if not df_sem_extra.empty:
            st.altair_chart(criar_grafico_pizza_total(df_sem_extra), use_container_width=True)
    with col_pizza_com:
        if not df_com_extra.empty:
            st.altair_chart(criar_grafico_pizza_total(df_com_extra), use_container_width=True)

    st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)
    st.header("Análise Detalhada da Evolução")
    
    df_plot = df_sem_extra.copy(); df_plot['Cenário'] = 'Padrão'
    if not df_com_extra.empty:
        df_com_extra_plot = df_com_extra.copy(); df_com_extra_plot['Cenário'] = 'Com Amortização'
        df_plot = pd.concat([df_plot, df_com_extra_plot])
    
    tab_saldo, tab_comp, tab_parcela, tab_tabela = st.tabs(["📉 Saldo Devedor", "📊 Composição Mensal", "📉 Evolução da Parcela", "📋 Tabela Detalhada"])
    with tab_saldo:
        chart = alt.Chart(df_plot).mark_line().encode(
            x=alt.X('Mês:Q', title='Meses', axis=alt.Axis(grid=False)), 
            y=alt.Y('Saldo_Devedor:Q', title='Saldo Devedor (R$)', axis=alt.Axis(grid=False)), 
            color=alt.Color('Cenário:N', legend=alt.Legend(orient="top", title=None), scale=alt.Scale(domain=['Padrão', 'Com Amortização'], range=[SANTANDER_GRAY, SANTANDER_RED])), 
            tooltip=['Mês', 'Saldo_Devedor', 'Cenário']
        ).properties(height=500).configure_view(fill='transparent')
        st.altair_chart(chart, use_container_width=True)
    with tab_comp:
        df_melted = df_plot.melt(id_vars=['Mês', 'Cenário'], value_vars=['Juros', 'Amortização'], var_name='Componente', value_name='Valor')
        chart = alt.Chart(df_melted[df_melted['Mês'] <= 72]).mark_bar().encode(
            x=alt.X('Mês:O', title='Meses (primeiros 6 anos)', axis=alt.Axis(labelAngle=0, grid=False)), 
            y=alt.Y('Valor:Q', title='Valor da Parcela (R$)', stack='zero', axis=alt.Axis(grid=False)), 
            color=alt.Color('Componente:N', scale=alt.Scale(domain=['Juros', 'Amortização'], range=[SANTANDER_RED, SANTANDER_BLUE]), legend=alt.Legend(orient="top", title="Componente")), 
            tooltip=['Mês', 'Cenário', 'Componente', 'Valor']
        ).properties(height=500).configure_view(fill='transparent')
        st.altair_chart(chart, use_container_width=True)
    with tab_parcela:
        df_melted = df_plot.melt(id_vars=['Mês', 'Cenário'], value_vars=['Prestação_Total', 'Juros', 'Amortização'], var_name='Componente', value_name='Valor')
        chart = alt.Chart(df_melted).mark_line().encode(
            x=alt.X('Mês:Q', title='Meses', axis=alt.Axis(grid=False)),
            y=alt.Y('Valor:Q', title='Valor (R$)', axis=alt.Axis(grid=False)),
            color=alt.Color('Componente:N', legend=alt.Legend(orient="top", title='Variável'), 
                          scale=alt.Scale(domain=['Prestação_Total', 'Amortização', 'Juros'], range=[SANTANDER_RED, SANTANDER_BLUE, SANTANDER_GRAY])),
            strokeDash=alt.StrokeDash('Cenário:N', legend=alt.Legend(orient="top", title='Cenário')),
            tooltip=['Mês', 'Cenário', 'Componente', 'Valor']
        ).properties(height=500).configure_view(fill='transparent')
        st.altair_chart(chart, use_container_width=True)
    with tab_tabela:
        if not df_com_extra.empty:
            st.write("##### Cenário com Amortização Extra")
            st.dataframe(df_com_extra, use_container_width=True, height=500)
        st.write("##### Cenário Padrão")
        st.dataframe(df_sem_extra, use_container_width=True, height=500)
else:
    st.error("O 'Valor a ser Financiado' deve ser maior que zero. Ajuste os parâmetros da simulação.")

st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)
st.caption("Aviso Legal: Esta é uma ferramenta de simulação e os resultados são para fins ilustrativos. As condições reais do seu financiamento podem variar.")
