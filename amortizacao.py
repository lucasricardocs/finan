# simulador_financiamento_bokeh_ui.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from math import pi

# Importações do Bokeh
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter
from bokeh.transform import cumsum

# -------------------------------
# CONFIGURAÇÃO GERAL
# -------------------------------
st.set_page_config(
    page_title="Simulador de Financiamento (Bokeh)",
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
BORDER_COLOR = "#d1d5db"

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
    [data-testid="stMetric"] {{ background-color: transparent; }}
    [data-testid="stMetricLabel"] {{ font-size: 1rem; }}
    [data-testid="stMetricValue"] {{ font-size: 2rem; }}
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
st.title("Simulador de Financiamento (UI com Bokeh)")

param_col1, param_col2, param_col3 = st.columns(3)
# (Seção de parâmetros inalterada)
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
if entrada < min_entrada: st.warning(f"Atenção: A entrada está abaixo do mínimo recomendado.")
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

    def criar_grafico_pizza_bokeh(dataframe):
        if dataframe.empty: return None
        data = pd.DataFrame({'Componente': ['Principal', 'Juros', 'Taxas/Seguro'], 'Valor': [dataframe['Amortização'].sum(), dataframe['Juros'].sum(), dataframe['Taxas/Seguro'].sum()]})
        data['angle'] = data['Valor'] / data['Valor'].sum() * 2 * pi
        data['color'] = [PRIMARY_BLUE, SANTANDER_RED, BORDER_COLOR]
        data['percent'] = (data['Valor'] / data['Valor'].sum()) * 100
        
        p = figure(height=500, title="", toolbar_location=None, tools="hover", tooltips="@Componente: @Valor{,0.00 a} (@percent{0.0}%)", x_range=(-0.6, 0.6), y_range=(-0.6, 0.6))
        p.annular_wedge(x=0, y=0, inner_radius=0.15, outer_radius=0.4, direction="anticlock",
                        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                        line_color="white", fill_color='color', legend_field='Componente', source=data)
        
        # Estilo do gráfico
        p.axis.axis_label = None; p.axis.visible = False; p.grid.grid_line_color = None
        p.background_fill_color = None; p.border_fill_color = None; p.outline_line_color = None
        p.legend.location = "center"; p.legend.background_fill_alpha = 0; p.legend.border_line_alpha = 0
        p.legend.label_text_color = TEXT_COLOR
        
        return p

    st.header("Análise Comparativa")
    
    col_met_sem, col_met_com = st.columns(2)
    with col_met_sem:
        st.subheader("Cenário Padrão")
        if not df_sem_extra.empty:
            total_pagar, total_juros = df_sem_extra["Prestação_Total"].sum(), df_sem_extra["Juros"].sum()
            st.metric("Custo Total", f"R$ {total_pagar:,.2f}"); st.metric("Total em Juros", f"R$ {total_juros:,.2f}"); st.metric("Prazo Final", f"{len(df_sem_extra)} meses")
            st.bokeh_chart(criar_grafico_pizza_bokeh(df_sem_extra), use_container_width=True)
            
    with col_met_com:
        st.subheader("Cenário com Amortização Extra")
        if not df_com_extra.empty:
            total_pagar_extra, total_juros_extra = df_com_extra["Prestação_Total"].sum(), df_com_extra["Juros"].sum()
            economia = total_pagar - total_pagar_extra
            st.metric("Custo Total", f"R$ {total_pagar_extra:,.2f}", f"- R$ {economia:,.2f}"); st.metric("Total em Juros", f"R$ {total_juros_extra:,.2f}"); st.metric("Prazo Final", f"{len(df_com_extra)} meses")
            st.bokeh_chart(criar_grafico_pizza_bokeh(df_com_extra), use_container_width=True)
        else:
            st.info("Nenhum cenário com amortização extra para comparar.")

    st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)
    st.header("Análise Detalhada da Evolução")
    
    df_plot = df_sem_extra.copy(); df_plot['Cenário'] = 'Padrão'
    if not df_com_extra.empty:
        df_com_extra_plot = df_com_extra.copy(); df_com_extra_plot['Cenário'] = 'Com Amortização'
        df_plot = pd.concat([df_plot, df_com_extra_plot])
    
    tab_saldo, tab_comp, tab_parcela, tab_tabela = st.tabs(["📉 Saldo Devedor", "📊 Composição Mensal", "📉 Evolução da Parcela", "📋 Tabela Detalhada"])
    
    with tab_saldo:
        p = figure(height=500, x_axis_label="Meses", y_axis_label="Saldo Devedor (R$)", tooltips=[("Mês", "@Mês"), ("Saldo", "@Saldo_Devedor{,0.00 a}")])
        source_p = ColumnDataSource(df_plot[df_plot['Cenário'] == 'Padrão'])
        p.line(x='Mês', y='Saldo_Devedor', source=source_p, color=SUBTLE_TEXT_COLOR, legend_label="Padrão", width=2)
        if not df_com_extra.empty:
            source_c = ColumnDataSource(df_plot[df_plot['Cenário'] == 'Com Amortização'])
            p.line(x='Mês', y='Saldo_Devedor', source=source_c, color=SANTANDER_RED, legend_label="Com Amortização", width=2)
        p.grid.visible = False; p.background_fill_alpha = 0; p.border_fill_alpha = 0; p.outline_line_color = None; p.yaxis.formatter = NumeralTickFormatter(format="0,0 a")
        p.legend.location = "top_center"; p.legend.orientation = "horizontal"; p.legend.background_fill_alpha = 0; p.legend.border_line_alpha = 0; p.legend.label_text_color = TEXT_COLOR
        st.bokeh_chart(p, use_container_width=True)
        
    with tab_comp:
        source = ColumnDataSource(df_plot[df_plot['Mês'] <= 72])
        p = figure(height=500, x_range=source.data['Mês'].unique().astype(str), x_axis_label="Meses (primeiros 6 anos)", y_axis_label="Valor da Parcela (R$)", tooltips=[("Mês", "@Mês"),("Componente","$name"),("Valor", "@$name{,0.00 a}")])
        p.vbar_stack(stackers=['Juros', 'Amortização'], x='Mês', source=source, color=[SANTANDER_RED, PRIMARY_BLUE], legend_label=['Juros', 'Amortização'], width=0.9)
        p.grid.visible = False; p.background_fill_alpha = 0; p.border_fill_alpha = 0; p.outline_line_color = None; p.yaxis.formatter = NumeralTickFormatter(format="0,0 a")
        p.legend.location = "top_center"; p.legend.orientation = "horizontal"; p.legend.background_fill_alpha = 0; p.legend.border_line_alpha = 0; p.legend.label_text_color = TEXT_COLOR
        st.bokeh_chart(p, use_container_width=True)

    with tab_parcela:
        p = figure(height=500, x_axis_label="Meses", y_axis_label="Valor (R$)", tooltips=[("Mês", "@Mês"),("Variável", "$name"),("Valor", "@$y{,0.00 a}")])
        if not df_sem_extra.empty:
            source_p = ColumnDataSource(df_sem_extra)
            p.line(x='Mês', y='Prestação_Total', source=source_p, color=SANTANDER_RED, legend_label="Total da Parcela (Padrão)", width=2.5)
            p.line(x='Mês', y='Amortização', source=source_p, color=PRIMARY_BLUE, legend_label="Amortização (Padrão)", width=2)
            p.line(x='Mês', y='Juros', source=source_p, color=SUBTLE_TEXT_COLOR, legend_label="Juros (Padrão)", width=2)
        if not df_com_extra.empty:
            source_c = ColumnDataSource(df_com_extra)
            p.line(x='Mês', y='Prestação_Total', source=source_c, color=SANTANDER_RED, legend_label="Total da Parcela (Com Amort.)", width=2.5, line_dash='dashed')
            p.line(x='Mês', y='Amortização', source=source_c, color=PRIMARY_BLUE, legend_label="Amortização (Com Amort.)", width=2, line_dash='dashed')
            p.line(x='Mês', y='Juros', source=source_c, color=SUBTLE_TEXT_COLOR, legend_label="Juros (Com Amort.)", width=2, line_dash='dashed')
        p.grid.visible = False; p.background_fill_alpha = 0; p.border_fill_alpha = 0; p.outline_line_color = None; p.yaxis.formatter = NumeralTickFormatter(format="0,0 a")
        p.legend.location = "top_center"; p.legend.orientation = "horizontal"; p.legend.background_fill_alpha = 0; p.legend.border_line_alpha = 0; p.legend.label_text_color = TEXT_COLOR; p.legend.click_policy="hide"
        st.bokeh_chart(p, use_container_width=True)

    with tab_tabela:
        if not df_com_extra.empty:
            st.subheader("Cenário com Amortização Extra")
            st.dataframe(df_com_extra, use_container_width=True, height=500)
        st.subheader("Cenário Padrão")
        st.dataframe(df_sem_extra, use_container_width=True, height=500)
else:
    st.error("O 'Valor a ser Financiado' deve ser maior que zero. Ajuste os parâmetros da simulação.")

st.markdown("<hr class='styled-hr'>", unsafe_allow_html=True)
st.caption("Aviso Legal: Esta é uma ferramenta de simulação e os resultados são para fins ilustrativos.")
