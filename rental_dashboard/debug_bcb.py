from bcb import sgs
import pandas as pd
import datetime

try:
    start_date = (pd.Timestamp.now() - pd.DateOffset(months=12)).strftime('%Y-%m-%d')
    print(f"Requesting start_date: {start_date}")
    
    # Simulate API call
    ipca_series = sgs.get({'IPCA': 433}, start=start_date)
    
    print("\n--- IPCA Series Info ---")
    print(f"Type: {type(ipca_series)}")
    print(ipca_series)
    
    acumulado_series = ipca_series.sum()
    print("\n--- Sum Result ---")
    print(f"Type: {type(acumulado_series)}")
    print(acumulado_series)
    
    val = acumulado_series.iloc[0]
    print("\n--- iloc[0] extraction ---")
    print(f"Value: {val}")
    print(f"Type: {type(val)}")
    
    formatted = f"{val:.2f}%"
    print(f"Formatted: {formatted}")

except Exception as e:
    print(f"ERROR: {e}")
