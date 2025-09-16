import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Simulador de Financiamento Caixa", layout="wide")

st.title('🏦 Simulador de Financiamento (Baseado em Simulação Real da Caixa)')
st.markdown("Calcule e planeje a quitação do seu financiamento com dados e custos reais do mercado.")

# --- NOVOS DADOS BASEADOS NA IMAGEM ---
TAXAS_BASE_ATUALIZADAS = {
    'Poupança CAIXA + TR': 0.0993, # Taxa nominal de 9.93% a.a. da imagem
    'IPCA + Taxa Fixa': 0.0485,
    'Taxa Fixa': 0.1250,
}
TAXA_SERVIDOR_REDUCAO = 0.005

# Pacotes de seguro e suas taxas CESH (Custo Efetivo do Seguro Habitacional) anuais
PACOTES_SEGURO_CESH = {
    "Caixa Residencial": 0.0297,
    "Tokio Marine Seguradora": 0.0290,
    "Caixa Residencial Especial": 0.0407,
    "Caixa Residencial Especial Ampliado": 0.0571,
    "Nenhum (Não recomendado)": 0.0
}


# --- FUNÇÕES DE CÁLCULO (Ajustada para usar o CESH) ---

def get_taxas_mensais(taxa_anual, projecoes):
    taxas = {}
    for key, val in projecoes.items():
        taxas[f'{key}_mensal'] = (1 + val / 100)**(1/12) - 1
    taxas['juros_mensal'] = (1 + taxa_anual)**(1/12) - 1
    return taxas

def calcular_financiamento_sac(params):
    saldo_devedor = params['valor_financiado']
    taxas = get_taxas_mensais(params['taxa_juros_aa'], params['projecoes'])
    
    amortizacao_base = params['valor_financiado'] / params['prazo_meses']
    
    # Calcula o custo mensal do seguro com base na taxa CESH e no valor financiado
    custo_seguro_mensal = (params['valor_financiado'] * params['taxa_cesh_anual']) / 12

    dados, mes = [], 0
    while saldo_devedor > 1:
        mes += 1
        if mes > params['prazo_meses'] * 2: break

        if mes <= 24: periodo = 'curto'
        elif mes <= 60: periodo = 'medio'
        else: periodo = 'longo'

        correcao_monetaria = 0
        if params['modalidade'] == 'Poupança CAIXA + TR':
            correcao_monetaria = saldo_devedor * taxas[f'tr_{periodo}_mensal']
        elif params['modalidade'] == 'IPCA + Taxa Fixa':
            correcao_monetaria = saldo_devedor * taxas[f'ipca_{periodo}_mensal']
        
        saldo_devedor += correcao_monetaria
        juros_mes = saldo_devedor * taxas['juros_mensal']
        
        prestacao_base = amortizacao_base + juros_mes
        desembolso_mensal = prestacao_base + custo_seguro_mensal
        
        saldo_devedor -= (amortizacao_base + params['amortizacao_extra_mensal'])

        if saldo_devedor < 0:
            desembolso_mensal += saldo_devedor
            saldo_devedor = 0

        dados.append({
            'Mês': mes, 'Prestação': prestacao_base, 'Juros': juros_mes,
            'Amortização': amortizacao_base, 'Seguros/Taxas': custo_seguro_mensal,
            'Desembolso Total': desembolso_mensal, 'Saldo Devedor': saldo_devedor
        })

    return pd.DataFrame(dados)

# --- FUNÇÕES DE GRÁFICOS (sem alteração) ---
def criar_grafico_comparativo(df_com_amort, df_sem_amort, valor_financiado):
    df_com_amort['Cenário'] = 'Com Amortização Extra'
    df_sem_amort['Cenário'] = 'Plano Original'
    
    df_plot = pd.concat([
        df_com_amort[['Mês', 'Saldo Devedor', 'Cenário']],
        df_sem_amort[['Mês', 'Saldo Devedor', 'Cenário']]
    ])
    
    chart = alt.Chart(df_plot).mark_line().encode(
        x=alt.X('Mês', title='Tempo (meses)'),
        y=alt.Y('Saldo Devedor', title='Saldo Devedor (R$)'),
        color=alt.Color('Cenário', title='Cenário', scale=alt.Scale(domain=['Com Amortização Extra', 'Plano Original'], range=['#1f77b4', '#aec7e8'])),
        strokeDash=alt.StrokeDash('Cenário', scale=alt.Scale(domain=['Com Amortização Extra', 'Plano Original'], range=[[1,0], [5,5]])),
        tooltip=['Mês', 'Cenário', alt.Tooltip('Saldo Devedor', format='$,.2f')]
    ).properties(title='Comparativo de Quitação: Plano Original vs. Acelerado', height=400)
    return chart

# --- INTERFACE DO USUÁRIO (com inputs atualizados) ---
main_tabs = st.tabs(["🎯 Calculadora de Prazo", " ক্যালকুলেটর Calculadora de Meta"])

with main_tabs[0]:
    st.header("Se eu amortizar R$ X por mês, em quanto tempo quito?")
    amortizacao_extra_mensal_prazo = st.number_input('Valor da amortização extra MENSAL (R$)', 0.0, 10000.0, 500.0, 50.0, key="amort_prazo")
    meta_prazo_anos = None

with main_tabs[1]:
    st.header("Para quitar em Y anos, quanto preciso amortizar por mês?")
    meta_prazo_anos = st.slider('Meta de prazo para quitação (anos)', 1, 35, 15, key="meta_slider")
    amortizacao_extra_mensal_prazo = 0

st.subheader("1. Dados do Financiamento")
col1, col2, col3 = st.columns(3)
with col1:
    valor_imovel = st.number_input('Valor do imóvel (R$)', 100000.0, 5000000.0, 500000.0, 10000.0)
    modalidade = st.selectbox('Modalidade de Financiamento', list(TAXAS_BASE_ATUALIZADAS.keys()))
with col2:
    valor_entrada = st.number_input('Valor da entrada (R$)', 0.0, 4000000.0, 150000.0, 5000.0)
    pacote_seguro = st.selectbox("Pacote de Seguro (CESH)", list(PACOTES_SEGURO_CESH.keys()))
with col3:
    prazo_anos = st.slider('Prazo original do contrato (anos)', 5, 35, 35) # 420 meses = 35 anos
    is_servidor = st.checkbox('Sou funcionário público', help="Aplica uma pequena redução na taxa de juros.")

# ... (Restante da interface e lógica de cálculo permanecem os mesmos) ...
with st.expander("Clique para configurar projeções de indexadores (Avançado)"):
    st.write("Configure a projeção média dos indexadores para diferentes períodos do financiamento.")
    p_col1, p_col2, p_col3 = st.columns(3)
    projecoes = {}
    with p_col1:
        st.markdown("**Curto Prazo (anos 1-2)**")
        projecoes['ipca_curto'] = st.slider('IPCA (% a.a.)', 2.0, 15.0, 4.5, 0.1, key='ipca_c')
        projecoes['tr_curto'] = st.slider('TR (% a.a.)', 0.0, 5.0, 1.5, 0.1, key='tr_c')
    with p_col2:
        st.markdown("**Médio Prazo (anos 3-5)**")
        projecoes['ipca_medio'] = st.slider('IPCA (% a.a.)', 2.0, 15.0, 4.0, 0.1, key='ipca_m')
        projecoes['tr_medio'] = st.slider('TR (% a.a.)', 0.0, 5.0, 1.0, 0.1, key='tr_m')
    with p_col3:
        st.markdown("**Longo Prazo (ano 6+)**")
        projecoes['ipca_longo'] = st.slider('IPCA (% a.a.)', 2.0, 15.0, 3.5, 0.1, key='ipca_l')
        projecoes['tr_longo'] = st.slider('TR (% a.a.)', 0.0, 5.0, 1.0, 0.1, key='tr_l')

if st.button('Executar Simulação Estratégica', type="primary"):
    valor_financiado = valor_imovel - valor_entrada
    taxa_juros_aa = TAXAS_BASE_ATUALIZADAS[modalidade] - (TAXA_SERVIDOR_REDUCAO if is_servidor else 0)
    taxa_cesh_anual = PACOTES_SEGURO_CESH[pacote_seguro]
    
    base_params = {
        'valor_financiado': valor_financiado, 'prazo_meses': prazo_anos * 12,
        'taxa_juros_aa': taxa_juros_aa, 'modalidade': modalidade,
        'taxa_cesh_anual': taxa_cesh_anual, 'projecoes': projecoes
    }

    if meta_prazo_anos:
        low, high = 0, valor_financiado / meta_prazo_anos
        for _ in range(20):
            mid = (low + high) / 2
            df_teste = calcular_financiamento_sac({**base_params, 'amortizacao_extra_mensal': mid})
            if len(df_teste) > meta_prazo_anos * 12: low = mid
            else: high = mid
        amortizacao_extra_mensal_prazo = high
        st.session_state.amortizacao_calculada = high

    df_sem_amort = calcular_financiamento_sac({**base_params, 'amortizacao_extra_mensal': 0})
    df_com_amort = calcular_financiamento_sac({**base_params, 'amortizacao_extra_mensal': amortizacao_extra_mensal_prazo})
    
    st.session_state.simulacao_resultados = {
        'df_com': df_com_amort, 'df_sem': df_sem_amort,
        'params': base_params, 'amort_extra': amortizacao_extra_mensal_prazo
    }

# --- EXIBIÇÃO DOS RESULTADOS ---
if 'simulacao_resultados' in st.session_state:
    res = st.session_state.simulacao_resultados
    df_com, df_sem, params = res['df_com'], res['df_sem'], res['params']
    
    st.markdown("---")
    st.header("2. Análise de Resultados da Estratégia")

    novo_prazo_meses = len(df_com)
    economia_tempo_meses = len(df_sem) - novo_prazo_meses
    custo_total_sem = df_sem['Desembolso Total'].sum()
    custo_total_com = df_com['Desembolso Total'].sum()
    economia_dinheiro = custo_total_sem - custo_total_com

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Novo Prazo de Quitação", f"{novo_prazo_meses} meses (~{novo_prazo_meses/12:.1f} anos)")
    m_col2.metric("Redução de Tempo", f"{economia_tempo_meses} meses (~{economia_tempo_meses/12:.1f} anos)")
    m_col3.metric("Economia Financeira Total", f"R$ {economia_dinheiro:,.2f}")

    st.altair_chart(criar_grafico_comparativo(df_com, df_sem, params['valor_financiado']), use_container_width=True)

    if meta_prazo_anos:
        st.success(f"**Estratégia Definida:** Para quitar seu financiamento em **{meta_prazo_anos} anos**, você precisará fazer amortizações mensais de **R$ {res['amort_extra']:,.2f}**. Isso resultará em uma economia total de **R$ {economia_dinheiro:,.2f}**!")
    elif res['amort_extra'] > 0:
        st.success(f"**Ótima Estratégia!** Amortizando **R$ {res['amort_extra']:,.2f}** por mês, você quitará seu imóvel em **~{novo_prazo_meses/12:.1f} anos** em vez de {params['prazo_meses']/12}, economizando **R$ {economia_dinheiro:,.2f}** e antecipando sua liberdade financeira em **~{economia_tempo_meses/12:.1f} anos**!")

    with st.expander("Ver plano de pagamento detalhado da sua nova estratégia"):
        st.dataframe(df_com.style.format({
            'Prestação': "R$ {:,.2f}", 'Juros': "R$ {:,.2f}",
            'Amortização': "R$ {:,.2f}", 'Seguros/Taxas': "R$ {:,.2f}",
            'Desembolso Total': "R$ {:,.2f}", 'Saldo Devedor': "R$ {:,.2f}"
        }), use_container_width=True)
