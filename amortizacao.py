# simulador_financiamento_v_final.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from contextlib import contextmanager

# -------------------------------
# Paleta de Cores
SANTANDER_RED = "#EC0000"
SANTANDER_GRAY = "#666666"
SANTANDER_BLUE = "#0066CC"

# -------------------------------
# Configuração da Página
st.set_page_config(
    page_title="Simulador de Financiamento e Amortização",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------
# Estilos CSS Customizados
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {{
        background: #f8f9fa;
        font-family: 'Inter', sans-serif;
    }}
    
    .section-card {{
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        height: 100%;
    }}
    
    .metric-row {{
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #e5e7eb;
    }}
    
    .metric-label {{ color: #374151; font-size: 14px; }}
    .metric-value {{ color: #111827; font-weight: 600; font-size: 14px; }}
    
    .section-title {{
        font-size: 24px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid {SANTANDER_RED};
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
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# Função Auxiliar para Criar Containers Estilizados
@contextmanager
def styled_container(class_name: str):
    st.markdown(f"<div class='{class_name}'>", unsafe_allow_html=True)
    yield
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------
# Funções de Cálculo da Amortização
@st.cache_data
def calcular_reducao_prazo(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra_mensal=0.0):
    if valor_financiado <= 0 or prazo_meses <= 0: return pd.DataFrame()
    saldo_devedor = valor_financiado
    amortizacao_mensal_fixa = valor_financiado / prazo_meses
    dados = []
    mes = 1
    while saldo_devedor > 0.01:
        juros, amortizacao = saldo_devedor * taxa_juros_mes, amortizacao_mensal_fixa
        seguro, taxa_admin = saldo_devedor * 0.0004, 25.0
        amortizacao_total = amortizacao + amortizacao_extra_mensal
        prestacao_total = juros + amortizacao_total + seguro + taxa_admin
        saldo_devedor -= amortizacao_total
        if saldo_devedor < 0:
            amortizacao_total += saldo_devedor; prestacao_total += saldo_devedor; saldo_devedor = 0
        dados.append({"Mês": mes, "Prestação_Total": prestacao_total, "Juros": juros, "Amortização": amortizacao_total, "Saldo_Devedor": saldo_devedor, "Seguro": seguro, "Taxa_Admin": taxa_admin, "Taxas/Seguro": seguro + taxa_admin})
        mes += 1
        if mes > prazo_meses * 2: break
    return pd.DataFrame(dados)

@st.cache_data
def calcular_reducao_parcela(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra_mensal=0.0):
    if valor_financiado <= 0 or prazo_meses <= 0: return pd.DataFrame()
    saldo_devedor, dados, prazo_restante = valor_financiado, [], prazo_meses
    for mes in range(1, prazo_meses + 1):
        if saldo_devedor < 0.01: break
        amortizacao_mensal_variavel = saldo_devedor / prazo_restante if prazo_restante > 0 else 0
        juros, seguro, taxa_admin = saldo_devedor * taxa_juros_mes, saldo_devedor * 0.0004, 25.0
        amortizacao_total = amortizacao_mensal_variavel + amortizacao_extra_mensal
        prestacao_total = juros + amortizacao_total + seguro + taxa_admin
        saldo_devedor -= amortizacao_total
        if saldo_devedor < 0:
            amortizacao_total += saldo_devedor; prestacao_total += saldo_devedor; saldo_devedor = 0
        dados.append({"Mês": mes, "Prestação_Total": prestacao_total, "Juros": juros, "Amortização": amortizacao_total, "Saldo_Devedor": saldo_devedor, "Seguro": seguro, "Taxa_Admin": taxa_admin, "Taxas/Seguro": seguro + taxa_admin})
        prazo_restante -= 1
    return pd.DataFrame(dados)

# -------------------------------
# Início da Interface da Aplicação

with styled_container("section-card"):
    st.markdown("<div class='section-title'>Simulador de Financiamento e Amortização</div>", unsafe_allow_html=True)
    param_col1, param_col2 = st.columns(2)
    with param_col1:
        st.markdown("##### Detalhes do Imóvel e Financiamento")
        valor_imovel = st.number_input("Valor Total do Imóvel (R$)", value=600000.0, format="%.2f", key="valor_imovel", min_value=0.0)
        min_entrada = valor_imovel * 0.20
        entrada = st.number_input("Valor da Entrada (R$)", value=max(min_entrada, 120000.0), format="%.2f", key="entrada", min_value=0.0)
        st.caption(f"Entrada mínima recomendada (20%): R$ {min_entrada:,.2f}")
        if entrada < min_entrada: st.warning("O valor da entrada está abaixo dos 20% do valor do imóvel.")
        valor_financiado = valor_imovel - entrada
        st.metric("Valor a ser Financiado", f"R$ {valor_financiado:,.2f}")
    with param_col2:
        st.markdown("##### Condições do Financiamento")
        data_inicio = st.date_input("Data de Início", value=datetime.now().date(), key="inicio")
        taxa_juros = st.number_input("Taxa de Juros Anual (%)", value=10.5, format="%.2f", key="taxa")
        num_parcelas = st.number_input("Prazo do Financiamento (meses)", value=360, step=12, key="parcelas")
        st.markdown("##### Amortização Extra (Opcional)")
        amortizacao_extra = st.number_input("Valor da Amortização Extra Mensal (R$)", value=500.0, format="%.2f", key="extra", min_value=0.0)
        tipo_amortizacao = "Nenhum"
        if amortizacao_extra > 0:
            tipo_amortizacao = st.radio("Objetivo da amortização extra:", ("Reduzir o prazo do financiamento", "Reduzir o valor das parcelas"), key="tipo_amortizacao", horizontal=True)

# --- Bloco Principal de Cálculos e Exibição de Resultados ---
if valor_financiado > 0:
    prazo_meses = int(num_parcelas)
    taxa_juros_mes = (1 + taxa_juros / 100) ** (1/12) - 1
    df_sem_extra = calcular_reducao_prazo(valor_financiado, taxa_juros_mes, prazo_meses, 0.0)
    df_com_extra = pd.DataFrame()
    if amortizacao_extra > 0:
        df_com_extra = calcular_reducao_prazo(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra) if tipo_amortizacao == "Reduzir o prazo do financiamento" else calcular_reducao_parcela(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra)

    def display_metric(label, value): st.markdown(f"<div class='metric-row'><span class='metric-label'>{label}</span><span class='metric-value'>{value}</span></div>", unsafe_allow_html=True)
    def criar_grafico_pizza_total(dataframe, titulo):
        if dataframe.empty: return
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        total_pago = dataframe[['Amortização', 'Juros', 'Taxas/Seguro']].sum().sum()
        pie_data_df = pd.DataFrame({'Componente': ['Principal', 'Juros', 'Taxas/Seguro'], 'Valor': [dataframe['Amortização'].sum(), dataframe['Juros'].sum(), dataframe['Taxas/Seguro'].sum()]})
        pie_data_df['Percentual'] = (pie_data_df['Valor'] / total_pago) * 100
        pie_data_df['Label'] = pie_data_df.apply(lambda row: f"{row['Componente']} {row['Percentual']:.1f}%", axis=1)
        chart_base = alt.Chart(pie_data_df).encode(theta=alt.Theta(field="Valor", type="quantitative", stack=True), color=alt.Color(field="Componente", type="nominal", scale=alt.Scale(domain=['Principal', 'Juros', 'Taxas/Seguro'], range=[SANTANDER_BLUE, SANTANDER_RED, SANTANDER_GRAY]), legend=None))
        chart_arc = chart_base.mark_arc(outerRadius=120, innerRadius=70)
        chart_text = chart_base.mark_text(radius=155, size=12).encode(text='Label:N')
        final_chart = (chart_arc + chart_text).properties(title=alt.TitleParams(text=titulo, anchor='middle', fontSize=16), height=320).configure_view(strokeWidth=0, fill='transparent')
        st.altair_chart(final_chart, use_container_width=True)

    col_sem_extra, col_com_extra = st.columns(2)
    with col_sem_extra:
        with styled_container("section-card"):
            if not df_sem_extra.empty:
                total_pagar, total_juros = df_sem_extra["Prestação_Total"].sum(), df_sem_extra["Juros"].sum()
                data_ultima = data_inicio + timedelta(days=30.4375 * len(df_sem_extra))
                display_metric("Custo Total", f"R$ {total_pagar:,.2f}"); display_metric("Total de Juros", f"R$ {total_juros:,.2f}"); display_metric("Prazo Final", f"{len(df_sem_extra)} meses"); display_metric("Término", data_ultima.strftime('%b/%Y'))
                criar_grafico_pizza_total(df_sem_extra, "Composição Total - Cenário Padrão")
    with col_com_extra:
        with styled_container("section-card"):
            if not df_com_extra.empty and amortizacao_extra > 0:
                titulo_estrategia = "Red. Prazo" if tipo_amortizacao == "Reduzir o prazo do financiamento" else "Red. Parcela"
                total_pagar_extra, total_juros_extra = df_com_extra["Prestação_Total"].sum(), df_com_extra["Juros"].sum()
                data_ultima_extra = data_inicio + timedelta(days=30.4375 * len(df_com_extra))
                economia = df_sem_extra["Prestação_Total"].sum() - total_pagar_extra
                display_metric("Custo Total", f"R$ {total_pagar_extra:,.2f}"); display_metric("Total de Juros", f"R$ {total_juros_extra:,.2f}"); display_metric("Prazo Final", f"{len(df_com_extra)} meses"); display_metric("Término", data_ultima_extra.strftime('%b/%Y'))
                criar_grafico_pizza_total(df_com_extra, f"Composição Total ({titulo_estrategia})")
                if economia > 0: st.success(f"Economia total em juros: R$ {economia:,.2f}")
            else:
                st.info("Simule uma amortização extra para comparar os cenários.")

    with styled_container("section-card"):
        st.markdown("<h2 class='section-title' style='font-size: 18px; font-weight: 600;'>Análise Detalhada da Evolução</h2>", unsafe_allow_html=True)
        tab_saldo, tab_composicao, tab_acumulado, tab_tabela = st.tabs(["Saldo Devedor", "Composição Mensal", "Pagamento Acumulado", "Tabela Detalhada"])
        
        with tab_saldo:
            df_sem_extra_plot = df_sem_extra[['Mês', 'Saldo_Devedor']].assign(Cenário='Padrão')
            df_plot = df_sem_extra_plot
            if not df_com_extra.empty:
                estrategia = "Red. Prazo" if tipo_amortizacao == "Reduzir o prazo do financiamento" else "Red. Parcela"
                df_com_extra_plot = df_com_extra[['Mês', 'Saldo_Devedor']].assign(Cenário=f"Com Amortização ({estrategia})")
                df_plot = pd.concat([df_sem_extra_plot, df_com_extra_plot])
            chart = alt.Chart(df_plot).mark_line().encode(x=alt.X('Mês:Q', axis=alt.Axis(title='Meses')), y=alt.Y('Saldo_Devedor:Q', axis=alt.Axis(title='Saldo Devedor (R$)')), color=alt.Color('Cenário:N', legend=alt.Legend(orient="top", title=None))).properties(height=400).configure_view(fill='transparent')
            st.altair_chart(chart, use_container_width=True)

        with tab_composicao:
            df_plot_comp = df_sem_extra[['Mês', 'Juros', 'Amortização']].assign(Cenário='Padrão')
            if not df_com_extra.empty:
                estrategia = "Red. Prazo" if tipo_amortizacao == "Reduzir o prazo do financiamento" else "Red. Parcela"
                df_plot_comp_extra = df_com_extra[['Mês', 'Juros', 'Amortização']].assign(Cenário=f"Com Amortização ({estrategia})")
                df_plot_comp = pd.concat([df_plot_comp, df_plot_comp_extra])
            
            df_melted = df_plot_comp.melt(id_vars=['Mês', 'Cenário'], value_vars=['Juros', 'Amortização'], var_name='Componente', value_name='Valor')
            chart = alt.Chart(df_melted[df_melted['Mês'] <= 72]).mark_bar().encode(x=alt.X('Mês:O', axis=alt.Axis(title='Meses (primeiros 6 anos)', labelAngle=0)), y=alt.Y('Valor:Q', axis=alt.Axis(title='Valor da Parcela (R$)')), color=alt.Color('Componente:N', scale=alt.Scale(domain=['Juros', 'Amortização'], range=[SANTANDER_RED, SANTANDER_BLUE]), legend=alt.Legend(orient="top", title="Componente")), tooltip=['Mês', 'Cenário', 'Componente', 'Valor']).facet(row=alt.Row('Cenário:N', title=None, header=alt.Header(labelFontSize=14))).properties(height=200).configure_view(fill='transparent')
            st.altair_chart(chart, use_container_width=True)

        with tab_acumulado:
            df_sem_extra_acum = df_sem_extra.copy()
            df_sem_extra_acum[['Juros Acumulados', 'Principal Pago']] = df_sem_extra_acum[['Juros', 'Amortização']].cumsum()
            df_sem_extra_acum['Cenário'] = 'Padrão'
            df_plot_acum = df_sem_extra_acum
            if not df_com_extra.empty:
                df_com_extra_acum = df_com_extra.copy()
                df_com_extra_acum[['Juros Acumulados', 'Principal Pago']] = df_com_extra_acum[['Juros', 'Amortização']].cumsum()
                estrategia = "Red. Prazo" if tipo_amortizacao == "Reduzir o prazo do financiamento" else "Red. Parcela"
                df_com_extra_acum['Cenário'] = f"Com Amortização ({estrategia})"
                df_plot_acum = pd.concat([df_sem_extra_acum, df_com_extra_acum])
            
            df_melted = df_plot_acum.melt(id_vars=['Mês', 'Cenário'], value_vars=['Juros Acumulados', 'Principal Pago'], var_name='Componente', value_name='Valor Acumulado')
            chart = alt.Chart(df_melted).mark_area().encode(x=alt.X('Mês:Q', axis=alt.Axis(title='Meses')), y=alt.Y('Valor Acumulado:Q', axis=alt.Axis(title='Valor Acumulado (R$)')), color=alt.Color('Componente:N', scale=alt.Scale(domain=['Juros Acumulados', 'Principal Pago'], range=[SANTANDER_RED, SANTANDER_BLUE]), legend=alt.Legend(orient="top", title="Componente")), tooltip=['Mês', 'Cenário', 'Componente', 'Valor Acumulado']).facet(row=alt.Row('Cenário:N', title=None, header=alt.Header(labelFontSize=14))).properties(height=200).configure_view(fill='transparent')
            st.altair_chart(chart, use_container_width=True)

        with tab_tabela:
            st.markdown("###### Tabela de Amortização (primeiras 24 parcelas)")
            if not df_com_extra.empty:
                st.write("**Cenário com Amortização Extra**")
                st.dataframe(df_com_extra.head(24).style.format("R$ {:,.2f}", subset=["Prestação_Total", "Juros", "Amortização", "Saldo_Devedor", "Taxas/Seguro"]), use_container_width=True)
            st.write("**Cenário Padrão**")
            st.dataframe(df_sem_extra.head(24).style.format("R$ {:,.2f}", subset=["Prestação_Total", "Juros", "Amortização", "Saldo_Devedor", "Taxas/Seguro"]), use_container_width=True)

else:
    st.error("O 'Valor a ser Financiado' deve ser maior que zero. Ajuste o valor do imóvel ou da entrada.")

with styled_container("footer"):
    st.markdown("<p><strong>Aviso Legal:</strong> Esta é uma ferramenta de simulação e os resultados são para fins ilustrativos.</p><p>Desenvolvido com ❤️ usando Streamlit e Altair.</p>", unsafe_allow_html=True)
