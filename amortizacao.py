import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# --- CONFIGURAÇÕES DA PÁGINA E ESTILOS ---
st.set_page_config(page_title="Simulador de Quitação Antecipada", layout="wide")

st.title('🚀 Simulador de Quitação Antecipada de Financiamento')
st.markdown("Descubra em quanto tempo você pode quitar seu imóvel fazendo amortizações mensais constantes.")

# --- DADOS BASE ---
TAXAS_BASE = {
    'TR + Taxa Fixa': {'taxa_padrao': 0.1129, 'taxa_servidor': 0.1099},
    'IPCA + Taxa Fixa': {'taxa_padrao': 0.0485, 'taxa_servidor': 0.0395},
    'Poupança + Taxa Fixa': {'taxa_padrao': 0.0335, 'taxa_servidor': 0.0315},
    'Taxa Fixa': {'taxa_padrao': 0.1250, 'taxa_servidor': 0.1200},
}

# --- FUNÇÕES DE CÁLCULO ---

def calcular_financiamento_recorrente(valor_financiado, prazo_meses, amortizacao_extra_mensal, modalidade, taxa_juros_aa, tr_anual=0.0, ipca_anual=0.0, selic_anual=0.0):
    """
    Calcula a tabela de amortização (SAC) considerando pagamentos extras mensais constantes.
    O loop continua até o saldo devedor ser quitado.
    """
    taxa_juros_mensal = (1 + taxa_juros_aa)**(1/12) - 1
    amortizacao_base_mensal = valor_financiado / prazo_meses
    
    tr_mensal = (1 + tr_anual)**(1/12) - 1
    ipca_mensal = (1 + ipca_anual)**(1/12) - 1

    saldo_devedor = valor_financiado
    dados = []
    mes = 0

    while saldo_devedor > 0:
        mes += 1
        
        # 1. Correção Monetária
        correcao_monetaria = 0
        if modalidade == 'TR + Taxa Fixa':
            correcao_monetaria = saldo_devedor * tr_mensal
        elif modalidade == 'IPCA + Taxa Fixa':
            correcao_monetaria = saldo_devedor * ipca_mensal
        elif modalidade == 'Poupança + Taxa Fixa':
            rend_poup_anual = 0.70 * selic_anual if selic_anual <= 0.085 else 0.0617 + tr_anual
            rend_poup_mensal = (1 + rend_poup_anual)**(1/12) - 1
            correcao_monetaria = saldo_devedor * rend_poup_mensal
        
        saldo_devedor_corrigido = saldo_devedor + correcao_monetaria
        
        # 2. Cálculo dos Juros e da Parcela do Mês
        juros_mes = saldo_devedor_corrigido * taxa_juros_mensal
        prestacao = amortizacao_base_mensal + juros_mes
        
        # 3. Abatimento da Amortização Normal
        saldo_devedor = saldo_devedor_corrigido - amortizacao_base_mensal
        
        # 4. Abatimento da Amortização EXTRA
        saldo_devedor -= amortizacao_extra_mensal
        
        # Garante que a prestação não seja maior que o saldo devedor no final
        if saldo_devedor < 0:
            prestacao += saldo_devedor # Ajusta a última prestação
            amortizacao_extra_mensal += saldo_devedor

        dados.append({
            'Parcela': mes,
            'Amortização Base': amortizacao_base_mensal,
            'Amortização Extra': amortizacao_extra_mensal if saldo_devedor > 0 else max(0, amortizacao_extra_mensal),
            'Juros': juros_mes,
            'Correção Monetária': correcao_monetaria,
            'Prestação Total': prestacao + (amortizacao_extra_mensal if saldo_devedor > 0 else 0),
            'Saldo Devedor': max(saldo_devedor, 0)
        })

    return pd.DataFrame(dados)

# --- FUNÇÕES DE GRÁFICOS (permanecem as mesmas) ---
def criar_grafico_evolucao(df):
    df_melted = df.melt(id_vars=['Parcela'], value_vars=['Prestação Total', 'Juros', 'Amortização Base'], var_name='Componente', value_name='Valor')
    chart = alt.Chart(df_melted).mark_line().encode(
        x=alt.X('Parcela', title='Mês da Parcela'),
        y=alt.Y('Valor', title='Valor (R$)'),
        color=alt.Color('Componente', title='Componente da Parcela', scale=alt.Scale(scheme='category10')),
    ).properties(title='Evolução do Pagamento Mensal', height=350)
    return chart

def criar_grafico_saldo_devedor(df_atual, valor_financiado):
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
    ).properties(title='Evolução: Saldo Devedor vs. Principal Pago', height=350)
    return chart

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'simulacao_ativa' not in st.session_state:
    st.session_state.simulacao_ativa = None

# --- INTERFACE PRINCIPAL ---
st.header("1. Configure os Dados do Financiamento")

col1, col2, col3 = st.columns(3)
with col1:
    valor_imovel = st.number_input('Valor do imóvel (R$)', min_value=100000.0, step=10000.0, value=500000.0)
    valor_entrada = st.number_input('Valor da entrada (R$)', min_value=0.0, step=5000.0, value=100000.0)
with col2:
    prazo_anos = st.slider('Prazo original do contrato (anos)', 5, 35, 30)
    modalidade = st.selectbox('Modalidade de Financiamento', options=list(TAXAS_BASE.keys()))
with col3:
    amortizacao_extra_mensal = st.number_input('Valor da amortização extra MENSAL (R$)', 0.0, 10000.0, 500.0, 50.0)
    is_servidor = st.checkbox('Sou funcionário público', help="Reduz a taxa de juros da simulação.")

# ... (Inputs de indexadores) ...

if st.button('Calcular Financiamento', type="primary"):
    valor_financiado = valor_imovel - valor_entrada
    if valor_financiado <= 0:
        st.error("O valor do imóvel deve ser maior que o da entrada.")
        st.session_state.simulacao_ativa = None
    else:
        prazo_meses = prazo_anos * 12
        taxa_key = 'taxa_servidor' if is_servidor else 'taxa_padrao'
        taxa_juros_aa = TAXAS_BASE[modalidade][taxa_key]
        
        # Chama a nova função de cálculo
        df_sim = calcular_financiamento_recorrente(
            valor_financiado, prazo_meses, amortizacao_extra_mensal, modalidade, taxa_juros_aa
        )
        
        st.session_state.simulacao_ativa = {
            'tabela_atual': df_sim,
            'prazo_original_meses': prazo_meses,
            'valor_financiado': valor_financiado,
        }
        st.success("Cálculo realizado! Role para ver o resultado do seu plano de quitação.")

st.markdown("---")

# --- SEÇÃO DE RESULTADOS ---
if st.session_state.simulacao_ativa:
    sim = st.session_state.simulacao_ativa
    df_atual = sim['tabela_atual']
    prazo_original_meses = sim['prazo_original_meses']
    novo_prazo_meses = len(df_atual)
    
    st.header("2. Resultado do Plano de Quitação")

    # Métricas de comparação
    st.subheader("Comparativo de Prazos e Economia")
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Prazo Original", f"{prazo_original_meses} meses ({prazo_original_meses/12:.1f} anos)")
    col_m2.metric("Novo Prazo com Amortização", f"{novo_prazo_meses} meses ({novo_prazo_meses/12:.1f} anos)", delta=f"{novo_prazo_meses - prazo_original_meses} meses")
    
    # Cálculo da economia
    df_sem_extra = calcular_financiamento_recorrente(sim['valor_financiado'], prazo_original_meses, 0, modalidade, TAXAS_BASE[modalidade]['taxa_padrao'])
    juros_originais = df_sem_extra['Juros'].sum() + df_sem_extra['Correção Monetária'].sum()
    juros_novos = df_atual['Juros'].sum() + df_atual['Correção Monetária'].sum()
    economia = juros_originais - juros_novos
    col_m3.metric("Economia Total em Juros", f"R$ {economia:,.2f}")

    st.subheader("Análise Gráfica do Novo Plano")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.altair_chart(criar_grafico_evolucao(df_atual), use_container_width=True)
    with col_g2:
        st.altair_chart(criar_grafico_saldo_devedor(df_atual, sim['valor_financiado']), use_container_width=True)

    with st.expander("Ver tabela de pagamento detalhada"):
        st.dataframe(df_atual.style.format(formatter="{:,.2f}"), use_container_width=True)

else:
    st.info("Preencha os dados acima e clique em 'Calcular Financiamento' para iniciar.")

