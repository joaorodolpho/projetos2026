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
# --- Lógica Principal ---
def main():
    # Inicialização do Estado (Persistência)
    if 'main_df' not in st.session_state:
        st.session_state['main_df'] = None
    
    # 1. Carregamento e Processamento Inicial
    if uploaded_file:
        # Se mudou o arquivo ou ainda não processou
        # Check simples: se temos arquivo mas o df no state é None ou diferente (seria complexo checar diff, assumimos reload)
        # Para evitar reload a cada interação, usamos o cache do data_loader, mas precisamos colocar no session_state
        
        # Carrega brutos
        raw_df = data_loader.load_data(uploaded_file)
        
        if raw_df is not None:
             # Normaliza
            norm_df = data_loader.smart_normalize_columns(raw_df)
            
            # Validação Básica
            required_cols = ['Inquilino', 'Vencimento', 'Valor']
            missing = [c for c in required_cols if c not in norm_df.columns]
            
            if missing:
                st.error(f"❌ Erro: Colunas faltando: {', '.join(missing)}")
                st.stop()
            
            # Padronização de Tipos (Sempre que carregar novo arquivo)
            try:
                norm_df['Vencimento'] = pd.to_datetime(norm_df['Vencimento'], errors='coerce', dayfirst=True, format='mixed')
                if norm_df['Valor'].dtype == object:
                     norm_df['Valor'] = norm_df['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
                norm_df['Valor'] = pd.to_numeric(norm_df['Valor'], errors='coerce').fillna(0.0)
                if 'Status' not in norm_df.columns:
                    norm_df['Status'] = 'Pendente'
            except Exception as e:
                st.error(f"Erro ao processar dados: {e}")
                st.stop()
                
            # Salva no Session State APENAS SE FOR A PRIMEIRA VEZ DESSA SESSÃO OU UPLOAD
            # Para permitir persistência das edições, só sobrescrevemos se o usuário acabou de subir o arquivo (interação do uploader)
            # Como o uploader limpa no refresh, se ele está aqui é porque foi enviado agora.
            st.session_state['main_df'] = norm_df

    elif st.session_state['main_df'] is None:
        # Carrega dados de exemplo se não tiver nada
        st.info("ℹ️ Modo Demonstração (Carregue seu arquivo na lateral)")
        data = {
            'Inquilino': ['João Silva', 'Maria Oliveira', 'Construtora XYZ', 'Pedro Santos', 'Ana Costa', 'Roberto Freire'],
            'Imóvel': ['Apt 101', 'Sala 20', 'Galpão B', 'Apt 304', 'Loja 01', 'Casa 05'],
            'Vencimento': ['2026-02-10', '2026-02-15', '2025-12-10', '2026-02-25', '2026-01-30', '2026-02-05'],
            'Valor': [2500.00, 4200.00, 15000.00, 1800.00, 3000.00, 5500.00],
            'Status': ['Pago', 'Pendente', 'Atrasado', 'Pendente', 'Atrasado', 'Pago'],
            'Pago_em': ['2026-02-10', None, None, None, None, '2026-02-05']
        }
        ex_df = pd.DataFrame(data)
        ex_df['Vencimento'] = pd.to_datetime(ex_df['Vencimento'])
        st.session_state['main_df'] = ex_df

    # 2. Fluxo Principal (Trabalha sempre com o Session State)
    if st.session_state['main_df'] is not None:
        df = st.session_state['main_df'].copy()
        
        # --- Cálculos Preliminares (para mostrar na tabela) ---
        hoje = pd.Timestamp.now()
        df['Dias Atraso'] = (hoje - df['Vencimento']).dt.days
        df['Dias Atraso'] = df.apply(lambda x: max(0, x['Dias Atraso']) if x.get('Status') != 'Pago' else 0, axis=1)
        
        df['Multa Est.'] = df.apply(lambda x: financial_engine.calculate_late_fee(x['Valor'], taxa_multa) if x['Dias Atraso'] > 0 else 0, axis=1)
        df['Juros Est.'] = df.apply(lambda x: financial_engine.calculate_interest(x['Valor'], x['Dias Atraso'], taxa_juros) if x['Dias Atraso'] > 0 else 0, axis=1)
        df['Total Devido'] = df['Valor'] + df['Multa Est.'] + df['Juros Est.']

        # --- Interface ---
        
        # 2.1 Tabela Interativa (vem ANTES dos resultados para permitir edição)
        st.subheader("📋 Painel de Controle")
        st.caption("Edite os dados abaixo (Status, Datas) e veja os resultados atualizarem automaticamente.")
        
        edited_df = st.data_editor(
            df,
            column_config={
                "Valor": st.column_config.NumberColumn("Valor Original", format="R$ %.2f"),
                "Multa Est.": st.column_config.NumberColumn("Multa", format="R$ %.2f", disabled=True),
                "Juros Est.": st.column_config.NumberColumn("Juros", format="R$ %.2f", disabled=True),
                "Total Devido": st.column_config.NumberColumn("Total Cobrar", format="R$ %.2f", disabled=True),
                "Vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                "Status": st.column_config.SelectboxColumn("Status", options=["Pago", "Pendente", "Atrasado"], required=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_main" # Key importante para cache do widget
        )

        # Atualiza o session state com as edições para persistir se recarregar algo
        # (Opcional, mas bom para manter sincronia se tivermos outros inputs)
        
        # --- 3. Dashboard Analítico (Usa o EDITED_DF) ---
        
        st.markdown("---")
        st.subheader("📊 Performance Financeira")
        
        # Fazer cálculos finais sobre o DF EDITADO
        # Recalcula totais para garantir precisão pós-edição
        total_recebido = edited_df[edited_df['Status'] == 'Pago']['Valor'].sum()
        
        # Inadimplência Real (Total Devido atualizado)
        df_atrasados = edited_df[edited_df['Status'] == 'Atrasado'].copy()
        total_divida = df_atrasados['Total Devido'].sum()
        count_atrasados = len(df_atrasados)
        
        total_pendente = edited_df[edited_df['Status'] == 'Pendente']['Valor'].sum()

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("💰 Receita Confirmada", f"R$ {total_recebido:,.2f}", delta="Caixa Realizado")
        kpi2.metric("🚨 Inadimplência Total", f"R$ {total_divida:,.2f}", f"{count_atrasados} contratos", delta_color="inverse")
        kpi3.metric("📅 Receita Futura/Pendente", f"R$ {total_pendente:,.2f}", delta="Fluxo Previsto")
        
        # --- 4. Hall of Shame (Devedores) ---
        if not df_atrasados.empty:
            st.error(f"🚨 **ALERTA DE COBRANÇA:** Existem {count_atrasados} pagamentos atrasados!")
            
            # Mostra apenas colunas relevantes
            cols_show = ['Inquilino', 'Imóvel', 'Vencimento', 'Dias Atraso', 'Valor', 'Total Devido']
            # Garante que as colunas existem
            cols_final = [c for c in cols_show if c in df_atrasados.columns]
            
            st.dataframe(
                df_atrasados[cols_final].sort_values('Dias Atraso', ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total Devido": st.column_config.NumberColumn("Valor Atualizado", format="R$ %.2f"),
                    "Dias Atraso": st.column_config.ProgressColumn("Gravidade (Dias)", format="%d dias", min_value=0, max_value=90, help="Barra vermelha indica maior atraso")
                }
            )
        else:
            st.success("✅ Tudo em dia! Nenhum pagamento atrasado identificado.")

        # --- 5. Gráficos ---
        g1, g2 = st.columns(2)
        
        with g1:
            # Gráfico de Pizza ou Barra Stacked para Status
            fig_status = px.pie(edited_df, names='Status', values='Valor', hole=0.4, 
                                title="Distribuição da Carteira (Por Valor)",
                                color='Status',
                                color_discrete_map={'Pago': '#27AE60', 'Atrasado': '#E74C3C', 'Pendente': '#F1C40F'})
            st.plotly_chart(fig_status, use_container_width=True)
            
        with g2:
             # Evolução temporal
             edited_df['Mes'] = edited_df['Vencimento'].dt.strftime('%Y-%m')
             df_timeline = edited_df.groupby(['Mes', 'Status'])['Valor'].sum().reset_index()
             fig_time = px.bar(df_timeline, x='Mes', y='Valor', color='Status', 
                               title="Cronograma de Vencimentos",
                               color_discrete_map={'Pago': '#27AE60', 'Atrasado': '#E74C3C', 'Pendente': '#F1C40F'})
             st.plotly_chart(fig_time, use_container_width=True)

        # --- 6. Exportação e Ferramentas ---
        c_exp, c_calc = st.columns([1,1])
        with c_exp:
            st.download_button(
                label="📥 Baixar Relatório Completo",
                data=edited_df.to_csv(index=False).encode('utf-8'),
                file_name=f'relatorio_geral_{datetime.now().strftime("%d%m%Y")}.csv',
                mime='text/csv'
            )
        
        with c_calc:
             with st.popover("🧮 Calculadora Financeira"):
                st.write("**Simulador Rápido**")
                v = st.number_input("Valor", 1000.0)
                t = st.number_input("Taxa Anual %", 13.75)
                p = st.number_input("Meses", 12)
                st.code(f"Parcela: R$ {financial_engine.financial_calculator(t/100/12, p, v)*-1:,.2f}")

        # BCB (Mantido)
        st.markdown("---")
        if st.checkbox("Exibir Indicadores Econômicos (BCB)"):
             col_bcb1, col_bcb2 = st.columns(2)
             with col_bcb1:
                if st.button("Buscar IPCA"):
                    with st.spinner("Conectando ao Banco Central..."):
                        try:
                            start = (pd.Timestamp.now() - pd.DateOffset(months=12)).strftime('%Y-%m-%d')
                            s = data_loader.get_inflation_index('IPCA', start)
                            if s is not None:
                                val = s.sum()
                                if isinstance(val, pd.Series): val = val.iloc[0]
                                st.metric("IPCA 12 Meses", f"{val:.2f}%")
                                st.line_chart(s)
                        except Exception as e:
                            st.error(f"Erro BCB: {e}")

if __name__ == "__main__":
    main()
