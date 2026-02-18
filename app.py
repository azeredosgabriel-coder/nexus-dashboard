import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NEXUS | Executive View", layout="wide", page_icon="🚀")

# ==================================================
# ⚠️ COLE O LINK DA SUA PLANILHA AQUI EMBAIXO:
# ==================================================
url_planilha = "https://docs.google.com/spreadsheets/d/1nAz050dC3riITBhgvNvOM4wGSYtfE5ED/edit?usp=sharing&ouid=111439950490476718855&rtpof=true&sd=true"

# --- ESTILO (CAVE MODE) ---
st.markdown("""
<style>
    .stApp { background-color: #121212; color: white; }
    [data-testid="stSidebar"] { background-color: #0A0A0A; border-right: 1px solid #333; }
    div[data-testid="metric-container"] { background-color: #1E1E1E; border: 1px solid #333; padding: 10px; border-radius: 5px; }
    h1, h2, h3, p { color: white !important; font-family: sans-serif; }
    .stDataFrame { border: 1px solid #444 !important; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_data():
    # CONFIG: O cabeçalho está na linha 1 (padrão)
    df_c = conn.read(spreadsheet=url_planilha, worksheet="CONFIG")
    
    # DADOS: O cabeçalho está na linha 3 (index 2), pois temos 2 linhas de estilo antes
    df_b = conn.read(spreadsheet=url_planilha, worksheet="BRAIN", header=2)
    df_a = conn.read(spreadsheet=url_planilha, worksheet="ADS", header=2)
    
    return df_c, df_b, df_a

try:
    df_config, df_brain, df_ads = load_data()
    
    # --- TRATAMENTO DE ERROS DE LEITURA ---
    # Se a planilha tiver colunas vazias extras, removemos
    df_brain = df_brain.loc[:, ~df_brain.columns.str.contains('^Unnamed')]
    df_ads = df_ads.loc[:, ~df_ads.columns.str.contains('^Unnamed')]
    
    # Garante que a coluna DATE existe e converte
    if 'DATE' not in df_brain.columns:
        st.error("Erro: Não encontrei a coluna 'DATE'. Verifique se você apagou as linhas de cabeçalho da planilha.")
        st.stop()
        
    df_brain['DATE'] = pd.to_datetime(df_brain['DATE'])
    
    # --- BARRA LATERAL ---
    st.sidebar.title("🚀 NEXUS SaaS")
    st.sidebar.success("Sistema Online")
    
    # Filtro de Data
    min_date = df_brain['DATE'].min().date()
    max_date = df_brain['DATE'].max().date()
    rng = st.sidebar.date_input("Filtrar Período", (min_date, max_date))
    
    # --- DASHBOARD ---
    st.title("Visão Executiva")
    
    # Filtrando dados
    mask = (df_brain['DATE'].dt.date >= rng[0]) & (df_brain['DATE'].dt.date <= rng[1])
    df_b_f = df_brain.loc[mask]
    
    # Cards
    col1, col2, col3, col4 = st.columns(4)
    
    # Tratamento para garantir que são números
    rev = pd.to_numeric(df_b_f['GROSS REV'], errors='coerce').sum()
    lucro = pd.to_numeric(df_b_f['NET PROFIT'], errors='coerce').sum()
    ads = pd.to_numeric(df_b_f['TOTAL ADS'], errors='coerce').sum()
    roas = rev / ads if ads > 0 else 0
    
    col1.metric("FATURAMENTO", f"R$ {rev:,.2f}")
    col2.metric("LUCRO LÍQUIDO", f"R$ {lucro:,.2f}")
    col3.metric("INVESTIMENTO ADS", f"R$ {ads:,.2f}", delta="-Investimento", delta_color="inverse")
    col4.metric("ROAS GLOBAL", f"{roas:.2f}x")
    
    st.markdown("---")
    
    # Gráficos
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Evolução Financeira")
        if not df_b_f.empty:
            fig = px.bar(df_b_f, x='DATE', y=['GROSS REV', 'NET PROFIT'], 
                         barmode='group', color_discrete_map={'GROSS REV': '#1877F2', 'NET PROFIT': '#00C853'})
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', legend_title_text='')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sem dados para o período selecionado.")
            
    with c2:
        st.subheader("Parâmetros")
        st.dataframe(df_config, use_container_width=True, hide_index=True)

    # Tabelas
    t1, t2 = st.tabs(["🧠 Financeiro Detalhado", "📢 Ads Performance"])
    t1.dataframe(df_b_f.style.background_gradient(subset=['NET PROFIT'], cmap='RdYlGn'), use_container_width=True)
    t2.dataframe(df_ads, use_container_width=True)

except Exception as e:
    st.error("OPS! Deu erro na conexão.")
    st.code(f"Detalhe técnico: {e}")
    st.info("Dica: Verifique se o link da planilha foi colado dentro das aspas na linha 12.")
