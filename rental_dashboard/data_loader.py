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
            # Estratégia Robusta: Tentar combinações de separadores e encodings
            separators = [';', ',', '\t']
            encodings = ['utf-8', 'latin1', 'cp1252']
            
            for enc in encodings:
                for sep in separators:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, sep=sep, encoding=enc, engine='python')
                        
                        # Critério de sucesso: Ter mais de 1 coluna
                        if len(df.columns) > 1:
                            return df
                    except:
                        continue
            
            # Última tentativa: engine python com sep=None (sniffing)
            try:
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, sep=None, engine='python')
            except:
                st.error("Não foi possível ler o arquivo CSV. Verifique se ele não está corrompido.")
                return None
        else:
            df = pd.read_excel(uploaded_file)
        
        # Padronização básica de colunas (caso necessário)
        # df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return None

def smart_normalize_columns(df):
    """
    Tenta identificar automaticamente as colunas necessárias usando palavras-chave.
    """
    if df is None:
        return None
        
    df.columns = df.columns.str.strip() # Remove espaços extras
    
    # Dicionário de sinônimos para colunas padrão (Expandido)
    synonyms = {
        'Valor': [
            'valor', 'total', 'aluguel', 'preço', 'quantia', 'montante', 'devido', 'debito', 
            'arrecadado', 'pagar', 'cobrado', 'mensalidade', 'boleto', 'price', 'amount', 'value', 'cost'
        ],
        'Vencimento': [
            'vencimento', 'data', 'venc', 'dt_venc', 'dia', 'periodo', 'competencia', 
            'prazo', 'limite', 'date', 'due_date', 'deadline', 'when'
        ],
        'Inquilino': [
            'inquilino', 'cliente', 'locatario', 'nome', 'morador', 'pessoa', 'pagador', 
            'responsavel', 'condomino', 'usuario', 'sacado', 'tenant', 'name', 'client', 'payer'
        ],
        'Status': [
            'status', 'estado', 'situacao', 'pagamento', 'condicao', 'posicao', 
            'situ', 'estagio', 'state', 'condition', 'situation'
        ],
        'Pago_em': [
            'pago', 'data_pagamento', 'quitado', 'recebido', 'baixa', 'confirmacao', 
            'compensacao', 'paid', 'payment_date', 'receipt'
        ],
        'Imóvel': [
            'imovel', 'unidade', 'apartamento', 'sala', 'casa', 'loja', 'apto', 
            'bloco', 'edificio', 'condominio', 'property', 'unit', 'location'
        ]
    }
    
    # Mapeamento final
    rename_map = {}
    
    # Colunas que já existem no DF (lowercase para comparação)
    df_cols_lower = {c.lower(): c for c in df.columns}
    
    for target, keywords in synonyms.items():
        # Se a coluna já existe exatamente, pula
        if target in df.columns:
            continue
            
        # Busca por palavras-chave
        match = None
        for col_lower, original_col in df_cols_lower.items():
            # Verifica se alguma palavra-chave está contida no nome da coluna
            if any(key in col_lower for key in keywords):
                # Prioridade: 'total devido' ganha de 'multa total' se 'devido' for forte?
                # Simplificação: Pega a primeira que der match com keywords fortes
                match = original_col
                break
        
        if match:
            rename_map[match] = target
            # Remove do pool para não mapear a mesma coluna duas vezes
            if str(match).lower() in df_cols_lower:
                del df_cols_lower[str(match).lower()]

    if rename_map:
        df = df.rename(columns=rename_map)
        
    return df
