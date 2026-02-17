import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import data_loader
import financial_engine

# --- Configuração da Página ---
st.set_page_config(
    page_title="RentalEng Intelligence",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Personalizado (Premium Tech) ---
st.markdown("""
<style>
    /* Estilo Geral */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Métricas */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Cabeçalhos */
    h1, h2, h3 {
        color: #155F7A;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
    }
    
    /* Tabelas */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        padding: 10px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2659/2659360.png", width=60) # Placeholder Icon
    st.title("RentalEng\nIntelligence")
    
    st.markdown("---")
    
    # Upload
    uploaded_file = st.file_uploader("📂 Carregar Planilha (.xlsx)", type=['xlsx', 'csv'])
    
    # Filtros (Estado Global)
    if 'data_changed' not in st.session_state:
        st.session_state['data_changed'] = False

    st.markdown("### ⚙️ Configurações Global")
    taxa_multa = st.number_input("Multa Atraso (%)", value=10.0, step=0.5)
    taxa_juros = st.number_input("Juros Mensais (%)", value=1.0, step=0.1)
    
    st.caption("v1.5 - Correção BCB & Upload")

# --- Lógica Principal ---
def main():
    # Carregamento de Dados
    if uploaded_file:
        df = data_loader.load_data(uploaded_file)
        
        # Normalização Inteligente de Colunas
        if df is not None:
            df = data_loader.smart_normalize_columns(df)
            
            # Validação de Colunas Obrigatórias
            required_cols = ['Inquilino', 'Vencimento', 'Valor']
            missing = [c for c in required_cols if c not in df.columns]
            
            if missing:
                st.error(f"❌ Erro no formato do arquivo. Colunas obrigatórias não encontradas: {', '.join(missing)}")
                st.warning("O sistema tentou identificar automaticamente, mas falhou.")
                st.info(f"Colunas do seu arquivo: {list(df.columns)}")
                st.markdown("""
                **Dica:** Tente renomear as colunas da sua planilha para algo como:
                *   Nome do Cliente -> **Inquilino**
                *   Data de Vencimento -> **Vencimento**
                *   Valor Total -> **Valor**
                """)
                st.stop()
            
            # Se não tiver Status, cria padrão
            if 'Status' not in df.columns:
                df['Status'] = 'Pendente'

            # Se ainda não tiver a coluna Valor, tenta achar alguma numérica que pareça dinheiro? 
            # (Melhor avisar, mas 'Total Devido' já cobre o caso do usuário)
    else:
        # Dados de Exemplo para demonstração
        st.info("ℹ️ Carregue uma planilha para começar. Usando dados de exemplo...")
        data = {
            'Inquilino': ['João Silva', 'Maria Oliveira', 'Construtora XYZ', 'Pedro Santos'],
            'Imóvel': ['Apt 101', 'Sala Comercial 20', 'Galpão Ind.', 'Apt 304'],
            'Vencimento': ['2025-01-10', '2025-02-15', '2024-12-10', '2025-02-25'],
            'Valor': [2500.00, 4200.00, 15000.00, 1800.00],
            'Status': ['Pago', 'Pendente', 'Atrasado', 'Pendente'],
            'Pago_em': ['2025-01-10', None, None, None]
        }
        df = pd.DataFrame(data)
        df['Vencimento'] = pd.to_datetime(df['Vencimento'])


    if df is not None:
        # Normalização de Dados
        try:
            # Garante que a coluna de vencimento seja data (formato misto para maior robustez)
            df['Vencimento'] = pd.to_datetime(df['Vencimento'], errors='coerce', dayfirst=True, format='mixed')
            # Garante que valor seja numérico
            # Remove 'R$' e espaços se for string antes de converter
            if df['Valor'].dtype == object:
                 df['Valor'] = df['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
            
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0.0)
            
            # Remove linhas onde a data não pôde ser convertida (NaT)
            if df['Vencimento'].isna().any():
                st.warning("⚠️ Algumas datas não puderam ser lidas e foram ignoradas. Verifique se estão no formato Dia/Mês/Ano.")
                df = df.dropna(subset=['Vencimento'])
                
        except Exception as e:
            st.error(f"Erro ao processar dados: {e}")
            st.stop()
        
        # Processamento de Atrasos
        hoje = pd.Timestamp.now()
        
        # Filtros de Sidebar
        if 'Inquilino' in df.columns:
             inquilinos = st.multiselect("Filtrar Inquilino", options=df['Inquilino'].unique(), default=df['Inquilino'].unique())
             df_filtered = df[df['Inquilino'].isin(inquilinos)].copy()
        else:
             df_filtered = df.copy()

        # Cálculos de Atraso
        df_filtered['Dias Atraso'] = (hoje - df_filtered['Vencimento']).dt.days
        df_filtered['Dias Atraso'] = df_filtered.apply(lambda x: max(0, x['Dias Atraso']) if x.get('Status') != 'Pago' else 0, axis=1)
        
        # Cálculo Financeiro
        df_filtered['Multa Est.'] = df_filtered.apply(
            lambda x: financial_engine.calculate_late_fee(x['Valor'], taxa_multa) if x['Dias Atraso'] > 0 else 0, axis=1
        )
        df_filtered['Juros Est.'] = df_filtered.apply(
            lambda x: financial_engine.calculate_interest(x['Valor'], x['Dias Atraso'], taxa_juros) if x['Dias Atraso'] > 0 else 0, axis=1
        )
        df_filtered['Valor Total Devido'] = df_filtered['Valor'] + df_filtered['Multa Est.'] + df_filtered['Juros Est.']

        # --- Dashboard ---
        
        # KPIs
        total_recebido = df_filtered[df_filtered['Status'] == 'Pago']['Valor'].sum()
        total_atrasado = df_filtered[df_filtered['Status'] == 'Atrasado']['Valor Total Devido'].sum()
        total_pendente = df_filtered[df_filtered['Status'] == 'Pendente']['Valor'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Recebido", f"R$ {total_recebido:,.2f}", delta_color="normal")
        col2.metric("⚠️ Total em Atraso (c/ Multa)", f"R$ {total_atrasado:,.2f}", delta="-High", delta_color="inverse")
        col3.metric("📅 A Vencer/Pendente", f"R$ {total_pendente:,.2f}", delta_color="off")

        st.markdown("---")

        # Tabela Interativa
        st.subheader("📋 Gestão de Recebimentos")
        
        # Edição de dados
        edited_df = st.data_editor(
            df_filtered,
            column_config={
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "Multa Est.": st.column_config.NumberColumn("Multa (Est.)", format="R$ %.2f", disabled=True),
                "Juros Est.": st.column_config.NumberColumn("Juros (Est.)", format="R$ %.2f", disabled=True),
                "Valor Total Devido": st.column_config.NumberColumn("Total Devido", format="R$ %.2f", disabled=True),
                "Vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Pago", "Pendente", "Atrasado"],
                    help="Selecione o status do pagamento"
                )
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_grid"
        )
        
        
        # Botão para Salvar (Simulado)
        if st.button("💾 Salvar Alterações"):
            st.success("Dados atualizados com sucesso! (Integração com persistência pendente)")
            st.session_state['data_changed'] = True

        # Exportação
        st.download_button(
            label="📥 Gerar Relatório (Excel)",
            data=edited_df.to_csv(index=False).encode('utf-8'),
            file_name=f'relatorio_aluguel_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            help="Baixar tabela atualizada em formato CSV (compatível com Excel)"
        )


        # Gráficos e Calculadora
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("📈 Evolução Financeira")
            # Gráfico Simples
            if not df_filtered.empty:
                fig = px.bar(
                    df_filtered, 
                    x='Vencimento', 
                    y='Valor', 
                    color='Status',
                    color_discrete_map={'Pago': '#27AE60', 'Atrasado': '#E74C3C', 'Pendente': '#F1C40F'},
                    title="Recebimentos por Vencimento"
                )
                fig.update_layout(plot_bgcolor="white", height=350)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            with st.expander("🧮 Calculadora Científica", expanded=True):
                st.markdown("**Simulador de Amortização**")
                calc_valor = st.number_input("Valor Financiado", 100000.0)
                calc_taxa = st.number_input("Taxa Anual (%)", 12.0)
                calc_prazo = st.number_input("Prazo (Meses)", 24)
                
                if st.button("Calcular Parcela"):
                    pmt = financial_engine.financial_calculator(calc_taxa/100/12, calc_prazo, calc_valor)
                    st.metric("Parcela Mensal (PMT)", f"R$ {pmt*(-1):,.2f}")

        # BCB API Integration Check
        st.markdown("---")
        st.subheader("🏦 Indicadores Financeiros (BCB)")
        col_bcb1, col_bcb2 = st.columns(2)
        
        with col_bcb1:
            if st.button("Atualizar IPCA (Últimos 12 meses)"):
                with st.spinner("Buscando dados no Banco Central..."):
                    # Data de 1 ano atrás
                    start_date = (pd.Timestamp.now() - pd.DateOffset(months=12)).strftime('%Y-%m-%d')
                    ipca_series = data_loader.get_inflation_index('IPCA', start_date)
                    if ipca_series is not None:
                        # ipca_series é um DataFrame, sum() retorna uma Series
                        acumulado_series = ipca_series.sum()
                        # Extrai o valor escalar (float)
                        val_acumulado = acumulado_series.iloc[0] if isinstance(acumulado_series, pd.Series) else acumulado_series
                        
                        try:
                            st.metric("IPCA Acumulado (12m)", f"{val_acumulado:.2f}%")
                            st.line_chart(ipca_series)
                        except TypeError as e:
                            st.error(f"Erro de Tipo: {e}")
                            st.write(f"Valor recebido: {val_acumulado} (Tipo: {type(val_acumulado)})")
                            st.write("Dados brutos:", ipca_series)
                    else:
                        st.error("Não foi possível buscar dados do BCB.")

if __name__ == "__main__":
    main()
