#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_manager import OdooManager

def check_excluded_categories():
    print("=== VERIFICAR CATEGORÍAS EXCLUIDAS ===")
    
    odoo = OdooManager()
    
    # IDs de líneas que sabemos que existen
    missing_lines = [1189865, 1159874, 1159876, 1159877, 1159878, 1159886]
    excluded_categories = [315, 333, 304, 314, 318, 339]
    
    print(f"Líneas faltantes: {missing_lines}")
    print(f"Categorías excluidas: {excluded_categories}")
    
    try:
        # Buscar las líneas específicas
        lines = odoo.models.execute_kw(odoo.db, odoo.uid, odoo.password, 'account.move.line', 'search_read',
            [[['id', 'in', missing_lines]]],
            {'fields': ['id', 'move_id', 'product_id'], 'limit': 10})
        
        print(f"\nEncontradas {len(lines)} líneas:")
        
        # Para cada línea, obtener la categoría del producto
        for line in lines:
            line_id = line['id']
            product_id = line['product_id'][0] if line['product_id'] else None
            factura = line['move_id'][1] if line['move_id'] else 'N/A'
            
            if product_id:
                # Buscar el producto y su categoría
                products = odoo.models.execute_kw(odoo.db, odoo.uid, odoo.password, 'product.product', 'search_read',
                    [[['id', '=', product_id]]],
                    {'fields': ['id', 'name', 'default_code', 'categ_id'], 'limit': 1})
                
                if products:
                    product = products[0]
                    categ_id = product['categ_id'][0] if product['categ_id'] else None
                    categ_name = product['categ_id'][1] if product['categ_id'] else 'N/A'
                    
                    is_excluded = categ_id in excluded_categories
                    status = "❌ EXCLUIDA" if is_excluded else "✅ INCLUIDA"
                    
                    has_code = bool(product.get('default_code'))
                    code_status = "✅ CON CÓDIGO" if has_code else "❌ SIN CÓDIGO"
                    print(f"  Línea {line_id} | {factura} | Producto: {product['name'][:40]} | Categoría: {categ_id} ({categ_name}) | {status} | Código: '{product.get('default_code', 'N/A')}' | {code_status}")
                else:
                    print(f"  Línea {line_id} | {factura} | ❌ Producto no encontrado")
            else:
                print(f"  Línea {line_id} | {factura} | ❌ Sin producto")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_excluded_categories()