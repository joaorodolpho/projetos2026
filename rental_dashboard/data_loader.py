import streamlit as st
import pandas as pd
from bcb import sgs

@st.cache_data(ttl=3600)  # Cache de 1 hora para evitar chamadas excessivas
def get_inflation_index(indicator: str, start_date: str):
    """
    Busca o índice de inflação (IPCA ou IGP-M) do Banco Central.
    Codes: IPCA=433, IGP-M=189
    """
    codes = {'IPCA': 433, 'IGP-M': 189}
    try:
        if indicator not in codes:
            return None
        
        # Busca a série histórica
        serie = sgs.get({indicator: codes[indicator]}, start=start_date)
        return serie
    except Exception as e:
        st.error(f"Erro ao buscar dados do BCB: {e}")
        return None

def load_data(uploaded_file):
    """
    Carrega os dados do arquivo Excel ou CSV enviado.
    """
    if uploaded_file is None:
        return None
    
    try:
        if uploaded_file.name.endswith('.csv'):
            # Tenta ler com separador automático ou ponto e vírgula
            try:
                # Tenta primeiro com ponto e vírgula (comum no Brasil)
                df = pd.read_csv(uploaded_file, sep=';')
                if len(df.columns) <= 1: # Fallback se não separou corretamente
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=',')
            except:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=None, engine='python')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Padronização básica de colunas (caso necessário)
        # df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return None
