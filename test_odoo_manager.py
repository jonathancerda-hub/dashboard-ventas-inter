#!/usr/bin/env python
# test_odoo_manager.py - Prueba rápida del OdooManager actualizado

import sys
from odoo_manager import OdooManager

print("="*60)
print("PROBANDO ODOO MANAGER con JSON-RPC")
print("="*60)

# Inicializar OdooManager
print("\n1. Inicializando OdooManager...")
manager = OdooManager()

# Verificar conexión
if manager.uid:
    print(f"✅ Conexión exitosa!")
    print(f"   UID: {manager.uid}")
    print(f"   URL: {manager.url}")
    print(f"   DB: {manager.db}")
    print(f"   Usuario: {manager.username}")
    
    # Probar una consulta simple
    print("\n2. Probando consulta de productos...")
    try:
        product_ids = manager.models.execute_kw(
            manager.db, manager.uid, manager.password,
            'product.product', 'search',
            [[]], {'limit': 3}
        )
        
        if product_ids:
            print(f"✅ Encontrados {len(product_ids)} productos: {product_ids}")
            
            # Leer detalles
            products = manager.models.execute_kw(
                manager.db, manager.uid, manager.password,
                'product.product', 'read',
                [product_ids], {'fields': ['name', 'default_code']}
            )
            
            print("\n📦 Productos:")
            for p in products:
                print(f"   [{p.get('default_code', 'N/A')}] {p.get('name', 'Sin nombre')}")
        else:
            print("⚠️ No se encontraron productos")
            
    except Exception as e:
        print(f"❌ Error en consulta: {e}")
        sys.exit(1)
    
    # Probar get_sales_lines (método principal del dashboard)
    print("\n3. Probando get_sales_lines (método del dashboard)...")
    try:
        from datetime import datetime
        date_from = "2026-01-01"
        date_to = "2026-12-31"
        
        sales_lines, pagination = manager.get_sales_lines(
            date_from=date_from,
            date_to=date_to,
            limit=5
        )
        
        if sales_lines:
            print(f"✅ Encontradas {len(sales_lines)} líneas de venta")
            print(f"   Total items: {pagination.get('total', 'N/A')}")
            
            # Mostrar primera línea
            if len(sales_lines) > 0:
                first = sales_lines[0]
                print("\n📊 Primera línea de venta:")
                print(f"   Producto: {first.get('product_id', ['', 'N/A'])[1] if isinstance(first.get('product_id'), list) else 'N/A'}")
                print(f"   Cantidad: {first.get('quantity', 0)}")
                print(f"   Monto: ${first.get('amount_currency', 0):,.2f}")
        else:
            print("⚠️ No se encontraron líneas de venta para el período")
            
    except Exception as e:
        print(f"❌ Error en get_sales_lines: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ TODAS LAS PRUEBAS EXITOSAS")
    print("="*60)
    print("\n🚀 El dashboard ahora funcionará correctamente")
    print("   Ejecuta: python app.py")
    print("   Y abre: http://localhost:5000")
    
else:
    print("❌ No se pudo conectar a Odoo")
    print("   - Verifica las credenciales en .env")
    print("   - Verifica conectividad de red")
    sys.exit(1)
