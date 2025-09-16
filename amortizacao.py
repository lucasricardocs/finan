# amortizacao.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import io
import numpy as np

# -------------------------------
# Paleta (mantive tons sóbrios; ajuste se quiser cores da CAIXA/UBS)
PRIM_COLOR = "#E60000"        # destaque (ex: UBS red)
DARK = "#333333"
BG = "#F5F5F5"
WHITE = "#FFFFFF"

# -------------------------------
st.set_page_config(page_title="Simulador SAC/TR - Referência CAIXA", page_icon="🏦", layout="wide")

# CSS simples para visual clean
st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {BG}; }}
    .card {{ background: {WHITE}; padding: 12px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
    .small-muted {{ color: #6b7280; font-size:13px; }}
    hr{{border:0; height:1px; background:#e6e6e6; margin:18px 0;}}
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# Função SAC (mantém amortização fixa, aceita amortização extra mensal, para quando saldo = 0)
def calcular_sac(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra_mensal=0.0):
    saldo_devedor = valor_financiado
    amortizacao_mensal = valor_financiado / prazo_meses
    dados = []
    mes = 1

    while saldo_devedor > 0 and mes <= prazo_meses:
        juros = saldo_devedor * taxa_juros_mes
        amortizacao = amortizacao_mensal
        # seguro aproximado (usar 0.044% como referência)
        seguro = saldo_devedor * 0.00044
        taxa_admin = 25.0

        # soma amortização extra mensal (se houver)
        amortizacao_total = amortizacao + amortizacao_extra_mensal
        prestacao_total = juros + amortizacao_total + seguro + taxa_admin

        # abate do saldo
        saldo_devedor -= amortizacao_total

        # ajuste final se extrapolar
        if saldo_devedor < 0:
            # ajuste da última amortização e prestação
            amortizacao_total += saldo_devedor  # saldo_devedor é negativo
            prestacao_total += saldo_devedor
            saldo_devedor = 0

        dados.append({
            "Mês": mes,
            "Prestação_Total": prestacao_total,
            "Juros": juros,
            "Amortização": amortizacao_total,
            "Saldo_Devedor": saldo_devedor,
            "Seguro": seguro,
            "Taxa_Admin": taxa_admin
        })
        mes += 1

    df = pd.DataFrame(dados)
    return df

# -------------------------------
# Defaults alinhados com as imagens de referência (CAIXA)
# Valor imóvel: R$ 500.000, Entrada: R$ 150.000, Prazo máximo: 420 meses (35 anos),
# Juros nominais ~9.93% a.a. (definido como input abaixo)
DEFAULT_VALOR_IMOVEL = 500_000.0
DEFAULT_ENTRADA = 150_000.0
DEFAULT_PRAZO_ANOS = 35
DEFAULT_TAXA_ANUAL = 9.93   # taxa nominal anual - disponível na imagem de referência

# -------------------------------
# Layout: Tabs
tab1, tab2, tab3 = st.tabs(["📥 Parâmetros", "📊 Resultados", "📤 Exportar"])

# --- Tab 1: Parâmetros ---
with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Parâmetros do Financiamento")
    st.markdown("Use os valores iniciais (ajustados a partir das imagens de referência) ou altere conforme necessário.")
    col1, col2 = st.columns(2)

    with col1:
        valor_imovel = st.number_input("💰 Valor do imóvel (R$)", min_value=1_00_000.0, value=DEFAULT_VALOR_IMOVEL, step=1000.0, format="%.2f")
        valor_entrada = st.number_input("🏦 Valor da entrada (R$)", min_value=0.0, max_value=valor_imovel, value=DEFAULT_ENTRADA, step=1000.0, format="%.2f")
        prazo_anos = st.number_input("⏱️ Prazo do financiamento (anos)", min_value=5, max_value=35, value=DEFAULT_PRAZO_ANOS, step=1)
    with col2:
        taxa_juros_ano = st.number_input("📈 Taxa de juros nominal anual (% a.a.)", min_value=0.0, value=DEFAULT_TAXA_ANUAL, step=0.01, format="%.4f")
        st.markdown("<div class='small-muted'>Na sua referência havia Juros Nominais ≈ 9.93% a.a. e Juros Efetivos ≈ 10.39% a.a.</div>", unsafe_allow_html=True)
        amortizacao_extra = st.number_input("💵 Amortização extra mensal (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
        estrategia = st.selectbox("🎯 Estratégia (apenas informativa nesta versão)", ["Reduzir Parcela (padrão)", "Reduzir Prazo (não implementado)"])

    st.markdown("</div>", unsafe_allow_html=True)

    # validações simples
    if valor_entrada > valor_imovel * 0.7:
        st.warning("A referência mostra cota máxima de financiamento de 70% — entrada maior que 30% é atípica nessa regra.")
    valor_financiado = valor_imovel - valor_entrada
    prazo_meses = int(prazo_anos * 12)
    # converte taxa anual nominal em taxa mensal aproximada (capitalização mensal)
    taxa_juros_mes = (1 + taxa_juros_ano / 100) ** (1/12) - 1

# --- Tab 2: Resultados ---
with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Resumo e Gráficos")
    st.markdown("Resultados calculados pelo Sistema SAC (Sist. de Amortização Constante). A amortização extra é aplicada mensalmente e, nesta versão, reduz saldo (matriz mantém prazo mas para quando saldo = 0).")

    # cálculos
    df_normal = calcular_sac(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra_mensal=0.0)
    df_com = calcular_sac(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra_mensal=amortizacao_extra)

    # métricas
    total_normal = df_normal["Prestação_Total"].sum() if not df_normal.empty else 0.0
    total_com = df_com["Prestação_Total"].sum() if not df_com.empty else 0.0
    economia_total = total_normal - total_com

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Valor Financiado", f"R$ {valor_financiado:,.2f}")
    col2.metric("Total sem extra", f"R$ {total_normal:,.2f}")
    col3.metric("Total com extra", f"R$ {total_com:,.2f}", f"Economia R$ {economia_total:,.2f}")
    col4.metric("Prazo original (meses)", f"{len(df_normal)}")
    col5.metric("Prazo com amortização", f"{len(df_com)}")

    st.markdown("----")

    # limite do eixo X: 0 até prazo + 5 anos
    mes_max = (prazo_anos + 5) * 12

    # preparar df para gráficos comparativos (concat)
    df_normal_plot = df_normal.copy()
    df_normal_plot["Cenário"] = "Sem Extra"
    df_com_plot = df_com.copy()
    df_com_plot["Cenário"] = "Com Extra"
    df_grafico = pd.concat([df_normal_plot, df_com_plot], ignore_index=True, sort=False)

    # CORREÇÃO ECONOMIA: mapear por mês a prestação sem extra
    prest_sem_extra_map = df_normal.set_index("Mês")["Prestação_Total"].to_dict()
    # mapeia (se mês não existir no df_normal -> retorna np.nan)
    df_grafico["Prestacao_Sem_Extra"] = df_grafico["Mês"].map(lambda m: prest_sem_extra_map.get(m, np.nan))
    # calcular economia apenas onde houver valor de referência (prestacao_sem_extra não NaN) e cenário "Com Extra"
    df_grafico["Economia"] = df_grafico.apply(
        lambda r: (r["Prestacao_Sem_Extra"] - r["Prestação_Total"]) if (r["Cenário"] == "Com Extra" and not pd.isna(r["Prestacao_Sem_Extra"])) else 0.0,
        axis=1
    )
    # DataFrame com economia acumulada (somente cenário com extra)
    df_economia = df_grafico[df_grafico["Cenário"] == "Com Extra"].copy()
    if not df_economia.empty:
        df_economia["Economia_Acum"] = df_economia["Economia"].cumsum()
    else:
        df_economia["Economia_Acum"] = []

    # --- GRÁFICOS ---
    # 1) Saldo Devedor
    st.subheader("📈 Evolução do Saldo Devedor")
    chart_saldo = (
        alt.Chart(df_grafico)
        .mark_line(strokeWidth=3)
        .encode(
            x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max]), title="Mês"),
            y=alt.Y("Saldo_Devedor", title="Saldo Devedor (R$)"),
            color=alt.Color("Cenário", scale=alt.Scale(range=[DARK, PRIM_COLOR])),
            tooltip=[alt.Tooltip("Mês:Q"), alt.Tooltip("Saldo_Devedor:Q", format=",.2f"), "Cenário"]
        )
        .properties(height=380)
    )
    st.altair_chart(chart_saldo, use_container_width=True)

    # 2) Composição da parcela (Juros x Amortização) - usa df_com
    st.subheader("📊 Composição da Parcela (Juros x Amortização) - cenário com extra")
    if not df_com.empty:
        df_comp = df_com.melt(id_vars=["Mês"], value_vars=["Juros", "Amortização"], var_name="Componente", value_name="Valor")
        chart_comp = (
            alt.Chart(df_comp)
            .mark_area(opacity=0.7)
            .encode(
                x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max]), title="Mês"),
                y=alt.Y("Valor", title="R$"),
                color=alt.Color("Componente", scale=alt.Scale(domain=["Juros", "Amortização"], range=[PRIM_COLOR, DARK])),
                tooltip=[alt.Tooltip("Mês:Q"), alt.Tooltip("Valor:Q", format=",.2f"), "Componente"]
            )
            .properties(height=380)
        )
        st.altair_chart(chart_comp, use_container_width=True)
    else:
        st.info("Simulação vazia — verifique parâmetros.")

    # 3) Juros Mensais (comparativo)
    st.subheader("💰 Evolução dos Juros Mensais")
    chart_juros = (
        alt.Chart(df_grafico)
        .mark_line()
        .encode(
            x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
            y=alt.Y("Juros", title="Juros (R$)"),
            color=alt.Color("Cenário", scale=alt.Scale(range=[DARK, PRIM_COLOR])),
            tooltip=[alt.Tooltip("Mês:Q"), alt.Tooltip("Juros:Q", format=",.2f"), "Cenário"]
        )
        .properties(height=300)
    )
    st.altair_chart(chart_juros, use_container_width=True)

    # 4) Amortização Mensal (comparativo)
    st.subheader("🎯 Evolução da Amortização Mensal")
    chart_amort = (
        alt.Chart(df_grafico)
        .mark_bar(opacity=0.8)
        .encode(
            x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
            y=alt.Y("Amortização", title="Amortização (R$)"),
            color=alt.Color("Cenário", scale=alt.Scale(range=[DARK, PRIM_COLOR])),
            tooltip=[alt.Tooltip("Mês:Q"), alt.Tooltip("Amortização:Q", format=",.2f"), "Cenário"]
        )
        .properties(height=300)
    )
    st.altair_chart(chart_amort, use_container_width=True)

    # 5) Prestação Total (comparativo)
    st.subheader("💵 Evolução da Prestação Total (inclui seguro e taxa admin)")
    chart_prest = (
        alt.Chart(df_grafico)
        .mark_line()
        .encode(
            x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
            y=alt.Y("Prestação_Total", title="Prestação Total (R$)"),
            color=alt.Color("Cenário", scale=alt.Scale(range=[DARK, PRIM_COLOR])),
            tooltip=[alt.Tooltip("Mês:Q"), alt.Tooltip("Prestação_Total:Q", format=",.2f"), "Cenário"]
        )
        .properties(height=300)
    )
    st.altair_chart(chart_prest, use_container_width=True)

    # 6) Economia Acumulada (somente onde houver mapeamento)
    st.subheader("💸 Economia Acumulada (comparando mês a mês com cenário sem extra)")
    if not df_economia.empty:
        chart_econ = (
            alt.Chart(df_economia)
            .mark_line(color=PRIM_COLOR, strokeWidth=2)
            .encode(
                x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
                y=alt.Y("Economia_Acum", title="Economia Acumulada (R$)"),
                tooltip=[alt.Tooltip("Mês:Q"), alt.Tooltip("Economia_Acum:Q", format=",.2f")]
            )
            .properties(height=320)
        )
        st.altair_chart(chart_econ, use_container_width=True)
    else:
        st.info("Nenhuma economia acumulada calculável (verifique se cenário sem extra tem meses suficientes para comparar).")

    # 7) Composição de Custos (Juros + Amortização + Seguro + Taxa_Admin)
    st.subheader("📊 Composição de Custos - cenário com extra")
    if "Seguro" in df_com.columns and "Taxa_Admin" in df_com.columns:
        df_custo = df_com.melt(id_vars=["Mês"], value_vars=["Juros", "Amortização", "Seguro", "Taxa_Admin"], var_name="Componente", value_name="Valor")
        chart_custo = (
            alt.Chart(df_custo)
            .mark_area(opacity=0.7)
            .encode(
                x=alt.X("Mês", scale=alt.Scale(domain=[0, mes_max])),
                y=alt.Y("Valor", title="R$"),
                color="Componente:N",
                tooltip=[alt.Tooltip("Mês:Q"), alt.Tooltip("Valor:Q", format=",.2f"), "Componente"]
            )
            .properties(height=380)
        )
        st.altair_chart(chart_custo, use_container_width=True)
    else:
        st.info("Dados de seguro/taxa não disponíveis para composição de custos.")

    st.markdown("</div>", unsafe_allow_html=True)

# --- Tab 3: Exportar ---
with tab3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Exportar resultados")
    st.markdown("Baixe as tabelas completas (cenário sem amortização extra e com amortização extra).")

    buffer = io.BytesIO()
    # escreve os dataframes em um arquivo Excel na memória
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_normal.to_excel(writer, sheet_name="Sem_Amortizacao", index=False)
        df_com.to_excel(writer, sheet_name="Com_Amortizacao", index=False)
    buffer.seek(0)
    st.download_button(
        label="📥 Baixar simulação (Excel)",
        data=buffer,
        file_name="simulacao_financiamento_referencia_caixa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------
# Rodapé estilizado e informativo (com ano dinâmico)
current_year = datetime.today().year
st.markdown(
    f"""
    <hr>
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <div style="color:{DARK};">
        <strong>Simulador SAC/TR</strong> — parâmetros iniciais ajustados conforme referência da CAIXA.
        <div style="font-size:12px; color:#6b7280;">Valores apresentados são estimativas e meramente informativos.</div>
      </div>
      <div style="text-align:right; color:{DARK}; font-size:13px;">
        Desenvolvido por você • © {current_year}
      </div>
    </div>
    """,
    unsafe_allow_html=True
)
