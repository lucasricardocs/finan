# simulador_financiamento_plotly_ui.py
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
# ESTILOS E CORES (TEMA CLARO)
# -------------------------------
SANTANDER_RED = "#EC0000"
PRIMARY_BLUE = "#004481"
TEXT_COLOR = "#1f2937"
SUBTLE_TEXT_COLOR = "#4b5563"
BACKGROUND_COLOR = "#f0f2f6"
COMPONENT_BACKGROUND = "#ffffff"
BORDER_COLOR = "#d1d5db"
INPUT_BORDER_COLOR = "#6c757d" # Cinza escuro para a borda dos inputs

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
    [data-testid="stMetric"] {{ background-color: {COMPONENT_BACKGROUND}; padding: 15px; border-radius: 8px; border: 1px solid {BORDER_COLOR}; }}
    [data-testid="stMetricLabel"] {{ font-size: 1rem; color: {SUBTLE_TEXT_COLOR}; }}
    [data-testid="stMetricValue"] {{ font-size: 2rem; color: {TEXT_COLOR}; }}
    
    /* Estilo para os inputs */
    .stNumberInput, .stDateInput, .stRadio > div {{ /* stRadio precisa de > div */
        background-color: {COMPONENT_BACKGROUND};
        border-radius: 8px;
        padding: 5px 10px;
        border: 1px solid {INPUT_BORDER_COLOR}; /* Borda cinza escura */
    }}
    .stDateInput > label, .stNumberInput > label {{ /* Ajustar visibilidade de labels */
        visibility: hidden; 
        height: 0; 
        margin: 0; 
        padding: 0;
    }}
    /* Para labels do radio */
    .stRadio > label {{
        color: {SUBTLE_TEXT_COLOR};
        font-weight: 600;
        margin-bottom: 0.5rem;
    }}
    /* Abas */
    [data-testid="stTabs"] button {{
        color: {SUBTLE_TEXT_COLOR};
        font-weight: 500;
    }}
    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: {SANTANDER_RED};
        font-weight: 600;
        border-bottom: 2px solid {SANTANDER_RED};
    }}
    /* Tabelas */
    .stDataFrame {{
        border: 1px solid {BORDER_COLOR};
        border-radius: 8px;
    }}
    /* Mensagens de info/warning */
    .stAlert {{
        border-radius: 8px;
    }}
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

# --- Seção de Parâmetros ---
with st.container():
    param_col1, param_col2, param_col3 = st.columns(3)
    with param_col1:
        st.markdown("<h5>💵 Valores do Imóvel</h5>", unsafe_allow_html=True)
        valor_imovel = st.number_input("Valor Total (R$)", value=600000.0, format="%.2f", key="valor_imovel", min_value=0.0)
        min_entrada = valor_imovel * 0.20
        entrada = st.number_input("Entrada (R$)", value=max(min_entrada, 120000.0), format="%.2f", key="entrada", min_value=0.0)
        if entrada < min_entrada: st.warning(f"Atenção: A entrada de R$ {entrada:,.2f} está abaixo do mínimo recomendado de R$ {min_entrada:,.2f}.")

    with param_col2:
        st.markdown("<h5>⚙️ Condições do Contrato</h5>", unsafe_allow_html=True)
        taxa_juros = st.number_input("Taxa de Juros Anual (%)", value=10.5, format="%.2f", key="taxa")
        num_parcelas = st.number_input("Prazo (meses)", value=360, step=12, key="parcelas")
        data_inicio = st.date_input("Data de Início", value=datetime.now().date(), key="inicio")
    with param_col3:
        st.markdown("<h5>🚀 Amortização Extra</h5>", unsafe_allow_html=True)
        amortizacao_extra = st.number_input("Valor Extra Mensal (R$)", value=500.0, format="%.2f", key="extra", min_value=0.0)
        tipo_amortizacao = st.radio("Objetivo:", ("Reduzir prazo", "Reduzir parcela"), key="tipo_amortizacao", horizontal=True)

valor_financiado = valor_imovel - entrada
st.info(f"**Valor a ser Financiado:** R$ {valor_financiado:,.2f}  |  **Entrada:** R$ {entrada:,.2f}  |  **Prazo:** {int(num_parcelas)} meses")

st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)

# --- Bloco Principal de Cálculos e Exibição ---
if valor_financiado > 0:
    prazo_meses, taxa_juros_mes = int(num_parcelas), (1 + taxa_juros / 100) ** (1/12) - 1
    df_sem_extra = calcular_financiamento('prazo', valor_financiado, taxa_juros_mes, prazo_meses, 0.0)
    df_com_extra = pd.DataFrame()
    if amortizacao_extra > 0:
        tipo = 'prazo' if tipo_amortizacao == "Reduzir prazo" else 'parcela'
        df_com_extra = calcular_financiamento(tipo, valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra)

    # Função para criar o gráfico de pizza com Plotly
    def criar_grafico_pizza_plotly(dataframe):
        if dataframe.empty: return go.Figure()
        
        labels = ['Principal', 'Juros', 'Taxas/Seguro']
        values = [dataframe['Amortização'].sum(), dataframe['Juros'].sum(), dataframe['Taxas/Seguro'].sum()]
        colors = [PRIMARY_BLUE, SANTANDER_RED, BORDER_COLOR] # Cores ajustadas para o tema claro

        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, 
                                     marker_colors=colors, 
                                     # Adiciona a borda branca de 2px
                                     marker=dict(line=dict(color='white', width=2)), 
                                     # Texto no centro do donut (opcional, mas comum)
                                     # textinfo='percent+label',
                                     hoverinfo='label+percent+value',
                                     hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>"
                                    )])

        fig.update_layout(
            height=500,
            showlegend=True,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente da figura
            plot_bgcolor='rgba(0,0,0,0)',   # Fundo transparente da área de plotagem
            font=dict(color=TEXT_COLOR), # Cor da fonte para o tema claro
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color=SUBTLE_TEXT_COLOR) # Cor da legenda
            )
        )
        return fig

    st.header("Análise Comparativa")
    
    col_met_sem, col_met_com = st.columns(2)
    with col_met_sem:
        st.subheader("Cenário Padrão")
        if not df_sem_extra.empty:
            total_pagar, total_juros = df_sem_extra["Prestação_Total"].sum(), df_sem_extra["Juros"].sum()
            st.metric("Custo Total", f"R$ {total_pagar:,.2f}")
            st.metric("Total em Juros", f"R$ {total_juros:,.2f}")
            st.metric("Prazo Final", f"{len(df_sem_extra)} meses")
            st.plotly_chart(criar_grafico_pizza_plotly(df_sem_extra), use_container_width=True)
    with col_met_com:
        st.subheader("Cenário com Amortização Extra")
        if not df_com_extra.empty:
            total_pagar_extra, total_juros_extra = df_com_extra["Prestação_Total"].sum(), df_com_extra["Juros"].sum()
            economia = total_pagar - total_pagar_extra
            st.metric("Custo Total", f"R$ {total_pagar_extra:,.2f}", f"- R$ {economia:,.2f}")
            st.metric("Total em Juros", f"R$ {total_juros_extra:,.2f}")
            st.metric("Prazo Final", f"{len(df_com_extra)} meses")
            st.plotly_chart(criar_grafico_pizza_plotly(df_com_extra), use_container_width=True)
        else:
            st.info("Nenhum cenário com amortização extra para comparar.")

    st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)
    st.header("Análise Detalhada da Evolução")
    
    df_plot = df_sem_extra.copy(); df_plot['Cenário'] = 'Padrão'
    if not df_com_extra.empty:
        df_com_extra_plot = df_com_extra.copy(); df_com_extra_plot['Cenário'] = 'Com Amortização'
        df_plot = pd.concat([df_plot, df_com_extra_plot])
    
    tab_saldo, tab_comp, tab_parcela, tab_tabela = st.tabs(["📉 Saldo Devedor", "📊 Composição Mensal", "📉 Evolução da Parcela", "📋 Tabela Detalhada"])
    
    # Função para layouts comuns do Plotly
    def get_common_plotly_layout(title="", y_title="", legend_title="", show_legend=True):
        return go.Layout(
            height=500,
            title_text=title,
            title_x=0.05, # Alinha o título um pouco para a esquerda
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=TEXT_COLOR),
            xaxis=dict(showgrid=False, zeroline=False, linecolor=BORDER_COLOR, tickfont=dict(color=SUBTLE_TEXT_COLOR), title_font=dict(color=SUBTLE_TEXT_COLOR)),
            yaxis=dict(showgrid=False, zeroline=False, linecolor=BORDER_COLOR, tickformat=",.0f", tickfont=dict(color=SUBTLE_TEXT_COLOR), title_font=dict(color=SUBTLE_TEXT_COLOR)),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                title=legend_title,
                font=dict(color=SUBTLE_TEXT_COLOR),
                bgcolor='rgba(255,255,255,0.7)', # Fundo sutil para a legenda
                bordercolor=BORDER_COLOR,
                borderwidth=1
            ) if show_legend else None,
            margin=dict(l=20, r=20, t=50, b=20)
        )

    with tab_saldo:
        fig_saldo = go.Figure(layout=get_common_plotly_layout(y_title="Saldo Devedor (R$)", legend_title="Cenário"))
        fig_saldo.add_trace(go.Scatter(x=df_sem_extra['Mês'], y=df_sem_extra['Saldo_Devedor'],
                                       mode='lines', name='Padrão',
                                       line=dict(color=SUBTLE_TEXT_COLOR, width=2)))
        if not df_com_extra.empty:
            fig_saldo.add_trace(go.Scatter(x=df_com_extra['Mês'], y=df_com_extra['Saldo_Devedor'],
                                           mode='lines', name='Com Amortização',
                                           line=dict(color=SANTANDER_RED, width=2)))
        fig_saldo.update_yaxes(tickformat=",.2f") # Formato de moeda para Y
        st.plotly_chart(fig_saldo, use_container_width=True)
        
    with tab_comp:
        df_melted_comp = df_plot[df_plot['Mês'] <= 72].melt(id_vars=['Mês', 'Cenário'], value_vars=['Juros', 'Amortização'], var_name='Componente', value_name='Valor')
        fig_comp = go.Figure()
        
        cenarios = ['Padrão', 'Com Amortização']
        componentes = ['Juros', 'Amortização']
        colors = {
            'Juros': SANTANDER_RED,
            'Amortização': PRIMARY_BLUE
        }
        
        for cenario in cenarios:
            for comp in componentes:
                df_filtered = df_melted_comp[(df_melted_comp['Cenário'] == cenario) & (df_melted_comp['Componente'] == comp)]
                fig_comp.add_trace(go.Bar(
                    x=df_filtered['Mês'],
                    y=df_filtered['Valor'],
                    name=f'{comp} ({cenario})',
                    marker_color=colors[comp],
                    opacity=0.8,
                    showlegend=True
                ))
        
        fig_comp.update_layout(
            barmode='stack',
            xaxis_title="Meses (primeiros 6 anos)",
            yaxis_title="Valor da Parcela (R$)",
            **get_common_plotly_layout(y_title="Valor da Parcela (R$)", legend_title="Cenário / Componente").to_dict()
        )
        fig_comp.update_yaxes(tickformat=",.2f") # Formato de moeda para Y
        st.plotly_chart(fig_comp, use_container_width=True)

    with tab_parcela:
        fig_parcela = go.Figure(layout=get_common_plotly_layout(y_title="Valor (R$)", legend_title="Variável / Cenário"))
        
        if not df_sem_extra.empty:
            fig_parcela.add_trace(go.Scatter(x=df_sem_extra['Mês'], y=df_sem_extra['Prestação_Total'],
                                             mode='lines', name='Total (Padrão)',
                                             line=dict(color=SANTANDER_RED, width=2.5)))
            fig_parcela.add_trace(go.Scatter(x=df_sem_extra['Mês'], y=df_sem_extra['Amortização'],
                                             mode='lines', name='Amortização (Padrão)',
                                             line=dict(color=PRIMARY_BLUE, width=2)))
            fig_parcela.add_trace(go.Scatter(x=df_sem_extra['Mês'], y=df_sem_extra['Juros'],
                                             mode='lines', name='Juros (Padrão)',
                                             line=dict(color=SUBTLE_TEXT_COLOR, width=2)))
        if not df_com_extra.empty:
            fig_parcela.add_trace(go.Scatter(x=df_com_extra['Mês'], y=df_com_extra['Prestação_Total'],
                                             mode='lines', name='Total (Com Amort.)',
                                             line=dict(color=SANTANDER_RED, width=2.5, dash='dash')))
            fig_parcela.add_trace(go.Scatter(x=df_com_extra['Mês'], y=df_com_extra['Amortização'],
                                             mode='lines', name='Amortização (Com Amort.)',
                                             line=dict(color=PRIMARY_BLUE, width=2, dash='dash')))
            fig_parcela.add_trace(go.Scatter(x=df_com_extra['Mês'], y=df_com_extra['Juros'],
                                             mode='lines', name='Juros (Com Amort.)',
                                             line=dict(color=SUBTLE_TEXT_COLOR, width=2, dash='dash')))
        fig_parcela.update_yaxes(tickformat=",.2f") # Formato de moeda para Y
        st.plotly_chart(fig_parcela, use_container_width=True)

    with tab_tabela:
        st.header("Tabela de Amortização Completa")
        if not df_com_extra.empty:
            st.subheader("Cenário com Amortização Extra")
            st.dataframe(df_com_extra, use_container_width=True, height=500)
        st.subheader("Cenário Padrão")
        st.dataframe(df_sem_extra, use_container_width=True, height=500)
else:
    st.error("O 'Valor a ser Financiado' deve ser maior que zero. Ajuste os parâmetros da simulação.")

st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)
st.caption("Aviso Legal: Esta é uma ferramenta de simulação e os resultados são para fins ilustrativos.")
