import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import io
import numpy as np

# -------------------------------
# Cores UBS Corretora
UBS_RED = "#E60000"
UBS_GRAY_LIGHT = "#F5F5F5"
UBS_GRAY_DARK = "#333333"
UBS_WHITE = "#FFFFFF"
UBS_BLACK = "#000000"

# -------------------------------
# Configuração da página
st.set_page_config(page_title="Simulador de Financiamento - UBS", page_icon="🏦", layout="wide")

# CSS customizado
st.markdown(f"""
<style>
.stApp {{
    background-color: {UBS_GRAY_LIGHT};
}}
.stMetric {{
    background-color: {UBS_WHITE};
    color: {UBS_GRAY_DARK};
    border-radius:10px;
    padding:10px;
}}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Função SAC
def calcular_sac(valor_financiado, taxa_juros, prazo_meses, amortizacao_extra=0):
    saldo_devedor = valor_financiado
    amortizacao_mensal = valor_financiado / prazo_meses
    dados = []
    mes = 1

    while saldo_devedor > 0 and mes <= prazo_meses:
        juros = saldo_devedor * taxa_juros
        amortizacao = amortizacao_mensal
        parcela = juros + amortizacao

        # Seguro aproximado 0.044% do saldo
        seguro = saldo_devedor * 0.00044
        taxa_admin = 25.0

        # Adiciona amortização extra
        amortizacao_total = amortizacao + amortizacao_extra
        parcela_total = juros + amortizacao_total + seguro + taxa_admin

        saldo_devedor -= amortizacao_total
        if saldo_devedor < 0:
            amortizacao_total += saldo_devedor
            parcela_total += saldo_devedor
            saldo_devedor = 0

        dados.append([mes, parcela_total, juros, amortizacao_total, saldo_devedor, seguro, taxa_admin])
        mes += 1

    df = pd.DataFrame(dados, columns=["Mês", "Prestação_Total", "Juros", "Amortização", "Saldo_Devedor", "Seguro", "Taxa_Admin"])
    return df

# -------------------------------
# Tabs
tab1, tab2, tab3 = st.tabs(["📥 Parâmetros", "📊 Resultados", "📤 Exportar"])

# --- Tab 1: Inputs ---
with tab1:
    st.header("Parâmetros do Financiamento")
    
    col1, col2 = st.columns(2)
    with col1:
        valor_imovel = st.number_input("💰 Valor do Imóvel (R$)", min_value=100000, value=500000, step=1000)
        valor_entrada = st.number_input("🏦 Valor da Entrada (R$)", min_value=0, max_value=valor_imovel, value=100000, step=1000)
        prazo_anos = st.slider("⏱️ Prazo (anos)", min_value=5, max_value=35, value=20)
    with col2:
        taxa_juros_ano = st.number_input("📈 Taxa de Juros Anual (%)", min_value=0.1, max_value=20.0, value=8.0)
        amortizacao_extra = st.number_input("💵 Amortização Extra Mensal (R$)", min_value=0.0, value=1000.0)
        estrategia = st.selectbox("🎯 Estratégia de amortização extra", ["Reduzir Parcela", "Reduzir Prazo"])
    
    # Conversões e validações
    valor_financiado = valor_imovel - valor_entrada
    prazo_meses = prazo_anos * 12
    taxa_juros_mes = (1 + taxa_juros_ano / 100) ** (1/12) - 1

# --- Tab 2: Resultados ---
with tab2:
    st.header("Resumo da Simulação")
    
    df_normal = calcular_sac(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra=0)
    df_com_amortizacao = calcular_sac(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra=amortizacao_extra)
    
    total_normal = df_normal["Prestação_Total"].sum()
    total_com = df_com_amortizacao["Prestação_Total"].sum()
    economia = total_normal - total_com
    
    # Cards métricas
    st.markdown("### Principais Métricas")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💰 Total Sem Extra", f"R$ {total_normal:,.2f}")
    col2.metric("💰 Total Com Extra", f"R$ {total_com:,.2f}", f"Economia R$ {economia:,.2f}")
    col3.metric("⏳ Prazo Original", f"{len(df_normal)} meses")
    col4.metric("⏳ Prazo Final", f"{len(df_com_amortizacao)} meses")
    col5.metric("💵 Amortização Extra Mensal", f"R$ {amortizacao_extra:,.2f}")

    # Limite de meses para gráficos
    mes_max = (prazo_anos + 5) * 12

    # Dados para gráficos
    df_normal["Cenário"] = "Sem Extra"
    df_com_amortizacao["Cenário"] = "Com Extra"
    df_grafico = pd.concat([df_normal, df_com_amortizacao], ignore_index=True)

    # --- Corrigir cálculo da economia ---
    # Mapear Prestação_Total do cenário sem extra pelo mês
    prestacao_sem_extra_map = df_normal.set_index("Mês")["Prestação_Total"].to_dict()
    df_grafico["Prestação_Sem_Extra"] = df_grafico["Mês"].map(prestacao_sem_extra_map)
    df_grafico["Economia"] = df_grafico.apply(
        lambda x: x["Prestação_Sem_Extra"] - x["Prestação_Total"] if x["Cenário"]=="Com Extra" else 0,
        axis=1
    )
    df_economia = df_grafico[df_grafico["Cenário"]=="Com Extra"].copy()
    df_economia["Economia_Acum"] = df_economia["Economia"].cumsum()

    # 1️⃣ Saldo Devedor
    st.subheader("📈 Evolução do Saldo Devedor")
    chart_saldo = alt.Chart(df_grafico).mark_line(strokeWidth=3).encode(
        x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
        y="Saldo_Devedor",
        color=alt.Color("Cenário", scale=alt.Scale(range=[UBS_GRAY_DARK, UBS_RED])),
        tooltip=["Mês","Saldo_Devedor","Cenário"]
    ).properties(width=700, height=400)
    st.altair_chart(chart_saldo, use_container_width=True)

    # 2️⃣ Composição da Parcela
    st.subheader("📊 Composição da Parcela (Juros x Amortização)")
    df_comp = df_com_amortizacao.melt(id_vars=["Mês"], value_vars=["Juros","Amortização"], var_name="Componente", value_name="Valor")
    chart_comp = alt.Chart(df_comp).mark_area(opacity=0.7).encode(
        x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
        y="Valor",
        color=alt.Color("Componente", scale=alt.Scale(domain=["Juros","Amortização"], range=[UBS_RED, UBS_GRAY_DARK])),
        tooltip=["Mês","Componente","Valor"]
    ).properties(width=700, height=400)
    st.altair_chart(chart_comp, use_container_width=True)

    # 3️⃣ Juros Mensais
    st.subheader("💰 Evolução dos Juros Mensais")
    chart_juros = alt.Chart(df_grafico).mark_line(strokeWidth=2).encode(
        x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
        y="Juros",
        color=alt.Color("Cenário", scale=alt.Scale(range=[UBS_GRAY_DARK, UBS_RED])),
        tooltip=["Mês","Juros","Cenário"]
    ).properties(width=700, height=350)
    st.altair_chart(chart_juros, use_container_width=True)

    # 4️⃣ Amortização Mensal
    st.subheader("🎯 Evolução da Amortização Mensal")
    chart_amort = alt.Chart(df_grafico).mark_bar(opacity=0.7).encode(
        x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
        y="Amortização",
        color=alt.Color("Cenário", scale=alt.Scale(range=[UBS_GRAY_DARK, UBS_RED])),
        tooltip=["Mês","Amortização","Cenário"]
    ).properties(width=700, height=350)
    st.altair_chart(chart_amort, use_container_width=True)

    # 5️⃣ Prestação Total
    st.subheader("💵 Evolução da Prestação Total")
    chart_prest = alt.Chart(df_grafico).mark_line(strokeWidth=2).encode(
        x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
        y="Prestação_Total",
        color=alt.Color("Cenário", scale=alt.Scale(range=[UBS_GRAY_DARK, UBS_RED])),
        tooltip=["Mês","Prestação_Total","Cenário"]
    ).properties(width=700, height=350)
    st.altair_chart(chart_prest, use_container_width=True)

    # 6️⃣ Economia Acumulada
    st.subheader("💸 Economia Acumulada com Amortização Extra")
    chart_econ = alt.Chart(df_economia).mark_line(strokeWidth=2, color=UBS_RED).encode(
        x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
        y="Economia_Acum",
        tooltip=["Mês","Economia_Acum"]
    ).properties(width=700, height=350)
    st.altair_chart(chart_econ, use_container_width=True)

    # 7️⃣ Composição de Custos
    st.subheader("📊 Composição de Custos (Juros + Amortização + Seguro + Taxa Admin)")
    df_custo = df_com_amortizacao.melt(id_vars=["Mês"], value_vars=["Juros","Amortização","Seguro","Taxa_Admin"], var_name="Componente", value_name="Valor")
    chart_custo = alt.Chart(df_custo).mark_area(opacity=0.7).encode(
        x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
        y="Valor",
        color=alt.Color("Componente", scale=alt.Scale(range=[UBS_RED, UBS_GRAY_DARK, "#FFA500", "#008000"])),
        tooltip=["Mês","Componente","Valor"]
    ).properties(width=700, height=400)
    st.altair_chart(chart_custo, use_container_width=True)

# --- Tab 3: Exportar ---
with tab3:
    st.header("📤 Exportar Resultados")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_normal.to_excel(writer, sheet_name="Sem_Amortizacao", index=False)
        df_com_amortizacao.to_excel(writer, sheet_name="Com_Amortizacao", index=False)
        writer.save()
    st.download_button(
        label="📥 Baixar Simulação em Excel",
        data=buffer,
        file_name="simulacao_financiamento_ubs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Rodapé
st.mark
