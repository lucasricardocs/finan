import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# --- CONFIGURAÇÕES DA PÁGINA E ESTILOS ---
st.set_page_config(page_title="Simulador Avançado de Financiamento", layout="wide")

st.title('💰 Simulador Avançado de Financiamento Imobiliário')
st.markdown("""
Use este simulador para comparar diferentes modalidades de financiamento da Caixa.
Preencha os dados na barra lateral e adicione simulações para comparar os resultados.
""")

# --- DADOS BASE (TAXAS ATUALIZADAS COM BASE NA PESQUISA) ---
# Fonte: Pesquisa em sites de notícias e da própria Caixa. As taxas podem variar.
# As taxas aqui são nominais anuais.
TAXAS_BASE = {
    'TR + Taxa Fixa': {'taxa_padrao': 0.1129, 'taxa_servidor': 0.1099},
    'IPCA + Taxa Fixa': {'taxa_padrao': 0.0485, 'taxa_servidor': 0.0395},
    'Poupança + Taxa Fixa': {'taxa_padrao': 0.0335, 'taxa_servidor': 0.0315},
    'Taxa Fixa': {'taxa_padrao': 0.1250, 'taxa_servidor': 0.1200},
}

# --- FUNÇÕES DE CÁLCULO ---

def calcular_financiamento(
    valor_financiado, prazo_meses, modalidade, taxa_juros_aa,
    tr_anual=0.0, ipca_anual=0.0, selic_anual=0.0
):
    """
    Calcula a tabela de amortização (SAC) para diferentes modalidades de financiamento.
    A correção monetária é aplicada ao saldo devedor antes do cálculo dos juros.
    """
    taxa_juros_mensal = (1 + taxa_juros_aa)**(1/12) - 1
    amortizacao_mensal = valor_financiado / prazo_meses
    
    # Converte taxas anuais dos indexadores para mensais
    tr_mensal = (1 + tr_anual)**(1/12) - 1
    ipca_mensal = (1 + ipca_anual)**(1/12) - 1

    saldo_devedor = valor_financiado
    dados = []

    for mes in range(1, prazo_meses + 1):
        # 1. Correção do Saldo Devedor pelo indexador
        correcao_monetaria = 0
        if modalidade == 'TR + Taxa Fixa':
            correcao_monetaria = saldo_devedor * tr_mensal
        elif modalidade == 'IPCA + Taxa Fixa':
            correcao_monetaria = saldo_devedor * ipca_mensal
        elif modalidade == 'Poupança + Taxa Fixa':
            # Rendimento da poupança: 70% da Selic se Selic <= 8.5%, ou 0.5% a.m. + TR se Selic > 8.5%
            if selic_anual <= 0.085:
                rend_poup_anual = 0.70 * selic_anual
            else:
                rend_poup_anual = 0.0617 + tr_anual # 6.17% a.a. é aprox. 0.5% a.m.
            
            rend_poup_mensal = (1 + rend_poup_anual)**(1/12) - 1
            correcao_monetaria = saldo_devedor * rend_poup_mensal

        saldo_devedor += correcao_monetaria

        # 2. Cálculo dos Juros sobre o saldo corrigido
        juros_mes = saldo_devedor * taxa_juros_mensal
        
        # 3. Cálculo da Prestação
        prestacao = amortizacao_mensal + juros_mes
        
        # 4. Atualização do Saldo Devedor
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


def criar_grafico_evolucao(df):
    """Cria um gráfico com a evolução da Prestação, Juros e Amortização."""
    df_melted = df.melt(
        id_vars=['Parcela'], 
        value_vars=['Prestação', 'Juros', 'Amortização'],
        var_name='Componente', 
        value_name='Valor'
    )
    
    chart = alt.Chart(df_melted).mark_line().encode(
        x=alt.X('Parcela', title='Mês da Parcela'),
        y=alt.Y('Valor', title='Valor (R$)'),
        color=alt.Color('Componente', title='Componente da Parcela'),
        tooltip=['Parcela', 'Componente', alt.Tooltip('Valor', format='~s')]
    ).properties(
        title='Evolução da Prestação, Juros e Amortização (SAC)',
        height=350
    ).interactive()
    
    return chart

# --- INTERFACE DO USUÁRIO (SIDEBAR) ---

st.sidebar.header('Dados para Nova Simulação')

valor_imovel = st.sidebar.number_input('Valor do imóvel (R$)', min_value=100000.0, step=10000.0, value=500000.0)
valor_entrada = st.sidebar.number_input('Valor da entrada (R$)', min_value=0.0, step=5000.0, value=100000.0)
prazo_anos = st.sidebar.slider('Prazo do financiamento (anos)', min_value=5, max_value=35, value=30)

is_servidor = st.sidebar.checkbox('Sou funcionário público', help="Funcionários públicos podem ter acesso a taxas de juros reduzidas.")

st.sidebar.divider()

modalidade = st.sidebar.selectbox(
    'Escolha a Modalidade de Financiamento',
    options=list(TAXAS_BASE.keys())
)

# Inputs condicionais baseados na modalidade
tr_anual, ipca_anual, selic_anual = 0.0, 0.0, 0.0

if modalidade == 'TR + Taxa Fixa':
    tr_anual = st.sidebar.slider('Projeção da TR (anual %)', 0.0, 5.0, 1.5, 0.1) / 100.0
elif modalidade == 'IPCA + Taxa Fixa':
    st.sidebar.warning("Atenção: O IPCA pode variar muito, aumentando o risco do seu financiamento.")
    ipca_anual = st.sidebar.slider('Projeção do IPCA (anual %)', 2.0, 15.0, 4.5, 0.1) / 100.0
elif modalidade == 'Poupança + Taxa Fixa':
    st.sidebar.warning("Atenção: O rendimento da poupança varia com a Selic, alterando sua parcela.")
    selic_anual = st.sidebar.slider('Projeção da Selic (anual %)', 5.0, 20.0, 10.5, 0.25) / 100.0
    tr_anual = st.sidebar.slider('Projeção da TR (anual %)', 0.0, 5.0, 1.5, 0.1) / 100.0


# --- LÓGICA PRINCIPAL ---

if 'simulacoes' not in st.session_state:
    st.session_state['simulacoes'] = []

if st.sidebar.button('Adicionar Simulação', type="primary"):
    valor_financiado = valor_imovel - valor_entrada
    prazo_meses = prazo_anos * 12

    if valor_financiado <= 0:
        st.sidebar.error("O valor do imóvel deve ser maior que o da entrada.")
    else:
        taxa_key = 'taxa_servidor' if is_servidor else 'taxa_padrao'
        taxa_juros_aa = TAXAS_BASE[modalidade][taxa_key]

        df_sim = calcular_financiamento(
            valor_financiado, prazo_meses, modalidade, taxa_juros_aa,
            tr_anual, ipca_anual, selic_anual
        )
        
        sim_data = {
            'nome': f"{modalidade} ({'Servidor' if is_servidor else 'Padrão'})",
            'modalidade': modalidade,
            'valor_imovel': valor_imovel,
            'valor_financiado': valor_financiado,
            'prazo_meses': prazo_meses,
            'taxa_juros_aa': taxa_juros_aa,
            'is_servidor': is_servidor,
            'tabela': df_sim,
            'primeira_prestacao': df_sim.iloc[0]['Prestação'],
            'ultima_prestacao': df_sim.iloc[-1]['Prestação'],
            'custo_total': df_sim['Prestação'].sum(),
            'total_juros': df_sim['Juros'].sum() + df_sim['Correção Monetária'].sum()
        }
        st.session_state.simulacoes.append(sim_data)

# --- EXIBIÇÃO DOS RESULTADOS ---

if st.session_state.simulacoes:
    st.header("📊 Comparativo das Simulações")

    # Criar um DataFrame de resumo para comparação
    resumo_data = []
    for sim in st.session_state.simulacoes:
        resumo_data.append({
            'Simulação': sim['nome'],
            '1ª Parcela (R$)': sim['primeira_prestacao'],
            'Última Parcela (R$)': sim['ultima_prestacao'],
            'Total Pago (R$)': sim['custo_total'],
            'Total de Juros + Correção (R$)': sim['total_juros']
        })
    
    df_resumo = pd.DataFrame(resumo_data)
    st.dataframe(
        df_resumo.style.format({
            '1ª Parcela (R$)': "R$ {:,.2f}",
            'Última Parcela (R$)': "R$ {:,.2f}",
            'Total Pago (R$)': "R$ {:,.2f}",
            'Total de Juros + Correção (R$)': "R$ {:,.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.header("🔍 Detalhes de Cada Simulação")
    
    # Criar abas para cada simulação
    nomes_abas = [f"Sim. {i+1}: {s['nome']}" for i, s in enumerate(st.session_state.simulacoes)]
    tabs = st.tabs(nomes_abas)

    for i, sim in enumerate(st.session_state.simulacoes):
        with tabs[i]:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Valor Financiado", f"R$ {sim['valor_financiado']:,.2f}")
                st.metric("Taxa de Juros Efetiva", f"{sim['taxa_juros_aa']*100:.2f}% a.a.")
            with col2:
                st.metric("Primeira Prestação", f"R$ {sim['primeira_prestacao']:,.2f}")
                st.metric("Última Prestação", f"R$ {sim['ultima_prestacao']:,.2f}")

            st.altair_chart(criar_grafico_evolucao(sim['tabela']), use_container_width=True)
            
            with st.expander("Ver tabela de amortização completa"):
                st.dataframe(sim['tabela'].style.format({
                    'Amortização': "R$ {:,.2f}",
                    'Juros': "R$ {:,.2f}",
                    'Correção Monetária': "R$ {:,.2f}",
                    'Prestação': "R$ {:,.2f}",
                    'Saldo Devedor': "R$ {:,.2f}"
                }), use_container_width=True)

    if st.button("Limpar Todas as Simulações"):
        st.session_state.simulacoes = []
        st.rerun()

else:
    st.info("Adicione uma simulação usando o painel à esquerda para ver os resultados.")

