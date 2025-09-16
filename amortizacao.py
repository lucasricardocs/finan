import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
import math

# Configuração da página
st.set_page_config(
    page_title="Simulador Financiamento Habitacional CAIXA",
    page_icon="🏠",
    layout="wide"
)

# Título principal
st.title("🏠 Simulador de Financiamento Habitacional CAIXA")
st.markdown("### Sistema SAC/TR - Análise Completa e Simulação de Amortizações")

# Layout principal - Inputs no topo
st.subheader("📊 Parâmetros do Financiamento")

col1, col2, col3, col4 = st.columns(4)

with col1:
    valor_imovel_mil = st.number_input(
        "💰 Valor do Imóvel (em milhares R$)",
        min_value=50,
        max_value=5000,
        value=500,
        step=10,
        help="Digite o valor em milhares. Ex: 500 = R$ 500.000"
    )

with col2:
    valor_entrada_mil = st.number_input(
        "🏦 Valor da Entrada (em milhares R$)",
        min_value=0,
        max_value=int(valor_imovel_mil * 0.8),
        value=150,
        step=5,
        help="Digite o valor em milhares. Ex: 150 = R$ 150.000"
    )

with col3:
    tempo_anos = st.number_input(
        "⏱️ Tempo de Financiamento (anos)",
        min_value=5,
        max_value=35,
        value=35,
        step=1
    )

with col4:
    taxa_juros = st.number_input(
        "📈 Taxa de Juros (% a.a.)",
        min_value=3.0,
        max_value=15.0,
        value=9.9258,
        step=0.01,
        format="%.4f"
    )

# Segunda linha de inputs
col5, col6, col7, col8 = st.columns(4)

with col5:
    amortizacao_mensal_mil = st.number_input(
        "💵 Amortização Mensal Extra (em milhares R$)",
        min_value=0.0,
        max_value=50.0,
        value=0.0,
        step=0.5,
        help="Valor fixo mensal para amortização. Ex: 1 = R$ 1.000"
    )

# Converter valores de milhares para reais
valor_imovel = valor_imovel_mil * 1000
valor_entrada = valor_entrada_mil * 1000
amortizacao_mensal = amortizacao_mensal_mil * 1000

# Cálculos básicos
valor_financiado = valor_imovel - valor_entrada
tempo_meses = int(tempo_anos * 12)
taxa_mensal = (taxa_juros / 100) / 12
perc_entrada = (valor_entrada / valor_imovel) * 100

# Validações
if valor_entrada > valor_imovel * 0.8:
    st.error("❌ Entrada não pode ser superior a 80% do valor do imóvel")
    st.stop()

if valor_financiado <= 0:
    st.error("❌ Valor da entrada é igual ou superior ao valor do imóvel")
    st.stop()

# Resumo dos valores
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Valor do Imóvel", f"R$ {valor_imovel:,.2f}")

with col2:
    st.metric("Valor da Entrada", f"R$ {valor_entrada:,.2f}", f"{perc_entrada:.1f}%")

with col3:
    st.metric("Valor Financiado", f"R$ {valor_financiado:,.2f}")

with col4:
    st.metric("Prazo Total", f"{tempo_anos} anos ({tempo_meses} meses)")

# Função para calcular SAC
def calcular_sac(valor_financiado, tempo_meses, taxa_mensal, amortizacao_extra=0):
    amortizacao_principal = valor_financiado / tempo_meses
    
    dados = []
    saldo_devedor = valor_financiado
    data_atual = datetime(2025, 10, 16)  # Data inicial
    
    for mes in range(1, tempo_meses + 1):
        # Juros do mês
        juros = saldo_devedor * taxa_mensal
        
        # Prestação = amortização + juros
        prestacao = amortizacao_principal + juros
        
        # Seguro proporcional (aproximadamente 0.044% do saldo devedor)
        seguro = saldo_devedor * 0.00044
        
        # Taxa de administração fixa
        taxa_admin = 25.00
        
        # Total da parcela
        total_parcela = prestacao + seguro + taxa_admin
        
        # Adicionar amortização extra
        amortizacao_total = amortizacao_principal + amortizacao_extra
        
        # Data do vencimento
        data_vencimento = data_atual + timedelta(days=30*(mes-1))
        
        dados.append({
            'Mes': mes,
            'Data': data_vencimento,
            'Prestacao': prestacao,
            'Amortizacao': amortizacao_principal,
            'Juros': juros,
            'Seguro': seguro,
            'Taxa_Admin': taxa_admin,
            'Total_Parcela': total_parcela,
            'Amortizacao_Extra': amortizacao_extra,
            'Amortizacao_Total': amortizacao_total,
            'Saldo_Devedor_Inicial': saldo_devedor,
            'Saldo_Devedor_Final': max(0, saldo_devedor - amortizacao_total)
        })
        
        # Atualizar saldo devedor
        saldo_devedor = max(0, saldo_devedor - amortizacao_total)
        
        # Se saldo devedor zerou, parar
        if saldo_devedor <= 0:
            break
    
    return pd.DataFrame(dados)

# Calcular cenários
df_normal = calcular_sac(valor_financiado, tempo_meses, taxa_mensal, 0)
df_com_amortizacao = calcular_sac(valor_financiado, tempo_meses, taxa_mensal, amortizacao_mensal)

# Mostrar tabela SAC
st.markdown("---")
st.subheader("📋 Tabela SAC - Primeiros 24 Meses")

# Preparar tabela para exibição (como no formato original)
df_exibicao = df_normal.head(24).copy()

# Criar tabela no formato solicitado
tabela_sac = pd.DataFrame({
    'Nº': df_exibicao['Mes'],
    'Vencimento': df_exibicao['Data'].dt.strftime('%d/%m/%Y'),
    'Prestação': df_exibicao['Prestacao'].apply(lambda x: f"R$ {x:,.2f}"),
    'Seguro': df_exibicao['Seguro'].apply(lambda x: f"R$ {x:,.2f}"),
    'Taxa de Administração (TA)': df_exibicao['Taxa_Admin'].apply(lambda x: f"R$ {x:,.2f}"),
    'Saldo Devedor': df_exibicao['Saldo_Devedor_Final'].apply(lambda x: f"R$ {x:,.2f}")
})

st.dataframe(tabela_sac, use_container_width=True, hide_index=True)

# Análise comparativa
if amortizacao_mensal > 0:
    st.markdown("---")
    st.subheader("📊 Análise Comparativa: Com vs. Sem Amortização Extra")
    
    col1, col2, col3 = st.columns(3)
    
    # Cálculos comparativos
    total_normal = df_normal['Total_Parcela'].sum()
    total_com_amortizacao = df_com_amortizacao['Total_Parcela'].sum() + (amortizacao_mensal * len(df_com_amortizacao))
    economia = total_normal - total_com_amortizacao
    prazo_normal = len(df_normal)
    prazo_reduzido = len(df_com_amortizacao)
    reducao_prazo = prazo_normal - prazo_reduzido
    
    with col1:
        st.metric("💰 Economia Total", f"R$ {economia:,.2f}", f"-{(economia/total_normal)*100:.1f}%")
    
    with col2:
        st.metric("⏰ Redução de Prazo", f"{reducao_prazo} meses", f"{reducao_prazo/12:.1f} anos")
    
    with col3:
        st.metric("💵 Total Investido Extra", f"R$ {amortizacao_mensal * len(df_com_amortizacao):,.2f}")

# Preparar dados para gráficos
if amortizacao_mensal > 0:
    df_grafico = pd.DataFrame({
        'Mês': list(range(1, len(df_normal) + 1)) + list(range(1, len(df_com_amortizacao) + 1)),
        'Saldo_Devedor': list(df_normal['Saldo_Devedor_Final']) + list(df_com_amortizacao['Saldo_Devedor_Final']),
        'Juros': list(df_normal['Juros']) + list(df_com_amortizacao['Juros']),
        'Amortização': list(df_normal['Amortizacao']) + list(df_com_amortizacao['Amortizacao']),
        'Cenário': ['Sem Amortização Extra'] * len(df_normal) + ['Com Amortização Extra'] * len(df_com_amortizacao)
    })
else:
    df_grafico = pd.DataFrame({
        'Mês': list(range(1, len(df_normal) + 1)),
        'Saldo_Devedor': list(df_normal['Saldo_Devedor_Final']),
        'Juros': list(df_normal['Juros']),
        'Amortização': list(df_normal['Amortizacao']),
        'Cenário': ['Cenário Atual'] * len(df_normal)
    })

# Gráficos com Altair
st.markdown("---")
st.subheader("📈 Evolução do Financiamento")

# Gráfico 1: Evolução do Saldo Devedor
chart_saldo = alt.Chart(df_grafico).mark_line(point=False, strokeWidth=3).add_selection(
    alt.selection_interval(bind='scales')
).encode(
    x=alt.X('Mês:Q', title='Mês'),
    y=alt.Y('Saldo_Devedor:Q', title='Saldo Devedor (R$)', scale=alt.Scale(zero=False)),
    color=alt.Color('Cenário:N', scale=alt.Scale(scheme='category10')),
    tooltip=['Mês:Q', 'Saldo_Devedor:Q', 'Cenário:N']
).properties(
    title='Evolução do Saldo Devedor',
    width=700,
    height=400
)

st.altair_chart(chart_saldo, use_container_width=True)

# Gráfico 2: Evolução dos Juros
chart_juros = alt.Chart(df_grafico).mark_line(point=False, strokeWidth=3).add_selection(
    alt.selection_interval(bind='scales')
).encode(
    x=alt.X('Mês:Q', title='Mês'),
    y=alt.Y('Juros:Q', title='Juros Mensais (R$)'),
    color=alt.Color('Cenário:N', scale=alt.Scale(scheme='set2')),
    tooltip=['Mês:Q', 'Juros:Q', 'Cenário:N']
).properties(
    title='Evolução dos Juros Mensais',
    width=700,
    height=400
)

st.altair_chart(chart_juros, use_container_width=True)

# Gráfico 3: Evolução da Amortização
chart_amortizacao = alt.Chart(df_grafico).mark_line(point=False, strokeWidth=3).add_selection(
    alt.selection_interval(bind='scales')
).encode(
    x=alt.X('Mês:Q', title='Mês'),
    y=alt.Y('Amortização:Q', title='Amortização (R$)'),
    color=alt.Color('Cenário:N', scale=alt.Scale(scheme='dark2')),
    tooltip=['Mês:Q', 'Amortização:Q', 'Cenário:N']
).properties(
    title='Evolução da Amortização Mensal',
    width=700,
    height=400
)

st.altair_chart(chart_amortizacao, use_container_width=True)

# Gráfico 4: Composição da parcela (área empilhada)
df_composicao = pd.DataFrame({
    'Mês': list(range(1, min(120, len(df_normal)) + 1)) * 2,  # Primeiros 10 anos
    'Valor': list(df_normal['Juros'][:min(120, len(df_normal))]) + list(df_normal['Amortizacao'][:min(120, len(df_normal))]),
    'Componente': ['Juros'] * min(120, len(df_normal)) + ['Amortização'] * min(120, len(df_normal))
})

chart_composicao = alt.Chart(df_composicao).mark_area().encode(
    x=alt.X('Mês:Q', title='Mês'),
    y=alt.Y('Valor:Q', title='Valor (R$)'),
    color=alt.Color('Componente:N', scale=alt.Scale(range=['#ff6b6b', '#4ecdc4'])),
    tooltip=['Mês:Q', 'Valor:Q', 'Componente:N']
).properties(
    title='Composição da Parcela - Juros vs. Amortização (Primeiros 10 anos)',
    width=700,
    height=400
)

st.altair_chart(chart_composicao, use_container_width=True)

# Resumo final
st.markdown("---")
st.subheader("📊 Resumo Final")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("💰 Total de Juros", f"R$ {df_normal['Juros'].sum():,.2f}")

with col2:
    st.metric("🏠 Total de Seguros", f"R$ {df_normal['Seguro'].sum():,.2f}")

with col3:
    st.metric("📄 Total Taxas Admin", f"R$ {df_normal['Taxa_Admin'].sum():,.2f}")

with col4:
    st.metric("💵 Total Geral", f"R$ {df_normal['Total_Parcela'].sum():,.2f}")

# Informações adicionais
st.markdown("---")
st.info("""
💡 **Sistema SAC (Sistema de Amortização Constante):**
- ✅ Amortização do principal: **constante** (R$ {:,.2f}/mês)
- 📉 Juros mensais: **decrescentes** (diminuem a cada parcela)
- 📊 Prestação total: **decrescente** (parcelas menores com o tempo)
- 🎯 Amortizações extras nos primeiros anos geram **maior economia**
""".format(valor_financiado / tempo_meses))

st.markdown("---")
st.markdown("*Simulador de Financiamento Habitacional CAIXA - Sistema SAC/TR*")
