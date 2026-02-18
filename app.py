import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="NEXUS | Executive View", layout="wide", page_icon="🚀")

# ==================================================
# ⚠️ COLE O LINK DA SUA PLANILHA AQUI EMBAIXO:
# ==================================================
url_planilha = "COLE_O_LINK_DA_SUA_PLANILHA_DO_GOOGLE_AQUI"

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
# Cria a conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60) # O site recarrega os dados do Google a cada 60 segundos
def load_data():
    # Lê as 4 abas da planilha pelo link
    # O parametro usecols e header ajudam a garantir a leitura correta
    df_c = conn.read(spreadsheet=url_planilha, worksheet="CONFIG")
    df_b = conn.read(spreadsheet=url_planilha, worksheet="BRAIN")
    df_a = conn.read(spreadsheet=url_planilha, worksheet="ADS")
    # df_f = conn.read(spreadsheet=url_planilha, worksheet="FUNNEL") # Opcional se usar funil
    return df_c, df_b, df_a

try:
    df_config, df_brain, df_ads = load_data()
    
    # Tratamento básico de datas (garante que o pandas entenda que é data)
    df_brain['DATE'] = pd.to_datetime(df_brain['DATE'])
    
    # --- BARRA LATERAL (SIDEBAR) ---
    st.sidebar.title("🚀 NEXUS SaaS")
    st.sidebar.success("Sistema Online")
    
    # Filtro de Data
    min_date = df_brain['DATE'].min().date()
    max_date = df_brain['DATE'].max().date()
    rng = st.sidebar.date_input("Filtrar Período", (min_date, max_date))
    
    # --- DASHBOARD PRINCIPAL ---
    st.title("Visão Executiva")
    
    # Filtrando os dados pela data escolhida
    mask = (df_brain['DATE'].dt.date >= rng[0]) & (df_brain['DATE'].dt.date <= rng[1])
    df_b_f = df_brain.loc[mask]
    
    # Cards Superiores (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    
    rev = df_b_f['GROSS REV'].sum()
    lucro = df_b_f['NET PROFIT'].sum()
    ads = df_b_f['TOTAL ADS'].sum()
    # Evita divisão por zero
    roas = rev / ads if ads > 0 else 0
    margin = (lucro / rev * 100) if rev > 0 else 0
    
    col1.metric("FATURAMENTO", f"R$ {rev:,.2f}")
    col2.metric("LUCRO LÍQUIDO", f"R$ {lucro:,.2f}", f"{margin:.1f}% Margem")
    col3.metric("INVESTIMENTO ADS", f"R$ {ads:,.2f}", delta="-Investimento", delta_color="inverse")
    col4.metric("ROAS GLOBAL", f"{roas:.2f}x")
    
    st.markdown("---")
    
    # Gráficos
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Evolução Financeira")
        # Gráfico de Barras: Lucro vs Faturamento
        fig = px.bar(df_b_f, x='DATE', y=['GROSS REV', 'NET PROFIT'], 
                     barmode='group', color_discrete_map={'GROSS REV': '#1877F2', 'NET PROFIT': '#00C853'})
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', legend_title_text='')
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.subheader("Configurações Atuais")
        st.dataframe(df_config, use_container_width=True, hide_index=True)

    # Tabelas Detalhadas
    st.subheader("Base de Dados (Brain)")
    st.dataframe(df_b_f.style.background_gradient(subset=['NET PROFIT'], cmap='RdYlGn'), use_container_width=True)

except Exception as e:
    st.error(f"Erro ao conectar! Verifique se:\n1. O link da planilha está correto no código.\n2. A planilha está compartilhada como 'Qualquer pessoa com o link'.\n3. As abas se chamam exatamente CONFIG, BRAIN e ADS.\n\nDetalhe do erro: {e}")