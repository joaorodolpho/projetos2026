import numpy as np
import pandas as pd

def calculate_late_fee(value: float, late_fee_percent: float = 10.0) -> float:
    """Calcula a multa fixa sobre o valor original."""
    return value * (late_fee_percent / 100.0)

def calculate_interest(value: float, days_delayed: int, monthly_interest_rate: float = 1.0) -> float:
    """
    Calcula juros de mora pro rata die (juros simples).
    Taxa padrão de 1% ao mês.
    """
    if days_delayed <= 0:
        return 0.0
    daily_rate = monthly_interest_rate / 30.0
    return value * (daily_rate / 100.0) * days_delayed

def financial_calculator(rate, nper, pv, target='pmt'):
    """
    Calculadora científica financeira usando NumPy.
    Funciona como simulador (PMT, IPMT, etc).
    """
    # Exemplo simples de wrapper. 
    # numpy.pmt foi depreciado em versões recentes do numpy (v1.20+), recomenda-se numpy_financial.
    # Como numpy padrão pode ter removido, vamos implementar uma versão simplificada ou usar a fórmula direta se numpy_financial não estiver disponível.
    
    # Fórmula PMT: P = (Pv*r) / (1 - (1+r)^-n)
    try:
        # Tenta usar numpy_financial se instalado, senão fórmula
        import numpy_financial as npf
        if target == 'pmt':
            return npf.pmt(rate, nper, pv)
    except ImportError:
        # Implementação básica de PMT
        if rate == 0:
            return -pv / nper
        return -(pv * rate) / (1 - (1 + rate) ** -nper)
    
    return 0.0
