import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="NEXUS | Board Executive",
    layout="wide",
    page_icon="💎",
    initial_sidebar_state="collapsed"
)

# ==================================================
# LINK DA PLANILHA
# ==================================================
file_id = "1nAz050dC3riITBhgvNvOM4wGSYtfE5ED"
url_download = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"

# ==================================================
# DESIGN SYSTEM (PREMIUM NAVY)
# ==================================================
C_BG_MAIN = "#020b1c"       
C_BG_CARD = "#111625"       
C_TEXT_PRI = "#E0E6ED"      
C_TEXT_SEC = "#94A3B8"      
C_ACCENT = "#3B82F6"        
C_SUCCESS = "#10B981"       
C_DANGER = "#EF4444"        
C_WARNING = "#F59E0B"       

st.markdown(f"""
<style>
    .stApp {{
        background-color: {C_BG_MAIN};
        background-image: radial-gradient(circle at 50% 0%, #1e293b 0%, {C_BG_MAIN} 70%);
    }}
    [data-testid="stSidebar"] {{
        background-color: #0b101b;
        border-right: 1px solid #1e293b;
    }}
    div[data-testid="metric-container"] {{
        background-color: {C_BG_CARD};
        border: 1px solid #1e293b;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {C_TEXT_PRI} !important;
        font-family: 'Inter', sans-serif;
    }}
    p, span, label, div {{
        color: {C_TEXT_SEC} !important;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 28px !important;
        color: {C_TEXT_PRI} !important;
    }}
    .stDataFrame {{
        border: 1px solid #1e293b;
        border-radius: 8px;
    }}
</style>
""", unsafe_allow_html=True)

# --- LEITURA DE DADOS ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        xls = pd.ExcelFile(url)
        if "CONFIG" in xls.sheet_names: df_c = pd.read_excel(xls, "CONFIG")
        else: df_c = pd.read_excel(xls, 0)

        sheet_brain = next((s for s in xls.sheet_names if "BRAIN" in s), None)
        df_b = pd.read_excel(xls, sheet_brain, header=2) if sheet_brain else pd.DataFrame()

        sheet_ads = next((s for s in xls.sheet_names if "ADS" in s), None)
        df_a = pd.read_excel(xls, sheet_ads, header=2) if sheet_ads else pd.DataFrame()

        return df_c, df_b, df_a
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

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
# INTERFACE
# ==================================================

c_head_1, c_head_2 = st.columns([3, 1])
with c_head_1:
    st.title("NEXUS | DIRECT RESPONSE BOARD")

with c_head_2:
    if not df_brain.empty:
        min_date = df_brain['DATE'].min().date()
        max_date = df_brain['DATE'].max().date()
        rng = st.date_input("DATE RANGE", (min_date, max_date))
    else:
        st.warning("No Data Found")
        st.stop()

# --- CORREÇÃO DO ERRO DE DATA (INDEX ERROR) ---
if len(rng) == 2:
    start_date, end_date = rng
    mask_b = (df_brain['DATE'].dt.date >= start_date) & (df_brain['DATE'].dt.date <= end_date)
    mask_a = (df_ads['DATE'].dt.date >= start_date) & (df_ads['DATE'].dt.date <= end_date)
    df_b_f = df_brain.loc[mask_b]
    df_a_f = df_ads.loc[mask_a]
else:
    st.info("Selecione a data final no calendário.")
    st.stop()

st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

# ==================================================
# KPIs
# ==================================================
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

k1, k2, k3, k4 = st.columns(4)
k1.metric("REVENUE", f"R$ {rev:,.0f}")
k2.metric("AD SPEND", f"R$ {spend:,.0f}", delta_color="inverse")
k3.metric("NET PROFIT", f"R$ {profit:,.0f}", f"{margin_pct:.1f}% Margin")
k4.metric("GLOBAL ROAS", f"{roas:.2f}x")

k5, k6, k7, k8 = st.columns(4)
k5.metric("SALES (VOL)", f"{int(sales)}")
k6.metric("CPA (COST)", f"R$ {cpa:.2f}")
k7.metric("AOV (TICKET)", f"R$ {aov:.2f}")
k8.metric("CAC (BLEND)", f"R$ {cpa:.2f}")

st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

# ==================================================
# GRÁFICOS
# ==================================================
c_tactical_1, c_tactical_2 = st.columns([2, 1])

with c_tactical_1:
    st.markdown("#### CHANNEL PERFORMANCE")
    channels = ['FB ADS', 'TIKTOK', 'YOUTUBE']
    channel_data = []
    for ch in channels:
        if ch in df_a_f.columns:
            val = pd.to_numeric(df_a_f[ch].astype(str).str.replace('R$','').str.replace('.','').str.replace(',','.'), errors='coerce').sum()
            channel_data.append({'Channel': ch, 'Spend': val})
    
    df_ch = pd.DataFrame(channel_data)
    if not df_ch.empty:
        fig_ch = px.bar(df_ch, x='Spend', y='Channel', orientation='h', color_discrete_sequence=[C_ACCENT])
        fig_ch.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=C_TEXT_SEC)
        st.plotly_chart(fig_ch, use_container_width=True)

with c_tactical_2:
    st.markdown("#### FUNNEL")
    impr = safe_num(df_a_f, 'IMPR.') if 'IMPR.' in df_a_f.columns else 100000
    clicks = safe_num(df_a_f, 'CLICKS') if 'CLICKS' in df_a_f.columns else 2000
    funnel_values = [impr, clicks, int(sales)]
    funnel_stages = ['Impressions', 'Clicks', 'Sales']
    
    fig_fun = go.Figure(go.Funnel(y=funnel_stages, x=funnel_values, marker=dict(color=[C_TEXT_SEC, C_ACCENT, C_SUCCESS])))
    fig_fun.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=C_TEXT_SEC, height=300)
    st.plotly_chart(fig_fun, use_container_width=True)

st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

# ==================================================
# TABELA E GRÁFICO FINAL
# ==================================================
c_anal_1, c_anal_2 = st.columns([2, 1])

with c_anal_1:
    st.markdown("#### CREATIVE INTELLIGENCE")
    # Dados Mockados
    mock_creatives = pd.DataFrame({
        'CREATIVE_ID': ['VID_001', 'IMG_023', 'VID_005', 'IMG_011'],
        'SPEND': [12500, 8400, 5200, 3100],
        'ROAS': [3.4, 2.8, 1.9, 4.2],
        'CTR': ['2.1%', '1.5%', '0.9%', '2.8%']
    })
    
    # --- CORREÇÃO DO ERRO MATPLOTLIB ---
    # Só tenta aplicar gradiente se não der erro, senão mostra tabela normal
    try:
        st.dataframe(mock_creatives.style.background_gradient(subset=['ROAS'], cmap='Greens'), use_container_width=True, hide_index=True)
    except:
        st.dataframe(mock_creatives, use_container_width=True, hide_index=True)

with c_anal_2:
    st.markdown("#### DEMOGRAPHICS")
    fig_dem = px.pie(names=['18-24', '25-34', '35-44', '45+'], values=[15, 45, 30, 10], hole=0.7, color_discrete_sequence=[C_ACCENT, '#60A5FA', '#93C5FD', '#BFDBFE'])
    fig_dem.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=C_TEXT_SEC, height=300, showlegend=False)
    st.plotly_chart(fig_dem, use_container_width=True)
