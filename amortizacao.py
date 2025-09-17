# simulador_financiamento_report_ui.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -------------------------------
# CONFIGURAÇÃO GERAL
# -------------------------------
st.set_page_config(
    page_title="Relatório de Simulação de Financiamento",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    h1, h2 {{
        color: {TEXT_COLOR};
        font-weight: 700;
    }}
    h5 {{
        font-weight: 600;
        color: #475569;
        margin-bottom: 1rem;
    }}
    .styled-hr {{
        border: none;
        border-top: 3px solid {SANTANDER_RED};
        margin: 2.5rem 0;
    }}
    /* Tabela de Métricas Customizada */
    .metric-table {{ width: 100%; }}
    .metric-row {{
        display: flex;
        justify-content: space-between;
        padding: 0.75rem 0;
        border-bottom: 1px solid {BORDER_COLOR};
    }}
    .metric-label {{ color: {SUBTLE_TEXT_COLOR}; font-size: 0.9rem; }}
    .metric-value {{ font-weight: 600; color: {TEXT_COLOR}; font-size: 1rem; }}
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
st.title("Relatório de Simulação de Financiamento")

with st.expander("⚙️ Clique aqui para configurar os parâmetros da simulação", expanded=True):
    param_col1, param_col2, param_col3 = st.columns(3)
    with param_col1:
        st.markdown("<h5>💵 Valores do Imóvel</h5>", unsafe_allow_html=True)
        valor_imovel = st.number_input("Valor Total (R$)", value=600000.0, format="%.2f", key="valor_imovel")
        entrada = st.number_input("Entrada (R$)", value=120000.0, format="%.2f", key="entrada")
    with param_col2:
        st.markdown("<h5>⚙️ Condições do Contrato</h5>", unsafe_allow_html=True)
        taxa_juros = st.number_input("Taxa de Juros Anual (%)", value=10.5, format="%.2f", key="taxa")
        num_parcelas = st.number_input("Prazo (meses)", value=360, step=12, key="parcelas")
    with param_col3:
        st.markdown("<h5>🚀 Amortização Extra</h5>", unsafe_allow_html=True)
        amortizacao_extra = st.number_input("Valor Extra Mensal (R$)", value=500.0, format="%.2f", key="extra")
        tipo_amortizacao = st.radio("Objetivo:", ("Reduzir prazo", "Reduzir parcela"), key="tipo_amortizacao", horizontal=True)

valor_financiado = valor_imovel - entrada
st.info(f"**Valor a ser Financiado:** R$ {valor_financiado:,.2f}  |  **Entrada:** R$ {entrada:,.2f} ({entrada/valor_imovel:.1%} do total)")

st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)

if valor_financiado > 0:
    prazo_meses, taxa_juros_mes = int(num_parcelas), (1 + taxa_juros / 100) ** (1/12) - 1
    df_sem_extra = calcular_financiamento('prazo', valor_financiado, taxa_juros_mes, prazo_meses, 0.0)
    df_com_extra = pd.DataFrame()
    if amortizacao_extra > 0:
        tipo = 'prazo' if tipo_amortizacao == "Reduzir prazo" else 'parcela'
        df_com_extra = calcular_financiamento(tipo, valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra)

    st.header("Resumo Comparativo")
    
    col_sem, col_com = st.columns(2)
    with col_sem:
        st.subheader("Cenário Padrão")
        if not df_sem_extra.empty:
            total_pagar, total_juros = df_sem_extra["Prestação_Total"].sum(), df_sem_extra["Juros"].sum()
            st.markdown("<div class='metric-table'>"
                        f"<div class='metric-row'><span class='metric-label'>Custo Total</span><span class='metric-value'>R$ {total_pagar:,.2f}</span></div>"
                        f"<div class='metric-row'><span class='metric-label'>Total em Juros</span><span class='metric-value'>R$ {total_juros:,.2f}</span></div>"
                        f"<div class='metric-row'><span class='metric-label'>Prazo Final</span><span class='metric-value'>{len(df_sem_extra)} meses</span></div>"
                        "</div>", unsafe_allow_html=True)
    with col_com:
        st.subheader("Cenário com Amortização Extra")
        if not df_com_extra.empty:
            total_pagar_extra, total_juros_extra = df_com_extra["Prestação_Total"].sum(), df_com_extra["Juros"].sum()
            economia = total_pagar - total_pagar_extra
            st.markdown("<div class='metric-table'>"
                        f"<div class='metric-row'><span class='metric-label'>Custo Total</span><span class='metric-value'>R$ {total_pagar_extra:,.2f}</span></div>"
                        f"<div class='metric-row'><span class='metric-label'>Total em Juros</span><span class='metric-value'>R$ {total_juros_extra:,.2f}</span></div>"
                        f"<div class='metric-row'><span class='metric-label'>Prazo Final</span><span class='metric-value'>{len(df_com_extra)} meses</span></div>"
                        f"<div class='metric-row' style='background-color: #e8f5e9;'><span class='metric-label' style='font-weight:600;'>Economia Total</span><span class='metric-value' style='color:#16a34a; font-weight:700;'>R$ {economia:,.2f}</span></div>"
                        "</div>", unsafe_allow_html=True)
        else:
            st.info("Nenhum cenário com amortização extra para comparar.")
            
    st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)
    st.header("Análise Gráfica Detalhada")

    # Layout comum para gráficos
    common_layout = dict(height=550, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                         font=dict(color=TEXT_COLOR), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    # --- Gráfico de Pizza Comparativo ---
    st.subheader("Composição do Custo Total")
    pizza_col1, pizza_col2 = st.columns(2)
    with pizza_col1:
        if not df_sem_extra.empty:
            labels = ['Principal', 'Juros', 'Taxas']; values = [df_sem_extra['Amortização'].sum(), df_sem_extra['Juros'].sum(), df_sem_extra['Taxas/Seguro'].sum()]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker_colors=[PRIMARY_BLUE, SANTANDER_RED, BORDER_COLOR])])
            fig.update_layout(title_text='Cenário Padrão', **common_layout)
            st.plotly_chart(fig, use_container_width=True)
    with pizza_col2:
        if not df_com_extra.empty:
            labels = ['Principal', 'Juros', 'Taxas']; values = [df_com_extra['Amortização'].sum(), df_com_extra['Juros'].sum(), df_com_extra['Taxas/Seguro'].sum()]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker_colors=[PRIMARY_BLUE, SANTANDER_RED, BORDER_COLOR])])
            fig.update_layout(title_text='Com Amortização Extra', **common_layout)
            st.plotly_chart(fig, use_container_width=True)

    # --- Gráfico de Saldo Devedor Comparativo ---
    st.subheader("Evolução do Saldo Devedor")
    fig_saldo = go.Figure(layout=common_layout)
    fig_saldo.add_trace(go.Scatter(x=df_sem_extra['Mês'], y=df_sem_extra['Saldo_Devedor'], mode='lines', name='Padrão', line=dict(color=SUBTLE_TEXT_COLOR, width=2.5)))
    if not df_com_extra.empty:
        fig_saldo.add_trace(go.Scatter(x=df_com_extra['Mês'], y=df_com_extra['Saldo_Devedor'], mode='lines', name='Com Amortização', line=dict(color=SANTANDER_RED, width=3)))
    fig_saldo.update_xaxes(showgrid=False); fig_saldo.update_yaxes(showgrid=False)
    st.plotly_chart(fig_saldo, use_container_width=True)

    # --- Gráfico de Composição Mensal Comparativo ---
    st.subheader("Composição da Parcela Mensal (Primeiros 6 Anos)")
    fig_comp = go.Figure(layout=common_layout)
    fig_comp.update_layout(barmode='stack')
    df_view = df_sem_extra[df_sem_extra['Mês'] <= 72]
    fig_comp.add_trace(go.Bar(x=df_view['Mês'], y=df_view['Juros'], name='Juros (Padrão)', marker_color=SANTANDER_RED, opacity=0.7))
    fig_comp.add_trace(go.Bar(x=df_view['Mês'], y=df_view['Amortização'], name='Amortização (Padrão)', marker_color=PRIMARY_BLUE, opacity=0.7))
    if not df_com_extra.empty:
        df_view_extra = df_com_extra[df_com_extra['Mês'] <= 72]
        fig_comp.add_trace(go.Bar(x=df_view_extra['Mês'], y=df_view_extra['Juros'], name='Juros (Com Amort.)', marker_color=SANTANDER_RED, opacity=1.0))
        fig_comp.add_trace(go.Bar(x=df_view_extra['Mês'], y=df_view_extra['Amortização'], name='Amortização (Com Amort.)', marker_color=PRIMARY_BLUE, opacity=1.0))
    fig_comp.update_xaxes(showgrid=False); fig_comp.update_yaxes(showgrid=False)
    st.plotly_chart(fig_comp, use_container_width=True)

else:
    st.error("O 'Valor a ser Financiado' deve ser maior que zero. Ajuste os parâmetros da simulação.")

st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)
st.caption("Aviso Legal: Esta é uma ferramenta de simulação e os resultados são para fins ilustrativos.")
