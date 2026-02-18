import streamlit as st
import pandas as pd
import plotly.express as px

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

# --- FUNÇÃO DE CONEXÃO DIRETA (HACK DO CSV) ---
@st.cache_data(ttl=60)
def load_data_direct(url):
    # Tratamento do Link para virar CSV
    if "docs.google.com" in url:
        # Extrai o ID da planilha
        sheet_id = url.split("/d/")[1].split("/")[0]
        base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="
    else:
        st.error("Link inválido. Certifique-se de usar o link do Google Sheets.")
        st.stop()

    # Lê cada aba diretamente como CSV (Pula as 2 primeiras linhas de estilo header=2)
    try:
        df_c = pd.read_csv(base_url + "CONFIG") # Config geralmente nao tem estilo no topo
        df_b = pd.read_csv(base_url + "BRAIN", header=2)
        df_a = pd.read_csv(base_url + "ADS", header=2)
        return df_c, df_b, df_a
    except Exception as e:
        st.error(f"Erro ao ler abas. Verifique se os nomes são CONFIG, BRAIN, ADS (Maiúsculo). Erro: {e}")
        st.stop()

try:
    # Carrega os dados usando o método direto
    df_config, df_brain, df_ads = load_data_direct(url_planilha)
    
    # --- LIMPEZA DE DADOS (CRUCIAL) ---
    # Remove colunas fantasmas (Unnamed)
    df_brain = df_brain.loc[:, ~df_brain.columns.str.contains('^Unnamed')]
    df_ads = df_ads.loc[:, ~df_ads.columns.str.contains('^Unnamed')]
    
    # Converte coluna DATE para data
    if 'DATE' in df_brain.columns:
        df_brain['DATE'] = pd.to_datetime(df_brain['DATE'], errors='coerce')
    else:
        st.error("A coluna 'DATE' não foi encontrada na aba BRAIN. Verifique se você deletou as linhas de cabeçalho coloridas.")
        st.stop()

    # --- BARRA LATERAL ---
    st.sidebar.title("🚀 NEXUS SaaS")
    st.sidebar.success("Sistema Online")
    
    # Filtro de Data
    # Remove NaT (Not a Time) se houver erros de data
    df_brain = df_brain.dropna(subset=['DATE'])
    
    if not df_brain.empty:
        min_date = df_brain['DATE'].min().date()
        max_date = df_brain['DATE'].max().date()
        rng = st.sidebar.date_input("Filtrar Período", (min_date, max_date))
    else:
        st.warning("A planilha parece estar vazia ou as datas estão ilegíveis.")
        st.stop()
    
    # --- DASHBOARD ---
    st.title("Visão Executiva")
    
    # Filtrando
    mask = (df_brain['DATE'].dt.date >= rng[0]) & (df_brain['DATE'].dt.date <= rng[1])
    df_b_f = df_brain.loc[mask]
    
    # KPIs (Convertendo para número para evitar erro de texto)
    col1, col2, col3, col4 = st.columns(4)
    
    def safe_sum(df, col):
        return pd.to_numeric(df[col], errors='coerce').sum()

    rev = safe_sum(df_b_f, 'GROSS REV')
    lucro = safe_sum(df_b_f, 'NET PROFIT')
    ads = safe_sum(df_b_f, 'TOTAL ADS')
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
            
    with c2:
        st.subheader("Parâmetros")
        st.dataframe(df_config, use_container_width=True, hide_index=True)

    # Tabelas
    t1, t2 = st.tabs(["🧠 Financeiro", "📢 Ads"])
    t1.dataframe(df_b_f.style.background_gradient(subset=['NET PROFIT'], cmap='RdYlGn'), use_container_width=True)
    t2.dataframe(df_ads, use_container_width=True)

except Exception as e:
    st.error("OPS! Erro Crítico.")
    st.write("Dica: Abra sua planilha numa Janela Anônima. Se pedir login, o link não é público.")
    st.code(f"Erro Python: {e}")
