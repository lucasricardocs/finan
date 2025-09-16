import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# --- CONFIGURAÇÕES DA PÁGINA E ESTILOS ---
st.set_page_config(page_title="Simulador com Amortização Extra", layout="wide")

st.title('📊 Simulador de Financiamento com Análise Gráfica')
st.markdown("Calcule seu financiamento, simule amortizações extras e analise os dados com múltiplos gráficos.")

# --- DADOS BASE (TAXAS ATUALIZADAS) ---
TAXAS_BASE = {
    'TR + Taxa Fixa': {'taxa_padrao': 0.1129, 'taxa_servidor': 0.1099},
    'IPCA + Taxa Fixa': {'taxa_padrao': 0.0485, 'taxa_servidor': 0.0395},
    'Poupança + Taxa Fixa': {'taxa_padrao': 0.0335, 'taxa_servidor': 0.0315},
    'Taxa Fixa': {'taxa_padrao': 0.1250, 'taxa_servidor': 0.1200},
}

# --- FUNÇÕES DE CÁLCULO ---

def calcular_financiamento(valor_financiado, prazo_meses, modalidade, taxa_juros_aa, tr_anual=0.0, ipca_anual=0.0, selic_anual=0.0):
    taxa_juros_mensal = (1 + taxa_juros_aa)**(1/12) - 1
    amortizacao_mensal = valor_financiado / prazo_meses
    
    tr_mensal = (1 + tr_anual)**(1/12) - 1
    ipca_mensal = (1 + ipca_anual)**(1/12) - 1

    saldo_devedor = valor_financiado
    dados = []

    for mes in range(1, prazo_meses + 1):
        correcao_monetaria = 0
        if modalidade == 'TR + Taxa Fixa':
            correcao_monetaria = saldo_devedor * tr_mensal
        elif modalidade == 'IPCA + Taxa Fixa':
            correcao_monetaria = saldo_devedor * ipca_mensal
        elif modalidade == 'Poupança + Taxa Fixa':
            rend_poup_anual = 0.70 * selic_anual if selic_anual <= 0.085 else 0.0617 + tr_anual
            rend_poup_mensal = (1 + rend_poup_anual)**(1/12) - 1
            correcao_monetaria = saldo_devedor * rend_poup_mensal

        saldo_devedor += correcao_monetaria
        juros_mes = saldo_devedor * taxa_juros_mensal
        prestacao = amortizacao_mensal + juros_mes
        saldo_devedor -= amortizacao_mensal

        dados.append({
            'Parcela': mes,
            'Amortização': amortizacao_mensal,
            'Juros': juros_mes,
            'Correção Monetária': correcao_monetaria,
            'Prestação': prestacao,
            'Saldo Devedor': max(saldo_devedor, 0)
        })

    return pd.DataFrame(dados)

# --- FUNÇÕES DE GRÁFICOS ---

def criar_grafico_evolucao(df):
    """Cria um gráfico de linhas (NÃO interativo) com a evolução da Prestação, Juros e Amortização."""
    df_melted = df.melt(id_vars=['Parcela'], value_vars=['Prestação', 'Juros', 'Amortização'], var_name='Componente', value_name='Valor')
    chart = alt.Chart(df_melted).mark_line().encode(
        x=alt.X('Parcela', title='Mês da Parcela'),
        y=alt.Y('Valor', title='Valor (R$)'),
        color=alt.Color('Componente', title='Componente da Parcela', scale=alt.Scale(scheme='category10')),
        tooltip=['Parcela', 'Componente', alt.Tooltip('Valor', format='~s')]
    ).properties(title='Evolução da Prestação, Juros e Amortização', height=350)
    return chart

def criar_grafico_composicao_total(valor_financiado, df_atual):
    """Cria um gráfico de pizza mostrando a composição do custo total."""
    total_juros = df_atual['Juros'].sum()
    total_correcao = df_atual['Correção Monetária'].sum()
    
    data = pd.DataFrame({
        'Componente': ['Principal', 'Juros + Correção'],
        'Valor': [valor_financiado, total_juros + total_correcao]
    })
    
    chart = alt.Chart(data).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field="Valor", type="quantitative"),
        color=alt.Color(field="Componente", type="nominal", title="Composição do Custo", scale=alt.Scale(scheme='viridis')),
        tooltip=['Componente', alt.Tooltip('Valor', format='$,.2f')]
    ).properties(title='Custo Total: Principal vs. Juros')
    return chart

def criar_grafico_saldo_devedor(df_atual, valor_financiado):
    """Cria um gráfico de área mostrando Saldo Devedor vs. Principal Pago."""
    df_plot = pd.DataFrame({
        'Parcela': df_atual['Parcela'],
        'Saldo Devedor': df_atual['Saldo Devedor'],
        'Principal Pago': valor_financiado - df_atual['Saldo Devedor']
    })
    df_melted = df_plot.melt(id_vars=['Parcela'], value_vars=['Saldo Devedor', 'Principal Pago'], var_name='Variável', value_name='Valor')
    
    chart = alt.Chart(df_melted).mark_area(opacity=0.7).encode(
        x=alt.X("Parcela", title="Mês da Parcela"),
        y=alt.Y("Valor:Q", stack='zero', title="Valor (R$)"),
        color=alt.Color("Variável:N", title="Componente", scale=alt.Scale(scheme='set2')),
        tooltip=['Parcela', 'Variável', alt.Tooltip('Valor', format='~s')]
    ).properties(title='Evolução: Saldo Devedor vs. Principal Pago', height=350)
    return chart

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'simulacao_ativa' not in st.session_state:
    st.session_state.simulacao_ativa = None

# --- INTERFACE PRINCIPAL ---
st.header("1. Configure sua Simulação")
# ... (código da interface de input permanece o mesmo) ...
col1, col2, col3 = st.columns(3)
with col1:
    valor_imovel = st.number_input('Valor do imóvel (R$)', min_value=100000.0, step=10000.0, value=500000.0)
    modalidade = st.selectbox('Modalidade de Financiamento', options=list(TAXAS_BASE.keys()))
with col2:
    valor_entrada = st.number_input('Valor da entrada (R$)', min_value=0.0, step=5000.0, value=100000.0)
    is_servidor = st.checkbox('Sou funcionário público', help="Reduz a taxa de juros da simulação.")
with col3:
    prazo_anos = st.slider('Prazo do financiamento (anos)', min_value=5, max_value=35, value=30)

tr_anual, ipca_anual, selic_anual = 0.0, 0.0, 0.0
st.markdown("---")
st.subheader("Projeções dos Indexadores (se aplicável)")
col_idx1, col_idx2, col_idx3 = st.columns(3)

if modalidade == 'TR + Taxa Fixa':
    with col_idx1:
        tr_anual = st.slider('Projeção da TR (anual %)', 0.0, 5.0, 1.5, 0.1, key='tr_slider') / 100.0
elif modalidade == 'IPCA + Taxa Fixa':
    with col_idx1:
        st.warning("Atenção: O IPCA pode variar, aumentando o risco.")
        ipca_anual = st.slider('Projeção do IPCA (anual %)', 2.0, 15.0, 4.5, 0.1, key='ipca_slider') / 100.0
elif modalidade == 'Poupança + Taxa Fixa':
    with col_idx1:
        st.warning("Atenção: Sua parcela varia com a Selic.")
        selic_anual = st.slider('Projeção da Selic (anual %)', 5.0, 20.0, 10.5, 0.25, key='selic_slider') / 100.0
    with col_idx2:
        tr_anual = st.slider('Projeção da TR (anual %)', 0.0, 5.0, 1.5, 0.1, key='tr_poup_slider') / 100.0

if st.button('Iniciar / Resetar Simulação', type="primary"):
    valor_financiado = valor_imovel - valor_entrada
    if valor_financiado <= 0:
        st.error("O valor do imóvel deve ser maior que o da entrada.")
        st.session_state.simulacao_ativa = None
    else:
        prazo_meses = prazo_anos * 12
        taxa_key = 'taxa_servidor' if is_servidor else 'taxa_padrao'
        taxa_juros_aa = TAXAS_BASE[modalidade][taxa_key]
        df_sim = calcular_financiamento(valor_financiado, prazo_meses, modalidade, taxa_juros_aa, tr_anual, ipca_anual, selic_anual)
        st.session_state.simulacao_ativa = {
            'tabela_original': df_sim.copy(), 'tabela_atual': df_sim.copy(),
            'amortizacao_mensal': df_sim.iloc[0]['Amortização'], 'prazo_original_meses': prazo_meses,
            'valor_financiado': valor_financiado, 'taxa_juros_aa': taxa_juros_aa,
            'parcelas_amortizadas': 0
        }
        st.success("Simulação criada! Role para baixo para ver os detalhes e amortizar.")

st.markdown("---")

# --- SEÇÃO DE RESULTADOS E AMORTIZAÇÃO ---
if st.session_state.simulacao_ativa:
    sim = st.session_state.simulacao_ativa
    df_atual = sim['tabela_atual']
    
    st.header("2. Resultados e Amortização Extra")

    # Seção de Amortização
    with st.container(border=True):
        st.subheader("Amortizar Saldo Devedor (Reduzindo Prazo)")
        col_amort1, col_amort2 = st.columns([1, 1])
        with col_amort1:
            valor_amortizacao = st.number_input("Valor a ser amortizado (R$)", min_value=0.0, step=100.0, value=10000.0)
        if st.button("Amortizar Agora"):
            amortizacao_base = sim['amortizacao_mensal']
            if valor_amortizacao > 0 and amortizacao_base > 0:
                parcelas_a_quitar = int(np.floor(valor_amortizacao / amortizacao_base))
                if parcelas_a_quitar > 0:
                    df_atual = df_atual.iloc[:-parcelas_a_quitar]
                    sim['tabela_atual'] = df_atual
                    sim['parcelas_amortizadas'] += parcelas_a_quitar
                    st.success(f"🎉 Valor amortizado! Você quitou o equivalente a **{parcelas_a_quitar} parcelas** do final do seu contrato.")
                else:
                    st.warning("O valor é muito baixo para quitar ao menos uma parcela de amortização.")
            else:
                st.error("Valor de amortização inválido.")
            st.rerun()

    # Métricas
    prazo_restante_meses = len(df_atual)
    prazo_restante_anos = prazo_restante_meses / 12
    st.subheader("Situação Atual do Financiamento")
    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
    col_metric1.metric("Prazo Restante", f"{prazo_restante_meses} meses (~{prazo_restante_anos:.1f} anos)")
    col_metric2.metric("Parcelas Quitadas (Extra)", f"{sim['parcelas_amortizadas']} parcelas")
    col_metric3.metric("Próxima Parcela", f"R$ {df_atual.iloc[0]['Prestação']:,.2f}" if not df_atual.empty else "Quitado")
    col_metric4.metric("Saldo Devedor Atual", f"R$ {df_atual['Amortização'].sum():,.2f}" if not df_atual.empty else "R$ 0,00")

    st.subheader("Análise Gráfica do Financiamento")
    
    # Gráfico principal
    st.altair_chart(criar_grafico_evolucao(df_atual), use_container_width=True)
    
    # Gráficos secundários
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.altair_chart(criar_grafico_composicao_total(sim['valor_financiado'], df_atual), use_container_width=True)
    with col_g2:
        st.altair_chart(criar_grafico_saldo_devedor(df_atual, sim['valor_financiado']), use_container_width=True)

    with st.expander("Ver tabela de amortização restante"):
        st.dataframe(df_atual.style.format(formatter={
            'Amortização': "R$ {:,.2f}", 'Juros': "R$ {:,.2f}", 'Correção Monetária': "R$ {:,.2f}",
            'Prestação': "R$ {:,.2f}", 'Saldo Devedor': "R$ {:,.2f}"
        }), use_container_width=True)

else:
    st.info("Configure os dados e clique em 'Iniciar Simulação' para começar.")
