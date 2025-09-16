# simulador_santander_comparativo.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import numpy as np

# -------------------------------
# Paleta Santander
SANTANDER_RED = "#EC0000"      
SANTANDER_DARK = "#B30000"     
SANTANDER_GRAY = "#666666"     
SANTANDER_LIGHT_GRAY = "#F5F5F5"
SANTANDER_BLUE = "#0066CC"
WHITE = "#FFFFFF"
SUCCESS_GREEN = "#28A745"
WARNING_ORANGE = "#FF8C00"

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
    
    .action-buttons {{
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }}
    
    .btn-nova {{
        background: #1e3a8a;
        color: white;
        padding: 10px 20px;
        border-radius: 4px;
        text-align: center;
        font-weight: 500;
        flex: 1;
    }}
    
    .btn-baixar {{
        background: {SANTANDER_RED};
        color: white;
        padding: 10px 20px;
        border-radius: 4px;
        text-align: center;
        font-weight: 500;
        flex: 1;
    }}
    
    .section-tabs {{
        display: flex;
        background: #1e3a8a;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 20px;
    }}
    
    .tab {{
        background: #1e3a8a;
        color: white;
        padding: 10px 20px;
        text-align: center;
        font-weight: 500;
        flex: 1;
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
    
    .warning-box {{
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 4px;
        padding: 12px;
        margin: 10px 0;
        color: #92400e;
        font-size: 14px;
    }}
    
    .chart-container {{
        background: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# Função SAC
def calcular_sac(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra_mensal=0.0):
    if valor_financiado <= 0 or prazo_meses <= 0:
        return pd.DataFrame()
    
    saldo_devedor = valor_financiado
    amortizacao_mensal = valor_financiado / prazo_meses
    dados = []
    mes = 1

    while saldo_devedor > 0.01 and mes <= prazo_meses:
        juros = saldo_devedor * taxa_juros_mes
        amortizacao = amortizacao_mensal
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
            "Mês": mes,
            "Prestação_Total": prestacao_total,
            "Juros": juros,
            "Amortização": amortizacao_total,
            "Saldo_Devedor": saldo_devedor,
            "Seguro": seguro,
            "Taxa_Admin": taxa_admin
        })
        mes += 1

    return pd.DataFrame(dados)

# -------------------------------
# Header
st.markdown(
    """
    <div class='main-header'>
        <h1 style='margin:0; font-size:24px; color:#111827;'>Simulação de amortização de financiamento</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Action buttons
st.markdown(
    """
    <div class='action-buttons'>
        <div class='btn-nova'>🔄 Nova simulação</div>
        <div class='btn-baixar'>📥 Baixar simulação</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Section tabs
st.markdown(
    """
    <div class='section-tabs'>
        <div class='tab'>Amortizar</div>
        <div class='tab'>Taxas</div>
        <div class='tab'>Correção</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Layout principal
col_params, col_sem_extra, col_com_extra = st.columns([1, 1, 1])

# --- PARÂMETROS ---
with col_params:
    st.markdown("<div class='params-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Parâmetros de financiamento</div>", unsafe_allow_html=True)
    
    # Empréstimo
    st.markdown("**Empréstimo**")
    emprestimo = st.number_input("", value=500000.0, format="%.2f", key="emprestimo", label_visibility="collapsed")
    st.markdown(f"**R$ {emprestimo:,.2f}**")
    
    # Data início
    st.markdown("**Início**")
    data_inicio = st.date_input("", value=datetime(2025, 9, 1), key="inicio", label_visibility="collapsed")
    st.markdown(f"**{data_inicio.strftime('%B de %Y')}**")
    
    # Tabela
    st.markdown("**Tabela**")
    sistema = st.selectbox("", ["SAC"], key="sistema", label_visibility="collapsed")
    st.markdown("**SAC**")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Taxa de juros
    col_taxa, col_juros = st.columns(2)
    with col_taxa:
        st.markdown("**Taxa de juros**")
        taxa_juros = st.number_input("", value=9.93, format="%.2f", key="taxa", label_visibility="collapsed")
        st.markdown(f"**{taxa_juros:.2f} %**")
    
    with col_juros:
        st.markdown("**Juros**")
        st.markdown("**a.a**")
    
    # Número de parcelas
    st.markdown("**Nº de parcelas**")
    num_parcelas = st.number_input("", value=360, step=12, key="parcelas", label_visibility="collapsed")
    st.markdown(f"**{num_parcelas}**")
    
    # Amortização extra
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Amortização extra mensal**")
    amortizacao_extra = st.number_input("", value=0.0, format="%.2f", key="extra", label_visibility="collapsed")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Plano de amortização
    st.markdown("<div class='params-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Plano de amortização</div>", unsafe_allow_html=True)
    
    if amortizacao_extra == 0:
        st.markdown("<div class='warning-box'>Ainda não foi feita nenhuma amortização</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='padding:10px; background:#f0f9ff; border:1px solid #0ea5e9; border-radius:4px;'>Amortização extra mensal: R$ {amortizacao_extra:,.2f}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Cálculos
valor_financiado = emprestimo
prazo_meses = int(num_parcelas)
taxa_juros_mes = (1 + taxa_juros / 100) ** (1/12) - 1

df_sem_extra = calcular_sac(valor_financiado, taxa_juros_mes, prazo_meses, 0.0)
df_com_extra = calcular_sac(valor_financiado, taxa_juros_mes, prazo_meses, amortizacao_extra)

# --- SEM AMORTIZAÇÃO EXTRA ---
with col_sem_extra:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='comparison-title'>Sem amortização extra</div>", unsafe_allow_html=True)
    
    if not df_sem_extra.empty:
        total_pagar = df_sem_extra["Prestação_Total"].sum()
        total_juros = df_sem_extra["Juros"].sum()
        primeira_parcela = df_sem_extra.iloc[0]["Prestação_Total"]
        ultima_parcela = df_sem_extra.iloc[-1]["Prestação_Total"]
        data_ultima = data_inicio + timedelta(days=30 * len(df_sem_extra))
        
        # Métricas
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Valor financiado</span><span class='metric-value'>R$ {valor_financiado:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Total a ser pago</span><span class='metric-value'>R$ {total_pagar:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Total amortizado</span><span class='metric-value'>--</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Total de juros</span><span class='metric-value'>R$ {total_juros:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Total de taxas/seguros</span><span class='metric-value'>R$ 0,00</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Correção</span><span class='metric-value'>R$ 0,00</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Taxa de juros</span><span class='metric-value'>{taxa_juros:.2f}% (a.a)</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Quantidade de parcelas</span><span class='metric-value'>{len(df_sem_extra)}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Valor da primeira parcela</span><span class='metric-value'>R$ {primeira_parcela:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Valor da última parcela</span><span class='metric-value'>R$ {ultima_parcela:,.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Data da última parcela</span><span class='metric-value'>{data_ultima.strftime('%B de %Y')}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-row'><span class='metric-label'>Sistema de amortização</span><span class='metric-value'>SAC</span></div>", unsafe_allow_html=True)
        
        st.markdown("<br><strong>Sem amortização extra</strong>", unsafe_allow_html=True)
        
        # Gráfico de pizza
        primeira_parcela_data = df_sem_extra.iloc[0]
        pie_data = {
            'Componente': ['Financiado', 'Juros', 'Taxas/Seguro', 'Correção'],
            'Valor': [
                primeira_parcela_data['Amortização'],
                primeira_parcela_data['Juros'],
                primeira_parcela_data['Seguro'] + primeira_parcela_data['Taxa_Admin'],
                0
            ],
            'Percentual': [
                (primeira_parcela_data['Amortização'] / primeira_parcela_data['Prestação_Total']) * 100,
                (primeira_parcela_data['Juros'] / primeira_parcela_data['Prestação_Total']) * 100,
                ((primeira_parcela_data['Seguro'] + primeira_parcela_data['Taxa_Admin']) / primeira_parcela_data['Prestação_Total']) * 100,
                0
            ]
        }
        
        fig_pie = px.pie(
            pie_data, 
            values='Valor', 
            names='Componente',
            color_discrete_sequence=[SANTANDER_BLUE, SANTANDER_RED, SANTANDER_GRAY, WARNING_ORANGE]
        )
        fig_pie.update_traces(
            textposition='inside', 
            textinfo='percent',
            textfont_size=12,
            showlegend=True
        )
        fig_pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Gráfico de composição das parcelas
        st.markdown("**Composição das parcelas**")
        df_display = df_sem_extra.head(36)  # Primeiros 36 meses
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df_display['Mês'],
            y=df_display['Amortização'],
            name='Amortização mensal',
            marker_color=SANTANDER_BLUE,
            yaxis='y'
        ))
        fig_bar.add_trace(go.Bar(
            x=df_display['Mês'],
            y=df_display['Juros'],
            name='Juros',
            marker_color=SANTANDER_RED,
            yaxis='y'
        ))
        fig_bar.add_trace(go.Bar(
            x=df_display['Mês'],
            y=df_display['Seguro'] + df_display['Taxa_Admin'],
            name='Taxas/Seguro',
            marker_color=SANTANDER_GRAY,
            yaxis='y'
        ))
        
        fig_bar.update_layout(
            barmode='stack',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=250,
            margin=dict(l=40, r=20, t=20, b=40),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="", showgrid=True, gridcolor='lightgray')
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Gráfico de linha
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=df_display['Mês'],
            y=df_display['Prestação_Total'],
            name='Parcela',
            line=dict(color=SANTANDER_BLUE, width=2)
        ))
        fig_line.add_trace(go.Scatter(
            x=df_display['Mês'],
            y=df_display['Amortização'],
            name='Amortização mensal',
            line=dict(color=SANTANDER_RED, width=2)
        ))
        
        fig_line.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=250,
            margin=dict(l=40, r=20, t=20, b=40),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="", showgrid=True, gridcolor='lightgray')
        )
        
        st.plotly_chart(fig_line, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- COM AMORTIZAÇÃO EXTRA ---
with col_com_extra:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    
    if amortizacao_extra > 0:
        st.markdown("<div class='comparison-title'>Com amortização</div>", unsafe_allow_html=True)
        
        if not df_com_extra.empty:
            total_pagar_extra = df_com_extra["Prestação_Total"].sum()
            total_juros_extra = df_com_extra["Juros"].sum()
            primeira_parcela_extra = df_com_extra.iloc[0]["Prestação_Total"]
            ultima_parcela_extra = df_com_extra.iloc[-1]["Prestação_Total"]
            data_ultima_extra = data_inicio + timedelta(days=30 * len(df_com_extra))
            total_amortizado = (len(df_sem_extra) - len(df_com_extra)) * amortizacao_extra if not df_sem_extra.empty else 0
            economia = total_pagar - total_pagar_extra if not df_sem_extra.empty else 0
            
            # Métricas
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Valor financiado</span><span class='metric-value'>R$ {valor_financiado:,.2f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Total a ser pago</span><span class='metric-value'>R$ {total_pagar_extra:,.2f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Total amortizado</span><span class='metric-value'>R$ {total_amortizado:,.2f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Total de juros</span><span class='metric-value'>R$ {total_juros_extra:,.2f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Total de taxas/seguros</span><span class='metric-value'>R$ 0,00</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Correção</span><span class='metric-value'>R$ 0,00</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Taxa de juros</span><span class='metric-value'>{taxa_juros:.2f}% (a.a)</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Quantidade de parcelas</span><span class='metric-value'>{len(df_com_extra)}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Valor da primeira parcela</span><span class='metric-value'>R$ {primeira_parcela_extra:,.2f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Valor da última parcela</span><span class='metric-value'>R$ {ultima_parcela_extra:,.2f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Data da última parcela</span><span class='metric-value'>{data_ultima_extra.strftime('%B de %Y')}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-row'><span class='metric-label'>Sistema de amortização</span><span class='metric-value'>SAC</span></div>", unsafe_allow_html=True)
            
            # Destaque da economia
            if economia > 0:
                st.markdown(f"<div style='background:#dcfce7; border:1px solid #16a34a; border-radius:4px; padding:12px; margin:15px 0; text-align:center;'><strong>Economia total: R$ {economia:,.2f}</strong></div>", unsafe_allow_html=True)
            
            st.markdown("<br><strong>Com amortização</strong>", unsafe_allow_html=True)
            
            # Gráfico de pizza para cenário com extra
            primeira_parcela_extra_data = df_com_extra.iloc[0]
            pie_data_extra = {
                'Componente': ['Financiado', 'Juros', 'Taxas/Seguro', 'Correção'],
                'Valor': [
                    primeira_parcela_extra_data['Amortização'],
                    primeira_parcela_extra_data['Juros'],
                    primeira_parcela_extra_data['Seguro'] + primeira_parcela_extra_data['Taxa_Admin'],
                    0
                ]
            }
            
            fig_pie_extra = px.pie(
                pie_data_extra, 
                values='Valor', 
                names='Componente',
                color_discrete_sequence=[SANTANDER_BLUE, SANTANDER_RED, SANTANDER_GRAY, WARNING_ORANGE]
            )
            fig_pie_extra.update_traces(
                textposition='inside', 
                textinfo='percent',
                textfont_size=12,
                showlegend=True
            )
            fig_pie_extra.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )
            
            st.plotly_chart(fig_pie_extra, use_container_width=True)
            
            # Gráficos similares ao cenário sem extra
            st.markdown("**Composição das parcelas**")
            df_display_extra = df_com_extra.head(36)
            
            fig_bar_extra = go.Figure()
            fig_bar_extra.add_trace(go.Bar(
                x=df_display_extra['Mês'],
                y=df_display_extra['Amortização'],
                name='Amortização mensal',
                marker_color=SANTANDER_BLUE
            ))
            fig_bar_extra.add_trace(go.Bar(
                x=df_display_extra['Mês'],
                y=df_display_extra['Juros'],
                name='Juros',
                marker_color=SANTANDER_RED
            ))
            fig_bar_extra.add_trace(go.Bar(
                x=df_display_extra['Mês'],
                y=df_display_extra['Seguro'] + df_display_extra['Taxa_Admin'],
                name='Taxas/Seguro',
                marker_color=SANTANDER_GRAY
            ))
            
            fig_bar_extra.update_layout(
                barmode='stack',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=250,
                margin=dict(l=40, r=20, t=20, b=40),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                ),
                xaxis=dict(title="", showgrid=False),
                yaxis=dict(title="", showgrid=True, gridcolor='lightgray')
            )
            
            st.plotly_chart(fig_bar_extra, use_container_width=True)
            
            # Gráfico de linha para cenário com extra
            fig_line_extra = go.Figure()
            fig_line_extra.add_trace(go.Scatter(
                x=df_display_extra['Mês'],
                y=df_display_extra['Prestação_Total'],
                name='Parcela',
                line=dict(color=SANTANDER_BLUE, width=2)
            ))
            fig_line_extra.add_trace(go.Scatter(
                x=df_display_extra['Mês'],
                y=df_display_extra['Amortização'],
                name='Amortização mensal',
                line=dict(color=SANTANDER_RED, width=2)
            ))
            
            fig_line_extra.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=250,
                margin=dict(l=40, r=20, t=20, b=40),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                ),
                xaxis=dict(title="", showgrid=False),
                yaxis=dict(title="", showgrid=True, gridcolor='lightgray')
            )
            
            st.plotly_chart(fig_line_extra, use_container_width=True)
            
    else:
        st.markdown("<div class='comparison-title'>Com amortização</div>", unsafe_allow_html=True)
        st.markdown("<div class='warning-box'>Ainda não foi feita nenhuma amortização</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Tabela detalhada
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Tabela detalhada</div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Sem amortização", "Com amortização"])

with tab1:
    if not df_sem_extra.empty:
        # Mostrar apenas os primeiros 24 meses para melhor visualização
        df_display_table = df_sem_extra.head(24).copy()
        df_display_table['Data'] = [(data_inicio + timedelta(days=30 * (i))).strftime('%m/%Y') for i in range(len(df_display_table))]
        
        # Reorganizar colunas para exibição
        df_display_table = df_display_table[['Mês', 'Data', 'Prestação_Total', 'Juros', 'Amortização', 'Saldo_Devedor']]
        df_display_table.columns = ['Parcela', 'Data', 'Valor Total', 'Juros', 'Amortização', 'Saldo Devedor']
        
        st.dataframe(
            df_display_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Valor Total": st.column_config.NumberColumn(
                    "Valor Total",
                    format="R$ %.2f"
                ),
                "Juros": st.column_config.NumberColumn(
                    "Juros", 
                    format="R$ %.2f"
                ),
                "Amortização": st.column_config.NumberColumn(
                    "Amortização",
                    format="R$ %.2f"
                ),
                "Saldo Devedor": st.column_config.NumberColumn(
                    "Saldo Devedor",
                    format="R$ %.2f"
                )
            }
        )
        
        st.markdown(f"<div style='text-align:center; color:#666; font-size:12px; margin-top:10px;'>Exibindo primeiros 24 meses de {len(df_sem_extra)} parcelas totais</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='warning-box'>Nenhum dado disponível para exibição</div>", unsafe_allow_html=True)

with tab2:
    if amortizacao_extra > 0 and not df_com_extra.empty:
        # Mostrar apenas os primeiros 24 meses para melhor visualização
        df_display_table_extra = df_com_extra.head(24).copy()
        df_display_table_extra['Data'] = [(data_inicio + timedelta(days=30 * (i))).strftime('%m/%Y') for i in range(len(df_display_table_extra))]
        
        # Reorganizar colunas para exibição
        df_display_table_extra = df_display_table_extra[['Mês', 'Data', 'Prestação_Total', 'Juros', 'Amortização', 'Saldo_Devedor']]
        df_display_table_extra.columns = ['Parcela', 'Data', 'Valor Total', 'Juros', 'Amortização', 'Saldo Devedor']
        
        st.dataframe(
            df_display_table_extra,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Valor Total": st.column_config.NumberColumn(
                    "Valor Total",
                    format="R$ %.2f"
                ),
                "Juros": st.column_config.NumberColumn(
                    "Juros", 
                    format="R$ %.2f"
                ),
                "Amortização": st.column_config.NumberColumn(
                    "Amortização",
                    format="R$ %.2f"
                ),
                "Saldo Devedor": st.column_config.NumberColumn(
                    "Saldo Devedor",
                    format="R$ %.2f"
                )
            }
        )
        
        st.markdown(f"<div style='text-align:center; color:#666; font-size:12px; margin-top:10px;'>Exibindo primeiros 24 meses de {len(df_com_extra)} parcelas totais</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='warning-box'>Ainda não foi feita nenhuma amortização</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Funcionalidade de download
st.markdown("<br>", unsafe_allow_html=True)
if st.button("📥 Baixar Simulação Completa", type="primary", use_container_width=True):
    if not df_sem_extra.empty:
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            # Preparar dados para exportação
            df_export_sem = df_sem_extra.copy()
            df_export_sem['Data'] = [(data_inicio + timedelta(days=30 * (i-1))).strftime('%d/%m/%Y') for i in df_export_sem['Mês']]
            df_export_sem = df_export_sem[['Mês', 'Data', 'Prestação_Total', 'Juros', 'Amortização', 'Saldo_Devedor', 'Seguro', 'Taxa_Admin']]
            df_export_sem.columns = ['Parcela', 'Data', 'Valor Total', 'Juros', 'Amortização', 'Saldo Devedor', 'Seguro', 'Taxa Admin']
            df_export_sem.to_excel(writer, sheet_name="Sem_Amortizacao_Extra", index=False)
            
            if amortizacao_extra > 0 and not df_com_extra.empty:
                df_export_com = df_com_extra.copy()
                df_export_com['Data'] = [(data_inicio + timedelta(days=30 * (i-1))).strftime('%d/%m/%Y') for i in df_export_com['Mês']]
                df_export_com = df_export_com[['Mês', 'Data', 'Prestação_Total', 'Juros', 'Amortização', 'Saldo_Devedor', 'Seguro', 'Taxa_Admin']]
                df_export_com.columns = ['Parcela', 'Data', 'Valor Total', 'Juros', 'Amortização', 'Saldo Devedor', 'Seguro', 'Taxa Admin']
                df_export_com.to_excel(writer, sheet_name="Com_Amortizacao_Extra", index=False)
            
            # Criar resumo comparativo
            total_sem_extra = df_sem_extra["Prestação_Total"].sum() if not df_sem_extra.empty else 0
            total_com_extra = df_com_extra["Prestação_Total"].sum() if not df_com_extra.empty else 0
            economia_total = total_sem_extra - total_com_extra if amortizacao_extra > 0 else 0
            
            resumo = pd.DataFrame({
                'Descrição': [
                    'Valor Financiado',
                    'Amortização Extra Mensal',
                    'Taxa de Juros (a.a.)',
                    'Prazo Original (meses)',
                    'Prazo com Extra (meses)',
                    'Total sem Extra',
                    'Total com Extra', 
                    'Economia Total',
                    'Primeira Parcela sem Extra',
                    'Primeira Parcela com Extra',
                    'Redução no Prazo (meses)'
                ],
                'Valor': [
                    f"R$ {valor_financiado:,.2f}",
                    f"R$ {amortizacao_extra:,.2f}",
                    f"{taxa_juros:.2f}%",
                    len(df_sem_extra) if not df_sem_extra.empty else 0,
                    len(df_com_extra) if not df_com_extra.empty else 0,
                    f"R$ {total_sem_extra:,.2f}",
                    f"R$ {total_com_extra:,.2f}",
                    f"R$ {economia_total:,.2f}",
                    f"R$ {df_sem_extra.iloc[0]['Prestação_Total']:,.2f}" if not df_sem_extra.empty else "R$ 0,00",
                    f"R$ {df_com_extra.iloc[0]['Prestação_Total']:,.2f}" if not df_com_extra.empty else "R$ 0,00",
                    len(df_sem_extra) - len(df_com_extra) if not df_sem_extra.empty and not df_com_extra.empty else 0
                ]
            })
            resumo.to_excel(writer, sheet_name="Resumo_Comparativo", index=False)
        
        buffer.seek(0)
        st.download_button(
            label="📥 Download do arquivo Excel",
            data=buffer,
            file_name=f"simulacao_financiamento_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.success("✅ Simulação pronta para download!")
    else:
        st.error("❌ Erro: Não há dados para exportar. Verifique os parâmetros da simulação.")
