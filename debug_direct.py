#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_manager import OdooManager

def debug_s00791_specific():
    print("=== DEBUG ESPECÍFICO S00791 ===")
    
    odoo = OdooManager()
    print("✅ Conexión establecida")
    
    # Buscar directamente las facturas problemáticas
    try:
        # Usar conexión existente
        models = odoo.models
        uid = odoo.uid
        
        print("\n🔍 BUSCANDO FACTURAS ESPECÍFICAS...")
        
        # Buscar las facturas específicas (con prefijo F)
        target_invoices = ['F F15-00000187', 'F F15-00000154', 'F F15-00000149']
        
        for invoice_name in target_invoices:
            print(f"\n--- Factura {invoice_name} ---")
            
            # Buscar la factura
            moves = models.execute_kw(odoo.db, uid, odoo.password, 'account.move', 'search_read', 
                [[['name', '=', invoice_name], ['move_type', '=', 'out_invoice']]], 
                {'fields': ['id', 'name', 'state', 'invoice_date', 'invoice_origin', 'team_id']})
            
            if moves:
                move = moves[0]
                print(f"  Factura encontrada: ID={move['id']}, Estado={move['state']}, Fecha={move['invoice_date']}")
                print(f"  Origen: {move.get('invoice_origin', 'N/A')}, Canal: {move.get('team_id', 'N/A')}")
                
                # Buscar líneas de esta factura
                lines = models.execute_kw(odoo.db, uid, odoo.password, 'account.move.line', 'search_read',
                    [[['move_id', '=', move['id']], ['exclude_from_invoice_tab', '=', False]]],
                    {'fields': ['id', 'product_id', 'quantity', 'balance', 'account_id'], 'limit': 50})
                
                print(f"  Líneas encontradas: {len(lines)}")
                for line in lines:
                    if line.get('product_id'):
                        print(f"    ID: {line['id']}, Producto: {line['product_id'][0] if line['product_id'] else 'N/A'}, Cantidad: {line['quantity']}, Balance: {line['balance']}")
                        
            else:
                print(f"  ❌ Factura {invoice_name} NO encontrada")
                
        print("\n🔍 BUSCANDO EN ACCOUNT.MOVE.LINE DIRECTAMENTE...")
        
        # Buscar todas las líneas que contengan estos números de factura
        all_lines = models.execute_kw(odoo.db, uid, odoo.password, 'account.move.line', 'search_read',
            [[['move_id.name', 'in', target_invoices]]],
            {'fields': ['id', 'move_id', 'product_id', 'quantity', 'balance'], 'limit': 20})
        
        print(f"Total líneas encontradas directamente: {len(all_lines)}")
        for line in all_lines:
            print(f"  ID: {line['id']}, Factura: {line['move_id'][1] if line['move_id'] else 'N/A'}, Producto: {line['product_id'][0] if line['product_id'] else 'N/A'}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_s00791_specific()