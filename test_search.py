#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_manager import OdooManager

def test_search_functionality():
    print("=== PROBANDO FUNCIONALIDAD DE BÚSQUEDA ===")
    
    odoo = OdooManager()
    
    # Test 1: Búsqueda de S00791
    print("\n1. 🔍 Probando búsqueda: 'S00791'")
    results_s00791 = odoo.get_sales_lines(
        date_from='2025-01-01',
        date_to='2025-12-31',
        search='S00791',
        limit=5000
    )
    
    print(f"   ✅ Resultados: {len(results_s00791)} líneas")
    pedidos_s00791 = set()
    facturas_s00791 = set()
    for line in results_s00791:
        if line.get('pedido'):
            pedidos_s00791.add(line.get('pedido'))
        if line.get('factura'):
            facturas_s00791.add(line.get('factura'))
    
    print(f"   📋 Pedidos encontrados: {list(pedidos_s00791)}")
    print(f"   📄 Facturas encontradas: {len(facturas_s00791)} facturas")
    
    # Test 2: Búsqueda de S01872 (pedido con 9 facturas)
    print("\n2. 🔍 Probando búsqueda: 'S01872'")
    results_s01872 = odoo.get_sales_lines(
        date_from='2025-01-01',
        date_to='2025-12-31',
        search='S01872',
        limit=5000
    )
    
    print(f"   ✅ Resultados: {len(results_s01872)} líneas")
    pedidos_s01872 = set()
    facturas_s01872 = set()
    for line in results_s01872:
        if line.get('pedido'):
            pedidos_s01872.add(line.get('pedido'))
        if line.get('factura'):
            facturas_s01872.add(line.get('factura'))
    
    print(f"   📋 Pedidos encontrados: {list(pedidos_s01872)}")
    print(f"   📄 Facturas encontradas: {len(facturas_s01872)} facturas")
    
    # Test 3: Búsqueda de producto específico
    print("\n3. 🔍 Probando búsqueda: 'CEFA-MILK'")
    results_product = odoo.get_sales_lines(
        date_from='2025-01-01',
        date_to='2025-12-31',
        search='CEFA-MILK',
        limit=5000
    )
    
    print(f"   ✅ Resultados: {len(results_product)} líneas")
    pedidos_product = set()
    productos_product = set()
    for line in results_product:
        if line.get('pedido'):
            pedidos_product.add(line.get('pedido'))
        if line.get('producto'):
            productos_product.add(line.get('producto'))
    
    print(f"   📋 Pedidos encontrados: {len(pedidos_product)} pedidos únicos")
    print(f"   📦 Productos únicos: {len(productos_product)}")
    
    # Verificar si incluye líneas de pedidos multi-factura
    multi_factura_pedidos = ['S00791', 'S01872', 'S02078', 'S03826']
    found_multi = [p for p in multi_factura_pedidos if p in pedidos_product]
    if found_multi:
        print(f"   🎯 Pedidos multi-factura incluidos: {found_multi}")
    
    print("\n=== RESUMEN ===")
    print(f"✅ Búsqueda S00791: {len(results_s00791)} líneas")
    print(f"✅ Búsqueda S01872: {len(results_s01872)} líneas") 
    print(f"✅ Búsqueda producto: {len(results_product)} líneas")
    
    if len(results_s00791) >= 10 and len(results_s01872) > 0:
        print("🎉 ¡Búsqueda funcionando correctamente!")
    else:
        print("⚠️ La búsqueda necesita ajustes")

if __name__ == "__main__":
    test_search_functionality()