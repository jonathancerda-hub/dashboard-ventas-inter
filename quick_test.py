#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_manager import OdooManager

def main():
    print("=== PRUEBA DIRECTA S00791 ===")
    
    odoo = OdooManager()
    print("✅ Conexión establecida")
    
    # Obtener datos con el rango de fechas correcto
    data = odoo.get_sales_lines(
        date_from='2024-01-01',  # Cambiar a 2024 por si acaso
        date_to='2025-12-31',
        partner_id=None,
        linea_id=None,
        limit=5000
    )
    
    print(f"Total registros obtenidos: {len(data)}")
    
    # Buscar líneas S00791
    s00791_lines = []
    for line in data:
        pedido = line.get('pedido', '')
        factura = line.get('factura', '')
        if 'S00791' in pedido or any(f in factura for f in ['F15-00000187', 'F15-00000154', 'F15-00000149']):
            s00791_lines.append(line)
    
    print(f"\n🎯 LÍNEAS S00791 ENCONTRADAS: {len(s00791_lines)}")
    
    # Agrupar por factura
    facturas = {}
    for line in s00791_lines:
        factura = line.get('factura', 'N/A')
        if factura not in facturas:
            facturas[factura] = []
        facturas[factura].append(line)
    
    print(f"\nFacturas detectadas: {list(facturas.keys())}")
    
    for factura, lines in facturas.items():
        print(f"\n--- {factura}: {len(lines)} líneas ---")
        for i, line in enumerate(lines[:2]):  # Mostrar 2 líneas por factura
            print(f"  {i+1}. Pedido: '{line.get('pedido', 'N/A')}' | Producto: {line.get('producto', 'N/A')[:40]}")
    
    return len(s00791_lines)

if __name__ == "__main__":
    total = main()
    print(f"\n🔢 TOTAL FINAL: {total} líneas S00791")