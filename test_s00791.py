#!/usr/bin/env python3
from odoo_manager import OdooManager
import json

def test_s00791():
    print("=== TESTING S00791 DATA RETRIEVAL ===")
    
    # Initialize Odoo manager
    odoo = OdooManager()
    
    # Get sales data
    print("Fetching sales data...")
    data = odoo.get_sales_lines(
        date_from='2025-01-01', 
        date_to='2025-12-31', 
        partner_id=None, 
        linea_id=None, 
        limit=5000
    )
    
    # Filter S00791 lines
    s00791_lines = [
        d for d in data 
        if 'S00791' in d.get('pedido', '') or 'F15-000001' in d.get('factura', '')
    ]
    
    print(f"\nTotal S00791 lines found: {len(s00791_lines)}")
    
    # Group by factura
    facturas = {}
    for line in s00791_lines:
        factura = line.get('factura', 'N/A')
        if factura not in facturas:
            facturas[factura] = []
        facturas[factura].append(line)
    
    print(f"\nFacturas found: {list(facturas.keys())}")
    
    for factura, lines in facturas.items():
        print(f"\n--- Factura {factura}: {len(lines)} lines ---")
        for i, line in enumerate(lines[:3]):  # Show first 3 lines per factura
            print(f"  {i+1}. Pedido: {line.get('pedido', 'N/A')}, Producto: {line.get('producto', 'N/A')[:50]}...")

if __name__ == "__main__":
    test_s00791()