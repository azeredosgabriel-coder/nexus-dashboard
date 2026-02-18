import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NEXUS | Executive View", layout="wide", page_icon="🚀")

# ==================================================
# SEU LINK JÁ CONFIGURADO AQUI:
# ==================================================
# O código vai usar este ID para baixar o arquivo XLSX direto
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

# --- FUNÇÃO DE LEITURA (XLSX DIRETO) ---
@st.cache_data(ttl=60)
def load_data_xlsx(url):
    try:
        # Lê o arquivo Excel inteiro (todas as abas) de uma vez
        xls = pd.ExcelFile(url)
        
        # Carrega cada aba (tratando os cabeçalhos diferentes)
        # Aba CONFIG: Cabeçalho na linha 0
        df_c = pd.read_excel(xls, "CONFIG")
        
        # Aba BRAIN e ADS: Cabeçalho na linha 2 (pula as 2 primeiras de estilo)
        df_b = pd.read_excel(xls, "COMPANY_BRAIN", header=2)
        df_a = pd.read_excel(xls, "ADS_PERFORMANCE", header=2)
        
        return df_c, df_b, df_a
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel. Detalhe: {e}")
        st.stop()

try:
    # Carrega os dados
    df_config, df_brain, df_ads = load_data_xlsx(url_download)
    
    # --- LIMPEZA DE DADOS ---
    # Remove colunas vazias
    df_brain = df_brain.loc[:, ~df_brain.columns.str.contains('^Unnamed')]
    
    # Converte coluna DATE para data (se houver erro, vira NaT)
    if 'DATE' in df_brain.columns:
        df_brain['DATE'] = pd.to_datetime(df_brain['DATE'], errors='coerce')
        # Remove linhas onde a data é inválida (ex: linhas vazias no fim)
        df_brain = df_brain.dropna(subset=['DATE'])
    else:
        st.error("Coluna 'DATE' não encontrada na aba COMPANY_BRAIN.")
        st.stop()

    # --- BARRA LATERAL ---
    st.sidebar.title("🚀 NEXUS SaaS")
    st.sidebar.success("Conexão XLSX Ativa")
    
    # Filtro de Data
    if not df_brain.empty:
        min_date = df_brain['DATE'].min().date()
        max_date = df_brain['DATE'].max().date()
        rng = st.sidebar.date_input("Filtrar Período", (min_date, max_date))
    else:
        st.warning("A planilha parece estar vazia.")
        st.stop()
    
    # --- DASHBOARD ---
    st.title("Visão Executiva")
    
    # Filtrando
    mask = (df_brain['DATE'].dt.date >= rng[0]) & (df_brain['DATE'].dt.date <= rng[1])
    df_b_f = df_brain.loc[mask]
    
    # Função segura para somar valores monetários
    def safe_sum(df, col_name):
        if col_name in df.columns:
            # Converte para string, limpa R$ e converte para float
            return pd.to_numeric(df[col_name].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.'), errors='coerce').sum()
        return 0

    rev = safe_sum(df_b_f, 'GROSS REV')
    lucro = safe_sum(df_b_f, 'NET PROFIT')
    ads = safe_sum(df_b_f, 'TOTAL ADS')
    roas = rev / ads if ads > 0 else 0
    
    # Cards
    col1, col2, col3, col4 = st.columns(4)
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
            # Prepara dados para o gráfico (garante numérico)
            df_chart = df_b_f.copy()
            for col in ['GROSS REV', 'NET PROFIT']:
                if col in df_chart.columns:
                     df_chart[col] = pd.to_numeric(df_chart[col].astype(str).str.replace('R$','').str.replace('.','').str.replace(',','.'), errors='coerce')
            
            fig = px.bar(df_chart, x='DATE', y=['GROSS REV', 'NET PROFIT'], 
                         barmode='group', color_discrete_map={'GROSS REV': '#1877F2', 'NET PROFIT': '#00C853'})
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', legend_title_text='')
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.subheader("Parâmetros")
        st.dataframe(df_config, use_container_width=True, hide_index=True)

    # Tabelas
    t1, t2 = st.tabs(["🧠 Financeiro", "📢 Ads"])
    t1.dataframe(df_b_f, use_container_width=True)
    t2.dataframe(df_ads, use_container_width=True)

except Exception as e:
    st.error("OPS! Erro ao carregar dados.")
    st.code(f"Erro Python: {e}")
