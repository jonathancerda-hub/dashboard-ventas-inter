#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_manager import OdooManager

def test_webapp_flow():
    print("=== SIMULANDO FLUJO DE LA WEB APP ===")
    
    # Simular exactamente lo que hace app.py en /sales
    odoo = OdooManager()
    
    # Usar los mismos parámetros que la web app
    sales_data_raw = odoo.get_sales_lines(
        date_from='2025-01-01',
        date_to='2025-12-31', 
        partner_id=None,
        linea_id=None,
        limit=5000
    )
    
    print(f"📊 Total datos obtenidos: {len(sales_data_raw)}")
    
    # Filtrar solo canal internacional como hace app.py
    international_sales = []
    for sale in sales_data_raw:
        team_id = sale.get('team_id')
        if team_id and isinstance(team_id, list) and len(team_id) > 1:
            nombre_canal = team_id[1]
            if 'INTERNACIONAL' in nombre_canal.upper():
                international_sales.append(sale)
    
    print(f"🌍 Ventas internacionales: {len(international_sales)}")
    
    # Buscar específicamente S00791
    s00791_sales = []
    for sale in international_sales:
        pedido = sale.get('pedido', '')
        factura = sale.get('factura', '')
        if 'S00791' in pedido or any(f in factura for f in ['F F15-00000187', 'F F15-00000154', 'F F15-00000149']):
            s00791_sales.append(sale)
    
    print(f"\n🎯 LÍNEAS S00791 EN CANAL INTERNACIONAL: {len(s00791_sales)}")
    
    # Agrupar por factura
    facturas = {}
    for sale in s00791_sales:
        factura = sale.get('factura', 'N/A')
        pedido = sale.get('pedido', 'N/A')
        if factura not in facturas:
            facturas[factura] = []
        facturas[factura].append({'pedido': pedido, 'producto': sale.get('producto', 'N/A')})
    
    print(f"\nFacturas encontradas: {list(facturas.keys())}")
    
    total_lines = 0
    for factura, lines in facturas.items():
        print(f"\n--- {factura}: {len(lines)} líneas ---")
        total_lines += len(lines)
        for i, line in enumerate(lines[:3]):  # Mostrar primeras 3 líneas
            print(f"  {i+1}. Pedido: '{line['pedido']}' | Producto: {line['producto'][:50]}...")
    
    print(f"\n🔢 TOTAL FINAL WEBAPP: {total_lines} líneas S00791")
    return total_lines

if __name__ == "__main__":
    result = test_webapp_flow()
    if result == 10:
        print("✅ SUCCESS: Se encontraron las 10 líneas esperadas!")
    elif result == 4:
        print("❌ PROBLEMA: Solo se encontraron 4 líneas (falta el fix)")
    else:
        print(f"❓ RESULTADO INESPERADO: {result} líneas")