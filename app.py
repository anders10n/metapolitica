import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from datetime import date

# Configuração da página
st.set_page_config(page_title="Análise de Leis Simbólicas", layout="wide")

# ==========================================
# VARIÁVEIS DE MEMÓRIA (ESTADO DA SESSÃO)
# ==========================================
if 'linhas_tabela' not in st.session_state:
    st.session_state.linhas_tabela = 20

if 'data_inicio' not in st.session_state:
    st.session_state.data_inicio = date(1988, 1, 1)

if 'data_fim' not in st.session_state:
    st.session_state.data_fim = date(2025, 12, 31)

def carregar_mais_linhas():
    st.session_state.linhas_tabela += 20

def definir_periodo(inicio, fim):
    st.session_state.data_inicio = inicio
    st.session_state.data_fim = fim

# ==========================================
# CARREGAMENTO DE DADOS
# ==========================================
@st.cache_data
def carregar_dados():
    nome_arquivo = 'livro_leis.xlsx - total.csv'
    
    if not os.path.exists(nome_arquivo):
        st.error(f"Erro: O arquivo '{nome_arquivo}' não foi encontrado.")
        return pd.DataFrame() 
        
    try:
        df = pd.read_csv(nome_arquivo, sep=',', on_bad_lines='skip', encoding='utf-8')
        df.columns = df.columns.str.strip()
        
        if 'anoassinatura' not in df.columns:
            df = pd.read_csv(nome_arquivo, sep=';', on_bad_lines='skip', encoding='utf-8')
            df.columns = df.columns.str.strip()
            
            if 'anoassinatura' not in df.columns:
                df = pd.read_csv(nome_arquivo, sep=';', on_bad_lines='skip', encoding='latin1')
                df.columns = df.columns.str.strip()
                
    except Exception as e:
        st.error(f"Erro ao ler o CSV: {e}")
        return pd.DataFrame()

    if 'anoassinatura' not in df.columns or 'dataassinatura' not in df.columns:
        return pd.DataFrame()

    df['anoassinatura'] = pd.to_numeric(df['anoassinatura'], errors='coerce')
    df['dataassinatura'] = pd.to_datetime(df['dataassinatura'], errors='coerce')
    
    df = df[(df['anoassinatura'] >= 1988) & (df['anoassinatura'] <= 2025)].copy()
    
    df['competencia_exclusiva'] = df['competencia_exclusiva'].astype(str).str.strip().str.lower()
    df['is_simbolica'] = df['simbólica'].isin(['sim', 'Pensão'])
    
    df['categoria_lei'] = np.where(df['is_simbolica'], 'Simbólicas',
                          np.where(df['competencia_exclusiva'] == 'sim', 'Exclusivas', 'Substantivas'))
    
    return df

df_leis = carregar_dados()

if not df_leis.empty:
    # ==========================================
    # BARRA LATERAL (MENU DE PERÍODOS E FILTROS)
    # ==========================================
    st.sidebar.header("⚙️ Controles e Filtros")

    st.sidebar.markdown("**📌 Selecione o Período de Análise:**")
    st.sidebar.button("📅 1. Período Total (01/01/1988+)", 
                      on_click=definir_periodo, args=(date(1988, 1, 1), date(2025, 12, 31)), use_container_width=True)
    st.sidebar.button("📜 2. Pós-Constituição (05/10/1988+)", 
                      on_click=definir_periodo, args=(date(1988, 10, 5), date(2025, 12, 31)), use_container_width=True)
    st.sidebar.button("🏛️ 3. Pós-EC 32 (11/09/2001+)", 
                      on_click=definir_periodo, args=(date(2001, 9, 11), date(2025, 12, 31)), use_container_width=True)
    
    datas_selecionadas = st.sidebar.date_input(
        "Ou personalize a data:",
        value=(st.session_state.data_inicio, st.session_state.data_fim),
        min_value=date(1988, 1, 1),
        max_value=date(2025, 12, 31)
    )
    
    if isinstance(datas_selecionadas, tuple) and len(datas_selecionadas) == 2:
        data_inicio_filtro, data_fim_filtro = datas_selecionadas
    else:
        data_inicio_filtro = st.session_state.data_inicio
        data_fim_filtro = st.session_state.data_fim

    st.sidebar.divider()

    remover_exclusivas = st.sidebar.checkbox("Excluir Leis de Competência Exclusiva", value=False)
    detalhar_exclusivas = st.sidebar.checkbox("Detalhar Leis de Competência Exclusiva", value=False)
    apenas_simbolicas = st.sidebar.checkbox("Mostrar apenas Leis Simbólicas", value=False)

    st.sidebar.divider()
    
    # ==========================================
    # O FILTRO DO FILTRO (Filtros Dinâmicos)
    # ==========================================
    st.sidebar.markdown("**🔍 Filtros Específicos**")
    filtros_opcionais = st.sidebar.multiselect(
        "Quais categorias deseja filtrar?",
        ["Autor", "Partido", "UF", "Classificação"]
    )
    
    autores_selecionados, partidos_selecionados, ufs_selecionadas, classes_selecionadas = [], [], [], []

    if "Autor" in filtros_opcionais:
        lista_autores = sorted(df_leis['autor'].dropna().astype(str).unique().tolist())
        autores_selecionados = st.sidebar.multiselect("Selecione os Autores", lista_autores)
        
    if "Partido" in filtros_opcionais:
        lista_partidos = sorted(df_leis['partido'].dropna().astype(str).unique().tolist())
        partidos_selecionados = st.sidebar.multiselect("Selecione os Partidos", lista_partidos)
        
    if "UF" in filtros_opcionais:
        lista_ufs = sorted(df_leis['uf'].dropna().astype(str).unique().tolist())
        ufs_selecionadas = st.sidebar.multiselect("Selecione os Estados (UF)", lista_ufs)
        
    if "Classificação" in filtros_opcionais:
        if apenas_simbolicas:
            lista_classes = sorted(df_leis['simbólica_tipo'].dropna().astype(str).unique().tolist())
        else:
            lista_classes = sorted(df_leis['classe_extra'].dropna().astype(str).unique().tolist())
        classes_selecionadas = st.sidebar.multiselect("Selecione as Classificações", lista_classes)

    # ==========================================
    # APLICANDO TODOS OS FILTROS BASE NOS DADOS
    # ==========================================
    df_filtrado = df_leis[(df_leis['dataassinatura'].dt.date >= data_inicio_filtro) & 
                          (df_leis['dataassinatura'].dt.date <= data_fim_filtro)]

    if remover_exclusivas and not detalhar_exclusivas:
        df_filtrado = df_filtrado[df_filtrado['competencia_exclusiva'] != 'sim']

    if detalhar_exclusivas:
        df_filtrado = df_filtrado[df_filtrado['competencia_exclusiva'] == 'sim']
        
    if apenas_simbolicas:
        df_filtrado = df_filtrado[df_filtrado['is_simbolica'] == True]

    if autores_selecionados:
        df_filtrado = df_filtrado[df_filtrado['autor'].isin(autores_selecionados)]
    if partidos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['partido'].isin(partidos_selecionados)]
    if ufs_selecionadas:
        df_filtrado = df_filtrado[df_filtrado['uf'].isin(ufs_selecionadas)]
    if classes_selecionadas:
        if apenas_simbolicas:
            df_filtrado = df_filtrado[df_filtrado['simbólica_tipo'].isin(classes_selecionadas)]
        else:
            df_filtrado = df_filtrado[df_filtrado['classe_extra'].isin(classes_selecionadas)]

    # ==========================================
    # CORPO DO PAINEL PRINCIPAL
    # ==========================================
    st.title("🏛️ Painel de Produção Legislativa")
    st.markdown("Análise da proporção de **Leis Simbólicas** vs **Leis Substantivas** no Congresso Nacional.")

    st.divider()

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros atuais.")
    else:
        # --- MÉTRICAS ---
        total_leis = len(df_filtrado)
        total_simbolicas = df_filtrado['is_simbolica'].sum()
        pct_simbolicas = (total_simbolicas / total_leis) * 100 if total_leis > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Leis (Nesta Visão)", f"{total_leis:,}".replace(',', '.'))
        col2.metric("Leis Simbólicas", f"{total_simbolicas:,}".replace(',', '.'))
        col3.metric("Proporção de Simbólicas", f"{pct_simbolicas:.1f}%")

        st.divider()

        # Variáveis para armazenar a seleção do usuário nas tabelas de resumo (Cross-Filtering)
        filtro_selecao_exclusivas = []
        filtro_selecao_simbolicas = []

        # --- ÁREA DINÂMICA (GRÁFICOS OU RESUMOS INTERATIVOS) ---
        if not (detalhar_exclusivas or apenas_simbolicas):
            cores_map = {
                'Substantivas': '#1f77b4',
                'Exclusivas': '#003366',
                'Simbólicas': '#ff7f0e'
            }

            graf_col1, graf_col2 = st.columns((1, 1.5))

            with graf_col1:
                st.subheader("Proporção no Período Selecionado")
                contagem = df_filtrado['categoria_lei'].value_counts().reset_index()
                contagem.columns = ['categoria', 'quantidade']
                
                fig1 = px.pie(
                    contagem, names='categoria', values='quantidade', hole=0.6,
                    color='categoria', color_discrete_map=cores_map
                )
                fig1.update_traces(textinfo='percent', hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Fatia: %{percent}')
                fig1.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5))
                st.plotly_chart(fig1, use_container_width=True)

            with graf_col2:
                st.subheader("Evolução Histórica")
                agrupado = df_filtrado.groupby(['anoassinatura', 'categoria_lei']).size().reset_index(name='quantidade')
                
                fig2 = go.Figure()
                ordem_categorias = ['Exclusivas', 'Substantivas', 'Simbólicas']
                
                for cat in ordem_categorias:
                    df_cat = agrupado[agrupado['categoria_lei'] == cat]
                    if not df_cat.empty:
                        fig2.add_trace(go.Bar(
                            x=df_cat['anoassinatura'], y=df_cat['quantidade'],
                            name=cat, marker_color=cores_map[cat],
                            hovertemplate=f'Ano: %{{x}}<br>{cat}: %{{y}}<extra></extra>'
                        ))
                
                fig2.update_layout(
                    barmode='stack', hovermode='x unified',
                    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                    margin=dict(t=30, b=0, l=0, r=0)
                )
                
                if data_inicio_filtro <= date(1988, 10, 5) and data_fim_filtro >= date(1988, 10, 5):
                    fig2.add_vline(x=1988, line_width=2, line_dash="dash", line_color="red", 
                                   annotation_text=" Constituição", annotation_position="top right")
                
                if data_inicio_filtro <= date(2001, 9, 11) and data_fim_filtro >= date(2001, 9, 11):
                    fig2.add_vline(x=2001, line_width=2, line_dash="dash", line_color="green", 
                                   annotation_text=" EC 32", annotation_position="top right")

                st.plotly_chart(fig2, use_container_width=True)

        else:
            cols_resumo = st.columns(2) if (detalhar_exclusivas and apenas_simbolicas) else [st.container(), st.container()]
            
            # Tabela de Resumo Interativa: Competência Exclusiva
            if detalhar_exclusivas:
                with cols_resumo[0] if apenas_simbolicas else cols_resumo[0]:
                    st.subheader("📊 Resumo: Competência Exclusiva")
                    st.caption("Dica: Clique em uma ou mais linhas da tabela para filtrar a listagem abaixo.")
                    
                    resumo_exc = df_filtrado[df_filtrado['competencia_exclusiva'] == 'sim']['classe_extra'].fillna('Sem Classificação').value_counts().reset_index()
                    resumo_exc.columns = ['Classificação', 'Quantidade']
                    
                    # Cria a tabela interativa habilitando on_select
                    evento_selecao_exc = st.dataframe(
                        resumo_exc, 
                        hide_index=True, 
                        width='stretch',
                        on_select="rerun",           # Faz o painel recarregar automaticamente ao clicar
                        selection_mode="multi-row"   # Permite selecionar várias linhas
                    )
                    
                    # Se o usuário clicou em algo, guarda os nomes selecionados na variável
                    if evento_selecao_exc.selection.rows:
                        filtro_selecao_exclusivas = resumo_exc.iloc[evento_selecao_exc.selection.rows]['Classificação'].tolist()

            # Tabela de Resumo Interativa: Leis Simbólicas
            if apenas_simbolicas:
                with cols_resumo[1] if detalhar_exclusivas else cols_resumo[0]:
                    st.subheader("📊 Resumo: Leis Simbólicas por Tipo")
                    st.caption("Dica: Clique em uma ou mais linhas da tabela para filtrar a listagem abaixo.")
                    
                    resumo_simb = df_filtrado[df_filtrado['is_simbolica'] == True]['simbólica_tipo'].fillna('Tipo Não Especificado').value_counts().reset_index()
                    resumo_simb.columns = ['Tipo de Lei Simbólica', 'Quantidade']
                    
                    # Cria a tabela interativa habilitando on_select
                    evento_selecao_simb = st.dataframe(
                        resumo_simb, 
                        hide_index=True, 
                        width='stretch',
                        on_select="rerun",           # Faz o painel recarregar automaticamente ao clicar
                        selection_mode="multi-row"   # Permite selecionar várias linhas
                    )
                    
                    # Se o usuário clicou em algo, guarda os nomes selecionados na variável
                    if evento_selecao_simb.selection.rows:
                        filtro_selecao_simbolicas = resumo_simb.iloc[evento_selecao_simb.selection.rows]['Tipo de Lei Simbólica'].tolist()

        st.divider()

        # ==========================================
        # TABELA DESCRITIVA DAS LEIS E FILTRO CRUZADO
        # ==========================================
        st.subheader("📋 Listagem Descritiva das Leis")
        
        def formata_autor(row):
            autor = str(row['autor']) if pd.notna(row['autor']) else "Desconhecido"
            partido = str(row['partido']) if pd.notna(row['partido']) else ""
            uf = str(row['uf']) if pd.notna(row['uf']) else ""
            
            tem_partido = partido and partido not in ['nan', 'None', 'BR', '-', 'S/PARTIDO', 'S/PART.']
            tem_uf = uf and uf not in ['nan', 'None', 'BR', '-']
            
            if tem_partido and tem_uf:
                return f"{autor} ({partido}/{uf})"
            elif tem_partido:
                return f"{autor} ({partido})"
            else:
                return autor

        df_filtrado['Autor Formatado'] = df_filtrado.apply(formata_autor, axis=1)

        col_classificacao = 'simbólica_tipo' if apenas_simbolicas else 'classe_extra'
        
        df_tabela = df_filtrado[['normaNome', 'ementa', 'Autor Formatado', col_classificacao, 'link_origem']].copy()
        
        # Garante que os valores em branco correspondam exatamente ao que está no resumo
        texto_nulo = 'Tipo Não Especificado' if apenas_simbolicas else 'Sem Classificação'
        df_tabela[col_classificacao] = df_tabela[col_classificacao].fillna(texto_nulo)
        
        # ---------------------------------------------------------
        # A MÁGICA DO CROSS-FILTERING: APLICANDO A SELEÇÃO DOS CLIQUES
        # ---------------------------------------------------------
        if apenas_simbolicas and len(filtro_selecao_simbolicas) > 0:
            df_tabela = df_tabela[df_tabela[col_classificacao].isin(filtro_selecao_simbolicas)]
            st.success(f"📌 **Filtro Ativo:** Exibindo a(s) categoria(s): {', '.join(filtro_selecao_simbolicas)}")
            
        elif detalhar_exclusivas and len(filtro_selecao_exclusivas) > 0:
            df_tabela = df_tabela[df_tabela[col_classificacao].isin(filtro_selecao_exclusivas)]
            st.success(f"📌 **Filtro Ativo:** Exibindo a(s) classificação(ões): {', '.join(filtro_selecao_exclusivas)}")
        # ---------------------------------------------------------

        nome_coluna_visual = "Tipo Simbólica" if apenas_simbolicas else "Classificação"
        df_tabela.columns = ['Lei', 'Ementa', 'Autor', nome_coluna_visual, 'Link Oficial']

        st.dataframe(
            df_tabela.head(st.session_state.linhas_tabela),
            column_config={
                "Lei": st.column_config.TextColumn("Lei", width="medium"),
                "Ementa": st.column_config.TextColumn("Ementa", width="large"),
                "Autor": st.column_config.TextColumn("Autor", width="medium"),
                nome_coluna_visual: st.column_config.TextColumn(nome_coluna_visual, width="medium"),
                "Link Oficial": st.column_config.LinkColumn(
                    "Acesso Documento",
                    help="Clique para abrir a lei na íntegra no portal oficial",
                    display_text="🔗 Acessar Lei" 
                )
            },
            hide_index=True,
            width='stretch'
        )

        if st.session_state.linhas_tabela < len(df_tabela):
            st.button("⏬ Carregar mais 20 leis", on_click=carregar_mais_linhas)
