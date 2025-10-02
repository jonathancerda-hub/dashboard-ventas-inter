#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_manager import OdooManager

def find_multi_invoice_orders():
    print("=== BUSCANDO PEDIDOS MULTI-FACTURA ===")
    
    odoo = OdooManager()
    
    try:
        # Buscar todas las facturas del canal internacional en 2025
        print("🔍 Buscando facturas del canal internacional en 2025...")
        
        invoices = odoo.models.execute_kw(odoo.db, odoo.uid, odoo.password, 'account.move', 'search_read',
            [[
                ('invoice_date', '>=', '2025-01-01'),
                ('invoice_date', '<=', '2025-12-31'),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('invoice_origin', '!=', False),
                ('team_id.name', 'ilike', 'INTERNACIONAL')
            ]],
            {'fields': ['id', 'name', 'invoice_origin', 'invoice_date'], 'limit': 200})
        
        print(f"✅ Encontradas {len(invoices)} facturas del canal internacional")
        
        # Agrupar por invoice_origin (pedido)
        orders = {}
        for invoice in invoices:
            origin = invoice.get('invoice_origin', '')
            if origin not in orders:
                orders[origin] = []
            orders[origin].append(invoice)
        
        # Encontrar pedidos con múltiples facturas
        multi_invoice_orders = {}
        for origin, invoice_list in orders.items():
            if len(invoice_list) > 1:
                multi_invoice_orders[origin] = invoice_list
        
        print(f"\n🎯 PEDIDOS MULTI-FACTURA ENCONTRADOS: {len(multi_invoice_orders)}")
        
        for i, (origin, invoices) in enumerate(multi_invoice_orders.items()):
            if i < 10:  # Mostrar solo los primeros 10
                print(f"\n--- {origin}: {len(invoices)} facturas ---")
                for inv in invoices:
                    print(f"  • {inv['name']} - {inv['invoice_date']}")
            elif i == 10:
                print(f"\n... y {len(multi_invoice_orders) - 10} pedidos multi-factura más")
                break
        
        return len(multi_invoice_orders), list(multi_invoice_orders.keys())[:5]  # Retornar algunos ejemplos
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0, []

def test_with_real_data():
    print("\n=== PRUEBA CON DATOS REALES ===")
    
    count, examples = find_multi_invoice_orders()
    
    if count > 0:
        print(f"\n✅ El sistema detectó {count} pedidos multi-factura")
        print("🔍 Ahora la aplicación web debería mostrar líneas completas para todos estos pedidos")
        print(f"📝 Ejemplos: {examples}")
        
        # Probar con el odoo_manager
        odoo = OdooManager()
        data = odoo.get_sales_lines(
            date_from='2025-01-01',
            date_to='2025-12-31',
            limit=5000
        )
        
        # Contar pedidos únicos
        unique_orders = set()
        for line in data:
            if line.get('pedido'):
                unique_orders.add(line.get('pedido'))
        
        print(f"📊 Total pedidos únicos en resultado: {len(unique_orders)}")
        print(f"📊 Total líneas procesadas: {len(data)}")
        
        # Buscar algunos de los pedidos multi-factura en los resultados
        found_multi = []
        for example in examples:
            if any(example in line.get('pedido', '') for line in data):
                found_multi.append(example)
        
        print(f"🎯 Pedidos multi-factura encontrados en resultado: {len(found_multi)}")
        if found_multi:
            print(f"   Ejemplos encontrados: {found_multi}")
        
    else:
        print("⚠️ No se encontraron otros pedidos multi-factura además de S00791")

if __name__ == "__main__":
    test_with_real_data()