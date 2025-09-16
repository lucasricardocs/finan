# simulador_santander_comparativo_altair_v3.py
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
    """Calcula a amortização quitando o financiamento mais rápido."""
    if valor_financiado <= 0 or prazo_meses <= 0:
        return pd.DataFrame()
    
    saldo_devedor = valor_financiado
    amortizacao_mensal_fixa = valor_financiado / prazo_meses
    dados = []
    mes = 1

    while saldo_devedor > 0.01:
        juros = saldo_devedor * taxa_juros_mes
        amortizacao = amortizacao_mensal_fixa
        seguro = saldo_devedor * 0.00044
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
        if mes > prazo_meses * 2: # Trava de segurança
            break

    return pd.DataFrame(dados)

def calcular_reducao_parcela(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra_mensal=0.0):
    """Calcula a amortização mantendo o prazo e diminuindo o valor da parcela."""
    if valor_financiado <= 0 or prazo_meses <= 0:
        return pd.DataFrame()

    saldo_devedor = valor_financiado
    dados = []
    prazo_restante = prazo_meses

    for mes in range(1, prazo_meses + 1):
        if saldo_devedor < 0.01: break
        
        amortizacao_mensal_variavel = saldo_devedor / prazo_restante if prazo_restante > 0 else 0
        juros = saldo_devedor * taxa_juros_mes
        seguro = saldo_devedor * 0.00044
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
        <h1 style='margin:0; font-size:24px; color:#111827;'>Simulador de Amortização de Financiamento</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- SEÇÃO DE PARÂMETROS (LARGURA TOTAL) ---
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Parâmetros da Simulação</div>", unsafe_allow_html=True)

param_col1, param_col2 = st.columns(2)

with param_col1:
    st.markdown("##### Detalhes do Financiamento")
    emprestimo = st.number_input("Valor do Empréstimo (R$)", value=500000.0, format="%.2f", key="emprestimo")
    taxa_juros = st.number_input("Taxa de Juros Anual (%)", value=9.93, format="%.2f", key="taxa")
    num_parcelas = st.number_input("Número de Parcelas (meses)", value=360, step=12, key="parcelas")
    data_inicio = st.date_input("Data de Início", value=datetime(2025, 9, 1), key="inicio")
    sistema = st.selectbox("Sistema de Amortização", ["SAC"], key="sistema", disabled=True)

with param_col2:
    st.markdown("##### Plano de Amortização Extra")
    amortizacao_extra = st.number_input("Valor da Amortização Extra Mensal (R$)", value=0.0, format="%.2f", key="extra", min_value=0.0)
    
    tipo_amortizacao = "Nenhum"
    if amortizacao_extra > 0:
        tipo_amortizacao = st.radio(
            "Qual o seu objetivo com a amortização extra?",
            ("Reduzir o prazo do financiamento", "Reduzir o valor das parcelas"),
            key="tipo_amortizacao"
        )
    else:
        st.info("Insira um valor de amortização extra para habilitar as opções de simulação.")

st.markdown("</div>", unsafe_allow_html=True)

# --- BLOCO DE CÁLCULOS (EXECUTADO APÓS OS PARÂMETROS) ---
valor_financiado = emprestimo
prazo_meses = int(num_parcelas)
taxa_juros_mes = (1 + taxa_juros / 100) ** (1/12) - 1

df_sem_extra = calcular_reducao_prazo(valor_financiado, taxa_juros_mes, prazo_meses, 0.0)

df_com_extra = pd.DataFrame()
if amortizacao_extra > 0:
    if tipo_amortizacao == "Reduzir o prazo do financiamento":
        df_com_extra = calcular_reducao_prazo(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra)
    elif tipo_amortizacao == "Reduzir o valor das parcelas":
        df_com_extra = calcular_reducao_parcela(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra)

# --- SEÇÃO DE RESULTADOS (DUAS COLUNAS) ---
col_sem_extra, col_com_extra = st.columns(2)

# --- COLUNA: SEM AMORTIZAÇÃO EXTRA ---
with col_sem_extra:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='comparison-title'>Cenário Padrão</div>", unsafe_allow_html=True)
    
    if not df_sem_extra.empty:
        total_pagar = df_sem_extra["Prestação_Total"].sum()
        total_juros = df_sem_extra["Juros"].sum()
        primeira_parcela = df_sem_extra.iloc[0]["Prestação_Total"]
        ultima_parcela = df_sem_extra.iloc[-1]["Prestação_Total"]
        data_ultima = data_inicio + timedelta(days=30.4375 * len(df_sem_extra))
        
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Total a Pagar</span><span class='metric-value'>R$ {total_pagar:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Total de Juros</span><span class='metric-value'>R$ {total_juros:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Nº de Parcelas</span><span class='metric-value'>{len(df_sem_extra)}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>1ª Parcela</span><span class='metric-value'>R$ {primeira_parcela:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Última Parcela</span><span class='metric-value'>R$ {ultima_parcela:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Fim do Contrato</span><span class='metric-value'>{data_ultima.strftime('%b/%Y')}</span></div>", unsafe_allow_html=True)
        
        st.markdown("<strong>Composição do Pagamento Total</strong>", unsafe_allow_html=True)
        
        # ALTERAÇÃO AQUI: USANDO A SOMA TOTAL
        pie_data_df = pd.DataFrame({
            'Componente': ['Principal', 'Juros', 'Taxas/Seguro'],
            'Valor': [
                df_sem_extra['Amortização'].sum(), 
                df_sem_extra['Juros'].sum(), 
                df_sem_extra['Taxas/Seguro'].sum()
            ]
        })

        chart_pie = alt.Chart(pie_data_df).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Valor", type="quantitative"),
            color=alt.Color(field="Componente", type="nominal",
                            scale=alt.Scale(domain=['Principal', 'Juros', 'Taxas/Seguro'], range=[SANTANDER_BLUE, SANTANDER_RED, SANTANDER_GRAY]),
                            legend=alt.Legend(orient="bottom", title=None))
        ).properties(height=250)
        st.altair_chart(chart_pie, use_container_width=True)
        
    st.markdown("</div>", unsafe_allow_html=True)

# --- COLUNA: COM AMORTIZAÇÃO EXTRA ---
with col_com_extra:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    
    if amortizacao_extra > 0 and not df_com_extra.empty:
        titulo_estrategia = "Redução de Prazo" if tipo_amortizacao == "Reduzir o prazo do financiamento" else "Redução de Parcela"
        st.markdown(f"<div class='comparison-title'>Cenário com Amortização ({titulo_estrategia})</div>", unsafe_allow_html=True)
        
        total_pagar_extra = df_com_extra["Prestação_Total"].sum()
        total_juros_extra = df_com_extra["Juros"].sum()
        primeira_parcela_extra = df_com_extra.iloc[0]["Prestação_Total"]
        ultima_parcela_extra = df_com_extra.iloc[-1]["Prestação_Total"]
        data_ultima_extra = data_inicio + timedelta(days=30.4375 * len(df_com_extra))
        economia = df_sem_extra["Prestação_Total"].sum() - total_pagar_extra
        
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Total a Pagar</span><span class='metric-value'>R$ {total_pagar_extra:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Total de Juros</span><span class='metric-value'>R$ {total_juros_extra:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Nº de Parcelas</span><span class='metric-value'>{len(df_com_extra)}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>1ª Parcela</span><span class='metric-value'>R$ {primeira_parcela_extra:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Última Parcela</span><span class='metric-value'>R$ {ultima_parcela_extra:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Fim do Contrato</span><span class='metric-value'>{data_ultima_extra.strftime('%b/%Y')}</span></div>", unsafe_allow_html=True)
        
        if economia > 0:
            st.success(f"Economia total em juros: R$ {economia:,.2f}")
        
        st.markdown("<strong>Composição do Pagamento Total</strong>", unsafe_allow_html=True)
        
        # ALTERAÇÃO AQUI: USANDO A SOMA TOTAL
        pie_data_extra_df = pd.DataFrame({
            'Componente': ['Principal', 'Juros', 'Taxas/Seguro'],
            'Valor': [
                df_com_extra['Amortização'].sum(), 
                df_com_extra['Juros'].sum(), 
                df_com_extra['Taxas/Seguro'].sum()
            ]
        })

        chart_pie_extra = alt.Chart(pie_data_extra_df).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Valor", type="quantitative"),
            color=alt.Color(field="Componente", type="nominal",
                            scale=alt.Scale(domain=['Principal', 'Juros', 'Taxas/Seguro'], range=[SANTANDER_BLUE, SANTANDER_RED, SANTANDER_GRAY]),
                            legend=alt.Legend(orient="bottom", title=None))
        ).properties(height=250)
        st.altair_chart(chart_pie_extra, use_container_width=True)
        
    else:
        st.markdown("<div class='comparison-title'>Cenário com Amortização</div>", unsafe_allow_html=True)
        st.info("Nenhum cenário com amortização extra foi calculado.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- ANÁLISE DETALHADA (LARGURA TOTAL) ---
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
        titulo_estrategia = "Redução de Prazo" if tipo_amortizacao == "Reduzir o prazo do financiamento" else "Redução de Parcela"
        df_com_extra_plot['Cenário'] = titulo_estrategia
        df_plot = pd.concat([df_sem_extra_plot, df_com_extra_plot])

    chart_saldo_devedor = alt.Chart(df_plot).mark_line().encode(
        x=alt.X('Mês:Q', axis=alt.Axis(title='Meses')),
        y=alt.Y('Saldo_Devedor:Q', axis=alt.Axis(title='Saldo Devedor (R$)')),
        color=alt.Color('Cenário:N', legend=alt.Legend(orient="top", title=None))
    ).properties(
        height=400
    )
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
        <p>
            <strong>Aviso Legal:</strong> Esta é uma ferramenta de simulação e os resultados são para fins ilustrativos. 
            As condições reais do seu financiamento podem variar.
        </p>
        <p>
            Desenvolvido com ❤️ usando Streamlit e Altair.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
