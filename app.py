import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração da página (deve ser o primeiro comando)
st.set_page_config(page_title="Análise de Leis Simbólicas", layout="wide")
sns.set_theme(style="whitegrid", palette="muted")

# O st.cache_data guarda a leitura do CSV na memória, deixando o painel ultrarrápido
@st.cache_data
def carregar_dados():
    df = pd.read_csv('livro_leis.xlsx - total.csv')
    df['anoassinatura'] = pd.to_numeric(df['anoassinatura'], errors='coerce')
    df = df[(df['anoassinatura'] >= 1988) & (df['anoassinatura'] <= 2025)].copy()
    df['competencia_exclusiva'] = df['competencia_exclusiva'].astype(str).str.strip().str.lower()
    df['is_simbolica'] = df['simbólica'].isin(['sim', 'Pensão'])
    return df

df_leis = carregar_dados()

# ==========================================
# BARRA LATERAL (MENU DE FILTROS)
# ==========================================
st.sidebar.header("⚙️ Controles e Filtros")

# Filtro 1: Período
ano_min = int(df_leis['anoassinatura'].min())
ano_max = int(df_leis['anoassinatura'].max())
anos_selecionados = st.sidebar.slider("Selecione o Período", ano_min, ano_max, (1988, 2025))

# Filtro 2: Competência Exclusiva
remover_exclusivas = st.sidebar.checkbox("Excluir Leis de Competência Exclusiva", value=True, 
                                         help="Remove orçamentos, criação de cargos, etc.")

# Filtro 3: Partidos
lista_partidos = sorted(df_leis['partido'].dropna().astype(str).unique().tolist())
partidos_selecionados = st.sidebar.multiselect("Filtrar por Partido (Vazio = Todos)", lista_partidos)

# ==========================================
# APLICANDO OS FILTROS NOS DADOS
# ==========================================
df_filtrado = df_leis[(df_leis['anoassinatura'] >= anos_selecionados[0]) & 
                      (df_leis['anoassinatura'] <= anos_selecionados[1])]

if remover_exclusivas:
    df_filtrado = df_filtrado[df_filtrado['competencia_exclusiva'] != 'sim']

if partidos_selecionados:
    df_filtrado = df_filtrado[df_filtrado['partido'].isin(partidos_selecionados)]

# ==========================================
# CORPO DO PAINEL PRINCIPAL
# ==========================================
st.title("🏛️ Painel de Produção Legislativa")
st.markdown("Análise da proporção de **Leis Simbólicas** vs **Leis Substantivas** no Congresso Nacional.")

st.divider() # Linha de separação

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros atuais.")
else:
    # --- MÉTRICAS PRINCIPAIS ---
    total_leis = len(df_filtrado)
    total_simbolicas = df_filtrado['is_simbolica'].sum()
    pct_simbolicas = (total_simbolicas / total_leis) * 100 if total_leis > 0 else 0
    
    # Criando 3 colunas para os números em destaque
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Leis Aprovadas", f"{total_leis:,}".replace(',', '.'))
    col2.metric("Leis Simbólicas", f"{total_simbolicas:,}".replace(',', '.'))
    col3.metric("Proporção de Simbólicas", f"{pct_simbolicas:.1f}%")

    st.divider()

    # --- GRÁFICOS ---
    # Criando 2 colunas para colocar os gráficos lado a lado
    graf_col1, graf_col2 = st.columns(2)

    with graf_col1:
        st.subheader("Proporção no Período Selecionado")
        fig1, ax1 = plt.subplots(figsize=(6, 6))
        valores = [total_leis - total_simbolicas, total_simbolicas]
        labels = ['Leis Substantivas', 'Leis Simbólicas']
        cores = ['#1f77b4', '#ff7f0e']
        
        ax1.pie(valores, labels=labels, autopct='%1.1f%%', startangle=140, colors=cores, 
                wedgeprops={'edgecolor': 'white'})
        centro = plt.Circle((0,0), 0.70, fc='white')
        fig1.gca().add_artist(centro)
        st.pyplot(fig1)

    with graf_col2:
        st.subheader("Evolução Histórica")
        agrupado = df_filtrado.groupby('anoassinatura').agg(
            total=('numero', 'count'), simbolicas=('is_simbolica', 'sum')
        ).reset_index()
        
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        ax2.bar(agrupado['anoassinatura'], agrupado['total'], label='Total', color='#1f77b4', alpha=0.7)
        ax2.bar(agrupado['anoassinatura'], agrupado['simbolicas'], label='Simbólicas', color='#ff7f0e', alpha=0.9)
        ax2.legend()
        plt.xticks(rotation=45)
        st.pyplot(fig2)
        
    # --- TABELA DE DETALHES ---
    st.subheader("Top 5 - Tipos de Leis Simbólicas (Período)")
    tipos = df_filtrado[df_filtrado['is_simbolica']]['simbólica_tipo'].value_counts().reset_index()
    tipos.columns = ['Tipo de Lei Simbólica', 'Quantidade']
    st.dataframe(tipos.head(5), use_container_width=True)