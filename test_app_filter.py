from odoo_manager import OdooManager

# Simular la lógica de app.py para S00791
manager = OdooManager()

# Obtener datos como en app.py
query_filters = {
    'date_from': '2025-01-01',
    'date_to': '2025-12-31',
    'search_term': 'S00791'
}

print(f"🔍 DEBUG: Filtros recibidos - date_from: '{query_filters.get('date_from')}', date_to: '{query_filters.get('date_to')}'")
print("🔍 DEBUG: Usando fechas por defecto: 2025-01-01 a 2025-12-31")

# Obtener datos básicos de ventas
sales_data_raw = manager.get_sales_lines(
    date_from=query_filters.get('date_from'),
    date_to=query_filters.get('date_to'),
    partner_id=None,
    linea_id=None,
    limit=5000
)

print(f"🔍 DEBUG: Total de registros obtenidos: {len(sales_data_raw)}")

# Simular la lógica de filtrado exacta de app.py
sales_data_filtered = []
international_count = 0
canales_unicos = set()
search_term = query_filters.get('search_term', '').lower() if query_filters.get('search_term') else None

# DEBUG: Información de búsqueda
if search_term:
    print(f"🔍 DEBUG: Buscando término: '{search_term}'")

for sale in sales_data_raw:
    team_id = sale.get('team_id')
    nombre_canal = ''
    
    # Obtener información del pedido y factura
    pedido = sale.get('pedido', '')
    factura = sale.get('factura', '')
    
    # DEBUG: Para S00791 específicamente
    if search_term and 's00791' in pedido.lower():
        print(f"🔍 DEBUG S00791: Procesando línea con pedido: {pedido}")
        print(f"   team_id: {team_id}")
        print(f"   factura: {factura}")
    
    if team_id and isinstance(team_id, list) and len(team_id) > 1:
        nombre_canal = team_id[1]
        canales_unicos.add(nombre_canal)
        
        # DEBUG para S00791
        if search_term and 's00791' in pedido.lower():
            print(f"   nombre_canal: {nombre_canal}")
            print(f"   es internacional: {'INTERNACIONAL' in nombre_canal.upper()}")
        
        if 'INTERNACIONAL' in nombre_canal.upper():
            
            # Aplicar filtro de búsqueda después del filtro de canal
            if search_term:
                # Validar tipos y convertir a string de forma segura
                producto = str(sale.get('producto', '') or '').lower()
                codigo = str(sale.get('codigo_odoo', '') or '').lower()
                cliente = str(sale.get('cliente', '') or '').lower()
                pedido_lower = str(pedido or '').lower()
                factura_lower = str(factura or '').lower()
                
                # DEBUG para S00791
                if 's00791' in pedido_lower:
                    print(f"   Comprobando búsqueda:")
                    print(f"     - En pedido '{pedido_lower}': {search_term in pedido_lower}")
                    print(f"     - En producto '{producto}': {search_term in producto}")
                    print(f"     - En código '{codigo}': {search_term in codigo}")
                    print(f"     - En cliente '{cliente}': {search_term in cliente}")
                    print(f"     - En factura '{factura_lower}': {search_term in factura_lower}")
                
                if (search_term in producto or 
                    search_term in codigo or 
                    search_term in cliente or
                    search_term in pedido_lower or
                    search_term in factura_lower):
                    
                    # DEBUG para S00791
                    if 's00791' in pedido.lower():
                        print(f"   ✅ AÑADIDA línea S00791 a resultados")
                    
                    sales_data_filtered.append(sale)
                    international_count += 1
            else:
                sales_data_filtered.append(sale)
                international_count += 1
    else:
        # DEBUG para S00791
        if search_term and 's00791' in pedido.lower():
            print(f"   ❌ team_id inválido: {team_id}")

print(f"DEBUG: Terminó el bucle. Total encontrado: {international_count}")
print(f"DEBUG canales únicos encontrados: {sorted(list(canales_unicos))}")
print(f"🌍 DEBUG: Ventas internacionales encontradas: {international_count} de {len(sales_data_raw)}")
print(f"DEBUG: Datos filtrados antes de paginación: {len(sales_data_filtered)}")

# Verificar si hay líneas de S00791 en los resultados
s00791_results = [sale for sale in sales_data_filtered if 's00791' in sale.get('pedido', '').lower()]
print(f"📊 Líneas de S00791 en resultados finales: {len(s00791_results)}")