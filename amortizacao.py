import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import io

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

        # Adiciona amortização extra mensal
        amortizacao_total = amortizacao + amortizacao_extra
        parcela_total = juros + amortizacao_total

        saldo_devedor -= amortizacao_total
        if saldo_devedor < 0:
            amortizacao_total += saldo_devedor
            parcela_total += saldo_devedor
            saldo_devedor = 0

        dados.append([mes, parcela_total, juros, amortizacao_total, saldo_devedor])
        mes += 1

    df = pd.DataFrame(dados, columns=["Mês", "Parcela", "Juros", "Amortização", "Saldo_Devedor"])
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
    
    total_normal = df_normal["Parcela"].sum()
    total_com = df_com_amortizacao["Parcela"].sum()
    economia = total_normal - total_com
    
    # Cards métricas
    st.markdown("### Principais Métricas")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Sem Extra", f"R$ {total_normal:,.2f}")
    col2.metric("💰 Total Com Extra", f"R$ {total_com:,.2f}", f"Economia R$ {economia:,.2f}")
    col3.metric("⏳ Prazo Original", f"{len(df_normal)} meses")
    col4.metric("⏳ Prazo Final", f"{len(df_com_amortizacao)} meses")
    
    # Tabela SAC
    st.subheader("📋 Tabela de Amortização - Primeiros 24 Meses")
    st.dataframe(df_com_amortizacao.head(24).style.format({
        "Parcela":"R${:,.2f}", "Juros":"R${:,.2f}", "Amortização":"R${:,.2f}", "Saldo_Devedor":"R${:,.2f}"
    }))

    # Limite de meses para gráficos
    mes_max = (prazo_anos + 5) * 12
    
    # Gráfico Saldo Devedor
    st.subheader("📈 Evolução do Saldo Devedor")
    df_grafico = pd.concat([
        df_normal.assign(Cenário="Sem Extra"),
        df_com_amortizacao.assign(Cenário="Com Extra")
    ])
    chart_saldo = alt.Chart(df_grafico).mark_line(strokeWidth=3).encode(
        x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
        y="Saldo_Devedor",
        color=alt.Color("Cenário", scale=alt.Scale(range=[UBS_GRAY_DARK, UBS_RED])),
        tooltip=["Mês","Saldo_Devedor","Cenário"]
    ).properties(width=700, height=400)
    st.altair_chart(chart_saldo, use_container_width=True)
    
    # Gráfico Composição (Juros x Amortização)
    st.subheader("📊 Composição da Parcela (Juros x Amortização)")
    df_comp = df_com_amortizacao[df_com_amortizacao["Mês"] <= mes_max]
    df_comp = df_comp.melt(id_vars="Mês", var_name="Componente", value_name="Valor")
    
    chart_comp = alt.Chart(df_comp).mark_area(opacity=0.7).encode(
        x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
        y="Valor",
        color=alt.Color("Componente", scale=alt.Scale(domain=["Juros","Amortização"], range=[UBS_RED, UBS_GRAY_DARK])),
        tooltip=["Mês","Componente","Valor"]
    ).properties(width=700, height=400)
    st.altair_chart(chart_comp, use_container_width=True)

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
st.markdown("---")
st.markdown("*Simulador de Financiamento - UBS Corretora - Clean & Profissional*")
