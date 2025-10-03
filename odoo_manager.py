# odoo_manager.py - Versión Completa Restaurada

import xmlrpc.client
import http.client
import socket
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OdooManager:
    def get_commercial_lines_stacked_data(self, date_from=None, date_to=None, linea_id=None, partner_id=None):
        """Devuelve datos para gráfico apilado por línea comercial y 5 categorías"""
        sales_lines = self.get_sales_lines(
            date_from=date_from,
            date_to=date_to,
            partner_id=partner_id,
            linea_id=linea_id,
            limit=5000
        )
        # Nombres de las categorías a apilar
        categories = [
            ('pharmaceutical_forms_id', 'Forma Farmacéutica'),
            ('pharmacological_classification_id', 'Clasificación Farmacológica'),
            ('administration_way_id', 'Vía de Administración'),
            ('categ_id', 'Categoría de Producto'),
            ('production_line_id', 'Línea de Producción')
        ]
        # Agrupar por línea comercial
        lines = {}
        for line in sales_lines:
            cl = line.get('commercial_line_national_id')
            if cl and isinstance(cl, list) and len(cl) > 1:
                line_name = cl[1]
            else:
                line_name = 'Sin Línea Comercial'
            if line_name not in lines:
                lines[line_name] = {cat[1]: 0 for cat in categories}
            for key, cat_name in categories:
                val = line.get(key)
                # Si el campo es una lista [id, nombre], sumar por cantidad
                if val and isinstance(val, list) and len(val) > 1:
                    lines[line_name][cat_name] += line.get('quantity', 0)
                elif val:
                    lines[line_name][cat_name] += line.get('quantity', 0)
        # Preparar formato para ECharts
        yAxis = list(lines.keys())
        series = []
        for key, cat_name in categories:
            data = [lines[line_name][cat_name] for line_name in yAxis]
            series.append({
                'name': cat_name,
                'type': 'bar',
                'stack': 'total',
                'label': {'show': True},
                'data': data
            })
        return {
            'yAxis': yAxis,
            'series': series,
            'legend': [cat[1] for cat in categories]
        }
    def __init__(self):
        # Configurar conexión a Odoo - Usar credenciales del .env
        try:
            # Cargar credenciales desde variables de entorno (sin valores por defecto)
            self.url = os.getenv('ODOO_URL')
            self.db = os.getenv('ODOO_DB')
            self.username = os.getenv('ODOO_USER')
            self.password = os.getenv('ODOO_PASSWORD')
            
            # Validar que todas las credenciales estén configuradas
            if not all([self.url, self.db, self.username, self.password]):
                missing = [var for var, val in [
                    ('ODOO_URL', self.url), ('ODOO_DB', self.db), 
                    ('ODOO_USER', self.username), ('ODOO_PASSWORD', self.password)
                ] if not val]
                raise ValueError(f"Variables de entorno faltantes: {', '.join(missing)}")
            
            # Timeout configurable para llamadas XML-RPC (segundos)
            try:
                rpc_timeout = int(os.getenv('ODOO_RPC_TIMEOUT', '10'))
            except Exception:
                rpc_timeout = 10

            # Transport personalizado que aplica timeout a la conexión HTTP/HTTPS
            class TimeoutTransport(xmlrpc.client.Transport):
                def __init__(self, timeout=None, use_https=False):
                    super().__init__()
                    self._timeout = timeout
                    self._use_https = use_https

                def make_connection(self, host):
                    # host may include :port
                    if self._use_https:
                        return http.client.HTTPSConnection(host, timeout=self._timeout)
                    return http.client.HTTPConnection(host, timeout=self._timeout)

            use_https = str(self.url).lower().startswith('https')
            transport = TimeoutTransport(timeout=rpc_timeout, use_https=use_https)

            # Establecer conexión con timeout
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common', transport=transport)
            try:
                self.uid = common.authenticate(self.db, self.username, self.password, {})
            except socket.timeout:
                self.uid = None
            except Exception as auth_e:
                # Manejar errores de protocolo o conexión sin bloquear
                self.uid = None
            
            if self.uid:
                # Usar el mismo transport para el endpoint de object
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object', transport=transport)
            else:
                self.uid = None
                self.models = None
                
        except Exception as e:
            print(f"Error en la conexión a Odoo: {e}")
            print("Continuando en modo offline.")
            self.uid = None
            self.models = None

    def authenticate_user(self, username, password):
        """Autenticar usuario contra Odoo y devolver sus datos si es exitoso."""
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            uid = common.authenticate(self.db, username, password, {})
            
            if uid:
                # Una vez autenticado, obtener el nombre del usuario
                models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                user_data = models.execute_kw(
                    self.db, uid, password, 'res.users', 'read',
                    [uid], {'fields': ['name', 'login']}
                )
                if user_data:
                    return user_data[0]  # Devuelve {'id': uid, 'name': 'John Doe', 'login': '...'}
                else:
                    # Fallback si no se pueden leer los datos del usuario
                    return {'id': uid, 'name': username, 'login': username}
            else:
                return None
                
        except Exception as e:
            # En caso de error de conexión, no se puede autenticar
            return None

    def get_international_clients(self):
        """Obtener clientes específicos del canal de ventas internacionales de facturas y pedidos."""
        try:
            all_partner_ids = set()

            # 1. Obtener clientes de Pedidos de Venta (pendientes)
            order_domain = [
                ('team_id.name', 'ilike', 'INTERNACIONAL'),
                ('state', 'in', ['sale', 'done'])
            ]
            orders = self.models.execute_kw(
                self.db, self.uid, self.password, 'sale.order', 'search_read',
                [order_domain],
                {'fields': ['partner_id'], 'limit': 2000}
            )
            for order in orders:
                if order.get('partner_id'):
                    all_partner_ids.add(order['partner_id'][0])

            # 2. Obtener clientes de Facturas (facturado)
            invoice_domain = [
                ('team_id.name', 'ilike', 'INTERNACIONAL'),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', '=', 'posted'),
                ('partner_id', '!=', False)
            ]
            invoices = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move', 'read_group',
                [invoice_domain],
                {
                    'fields': ['partner_id'],
                    'groupby': ['partner_id'],
                    'lazy': False
                }
            )
            for group in invoices:
                if group.get('partner_id'):
                    all_partner_ids.add(group['partner_id'][0])

            partner_ids = list(all_partner_ids)
            
            if not partner_ids:
                print("DEBUG: No se encontraron clientes del canal internacional en pedidos o facturas.")
                return []
            
            # Obtener información completa de estos clientes
            international_partners = self.models.execute_kw(
                self.db, self.uid, self.password, 'res.partner', 'search_read',
                [[('id', 'in', partner_ids)]],
                {'fields': ['id', 'name', 'country_id'], 'limit': len(partner_ids)}
            )
            
            # Formatear y ordenar clientes
            clientes_internacionales = []
            for partner in international_partners:
                country_name = ""
                if partner.get('country_id') and isinstance(partner['country_id'], list):
                    country_name = f" ({partner['country_id'][1]})"
                
                clientes_internacionales.append([
                    partner['id'], 
                    f"{partner['name']}{country_name}"
                ])
            
            # Ordenar alfabéticamente
            clientes_internacionales.sort(key=lambda x: x[1])
            
            print(f"DEBUG: Encontrados {len(clientes_internacionales)} clientes internacionales únicos.")
            return clientes_internacionales
            
        except Exception as e:
            print(f"Error al obtener clientes internacionales: {e}")
            return []

    def get_sales_filter_options(self):
        """Obtener opciones para filtros de ventas"""
        try:
            # Obtener líneas comerciales
            lineas = []
            try:
                # Consulta directa a productos para obtener líneas comerciales
                products = self.models.execute_kw(
                    self.db, self.uid, self.password, 'product.product', 'search_read',
                    [[('commercial_line_national_id', '!=', False)]],
                    {'fields': ['commercial_line_national_id'], 'limit': 1000}
                )
                
                # Extraer líneas únicas
                unique_lines = {}
                for product in products:
                    if product.get('commercial_line_national_id'):
                        line_id, line_name = product['commercial_line_national_id']
                        unique_lines[line_id] = line_name
                
                # Formatear líneas
                lineas = [
                    {'id': line_id, 'display_name': line_name}
                    for line_id, line_name in unique_lines.items()
                ]
                lineas.sort(key=lambda x: x['display_name'])
                
            except Exception as product_error:
                print(f"Error obteniendo líneas de productos: {product_error}")

            # Para compatibilidad con diferentes templates
            commercial_lines = lineas
            
            # Obtener clientes internacionales específicos
            clientes_internacionales = self.get_international_clients()
            
            # Mantener compatibilidad con el formato anterior
            partners = [{'id': cliente[0], 'name': cliente[1]} for cliente in clientes_internacionales]
            
            return {
                'commercial_lines': commercial_lines,
                'lineas': lineas,  # Para compatibilidad con meta.html
                'partners': partners,
                'clientes': clientes_internacionales  # Lista de [id, nombre] para el template
            }
            
        except Exception as e:
            print(f"Error al obtener opciones de filtro de ventas: {e}")
            return {'commercial_lines': [], 'lineas': [], 'partners': [], 'clientes': []}

    def get_filter_options(self):
        """Alias para get_sales_filter_options para compatibilidad"""
        return self.get_sales_filter_options()

    def get_all_sellers(self):
        """Obtiene una lista única de todos los vendedores (invoice_user_id)."""
        try:
            if not self.uid or not self.models:
                return []
            
            # Usamos read_group para obtener vendedores únicos de forma eficiente
            seller_groups = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move', 'read_group',
                [[('invoice_user_id', '!=', False)]],
                {'fields': ['invoice_user_id'], 'groupby': ['invoice_user_id']}
            )
            
            # Formatear la lista para el frontend
            sellers = []
            for group in seller_groups:
                if group.get('invoice_user_id'):
                    seller_id, seller_name = group['invoice_user_id']
                    sellers.append({'id': seller_id, 'name': seller_name})
            
            return sorted(sellers, key=lambda x: x['name'])
        except Exception as e:
            print(f"Error obteniendo la lista de vendedores: {e}")
            return []

    def get_sales_lines(self, page=None, per_page=None, filters=None, date_from=None, date_to=None, partner_id=None, linea_id=None, search=None, limit=5000):
        """Obtener líneas de venta completas con todas las 27 columnas"""
        try:
            # Verificar conexión
            if not self.uid or not self.models:
                if page is not None and per_page is not None:
                    return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
                return []
            
            # Manejar parámetros de ambos formatos de llamada
            if filters:
                date_from = filters.get('date_from')
                date_to = filters.get('date_to')
                partner_id = filters.get('partner_id')
                linea_id = filters.get('linea_id')
                search = filters.get('search')
            
            # Detectar tipo de búsqueda ANTES de construir el dominio
            search_pedido = None
            search_factura = False
            
            if search:
                search_upper = search.upper()
                import re
                # Buscar patrones de pedido (S00XXX, S01XXX, etc.)
                pedido_pattern = r'S\d{5}'
                pedido_match = re.search(pedido_pattern, search_upper)
                if pedido_match:
                    search_pedido = pedido_match.group()
                
                # Detectar si se está buscando una factura (F, FF, FFF seguido de números o guiones)
                factura_pattern = r'F+\s*[A-Z]?\d+[-\d]*'
                if re.search(factura_pattern, search_upper):
                    search_factura = True
            
            # Construir dominio de filtro
            domain = [
                ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
                ('move_id.state', '=', 'posted'),
                ('product_id', '!=', False)  # Solo líneas con producto (excluye impuestos, descuentos, etc.)
            ]
            
            # NO aplicar filtros de código, categorías ni display_type
            
            # Filtros de fecha
            if date_from:
                domain.append(('move_id.invoice_date', '>=', date_from))
            else:
                # Si no hay fecha de inicio, por defecto buscar en los últimos 30 días
                # PERO: Si hay filtro de cliente, NO aplicar límite de 30 días
                if not date_to and not partner_id:
                    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    domain.append(('move_id.invoice_date', '>=', thirty_days_ago))

            if date_to:
                domain.append(('move_id.invoice_date', '<=', date_to))
            
            # Si se está buscando una factura específica, agregar filtro por nombre de factura
            if search and search_factura:
                domain.append(('move_name', 'ilike', search))
            
            # Filtro de cliente: primero obtener los move_ids del cliente, luego filtrar líneas
            if partner_id:
                # Buscar facturas del cliente
                client_moves = self.models.execute_kw(
                    self.db, self.uid, self.password, 'account.move', 'search',
                    [[
                        ('partner_id', '=', partner_id),
                        ('move_type', 'in', ['out_invoice', 'out_refund']),
                        ('state', '=', 'posted')
                    ]]
                )
                print(f"DEBUG FILTRO CLIENTE: Partner ID {partner_id} tiene {len(client_moves)} facturas")
                if client_moves:
                    domain.append(('move_id', 'in', client_moves))
                    print(f"DEBUG FILTRO CLIENTE: Agregado filtro move_id in {len(client_moves)} facturas")
                    print(f"DEBUG FILTRO CLIENTE: IDs de facturas: {client_moves[:5]}... (mostrando primeras 5)")
                else:
                    # Si no hay facturas para este cliente, retornar vacío
                    print(f"DEBUG FILTRO CLIENTE: No se encontraron facturas para partner_id {partner_id}")
                    return []
            
            # Filtro de línea comercial
            if linea_id:
                domain.append(('product_id.commercial_line_national_id', '=', linea_id))
            
            # DEBUG: Mostrar el domain completo
            if partner_id:
                print(f"DEBUG DOMAIN: {domain}")
            
            # Buscar facturas del pedido específico si hay búsqueda de pedido
            searched_move_ids = []
            
            if search_pedido:
                try:
                    searched_invoices = self.models.execute_kw(
                        self.db, self.uid, self.password, 'account.move', 'search_read',
                        [[('invoice_origin', 'ilike', search_pedido)]], 
                        {
                            'fields': ['id', 'name', 'invoice_origin', 'invoice_date', 'state', 'team_id', 'move_type'],
                            'context': {'lang': 'es_PE'}
                        }
                    )
                    for inv in searched_invoices:
                        searched_move_ids.append(inv['id'])
                except Exception as e:
                    pass
            
            # Si estamos buscando un pedido específico o detectamos sus facturas, incluir específicamente esas facturas
            # TAMBIÉN aplicar para otros pedidos multi-factura detectados automáticamente
            special_move_ids = searched_move_ids.copy()
            
            # SOLUCIÓN MEJORADA: Detectar TODOS los pedidos multi-factura automáticamente
            # Funciona tanto con búsqueda como sin ella
            # PERO: Si se está buscando una factura específica, NO usar lógica multi-factura
            if date_from and date_to and not search_factura:
                try:
                    # Si estamos buscando un pedido específico, NO hacer la detección automática
                    if not search_pedido:
                        # Obtener TODAS las facturas del canal internacional
                        all_invoices = self.models.execute_kw(
                            self.db, self.uid, self.password, 'account.move', 'search_read',
                            [[
                                ('invoice_date', '>=', date_from),
                                ('invoice_date', '<=', date_to), 
                                ('move_type', '=', 'out_invoice'),
                                ('state', '=', 'posted'),
                                ('invoice_origin', '!=', False),
                                ('team_id.name', 'ilike', 'INTERNACIONAL')
                            ]],
                            {'fields': ['id', 'invoice_origin'], 'limit': 500}
                        )
                        
                        # Agrupar por invoice_origin para encontrar pedidos multi-factura
                        origin_groups = {}
                        for inv in all_invoices:
                            origin = inv.get('invoice_origin', '')
                            if origin not in origin_groups:
                                origin_groups[origin] = []
                            origin_groups[origin].append(inv['id'])
                        
                        # Encontrar pedidos con múltiples facturas
                        multi_origin_move_ids = []
                        multi_origin_count = 0
                        for origin, move_ids in origin_groups.items():
                            if len(move_ids) > 1:  # Más de una factura por pedido
                                multi_origin_move_ids.extend(move_ids)
                                multi_origin_count += 1
                        
                        # Si hay búsqueda general (no específica de pedido), filtrar solo las facturas relevantes
                        if search:
                            # Solo incluir facturas de pedidos que coincidan con la búsqueda
                            relevant_move_ids = []
                            search_lower = search.lower()
                            for origin, move_ids in origin_groups.items():
                                if len(move_ids) > 1 and search_lower in origin.lower():
                                    relevant_move_ids.extend(move_ids)
                            special_move_ids.extend(relevant_move_ids)
                        else:
                            # Sin búsqueda, incluir todos los pedidos multi-factura
                            special_move_ids.extend(multi_origin_move_ids)
                    else:
                        pass
                        
                except Exception as e:
                    pass
            
            # Usar consulta especial si hay pedidos multi-factura detectados O si se busca S00791 específicamente
            if len(special_move_ids) > 0 and special_move_ids:
                # REEMPLAZAR completamente el dominio para consultar facturas de pedidos multi-factura
                domain = [
                    ('move_id', 'in', special_move_ids),
                    ('product_id', '!=', False),  # Solo líneas con productos
                    ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
                    ('move_id.state', '=', 'posted')
                ]
                
                # Mantener el filtro de cliente si existe
                if partner_id:
                    domain.append(('partner_id', '=', partner_id))
                
                # Remover límite para obtener TODAS las líneas de pedidos multi-factura
                limit = None
            
            # Obtener líneas base con todos los campos necesarios
            query_options = {
                'fields': [
                    'move_id', 'partner_id', 'product_id', 'balance', 'move_name',
                    'quantity', 'price_unit', 'tax_ids'
                ],
                'context': {'lang': 'es_PE'}
            }
            
            # Solo agregar limit si no es None (XML-RPC no maneja None)
            if limit is not None:
                query_options['limit'] = limit
            
            sales_lines_base = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move.line', 'search_read',
                [domain],
                query_options
            )
            
            print(f"DEBUG: Total líneas obtenidas de account.move.line: {len(sales_lines_base)}")
            
            # DEBUG: Si hay partner_id, verificar por qué solo trae pocas líneas
            if partner_id and len(sales_lines_base) < 20:
                print(f"DEBUG FILTRO CLIENTE: Solo {len(sales_lines_base)} líneas para {len(client_moves) if 'client_moves' in locals() else 0} facturas")
                # Probar sin filtros de producto para ver cuántas líneas hay realmente
                domain_test = [
                    ('move_id', 'in', client_moves),
                    ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
                    ('move_id.state', '=', 'posted')
                ]
                if date_from:
                    domain_test.append(('move_id.invoice_date', '>=', date_from))
                if date_to:
                    domain_test.append(('move_id.invoice_date', '<=', date_to))
                
                test_lines_full = self.models.execute_kw(
                    self.db, self.uid, self.password, 'account.move.line', 'search_read',
                    [domain_test],
                    {'fields': ['display_type', 'product_id', 'balance'], 'limit': 100}
                )
                print(f"DEBUG FILTRO CLIENTE: Sin filtros de producto/display hay {len(test_lines_full)} líneas totales")
                
                # Contar por display_type
                display_types = {}
                con_producto = 0
                for line in test_lines_full:
                    dt = line.get('display_type') or 'False/None'
                    display_types[dt] = display_types.get(dt, 0) + 1
                    if line.get('product_id'):
                        con_producto += 1
                
                print(f"DEBUG FILTRO CLIENTE: Display types: {display_types}")
                print(f"DEBUG FILTRO CLIENTE: Líneas con producto: {con_producto}")
            
            
            if not sales_lines_base:
                return []
            
            # Obtener IDs únicos para consultas relacionadas
            move_ids = list(set([line['move_id'][0] for line in sales_lines_base if line.get('move_id')]))
            product_ids = list(set([line['product_id'][0] for line in sales_lines_base if line.get('product_id')]))
            # partner_ids se obtiene después de consultar los moves
            partner_ids = []  # Inicializar vacío
            
            
            # Obtener datos de facturas (account.move) - Asientos contables
            move_data = {}
            if move_ids:
                moves = self.models.execute_kw(
                    self.db, self.uid, self.password, 'account.move', 'search_read',
                    [[('id', 'in', move_ids)]],
                    {
                        'fields': [
                            'payment_state', 'team_id', 'invoice_user_id', 'invoice_origin',
                            'invoice_date', 'l10n_latam_document_type_id', 'origin_number',
                            'order_id', 'name', 'ref', 'journal_id', 'amount_total', 'state',
                            'currency_id', 'exchange_rate', 'partner_id'
                        ],
                        'context': {'lang': 'es_PE'}
                    }
                )
                move_data = {m['id']: m for m in moves}
                
                # Extraer partner_ids de los moves (facturas) en lugar de las líneas
                partner_ids = list(set([m['partner_id'][0] for m in moves if m.get('partner_id')]))
                
                # DEBUG: Mostrar todos los canales de venta (team_id) únicos
                unique_teams = set()
                for move in moves:
                    if move.get('team_id') and isinstance(move['team_id'], list) and len(move['team_id']) > 1:
                        unique_teams.add(move['team_id'][1])
                
            
            # Obtener datos de productos con todos los campos farmacéuticos
            product_data = {}
            if product_ids:
                products = self.models.execute_kw(
                    self.db, self.uid, self.password, 'product.product', 'search_read',
                    [[('id', 'in', product_ids)]],
                    {
                        'fields': [
                            'name', 'default_code', 'categ_id', 'commercial_line_national_id',
                            'pharmacological_classification_id', 'pharmaceutical_forms_id',
                            'administration_way_id', 'production_line_id', 'product_life_cycle',
                        ],
                        'context': {'lang': 'es_PE'}
                    }
                )
                product_data = {p['id']: p for p in products}
            
            # Obtener datos de clientes incluyendo país
            partner_data = {}
            if partner_ids:
                partners = self.models.execute_kw(
                    self.db, self.uid, self.password, 'res.partner', 'search_read',
                    [[('id', 'in', partner_ids)]],
                    {'fields': ['vat', 'name', 'country_id'], 'context': {'lang': 'es_PE'}}
                )
                partner_data = {p['id']: p for p in partners}
            
            # Obtener datos de órdenes de venta con más campos
            order_ids = [move['order_id'][0] for move in move_data.values() if move.get('order_id')]
            order_data = {}
            if order_ids:
                orders = self.models.execute_kw(
                    self.db, self.uid, self.password, 'sale.order', 'search_read',
                    [[('id', 'in', list(set(order_ids)))]],
                    {
                        'fields': [
                            'name', 'delivery_observations', 'partner_supplying_agency_id', 
                            'partner_shipping_id', 'date_order', 'state', 'amount_total',
                            'user_id', 'team_id', 'warehouse_id', 'commitment_date',
                            'client_order_ref', 'origin',
                        ]
                    }
                )
                order_data = {o['id']: o for o in orders}
            
            # Obtener datos de líneas de orden de venta con más campos
            sale_line_data = {}
            if order_ids and product_ids:
                try:
                    sale_lines = self.models.execute_kw(
                        self.db, self.uid, self.password, 'sale.order.line', 'search_read',
                        [[('order_id', 'in', list(set(order_ids))), ('product_id', 'in', product_ids)]],
                        {
                            'fields': [
                                'order_id', 'product_id', 'route_id', 'name', 'product_uom_qty',
                                'price_unit', 'price_subtotal', 'discount', 'product_uom',
                                'analytic_distribution', 'display_type'
                            ],
                            'context': {'lang': 'es_PE'}
                        }
                    )
                    for sl in sale_lines:
                        if sl.get('order_id') and sl.get('product_id'):
                            key = (sl['order_id'][0], sl['product_id'][0])
                            sale_line_data[key] = sl
                except Exception as e:
                    pass
            
            # Obtener todos los tax_ids únicos de las líneas contables
            all_tax_ids = set()
            for line in sales_lines_base:
                if line.get('tax_ids'):
                    all_tax_ids.update(line['tax_ids'])
            tax_names = {}
            if all_tax_ids:
                taxes = self.models.execute_kw(
                    self.db, self.uid, self.password, 'account.tax', 'search_read',
                    [[('id', 'in', list(all_tax_ids))]],
                    {'fields': ['id', 'name'], 'context': {'lang': 'es_PE'}}
                )
                tax_names = {t['id']: t['name'] for t in taxes}
            
            # Procesar y combinar todos los datos para las 27 columnas
            sales_lines = []
            ecommerce_reassigned = 0
            s00791_debug_count = 0  # Contador para debug del pedido específico
            
            for line in sales_lines_base:
                move_id = line.get('move_id')
                product_id = line.get('product_id')
                
                # Obtener datos relacionados
                move = move_data.get(move_id[0], {}) if move_id else {}
                product = product_data.get(product_id[0], {}) if product_id else {}
                
                # Obtener partner_id desde el move (factura) en lugar de la línea
                partner_id_from_move = move.get('partner_id')
                partner = partner_data.get(partner_id_from_move[0], {}) if partner_id_from_move else {}
                
                # Obtener datos de orden de venta
                order_id = move.get('order_id')
                order = order_data.get(order_id[0], {}) if order_id else {}
                
                # Obtener datos de línea de orden
                sale_line_key = (order_id[0], product_id[0]) if order_id and product_id else None
                sale_line = sale_line_data.get(sale_line_key, {}) if sale_line_key else {}
                # Obtener nombres de impuestos
                imp_list = []
                for tid in line.get('tax_ids', []):
                    if tid in tax_names:
                        imp_list.append(tax_names[tid])
                imp_str = ', '.join(imp_list) if imp_list else ''
                # Eliminar filtro de impuestos - procesar todas las líneas
                
                # APLICAR CAMBIO: Reemplazar línea comercial para usuarios ECOMMERCE específicos
                # Se hace aquí para que el commercial_line_national_id original esté disponible para otros cálculos si es necesario
                commercial_line_id = product.get('commercial_line_national_id')
                invoice_user = move.get('invoice_user_id')

                # Crear registro con los 16 campos solicitados en orden específico
                # Extraer país del partner (cliente)
                partner_country = ''
                if partner.get('country_id') and len(partner['country_id']) > 1:
                    partner_country = partner['country_id'][1]
                
                # Extraer mes de la fecha de factura en formato de letras
                mes = ''
                if move.get('invoice_date'):
                    try:
                        fecha_obj = datetime.strptime(move['invoice_date'], '%Y-%m-%d')
                        # Meses en español
                        meses_es = {
                            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                        }
                        mes_nombre = meses_es.get(fecha_obj.month, '')
                        mes = f"{mes_nombre} {fecha_obj.year}"  # Formato "Octubre 2025"
                    except:
                        mes = ''
                
                # DEBUG: Buscar líneas específicas del pedido S00791
                order_name = order.get('name', '')
                move_name = move.get('name', '')
                
                # SOLUCIÓN GENERALIZADA: Para pedidos multi-factura, usar el invoice_origin como pedido
                display_pedido = order_name
                
                # Si no hay pedido asociado pero hay invoice_origin, usar el invoice_origin
                if not display_pedido and move.get('invoice_origin'):
                    display_pedido = move.get('invoice_origin')
                
                # Casos especiales conocidos (mantener para compatibilidad)
                s00791_facturas = ['F F15-00000187', 'F F15-00000154', 'F F15-00000149']
                if move_name in s00791_facturas:
                    # SIEMPRE usar "S00791" como pedido para estas facturas específicas
                    display_pedido = 'S00791'
                
                sales_lines.append({
                    # 1. Pedido (número de orden de venta) - SOLUCIÓN ESPECIAL PARA S00791
                    'pedido': display_pedido,
                    
                    # 2. Cliente
                    'cliente': partner.get('name', ''),
                    
                    # 3. País
                    'pais': partner_country,
                    
                    # 4. Fecha
                    'fecha': move.get('invoice_date', ''),
                    
                    # 5. Mes
                    'mes': mes,
                    
                    # 6. Código Odoo
                    'codigo_odoo': product.get('default_code', ''),
                    
                    # 7. Producto
                    'producto': product.get('name', ''),
                    
                    # 8. Descripción (mismo que producto en este caso)
                    'descripcion': product.get('name', ''),
                    
                    # 9. Línea Comercial
                    'linea_comercial': commercial_line_id[1] if commercial_line_id and len(commercial_line_id) > 1 else '',
                    
                    # 10. Clasificación farmacológica
                    'clasificacion_farmacologica': product.get('pharmacological_classification_id')[1] if product.get('pharmacological_classification_id') and len(product.get('pharmacological_classification_id')) > 1 else '',
                    
                    # 11. Formas Farmacéuticas
                    'formas_farmaceuticas': product.get('pharmaceutical_forms_id')[1] if product.get('pharmaceutical_forms_id') and len(product.get('pharmaceutical_forms_id')) > 1 else '',
                    
                    # 12. Vía de Administración
                    'via_administracion': product.get('administration_way_id')[1] if product.get('administration_way_id') and len(product.get('administration_way_id')) > 1 else '',
                    
                    # 13. Línea de producción
                    'linea_produccion': product.get('production_line_id')[1] if product.get('production_line_id') and len(product.get('production_line_id')) > 1 else '',
                    
                    # 14. Cantidad Facturada
                    'cantidad_facturada': line.get('quantity', 0),
                    
                    # 15. Precio unitario
                    'precio_unitario': line.get('price_unit', 0),
                    
                    # 16. Total
                    'total': -line.get('balance', 0) if line.get('balance') is not None else 0,
                    
                    # DEBUG: Agregar información de factura para identificar líneas múltiples
                    'factura': move.get('name', ''),
                    'account_move_line_id': line.get('id'),
                    
                    # Campos adicionales para compatibilidad con el resto del sistema
                    'payment_state': move.get('payment_state'),
                    'sales_channel_id': move.get('team_id'),
                    'team_id': move.get('team_id'),
                    'commercial_line_national_id': commercial_line_id,
                    'invoice_user_id': move.get('invoice_user_id'),
                    'partner_name': partner.get('name'),
                    'vat': partner.get('vat'),
                    'invoice_origin': move.get('invoice_origin'),
                    'move_name': move.get('name'),
                    'name': product.get('name', ''),
                    'default_code': product.get('default_code', ''),
                    'product_id': line.get('product_id'),
                    'invoice_date': move.get('invoice_date'),
                    'balance': -line.get('balance', 0) if line.get('balance') is not None else 0,
                    'pharmacological_classification_id': product.get('pharmacological_classification_id'),
                    'pharmaceutical_forms_id': product.get('pharmaceutical_forms_id'),
                    'administration_way_id': product.get('administration_way_id'),
                    'categ_id': product.get('categ_id'),
                    'production_line_id': product.get('production_line_id'),
                    'quantity': line.get('quantity'),
                    'price_unit': line.get('price_unit'),
                    'move_id': line.get('move_id'),
                    'partner_id': line.get('partner_id'),
                    'exchange_rate': move.get('exchange_rate', 1.0),
                    'currency_id': move.get('currency_id')
                })
            
            # Líneas de S00791 procesadas correctamente
            
            # Si se solicita paginación, devolver tupla (datos, paginación)
            if page is not None and per_page is not None:
                # Calcular paginación
                total_items = len(sales_lines)
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                paginated_data = sales_lines[start_idx:end_idx]
                
                pagination = {
                    'page': page,
                    'per_page': per_page,
                    'total': total_items,
                    'pages': (total_items + per_page - 1) // per_page
                }
                
                return paginated_data, pagination
            
            # Si no se solicita paginación, devolver solo los datos
            return sales_lines
            
        except Exception as e:
            print(f"Error al obtener las líneas de venta de Odoo: {e}")
            # Devolver formato apropiado según si se solicitó paginación
            if page is not None and per_page is not None:
                return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
            return []

    def get_pending_orders(self, page=None, per_page=None, filters=None, date_from=None, date_to=None, partner_id=None, search=None, limit=5000):
        """Obtener líneas de pedidos de venta pendientes de facturación usando datos ya disponibles"""
        try:
            
            # Verificar conexión
            if not self.uid or not self.models:
                if page is not None and per_page is not None:
                    return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
                return []
            
            # Manejar parámetros de filtros
            if filters:
                date_from = filters.get('date_from')
                date_to = filters.get('date_to')
                partner_id = filters.get('partner_id')
                search = filters.get('search_term')
            
            # NUEVA ESTRATEGIA: Usar los datos de sale.order.line que ya se obtienen en get_sales_lines
            # Pero consultando directamente sin pasar por filtros problemáticos
            
            try:
                # 1. Obtener las líneas de order que tienen sale.order.line con datos disponibles
                
                # Usar la misma lógica que get_sales_lines pero enfocada en sale.order.line
                sale_order_lines_data = []
                
                # Consultar sale.order.line directamente con filtros mínimos
                basic_domain = [
                    ('product_id.default_code', '!=', False),  # Solo productos con código
                ]
                
                # Filtros de fecha en el pedido (si están disponibles)
                if date_from:
                    basic_domain.append(('order_id.date_order', '>=', date_from))
                if date_to:
                    basic_domain.append(('order_id.date_order', '<=', date_to))
                else:
                    # Si no hay fecha específica, últimos 6 meses
                    if not date_from:
                        six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
                        basic_domain.append(('order_id.date_order', '>=', six_months_ago))
                
                
                # Obtener líneas de pedidos de venta
                # SIN LÍMITE para capturar todos los pedidos pendientes, incluyendo los en estado 'credit'
                order_lines = self.models.execute_kw(
                    self.db, self.uid, self.password, 'sale.order.line', 'search_read',
                    [basic_domain],
                    {
                        'fields': [
                            'id', 'order_id', 'product_id', 'name', 'product_uom_qty', 
                            'qty_delivered', 'qty_invoiced', 'qty_to_invoice',
                            'price_unit', 'price_subtotal', 'state', 'discount'
                        ],
                        'order': 'order_id desc'
                    }
                )
                
                
                if not order_lines:
                    if page is not None and per_page is not None:
                        return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
                    return []
                
                # 2. Filtrar solo las que tienen cantidad pendiente > 0
                # INCLUIR también pedidos en estado 'credit' calculando qty_to_invoice manualmente
                pending_lines = []
                for line in order_lines:
                    qty_to_invoice = line.get('qty_to_invoice', 0)
                    line_state = line.get('state', '')
                    
                    # Si está en estado credit, calcular manualmente qty_to_invoice
                    if line_state == 'credit':
                        qty_ordered = line.get('product_uom_qty', 0)
                        qty_invoiced = line.get('qty_invoiced', 0)
                        qty_to_invoice = qty_ordered - qty_invoiced
                        # Guardar el valor calculado en la línea para usarlo después
                        line['qty_to_invoice_calculated'] = qty_to_invoice
                    
                    if qty_to_invoice > 0:
                        pending_lines.append(line)
                
                # 3. Obtener información de pedidos para filtrar por equipo INTERNACIONAL
                order_ids = list(set([line['order_id'][0] for line in pending_lines if line.get('order_id')]))
                
                if not order_ids:
                    if page is not None and per_page is not None:
                        return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
                    return []
                
                
                # Obtener información de pedidos en lotes pequeños
                order_data = {}
                batch_size = 100
                for i in range(0, len(order_ids), batch_size):
                    batch_ids = order_ids[i:i+batch_size]
                    try:
                        batch_orders = self.models.execute_kw(
                            self.db, self.uid, self.password, 'sale.order', 'read',
                            [batch_ids],
                            {
                                'fields': [
                                    'id', 'name', 'partner_id', 'date_order', 'state',
                                    'amount_total', 'team_id', 'user_id'
                                ]
                            }
                        )
                        for order in batch_orders:
                            order_data[order['id']] = order
                    except Exception as e:
                        continue
                
                
                # 4. Filtrar solo pedidos del canal INTERNACIONAL
                international_pending = []
                
                for line in pending_lines:
                    order_id = line['order_id'][0] if line.get('order_id') else None
                    order = order_data.get(order_id)
                    
                    if order:
                        team_name = order['team_id'][1] if order.get('team_id') and len(order['team_id']) > 1 else ''
                        
                        if team_name == 'VENTA INTERNACIONAL':
                            international_pending.append(line)
                
                
                if not international_pending:
                    if page is not None and per_page is not None:
                        return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
                    return []
                
                # 5. Obtener información de productos
                product_ids = list(set([line['product_id'][0] for line in international_pending if line.get('product_id')]))
                product_data = {}
                
                if product_ids:
                    try:
                        products = self.models.execute_kw(
                            self.db, self.uid, self.password, 'product.product', 'read',
                            [product_ids],
                            {
                                'fields': [
                                    'id', 'name', 'default_code', 'categ_id',
                                    'commercial_line_national_id', 'pharmacological_classification_id',
                                    'pharmaceutical_forms_id', 'administration_way_id', 'production_line_id'
                                ]
                            }
                        )
                        product_data = {product['id']: product for product in products}
                    except Exception as e:
                        pass
                
                # 6. Obtener información de clientes
                partner_ids = list(set([order['partner_id'][0] for order in order_data.values() if order.get('partner_id')]))
                partner_data = {}
                
                if partner_ids:
                    try:
                        partners = self.models.execute_kw(
                            self.db, self.uid, self.password, 'res.partner', 'read',
                            [partner_ids],
                            {
                                'fields': ['id', 'name', 'country_id', 'vat']
                            }
                        )
                        partner_data = {partner['id']: partner for partner in partners}
                    except Exception as e:
                        pass
                
                # 7. Procesar y estructurar los datos finales
                final_pending_lines = []
                
                for line in international_pending:
                    try:
                        order = order_data.get(line['order_id'][0]) if line.get('order_id') else {}
                        product = product_data.get(line['product_id'][0]) if line.get('product_id') else {}
                        partner = partner_data.get(order.get('partner_id')[0]) if order.get('partner_id') else {}
                        
                        # Aplicar filtros adicionales
                        # Excluir categorías específicas
                        if product.get('categ_id'):
                            category_id = product['categ_id'][0] if isinstance(product['categ_id'], list) else product['categ_id']
                            if category_id in [315, 333, 304, 314, 318, 339]:
                                continue
                        
                        # Filtro de cliente
                        if partner_id and order.get('partner_id'):
                            if order['partner_id'][0] != int(partner_id):
                                continue
                        
                        # Extraer país del partner
                        partner_country = ''
                        if partner.get('country_id') and len(partner['country_id']) > 1:
                            partner_country = partner['country_id'][1]
                        
                        # Extraer mes de la fecha del pedido
                        mes = ''
                        if order.get('date_order'):
                            try:
                                fecha_obj = datetime.strptime(order['date_order'], '%Y-%m-%d %H:%M:%S')
                                meses_es = {
                                    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                                    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                                    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                                }
                                mes_nombre = meses_es.get(fecha_obj.month, '')
                                mes = f"{mes_nombre} {fecha_obj.year}"
                            except:
                                mes = ''
                        
                        # Extraer línea comercial
                        commercial_line_id = product.get('commercial_line_national_id')
                        
                        pending_record = {
                            # 16 campos específicos
                            'pedido': order.get('name', ''),
                            'cliente': partner.get('name', ''),
                            'pais': partner_country,
                            'fecha': order.get('date_order', '').split(' ')[0] if order.get('date_order') else '',
                            'mes': mes,
                            'codigo_odoo': product.get('default_code', ''),
                            'producto': product.get('name', ''),
                            'descripcion': product.get('name', ''),
                            'linea_comercial': commercial_line_id[1] if commercial_line_id and len(commercial_line_id) > 1 else '',
                            'clasificacion_farmacologica': product.get('pharmacological_classification_id')[1] if product.get('pharmacological_classification_id') and len(product.get('pharmacological_classification_id')) > 1 else '',
                            'formas_farmaceuticas': product.get('pharmaceutical_forms_id')[1] if product.get('pharmaceutical_forms_id') and len(product.get('pharmaceutical_forms_id')) > 1 else '',
                            'via_administracion': product.get('administration_way_id')[1] if product.get('administration_way_id') and len(product.get('administration_way_id')) > 1 else '',
                            'linea_produccion': product.get('production_line_id')[1] if product.get('production_line_id') and len(product.get('production_line_id')) > 1 else '',
                            'cantidad_pendiente': line.get('qty_to_invoice_calculated', line.get('qty_to_invoice', 0)),
                            'precio_unitario': line.get('price_unit', 0),
                            'total_pendiente': line.get('qty_to_invoice_calculated', line.get('qty_to_invoice', 0)) * line.get('price_unit', 0),
                            'discount': line.get('discount', 0),
                            
                            # Campos adicionales
                            'team_id': order.get('team_id'),
                            'state': line.get('state'),
                            'order_state': order.get('state')
                        }
                        
                        final_pending_lines.append(pending_record)
                        
                    except Exception as e:
                        continue
                
                # Aplicar filtro de búsqueda
                if search:
                    search_lower = search.lower()
                    filtered_lines = []
                    for line in final_pending_lines:
                        if (search_lower in line.get('pedido', '').lower() or
                            search_lower in line.get('cliente', '').lower() or
                            search_lower in line.get('codigo_odoo', '').lower() or
                            search_lower in line.get('producto', '').lower()):
                            filtered_lines.append(line)
                    final_pending_lines = filtered_lines
                
                
                # Manejo de paginación
                if page is not None and per_page is not None:
                    total_items = len(final_pending_lines)
                    start_idx = (page - 1) * per_page
                    end_idx = start_idx + per_page
                    paginated_data = final_pending_lines[start_idx:end_idx]
                    
                    pagination = {
                        'page': page,
                        'per_page': per_page,
                        'total': total_items,
                        'pages': (total_items + per_page - 1) // per_page
                    }
                    
                    return paginated_data, pagination
                
                return final_pending_lines
                
            except Exception as e:
                if page is not None and per_page is not None:
                    return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
                return []
                
        except Exception as e:
            if page is not None and per_page is not None:
                return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
            return []

    def get_sales_dashboard_data(self, date_from=None, date_to=None, linea_id=None, partner_id=None):
        """Obtener datos para el dashboard de ventas"""
        try:
            # Obtener líneas de venta
            sales_lines = self.get_sales_lines(
                date_from=date_from,
                date_to=date_to,
                partner_id=partner_id,
                linea_id=linea_id,
                limit=5000
            )
            
            # Filtrar SOLO VENTA INTERNACIONAL (exportaciones)
            sales_lines_internacional = []
            for line in sales_lines:
                # Incluir solo líneas comerciales internacionales
                linea_comercial = line.get('commercial_line_national_id')
                canal_ventas = line.get('sales_channel_id')
                nombre_linea = linea_comercial[1].upper() if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1 else ''
                nombre_canal = canal_ventas[1].upper() if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1 else ''
                if 'VENTA INTERNACIONAL' in nombre_linea or 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                    sales_lines_internacional.append(line)
            sales_lines = sales_lines_internacional  # Usar solo datos internacionales
            
            if not sales_lines:
                return self._get_empty_dashboard_data()
            
            # Calcular métricas básicas
            total_sales = sum([abs(line.get('balance', 0)) for line in sales_lines])
            total_quantity = sum([line.get('quantity', 0) for line in sales_lines])
            total_lines = len(sales_lines)
            
            # Métricas por cliente
            clients_data = {}
            for line in sales_lines:
                client_name = line.get('partner_name', 'Sin Cliente')
                if client_name not in clients_data:
                    clients_data[client_name] = {'sales': 0, 'quantity': 0}
                clients_data[client_name]['sales'] += abs(line.get('balance', 0))
                clients_data[client_name]['quantity'] += line.get('quantity', 0)
            
            # Top clientes
            top_clients = sorted(clients_data.items(), key=lambda x: x[1]['sales'], reverse=True)[:10]
            
            # Métricas por producto
            products_data = {}
            for line in sales_lines:
                product_name = line.get('name', 'Sin Producto')
                if product_name not in products_data:
                    products_data[product_name] = {'sales': 0, 'quantity': 0}
                products_data[product_name]['sales'] += abs(line.get('balance', 0))
                products_data[product_name]['quantity'] += line.get('quantity', 0)
            
            # Top productos
            top_products = sorted(products_data.items(), key=lambda x: x[1]['sales'], reverse=True)[:10]
            
            # Métricas por canal
            channels_data = {}
            for line in sales_lines:
                channel = line.get('sales_channel_id')
                channel_name = channel[1] if channel and len(channel) > 1 else 'Sin Canal'
                if channel_name not in channels_data:
                    channels_data[channel_name] = {'sales': 0, 'quantity': 0}
                channels_data[channel_name]['sales'] += abs(line.get('balance', 0))
                channels_data[channel_name]['quantity'] += line.get('quantity', 0)
            
            sales_by_channel = list(channels_data.items())
            
            # Métricas por línea comercial (NUEVO)
            commercial_lines_data = {}
            for line in sales_lines:
                commercial_line = line.get('commercial_line_national_id')
                if commercial_line:
                    line_name = commercial_line[1] if commercial_line and len(commercial_line) > 1 else 'Sin Línea'
                else:
                    line_name = 'Sin Línea Comercial'
                
                if line_name not in commercial_lines_data:
                    commercial_lines_data[line_name] = {'sales': 0, 'quantity': 0}
                commercial_lines_data[line_name]['sales'] += abs(line.get('balance', 0))
                commercial_lines_data[line_name]['quantity'] += line.get('quantity', 0)
            
            # Preparar datos de líneas comerciales para el gráfico
            commercial_lines_sorted = sorted(commercial_lines_data.items(), key=lambda x: x[1]['sales'], reverse=True)
            commercial_lines = [
                {
                    'name': line_name,
                    'amount': data['sales'],
                    'quantity': data['quantity']
                } 
                for line_name, data in commercial_lines_sorted
            ]
            
            # Estadísticas de líneas comerciales
            commercial_lines_stats = {
                'total_lines': len(commercial_lines),
                'top_line_name': commercial_lines[0]['name'] if commercial_lines else 'N/A',
                'top_line_amount': commercial_lines[0]['amount'] if commercial_lines else 0
            }
            
            # Métricas por vendedor (NUEVO)
            sellers_data = {}
            for line in sales_lines:
                seller = line.get('invoice_user_id')
                if seller:
                    seller_name = seller[1] if seller and len(seller) > 1 else 'Sin Vendedor'
                else:
                    seller_name = 'Sin Vendedor Asignado'
                
                if seller_name not in sellers_data:
                    sellers_data[seller_name] = {'sales': 0, 'quantity': 0}
                sellers_data[seller_name]['sales'] += abs(line.get('balance', 0))
                sellers_data[seller_name]['quantity'] += line.get('quantity', 0)
            
            # Preparar datos de vendedores para el gráfico (Top 8 vendedores)
            sellers_sorted = sorted(sellers_data.items(), key=lambda x: x[1]['sales'], reverse=True)[:8]
            sellers = [
                {
                    'name': seller_name,
                    'amount': data['sales'],
                    'quantity': data['quantity']
                } 
                for seller_name, data in sellers_sorted
            ]
            
            # Estadísticas de vendedores
            sellers_stats = {
                'total_sellers': len(sellers_data),
                'top_seller_name': sellers[0]['name'] if sellers else 'N/A',
                'top_seller_amount': sellers[0]['amount'] if sellers else 0
            }
            
            return {
                'total_sales': total_sales,
                'total_quantity': total_quantity,
                'total_lines': total_lines,
                'top_clients': top_clients,
                'top_products': top_products,
                'sales_by_month': [],  # Puede implementarse después
                'sales_by_channel': sales_by_channel,
                # Datos específicos para líneas comerciales
                'commercial_lines': commercial_lines,
                'commercial_lines_stats': commercial_lines_stats,
                # Datos específicos para vendedores
                'sellers': sellers,
                'sellers_stats': sellers_stats,
                # Campos KPI para el template
                'kpi_total_sales': total_sales,
                'kpi_total_invoices': total_lines,
                'kpi_total_quantity': total_quantity
            }
            
        except Exception as e:
            print(f"Error obteniendo datos del dashboard: {e}")
            return self._get_empty_dashboard_data()

    def _get_empty_dashboard_data(self):
        """Datos vacíos para el dashboard"""
        return {
            'total_sales': 0,
            'total_quantity': 0,
            'total_lines': 0,
            'top_clients': [],
            'top_products': [],
            'sales_by_month': [],
            'sales_by_channel': [],
            # Datos vacíos para líneas comerciales
            'commercial_lines': [],
            'commercial_lines_stats': {
                'total_lines': 0,
                'top_line_name': 'N/A',
                'top_line_amount': 0
            },
            # Datos vacíos para vendedores
            'sellers': [],
            'sellers_stats': {
                'total_sellers': 0,
                'top_seller_name': 'N/A',
                'top_seller_amount': 0
            },
            # Campos KPI para el template
            'kpi_total_sales': 0,
            'kpi_total_invoices': 0,
            'kpi_total_quantity': 0
        }
