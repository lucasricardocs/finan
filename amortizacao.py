# simulador_financiamento_plotly_final.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -------------------------------
# CONFIGURAÇÃO GERAL
# -------------------------------
st.set_page_config(
    page_title="Simulador de Financiamento (Plotly)",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------
# ESTILOS E CORES
# -------------------------------
SANTANDER_RED = "#EC0000"
PRIMARY_BLUE = "#004481"
TEXT_COLOR = "#1f2937"
SUBTLE_TEXT_COLOR = "#4b5563"
BACKGROUND_COLOR = "#f0f2f6"
COMPONENT_BACKGROUND = "#ffffff"
BORDER_COLOR = "#d1d5db"
SUCCESS_COLOR = "#16a34a" # Verde para economia

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
    h1 {{
        font-size: 2.5rem; font-weight: 700; color: {TEXT_COLOR};
        padding-bottom: 0.5rem; border-bottom: 4px solid {SANTANDER_RED};
        margin-bottom: 2rem;
    }}
    h2 {{
        font-size: 1.75rem; font-weight: 600; color: {SUBTLE_TEXT_COLOR};
        margin-top: 2rem; margin-bottom: 1.5rem;
    }}
    h5 {{
        font-weight: 600; color: #475569; margin-bottom: 1rem;
    }}
    .styled-hr {{
        border: none; border-top: 3px solid {SANTANDER_RED};
        margin: 2rem 0;
    }}
    /* Contêiner para os parâmetros */
    .param-container {{
        background-color: {COMPONENT_BACKGROUND};
        padding: 10px 25px 25px 25px;
        border-radius: 10px;
        border: 1px solid {BORDER_COLOR};
    }}
    /* Cartões de Métrica Customizados */
    .custom-metric-card {{
        background-color: {COMPONENT_BACKGROUND};
        padding: 25px;
        border-radius: 10px;
        border-top: 4px solid {SANTANDER_RED}; /* Bordinha vermelha */
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        height: 100%; /* Garante a mesma altura */
        display: flex;
        flex-direction: column;
    }}
    .metric-label {{ font-size: 1rem; color: {SUBTLE_TEXT_COLOR}; margin-bottom: 0.5rem; }}
    .metric-value-container {{ display: flex; align-items: baseline; gap: 10px; }}
    .metric-value {{ font-size: 2rem; font-weight: 600; color: {TEXT_COLOR}; }}
    .metric-delta {{ font-size: 1.1rem; font-weight: 600; color: {SUCCESS_COLOR}; }}
    
    /* Abas */
    [data-testid="stTabs"] button {{ color: {SUBTLE_TEXT_COLOR}; font-weight: 500; }}
    [data-testid="stTabs"] button[aria-selected="true"] {{ color: {SANTANDER_RED}; font-weight: 600; border-bottom: 2px solid {SANTANDER_RED}; }}
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
st.title("Simulador de Financiamento")

with st.container():
    st.markdown("<div class='param-container'>", unsafe_allow_html=True)
    param_col1, param_col2, param_col3 = st.columns(3)
    with param_col1:
        st.markdown("<h5>💵 Valores do Imóvel</h5>", unsafe_allow_html=True)
        valor_imovel = st.number_input("Valor Total (R$)", value=600000.0, format="%.2f", key="valor_imovel", label_visibility="collapsed")
        entrada = st.number_input("Entrada (R$)", value=120000.0, format="%.2f", key="entrada", label_visibility="collapsed")
    with param_col2:
        st.markdown("<h5>⚙️ Condições do Contrato</h5>", unsafe_allow_html=True)
        taxa_juros = st.number_input("Taxa de Juros Anual (%)", value=10.5, format="%.2f", key="taxa", label_visibility="collapsed")
        num_parcelas = st.number_input("Prazo (meses)", value=360, step=12, key="parcelas", label_visibility="collapsed")
    with param_col3:
        st.markdown("<h5>🚀 Amortização Extra</h5>", unsafe_allow_html=True)
        amortizacao_extra = st.number_input("Valor Extra Mensal (R$)", value=500.0, format="%.2f", key="extra", label_visibility="collapsed")
        tipo_amortizacao = st.radio("Objetivo:", ("Reduzir prazo", "Reduzir parcela"), key="tipo_amortizacao", horizontal=True)
    st.markdown("</div>", unsafe_allow_html=True)

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

    st.header("Análise Comparativa")
    
    col_sem, col_com = st.columns(2)
    with col_sem:
        st.markdown("<div class='custom-metric-card'>", unsafe_allow_html=True)
        st.markdown("<p class='section-header' style='margin-top:0; font-size: 1.5rem;'>Cenário Padrão</p>", unsafe_allow_html=True)
        if not df_sem_extra.empty:
            total_pagar, total_juros = df_sem_extra["Prestação_Total"].sum(), df_sem_extra["Juros"].sum()
            st.markdown(f"<p class='metric-label'>Custo Total</p><div class='metric-value-container'><p class='metric-value'>R$ {total_pagar:,.2f}</p></div>", unsafe_allow_html=True)
            st.markdown(f"<p class='metric-label'>Total em Juros</p><div class='metric-value-container'><p class='metric-value'>R$ {total_juros:,.2f}</p></div>", unsafe_allow_html=True)
            st.markdown(f"<p class='metric-label'>Prazo Final</p><div class='metric-value-container'><p class='metric-value'>{len(df_sem_extra)} meses</p></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_com:
        st.markdown("<div class='custom-metric-card'>", unsafe_allow_html=True)
        st.markdown("<p class='section-header' style='margin-top:0; font-size: 1.5rem;'>Cenário com Amortização Extra</p>", unsafe_allow_html=True)
        if not df_com_extra.empty:
            total_pagar_extra, total_juros_extra = df_com_extra["Prestação_Total"].sum(), df_com_extra["Juros"].sum()
            economia = total_pagar - total_pagar_extra
            st.markdown(f"<p class='metric-label'>Custo Total</p><div class='metric-value-container'><p class='metric-value'>R$ {total_pagar_extra:,.2f}</p><p class='metric-delta'>- R$ {economia:,.2f}</p></div>", unsafe_allow_html=True)
            st.markdown(f"<p class='metric-label'>Total em Juros</p><div class='metric-value-container'><p class='metric-value'>R$ {total_juros_extra:,.2f}</p></div>", unsafe_allow_html=True)
            st.markdown(f"<p class='metric-label'>Prazo Final</p><div class='metric-value-container'><p class='metric-value'>{len(df_com_extra)} meses</p></div>", unsafe_allow_html=True)
        else:
            st.info("Nenhum cenário com amortização extra para comparar.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)
    st.header("Análise Detalhada da Evolução")
    
    tab_saldo, tab_comp, tab_parcela, tab_pizza, tab_tabela = st.tabs(["📉 Saldo Devedor", "📊 Comp. Mensal", "📉 Evol. da Parcela", "🍕 Custo Total", "📋 Tabela"])
    
    def get_common_plotly_layout(y_title="", legend_title="", show_legend=True):
        layout = go.Layout(height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=TEXT_COLOR),
                           xaxis=dict(showgrid=False, zeroline=False, linecolor=BORDER_COLOR, tickfont=dict(color=SUBTLE_TEXT_COLOR), title_font=dict(color=SUBTLE_TEXT_COLOR)),
                           yaxis=dict(showgrid=False, zeroline=False, linecolor=BORDER_COLOR, tickformat=",.0f", tickfont=dict(color=SUBTLE_TEXT_COLOR), title_font=dict(color=SUBTLE_TEXT_COLOR), title_text=y_title),
                           legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=legend_title, font=dict(color=SUBTLE_TEXT_COLOR)),
                           margin=dict(l=20, r=20, t=50, b=20))
        if not show_legend: layout.update(showlegend=False)
        return layout

    with tab_saldo:
        fig = go.Figure(layout=get_common_plotly_layout(y_title="Saldo Devedor (R$)", legend_title="Cenário"))
        fig.add_trace(go.Scatter(x=df_sem_extra['Mês'], y=df_sem_extra['Saldo_Devedor'], mode='lines', name='Padrão', line=dict(color=SUBTLE_TEXT_COLOR, width=2)))
        if not df_com_extra.empty:
            fig.add_trace(go.Scatter(x=df_com_extra['Mês'], y=df_com_extra['Saldo_Devedor'], mode='lines', name='Com Amortização', line=dict(color=SANTANDER_RED, width=2)))
        st.plotly_chart(fig, use_container_width=True)
        
    with tab_comp:
        fig = go.Figure(layout=get_common_plotly_layout(y_title="Valor da Parcela (R$)"))
        fig.update_layout(barmode='stack', xaxis_title="Meses (primeiros 6 anos)")
        df_view = df_sem_extra[df_sem_extra['Mês'] <= 72]
        fig.add_trace(go.Bar(x=df_view['Mês'], y=df_view['Juros'], name='Juros', marker_color=SANTANDER_RED))
        fig.add_trace(go.Bar(x=df_view['Mês'], y=df_view['Amortização'], name='Amortização', marker_color=PRIMARY_BLUE))
        st.plotly_chart(fig, use_container_width=True)

    with tab_parcela:
        fig = go.Figure(layout=get_common_plotly_layout(y_title="Valor (R$)"))
        fig.add_trace(go.Scatter(x=df_sem_extra['Mês'], y=df_sem_extra['Prestação_Total'], mode='lines', name='Total (Padrão)', line=dict(color=SANTANDER_RED, width=2.5)))
        fig.add_trace(go.Scatter(x=df_sem_extra['Mês'], y=df_sem_extra['Amortização'], mode='lines', name='Amortização (Padrão)', line=dict(color=PRIMARY_BLUE, width=2)))
        if not df_com_extra.empty:
            fig.add_trace(go.Scatter(x=df_com_extra['Mês'], y=df_com_extra['Prestação_Total'], mode='lines', name='Total (Com Amort.)', line=dict(color=SANTANDER_RED, width=2.5, dash='dash')))
            fig.add_trace(go.Scatter(x=df_com_extra['Mês'], y=df_com_extra['Amortização'], mode='lines', name='Amortização (Com Amort.)', line=dict(color=PRIMARY_BLUE, width=2, dash='dash')))
        st.plotly_chart(fig, use_container_width=True)
        
    with tab_pizza:
        pizza_col_1, pizza_col_2 = st.columns(2)
        with pizza_col_1:
            st.subheader("Custo Total (Padrão)")
            if not df_sem_extra.empty:
                labels = ['Principal', 'Juros', 'Taxas/Seguro']; values = [df_sem_extra['Amortização'].sum(), df_sem_extra['Juros'].sum(), df_sem_extra['Taxas/Seguro'].sum()]
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker_colors=[PRIMARY_BLUE, SANTANDER_RED, BORDER_COLOR], marker=dict(line=dict(color='white', width=2)), hoverinfo='label+percent+value')])
                fig.update_layout(height=500, showlegend=True, paper_bgcolor='rgba(0,0,0,0)', font=dict(color=TEXT_COLOR))
                st.plotly_chart(fig, use_container_width=True)
        with pizza_col_2:
            st.subheader("Custo Total (Com Amort.)")
            if not df_com_extra.empty:
                labels = ['Principal', 'Juros', 'Taxas/Seguro']; values = [df_com_extra['Amortização'].sum(), df_com_extra['Juros'].sum(), df_com_extra['Taxas/Seguro'].sum()]
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker_colors=[PRIMARY_BLUE, SANTANDER_RED, BORDER_COLOR], marker=dict(line=dict(color='white', width=2)), hoverinfo='label+percent+value')])
                fig.update_layout(height=500, showlegend=True, paper_bgcolor='rgba(0,0,0,0)', font=dict(color=TEXT_COLOR))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum cenário com amortização extra para comparar.")

    with tab_tabela:
        st.header("Tabela de Amortização Completa")
        if not df_com_extra.empty:
            st.subheader("Cenário com Amortização Extra")
            st.dataframe(df_com_extra, use_container_width=True, height=500)
        st.subheader("Cenário Padrão")
        st.dataframe(df_sem_extra, use_container_width=True, height=500)
else:
    st.error("O 'Valor a ser Financiado' deve ser maior que zero. Ajuste os parâmetros da simulação.")
