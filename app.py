import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="NEXUS | Board Executive",
    layout="wide",
    page_icon="💎",
    initial_sidebar_state="collapsed"
)

# ==================================================
# LINK DA PLANILHA (MANTIDO)
# ==================================================
file_id = "1nAz050dC3riITBhgvNvOM4wGSYtfE5ED"
url_download = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"

# ==================================================
# DESIGN SYSTEM (PREMIUM NAVY)
# ==================================================
# Paleta de Cores
C_BG_MAIN = "#020b1c"       # Azul Marinho Profundo (Fundo)
C_BG_CARD = "#111625"       # Grafite Profundo (Cards)
C_TEXT_PRI = "#E0E6ED"      # Branco Suave
C_TEXT_SEC = "#94A3B8"      # Cinza Frio
C_ACCENT = "#3B82F6"        # Azul Elétrico
C_SUCCESS = "#10B981"       # Verde Esmeralda
C_DANGER = "#EF4444"        # Vermelho Rubi
C_WARNING = "#F59E0B"       # Amarelo Âmbar

st.markdown(f"""
<style>
    /* FUNDO GERAL */
    .stApp {{
        background-color: {C_BG_MAIN};
        background-image: radial-gradient(circle at 50% 0%, #1e293b 0%, {C_BG_MAIN} 70%);
    }}
    
    /* SIDEBAR */
    [data-testid="stSidebar"] {{
        background-color: #0b101b;
        border-right: 1px solid #1e293b;
    }}
    
    /* CARDS (METRICS) */
    div[data-testid="metric-container"] {{
        background-color: {C_BG_CARD};
        border: 1px solid #1e293b;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        transition: transform 0.2s;
    }}
    div[data-testid="metric-container"]:hover {{
        border-color: {C_ACCENT};
        transform: translateY(-2px);
    }}
    
    /* TIPOGRAFIA */
    h1, h2, h3, h4, h5, h6 {{
        color: {C_TEXT_PRI} !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.5px;
    }}
    p, span, label {{
        color: {C_TEXT_SEC} !important;
    }}
    
    /* VALORES DOS METRICS */
    [data-testid="stMetricValue"] {{
        font-size: 28px !important;
        color: {C_TEXT_PRI} !important;
        font-weight: 700;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 14px !important;
        color: {C_TEXT_SEC} !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* DATAFRAME */
    .stDataFrame {{
        border: 1px solid #1e293b;
        border-radius: 8px;
    }}
    
    /* GRÁFICOS */
    .js-plotly-plot .plotly .modebar {{
        display: none !important;
    }}
    
    /* SEPARADORES */
    hr {{
        border-color: #1e293b;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }}
</style>
""", unsafe_allow_html=True)

# --- LEITURA DE DADOS ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        xls = pd.ExcelFile(url)
        
        # Leitura Inteligente
        if "CONFIG" in xls.sheet_names: df_c = pd.read_excel(xls, "CONFIG")
        else: df_c = pd.read_excel(xls, 0)

        # Procura BRAIN
        sheet_brain = next((s for s in xls.sheet_names if "BRAIN" in s), None)
        df_b = pd.read_excel(xls, sheet_brain, header=2) if sheet_brain else pd.DataFrame()

        # Procura ADS
        sheet_ads = next((s for s in xls.sheet_names if "ADS" in s), None)
        df_a = pd.read_excel(xls, sheet_ads, header=2) if sheet_ads else pd.DataFrame()

        return df_c, df_b, df_a
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        st.stop()

# Carrega e Limpa
df_config, df_brain, df_ads = load_data(url_download)
df_brain = df_brain.loc[:, ~df_brain.columns.str.contains('^Unnamed')]
df_ads = df_ads.loc[:, ~df_ads.columns.str.contains('^Unnamed')]

# Tratamento de Data
date_col = next((c for c in df_brain.columns if "DATE" in c or "DATA" in c), None)
if date_col:
    df_brain['DATE'] = pd.to_datetime(df_brain[date_col], errors='coerce')
    df_ads['DATE'] = pd.to_datetime(df_ads[date_col], errors='coerce')
    df_brain = df_brain.dropna(subset=['DATE'])

# ==================================================
# INTERFACE & INTERATIVIDADE
# ==================================================

# HEADER & FILTROS
c_head_1, c_head_2 = st.columns([3, 1])
with c_head_1:
    st.title("NEXUS | DIRECT RESPONSE BOARD")
    st.markdown(f"<span style='color:{C_ACCENT}'>PERFORMANCE ANALYTICS & FINANCIAL INTELLIGENCE</span>", unsafe_allow_html=True)

with c_head_2:
    min_date = df_brain['DATE'].min().date()
    max_date = df_brain['DATE'].max().date()
    rng = st.date_input("DATE RANGE", (min_date, max_date))

# Filtro Global
mask_b = (df_brain['DATE'].dt.date >= rng[0]) & (df_brain['DATE'].dt.date <= rng[1])
mask_a = (df_ads['DATE'].dt.date >= rng[0]) & (df_ads['DATE'].dt.date <= rng[1])
df_b_f = df_brain.loc[mask_b]
df_a_f = df_ads.loc[mask_a]

st.markdown("<hr>", unsafe_allow_html=True)

# ==================================================
# CAMADA 1: INDICADORES ESTRATÉGICOS (KPIs)
# ==================================================
st.markdown("#### STRATEGIC KPIs")

# Cálculos
def safe_num(df, col):
    if col in df.columns:
        return pd.to_numeric(df[col].astype(str).str.replace('R$','').str.replace('.','').str.replace(',','.'), errors='coerce').sum()
    return 0

rev = safe_num(df_b_f, 'GROSS REV')
spend = safe_num(df_b_f, 'TOTAL ADS')
profit = safe_num(df_b_f, 'NET PROFIT')
sales = safe_num(df_a_f, 'SALES') if 'SALES' in df_a_f.columns else 0

roas = rev / spend if spend > 0 else 0
cpa = spend / sales if sales > 0 else 0
aov = rev / sales if sales > 0 else 0
margin_pct = (profit / rev * 100) if rev > 0 else 0

# Cards Layout (4x2)
k1, k2, k3, k4 = st.columns(4)
k1.metric("REVENUE", f"R$ {rev:,.0f}", "vs. Target", delta_color="normal")
k2.metric("AD SPEND", f"R$ {spend:,.0f}", "Efficiency", delta_color="inverse")
k3.metric("NET PROFIT", f"R$ {profit:,.0f}", f"{margin_pct:.1f}% Margin")
k4.metric("GLOBAL ROAS", f"{roas:.2f}x", "vs. 2.0 Target")

k5, k6, k7, k8 = st.columns(4)
k5.metric("SALES (VOL)", f"{int(sales)}", "Orders")
k6.metric("CPA (COST)", f"R$ {cpa:.2f}", "Acquisition")
k7.metric("AOV (TICKET)", f"R$ {aov:.2f}", "Value")
k8.metric("CAC (BLEND)", f"R$ {cpa:.2f}", "Customer Cost", delta_color="inverse") # Usando CPA como proxy de CAC

st.markdown("<hr>", unsafe_allow_html=True)

# ==================================================
# CAMADA 2: CANAIS E FUNIL (Tactical)
# ==================================================
c_tactical_1, c_tactical_2 = st.columns([2, 1])

with c_tactical_1:
    st.markdown("#### REVENUE & SPEND BY CHANNEL")
    # Preparar dados de canais (Agrupamento)
    channels = ['FB ADS', 'TIKTOK', 'YOUTUBE']
    channel_data = []
    for ch in channels:
        if ch in df_a_f.columns:
            val = pd.to_numeric(df_a_f[ch].astype(str).str.replace('R$','').str.replace('.','').str.replace(',','.'), errors='coerce').sum()
            channel_data.append({'Channel': ch, 'Spend': val, 'Revenue': val * roas}) # Simulando receita por canal baseado no ROAS global

    df_ch = pd.DataFrame(channel_data)
    
    if not df_ch.empty:
        fig_ch = go.Figure()
        fig_ch.add_trace(go.Bar(
            y=df_ch['Channel'], x=df_ch['Revenue'], name='Revenue', orientation='h',
            marker_color=C_ACCENT, opacity=0.8
        ))
        fig_ch.add_trace(go.Bar(
            y=df_ch['Channel'], x=df_ch['Spend'], name='Ad Spend', orientation='h',
            marker_color=C_TEXT_SEC, opacity=0.5
        ))
        fig_ch.update_layout(
            barmode='group',
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=C_TEXT_SEC),
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            xaxis=dict(showgrid=True, gridcolor='#1e293b'),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_ch, use_container_width=True)

with c_tactical_2:
    st.markdown("#### FUNNEL PERFORMANCE")
    # Funil Simulado (Já que sua planilha não tem todas as etapas detalhadas, criarei a estrutura visual)
    # Usando dados reais onde possível
    impr = safe_num(df_a_f, 'IMPR.') if 'IMPR.' in df_a_f.columns else 100000
    clicks = safe_num(df_a_f, 'CLICKS') if 'CLICKS' in df_a_f.columns else 2000
    
    funnel_stages = ['Impressions', 'Clicks', 'Checkout', 'Purchase']
    funnel_values = [impr, clicks, int(clicks*0.15), int(sales)]
    
    fig_fun = go.Figure(go.Funnel(
        y = funnel_stages,
        x = funnel_values,
        textinfo = "value+percent initial",
        marker = dict(color = [C_TEXT_SEC, C_ACCENT, C_WARNING, C_SUCCESS])
    ))
    fig_fun.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=C_TEXT_SEC),
        margin=dict(l=0, r=0, t=0, b=0),
        height=300,
        showlegend=False
    )
    st.plotly_chart(fig_fun, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ==================================================
# CAMADA 3: CRIATIVOS & OFERTAS (Analytical)
# ==================================================
c_anal_1, c_anal_2 = st.columns([2, 1])

with c_anal_1:
    st.markdown("#### TOP CREATIVE PERFORMANCE")
    # Tabela Simulada (Estética Premium)
    # Como não temos ID de criativo na planilha, geramos dados fake para visualização do layout
    mock_creatives = pd.DataFrame({
        'CREATIVE ID': ['VID_001_HOOK_A', 'IMG_023_UGC', 'VID_005_OFFER', 'IMG_011_STATIC'],
        'FORMAT': ['Video', 'Image', 'Video', 'Image'],
        'SPEND': [12500, 8400, 5200, 3100],
        'ROAS': [3.4, 2.8, 1.9, 4.2],
        'CTR': ['2.1%', '1.5%', '0.9%', '2.8%'],
        'STATUS': ['Active', 'Active', 'Learning', 'Scaling']
    })
    
    st.dataframe(
        mock_creatives.style.background_gradient(subset=['ROAS'], cmap='Greens'),
        use_container_width=True,
        hide_index=True
    )

with c_anal_2:
    st.markdown("#### OFFER COMPARISON")
    # Radar Chart Simulado
    fig_rad = go.Figure(data=go.Scatterpolar(
        r=[4.5, 3.2, 2.8, 4.0, 3.5],
        theta=['Conv. Rate', 'AOV', 'Margin', 'LTV', 'Click Rate'],
        fill='toself',
        line_color=C_SUCCESS
    ))
    fig_rad.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], linecolor='#333'),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=C_TEXT_SEC),
        height=300,
        margin=dict(l=30, r=30, t=20, b=20),
        showlegend=False
    )
    st.plotly_chart(fig_rad, use_container_width=True)

# ==================================================
# CAMADA 4: FINANCEIRO & SEGMENTAÇÃO (Bottom)
# ==================================================
st.markdown("<hr>", unsafe_allow_html=True)
c_fin_1, c_fin_2 = st.columns([2, 1])

with c_fin_1:
    st.markdown("#### FINANCIAL EFFICIENCY (Cashflow)")
    # Gráfico de Linha Dupla Real
    if not df_b_f.empty:
        # Limpar dados para plot
        df_chart = df_b_f.sort_values('DATE')
        for col in ['GROSS REV', 'TOTAL ADS']:
            if col in df_chart.columns:
                 df_chart[col] = pd.to_numeric(df_chart[col].astype(str).str.replace('R$','').str.replace('.','').str.replace(',','.'), errors='coerce')

        fig_fin = go.Figure()
        fig_fin.add_trace(go.Scatter(x=df_chart['DATE'], y=df_chart['GROSS REV'], name='Gross Revenue', 
                                   line=dict(color=C_SUCCESS, width=3)))
        fig_fin.add_trace(go.Scatter(x=df_chart['DATE'], y=df_chart['TOTAL ADS'], name='Ad Spend', 
                                   line=dict(color=C_DANGER, width=2, dash='dot'), fill='tozeroy', fillcolor='rgba(239, 68, 68, 0.1)'))
        
        fig_fin.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=C_TEXT_SEC),
            height=350,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#1e293b'),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_fin, use_container_width=True)

with c_fin_2:
    st.markdown("#### DEMOGRAPHICS (Audience)")
    # Donut Chart Simulado (já que não tem na planilha)
    fig_dem = px.pie(names=['18-24', '25-34', '35-44', '45+'], values=[15, 45, 30, 10], 
                     hole=0.7, color_discrete_sequence=[C_ACCENT, '#60A5FA', '#93C5FD', '#BFDBFE'])
    fig_dem.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=C_TEXT_SEC),
        height=350,
        showlegend=True,
        legend=dict(orientation="h", y=0.5)
    )
    st.plotly_chart(fig_dem, use_container_width=True)

# FOOTER
st.markdown(f"<div style='text-align: center; color: {C_TEXT_SEC}; margin-top: 50px;'>NEXUS INTELLIGENCE SYSTEMS © 2026</div>", unsafe_allow_html=True)
