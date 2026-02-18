import pandas as pd
import io

csv_content = """Inquilino;Imovel;Vencimento;Status;Pago em;Dias em Atraso;Multa;Juros;Total Devido
Ana Souza;Apt 101 - Ed. Solar;05/02/2026;Pago;03/02/2026;0;0.00;0.00;1500.00
Bruno Lima;Casa 22 - Vila Verde;10/02/2026;Pago;15/02/2026;5;60.00;5.00;3065.00
Carla Dias;Sala 404 - Business;12/02/2026;Pendente;;5;44.00;3.60;2247.60
Diego Silva;Apt 302 - Ed. Mar;01/02/2026;Pendente;;16;36.00;9.50;1845.50
Elena Rose;Loft 05 - Centro;15/02/2026;Pago;15/02/2026;0;0.00;0.00;1200.00"""

print("--- Testing CSV Read ---")
try:
    # Simulate the robust read logic
    # First attempt: sep=;
    df = pd.read_csv(io.StringIO(csv_content), sep=';')
    print("Read successful with sep=';'")
    print(df.head())
    print(df.columns)
    
    # Column mapping simulation
    column_map = {
        'Total Devido': 'Valor',
        'Valor Aluguel': 'Valor',
        'Pago em': 'Pago_em',
        'Data Vencimento': 'Vencimento',
        'Vencimento': 'Vencimento'
    }
    df.columns = df.columns.str.strip()
    df = df.rename(columns=column_map)
    print("\nColumns after rename:", df.columns)
    
    if 'Valor' not in df.columns:
        print("CRITICAL: 'Valor' column missing!")
    else:
        print("\n--- Valor Column Inspection ---")
        print(df['Valor'])
        print("Dtype:", df['Valor'].dtype)
        
        # Simulate the numeric conversion logic from app.py
        if df['Valor'].dtype == object:
             print("Converting object to numeric...")
             # The problematic line in app.py:
             # df['Valor'] = df['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
             
             # Let's test what happens with 1500.00
             test_val = df['Valor'].copy()
             test_val = test_val.astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
             print("\nAfter string replacement (current app logic):")
             print(test_val)
             
             numeric = pd.to_numeric(test_val, errors='coerce')
             print("\nFinal Numeric:")
             print(numeric)
        else:
            print("Already numeric.")

except Exception as e:
    print(f"Error: {e}")
