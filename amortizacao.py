# simulador_santander_comparativo_altair_v4.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import io

# -------------------------------
# Paleta Santander
SANTANDER_RED = "#EC0000"
SANTANDER_GRAY = "#666666"
SANTANDER_BLUE = "#0066CC"

# -------------------------------
st.set_page_config(
    page_title="Simulador de Amortização de Financiamento",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {{
        background: #f8f9fa;
        font-family: 'Inter', sans-serif;
    }}
    
    .main-header {{
        background: white;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid {SANTANDER_RED};
    }}
    
    .section-card {{
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        height: 100%;
    }}
    
    .params-card {{
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}
    
    .metric-row {{
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #e5e7eb;
    }}
    
    .metric-label {{
        color: #374151;
        font-size: 14px;
    }}
    
    .metric-value {{
        color: #111827;
        font-weight: 600;
        font-size: 14px;
    }}
    
    .section-title {{
        font-size: 18px;
        font-weight: 600;
        color: #111827;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid {SANTANDER_RED};
    }}
    
    .comparison-title {{
        font-size: 16px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 15px;
        text-align: center;
        padding: 10px;
        background: #f3f4f6;
        border-radius: 4px;
    }}
    
    .footer {{
        margin-top: 40px;
        padding: 20px;
        background: #111827;
        color: white;
        text-align: center;
        border-radius: 8px;
        font-size: 14px;
    }}
    .footer a {{
        color: {SANTANDER_RED};
        text-decoration: none;
        font-weight: 600;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# FUNÇÕES DE CÁLCULO

def calcular_reducao_prazo(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra_mensal=0.0):
    if valor_financiado <= 0 or prazo_meses <= 0: return pd.DataFrame()
    
    saldo_devedor = valor_financiado
    amortizacao_mensal_fixa = valor_financiado / prazo_meses
    dados = []
    mes = 1

    while saldo_devedor > 0.01:
        juros = saldo_devedor * taxa_juros_mes
        amortizacao = amortizacao_mensal_fixa
        # CÁLCULO DO SEGURO ATUALIZADO
        seguro = saldo_devedor * 0.0004 
        taxa_admin = 25.0
        amortizacao_total = amortizacao + amortizacao_extra_mensal
        prestacao_total = juros + amortizacao_total + seguro + taxa_admin
        saldo_devedor -= amortizacao_total

        if saldo_devedor < 0:
            amortizacao_total += saldo_devedor 
            prestacao_total += saldo_devedor
            saldo_devedor = 0

        dados.append({
            "Mês": mes, "Prestação_Total": prestacao_total, "Juros": juros,
            "Amortização": amortizacao_total, "Saldo_Devedor": saldo_devedor,
            "Seguro": seguro, "Taxa_Admin": taxa_admin, "Taxas/Seguro": seguro + taxa_admin
        })
        mes += 1
        if mes > prazo_meses * 2: break
    return pd.DataFrame(dados)

def calcular_reducao_parcela(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra_mensal=0.0):
    if valor_financiado <= 0 or prazo_meses <= 0: return pd.DataFrame()

    saldo_devedor = valor_financiado
    dados = []
    prazo_restante = prazo_meses

    for mes in range(1, prazo_meses + 1):
        if saldo_devedor < 0.01: break
        
        amortizacao_mensal_variavel = saldo_devedor / prazo_restante if prazo_restante > 0 else 0
        juros = saldo_devedor * taxa_juros_mes
        # CÁLCULO DO SEGURO ATUALIZADO
        seguro = saldo_devedor * 0.0004
        taxa_admin = 25.0
        amortizacao_total = amortizacao_mensal_variavel + amortizacao_extra_mensal
        prestacao_total = juros + amortizacao_total + seguro + taxa_admin
        saldo_devedor -= amortizacao_total
        
        if saldo_devedor < 0:
            amortizacao_total += saldo_devedor
            prestacao_total += saldo_devedor
            saldo_devedor = 0

        dados.append({
            "Mês": mes, "Prestação_Total": prestacao_total, "Juros": juros,
            "Amortização": amortizacao_total, "Saldo_Devedor": saldo_devedor,
            "Seguro": seguro, "Taxa_Admin": taxa_admin, "Taxas/Seguro": seguro + taxa_admin
        })
        prazo_restante -= 1
    return pd.DataFrame(dados)

# -------------------------------
# INTERFACE DA APLICAÇÃO

st.markdown(
    """
    <div class='main-header'>
        <h1 style='margin:0; font-size:24px; color:#111827;'>Simulador de Financiamento e Amortização</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- SEÇÃO DE PARÂMETROS COM VALOR DO IMÓVEL E ENTRADA ---
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Parâmetros da Simulação</div>", unsafe_allow_html=True)

param_col1, param_col2 = st.columns(2)

with param_col1:
    st.markdown("##### Detalhes do Imóvel e Financiamento")
    valor_imovel = st.number_input("Valor Total do Imóvel (R$)", value=500000.0, format="%.2f", key="valor_imovel", min_value=0.0)
    
    min_entrada = valor_imovel * 0.20
    entrada = st.number_input(
        "Valor da Entrada (R$)", 
        value=max(min_entrada, 100000.0), # Valor inicial padrão
        format="%.2f", 
        key="entrada",
        min_value=0.0
    )
    st.caption(f"Entrada mínima recomendada (20%): R$ {min_entrada:,.2f}")

    if entrada < min_entrada:
        st.warning("O valor da entrada está abaixo dos 20% do valor do imóvel, o que pode afetar a aprovação do financiamento.")
    
    valor_financiado = valor_imovel - entrada
    st.metric("Valor a ser Financiado", f"R$ {valor_financiado:,.2f}")


with param_col2:
    st.markdown("##### Condições do Financiamento")
    taxa_juros = st.number_input("Taxa de Juros Anual (%)", value=9.93, format="%.2f", key="taxa")
    num_parcelas = st.number_input("Prazo do Financiamento (meses)", value=360, step=12, key="parcelas")
    
    st.markdown("##### Amortização Extra (Opcional)")
    amortizacao_extra = st.number_input("Valor da Amortização Extra Mensal (R$)", value=0.0, format="%.2f", key="extra", min_value=0.0)
    
    tipo_amortizacao = "Nenhum"
    if amortizacao_extra > 0:
        tipo_amortizacao = st.radio(
            "Objetivo da amortização extra:",
            ("Reduzir o prazo do financiamento", "Reduzir o valor das parcelas"),
            key="tipo_amortizacao",
            horizontal=True
        )

st.markdown("</div>", unsafe_allow_html=True)


# --- BLOCO DE CÁLCULOS ---
prazo_meses = int(num_parcelas)
taxa_juros_mes = (1 + taxa_juros / 100) ** (1/12) - 1

df_sem_extra = calcular_reducao_prazo(valor_financiado, taxa_juros_mes, prazo_meses, 0.0)

df_com_extra = pd.DataFrame()
if amortizacao_extra > 0:
    if tipo_amortizacao == "Reduzir o prazo do financiamento":
        df_com_extra = calcular_reducao_prazo(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra)
    elif tipo_amortizacao == "Reduzir o valor das parcelas":
        df_com_extra = calcular_reducao_parcela(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra)


# --- SEÇÃO DE RESULTADOS ---
col_sem_extra, col_com_extra = st.columns(2)

def criar_grafico_pizza_total(dataframe, titulo):
    if dataframe.empty:
        return
    
    total_pago = dataframe['Amortização'].sum() + dataframe['Juros'].sum() + dataframe['Taxas/Seguro'].sum()
    
    pie_data_df = pd.DataFrame({
        'Componente': ['Principal', 'Juros', 'Taxas/Seguro'],
        'Valor': [
            dataframe['Amortização'].sum(), 
            dataframe['Juros'].sum(), 
            dataframe['Taxas/Seguro'].sum()
        ]
    })
    pie_data_df['Percentual'] = (pie_data_df['Valor'] / total_pago) * 100
    pie_data_df['Label'] = pie_data_df.apply(lambda row: f"{row['Componente']} {row['Percentual']:.1f}%", axis=1)

    chart_base = alt.Chart(pie_data_df).encode(
        theta=alt.Theta(field="Valor", type="quantitative", stack=True),
        color=alt.Color(field="Componente", type="nominal",
                        scale=alt.Scale(domain=['Principal', 'Juros', 'Taxas/Seguro'], range=[SANTANDER_BLUE, SANTANDER_RED, SANTANDER_GRAY]),
                        legend=None)
    )
    
    chart_arc = chart_base.mark_arc(outerRadius=120, innerRadius=70)
    chart_text = chart_base.mark_text(radius=155, size=12).encode(text='Label:N')
    
    final_chart = (chart_arc + chart_text).properties(
        title=alt.TitleParams(text=titulo, anchor='middle', fontSize=16),
        height=320 # GRÁFICO MAIOR
    ).configure_view(strokeWidth=0)
    
    st.altair_chart(final_chart, use_container_width=True)

with col_sem_extra:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    if not df_sem_extra.empty:
        total_pagar = df_sem_extra["Prestação_Total"].sum()
        total_juros = df_sem_extra["Juros"].sum()
        data_ultima = data_inicio + timedelta(days=30.4375 * len(df_sem_extra))
        
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Custo Total</span><span class='metric-value'>R$ {total_pagar:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Total de Juros</span><span class='metric-value'>R$ {total_juros:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Prazo Final</span><span class='metric-value'>{len(df_sem_extra)} meses</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Término</span><span class='metric-value'>{data_ultima.strftime('%b/%Y')}</span></div>", unsafe_allow_html=True)

        criar_grafico_pizza_total(df_sem_extra, "Composição Total - Cenário Padrão")
        
    st.markdown("</div>", unsafe_allow_html=True)

with col_com_extra:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    if amortizacao_extra > 0 and not df_com_extra.empty:
        titulo_estrategia = "Red. Prazo" if tipo_amortizacao == "Reduzir o prazo do financiamento" else "Red. Parcela"
        total_pagar_extra = df_com_extra["Prestação_Total"].sum()
        total_juros_extra = df_com_extra["Juros"].sum()
        data_ultima_extra = data_inicio + timedelta(days=30.4375 * len(df_com_extra))
        economia = df_sem_extra["Prestação_Total"].sum() - total_pagar_extra
        
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Custo Total</span><span class='metric-value'>R$ {total_pagar_extra:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Total de Juros</span><span class='metric-value'>R$ {total_juros_extra:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Prazo Final</span><span class='metric-value'>{len(df_com_extra)} meses</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Término</span><span class='metric-value'>{data_ultima_extra.strftime('%b/%Y')}</span></div>", unsafe_allow_html=True)

        criar_grafico_pizza_total(df_com_extra, f"Composição Total - Amortização ({titulo_estrategia})")
        
        if economia > 0:
            st.success(f"Economia total em juros: R$ {economia:,.2f}")
    else:
        st.info("Simule uma amortização extra para comparar os cenários.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- ANÁLISE DETALHADA ---
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Análise Detalhada</div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Evolução do Financiamento", "Tabela de Parcelas"])

with tab1:
    st.markdown("##### Evolução do Saldo Devedor")
    df_sem_extra_plot = df_sem_extra[['Mês', 'Saldo_Devedor']].copy()
    df_sem_extra_plot['Cenário'] = 'Padrão'
    df_plot = df_sem_extra_plot
    
    if not df_com_extra.empty:
        df_com_extra_plot = df_com_extra[['Mês', 'Saldo_Devedor']].copy()
        titulo_estrategia = "Red. Prazo" if tipo_amortizacao == "Reduzir o prazo do financiamento" else "Red. Parcela"
        df_com_extra_plot['Cenário'] = f"Com Amortização ({titulo_estrategia})"
        df_plot = pd.concat([df_sem_extra_plot, df_com_extra_plot])

    chart_saldo_devedor = alt.Chart(df_plot).mark_line().encode(
        x=alt.X('Mês:Q', axis=alt.Axis(title='Meses')),
        y=alt.Y('Saldo_Devedor:Q', axis=alt.Axis(title='Saldo Devedor (R$)')),
        color=alt.Color('Cenário:N', legend=alt.Legend(orient="top", title=None))
    ).properties(height=400)
    st.altair_chart(chart_saldo_devedor, use_container_width=True)

with tab2:
    st.markdown("###### Tabela de Amortização (primeiras 24 parcelas)")
    if not df_com_extra.empty:
        st.write("**Cenário com Amortização Extra**")
        st.dataframe(df_com_extra.head(24).style.format("R$ {:,.2f}", subset=["Prestação_Total", "Juros", "Amortização", "Saldo_Devedor", "Taxas/Seguro"]), use_container_width=True)

    st.write("**Cenário Padrão**")
    st.dataframe(df_sem_extra.head(24).style.format("R$ {:,.2f}", subset=["Prestação_Total", "Juros", "Amortização", "Saldo_Devedor", "Taxas/Seguro"]), use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- RODAPÉ ---
st.markdown(
    """
    <div class='footer'>
        <p><strong>Aviso Legal:</strong> Esta é uma ferramenta de simulação e os resultados são para fins ilustrativos.</p>
        <p>Desenvolvido com ❤️ usando Streamlit e Altair.</p>
    </div>
    """,
    unsafe_allow_html=True
)
