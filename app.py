import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NEXUS | Executive View", layout="wide", page_icon="🚀")

# ==================================================
# SEU LINK (MANTENHA O MESMO QUE JÁ ESTAVA):
# ==================================================
file_id = "1nAz050dC3riITBhgvNvOM4wGSYtfE5ED"
url_download = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"

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

# --- FUNÇÃO DE LEITURA BLINDADA ---
@st.cache_data(ttl=60)
def load_data_xlsx(url):
    try:
        xls = pd.ExcelFile(url)
        
        # --- DEBUG: SE DER ERRO, O SITE VAI MOSTRAR QUAIS ABAS EXISTEM ---
        st.sidebar.caption(f"Abas encontradas: {xls.sheet_names}")
        
        # Tenta ler CONFIG (geralmente sem cabeçalho estilizado)
        # Se não achar CONFIG, tenta pegar a primeira aba
        if "CONFIG" in xls.sheet_names:
            df_c = pd.read_excel(xls, "CONFIG")
        else:
            df_c = pd.read_excel(xls, 0) # Pega a primeira

        # Tenta ler BRAIN (Procura por 'BRAIN' ou 'COMPANY_BRAIN')
        sheet_brain = next((s for s in xls.sheet_names if "BRAIN" in s), None)
        if sheet_brain:
            df_b = pd.read_excel(xls, sheet_brain, header=2)
        else:
            st.error("ERRO: Não achei a aba BRAIN. Renomeie a aba da planilha para 'BRAIN'.")
            st.stop()

        # Tenta ler ADS (Procura por 'ADS' ou 'PERFORMANCE')
        sheet_ads = next((s for s in xls.sheet_names if "ADS" in s), None)
        if sheet_ads:
            df_a = pd.read_excel(xls, sheet_ads, header=2)
        else:
             # Se não achar ADS, cria um vazio para não quebrar
            df_a = pd.DataFrame() 

        return df_c, df_b, df_a

    except Exception as e:
        st.error(f"Erro Crítico na Leitura: {e}")
        st.stop()

try:
    # Carrega os dados
    df_config, df_brain, df_ads = load_data_xlsx(url_download)
    
    # --- LIMPEZA ---
    df_brain = df_brain.loc[:, ~df_brain.columns.str.contains('^Unnamed')]
    
    # Validação de Data
    # Procura coluna de data com flexibilidade (pode ser DATE ou DATA)
    date_col = next((c for c in df_brain.columns if "DATE" in c or "DATA" in c), None)
    
    if date_col:
        df_brain['DATE'] = pd.to_datetime(df_brain[date_col], errors='coerce')
        df_brain = df_brain.dropna(subset=['DATE'])
    else:
        st.error(f"Não encontrei a coluna de Data. Colunas lidas: {list(df_brain.columns)}")
        st.stop()

    # --- BARRA LATERAL ---
    st.sidebar.title("🚀 NEXUS SaaS")
    
    if not df_brain.empty:
        min_date = df_brain['DATE'].min().date()
        max_date = df_brain['DATE'].max().date()
        rng = st.sidebar.date_input("Filtrar Período", (min_date, max_date))
    else:
        st.warning("Planilha vazia ou datas inválidas.")
        st.stop()
    
    # --- DASHBOARD ---
    st.title("Visão Executiva")
    
    mask = (df_brain['DATE'].dt.date >= rng[0]) & (df_brain['DATE'].dt.date <= rng[1])
    df_b_f = df_brain.loc[mask]
    
    # Soma segura
    def safe_sum(df, col_name):
        if col_name in df.columns:
            return pd.to_numeric(df[col_name].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.'), errors='coerce').sum()
        return 0

    rev = safe_sum(df_b_f, 'GROSS REV')
    lucro = safe_sum(df_b_f, 'NET PROFIT')
    ads = safe_sum(df_b_f, 'TOTAL ADS')
    roas = rev / ads if ads > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("FATURAMENTO", f"R$ {rev:,.2f}")
    c2.metric("LUCRO LÍQUIDO", f"R$ {lucro:,.2f}")
    c3.metric("INVESTIMENTO ADS", f"R$ {ads:,.2f}", delta="-Investimento", delta_color="inverse")
    c4.metric("ROAS GLOBAL", f"{roas:.2f}x")
    
    st.markdown("---")
    
    # Gráficos
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        st.subheader("Evolução")
        if not df_b_f.empty:
             # Limpeza para gráfico
            df_chart = df_b_f.copy()
            for col in ['GROSS REV', 'NET PROFIT']:
                if col in df_chart.columns:
                     df_chart[col] = pd.to_numeric(df_chart[col].astype(str).str.replace('R$','').str.replace('.','').str.replace(',','.'), errors='coerce')
            
            fig = px.bar(df_chart, x='DATE', y=['GROSS REV', 'NET PROFIT'], barmode='group', 
                         color_discrete_map={'GROSS REV': '#1877F2', 'NET PROFIT': '#00C853'})
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', legend_title_text='')
            st.plotly_chart(fig, use_container_width=True)
            
    with col_g2:
        st.subheader("Config")
        st.dataframe(df_config, use_container_width=True, hide_index=True)

    t1, t2 = st.tabs(["🧠 Financeiro", "📢 Ads"])
    t1.dataframe(df_b_f, use_container_width=True)
    t2.dataframe(df_ads, use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}")
