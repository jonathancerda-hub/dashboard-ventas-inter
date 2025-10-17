# odoo_manager.py - Versión Completa Restaurada

import xmlrpc.client
import http.client
import socket
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class OdooManager:
    def get_commercial_lines_stacked_data(self, date_from=None, date_to=None, linea_id=None, partner_id=None):
        """Devuelve datos para gráfico apilado por línea comercial y 5 categorías"""
        # CORRECCIÓN: get_sales_lines devuelve una tupla (datos, paginación). Solo necesitamos los datos.
        sales_lines, _ = self.get_sales_lines(
            date_from=date_from,
            date_to=date_to,
            partner_id=partner_id,
            linea_id=linea_id
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
            cl = line.get('commercial_line_international_id') # CAMBIO: Usar la línea internacional
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
            logging.error(f"Error en la conexión a Odoo: {e}")
            logging.info("Continuando en modo offline.")
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

            # Obtener clientes directamente de las líneas de factura que ya estamos usando en el dashboard
            # para asegurar consistencia.
            client_fetch_domain = [
                ('move_id.journal_id.name', '=', 'F150 (Venta exterior)'), # Diario de Venta Exterior por nombre
                ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
                ('move_id.state', '=', 'posted'),
                ('account_id.code', 'like', '70%'), # La cuenta DEBE empezar con 70
                # Filtros de producto para consistencia
                ('product_id', '!=', False),
                ('product_id.default_code', 'not ilike', '%SERV%'),
                ('product_id.default_code', 'not like', '81%'),
            ]
            
            # Usar read_group para obtener partner_id únicos de forma eficiente
            partner_groups = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move.line', 'read_group',
                [client_fetch_domain],
                {
                    'fields': ['partner_id'],
                    'groupby': ['partner_id'],
                    'lazy': False
                }
            )

            for group in partner_groups:
                if group.get('partner_id'):
                    all_partner_ids.add(group['partner_id'][0])

            partner_ids = list(all_partner_ids)
            
            if not partner_ids:
                logging.debug("No se encontraron clientes del canal internacional en pedidos o facturas.")
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
            
            logging.debug(f"Encontrados {len(clientes_internacionales)} clientes internacionales únicos.")
            return clientes_internacionales
            
        except Exception as e:
            logging.error(f"Error al obtener clientes internacionales: {e}")
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
                logging.error(f"Error obteniendo líneas de productos: {product_error}")

            # Obtener clientes internacionales específicos
            clientes_internacionales = self.get_international_clients()
            
            return {
                'lineas': lineas,  # Para compatibilidad con meta.html
                'clientes': clientes_internacionales  # Lista de [id, nombre] para el template
            }
            
        except Exception as e:
            logging.error(f"Error al obtener opciones de filtro de ventas: {e}")
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
            logging.error(f"Error obteniendo la lista de vendedores: {e}")
            return []

    def get_sales_lines(self, page=1, per_page=1000, filters=None, date_from=None, date_to=None, partner_id=None, linea_id=None, search=None, limit=None):
        """Obtener líneas de venta completas con todas las 27 columnas"""
        try:
            # Verificar conexión
            if not self.uid or not self.models:
                if page is not None and per_page is not None:
                    return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
                return []
            
            # Obtener lista de facturas internacionales si no hay partner_id específico
            # Este filtro ahora se aplica directamente en el dominio principal
            # para que siempre se filtren las ventas internacionales.
            domain = [
                ('move_id.journal_id.name', '=', 'F150 (Venta exterior)'), # Diario de Venta Exterior por nombre
                ('move_id.state', '=', 'posted'),
                ('account_id.code', '=like', '70%'), # La cuenta DEBE empezar con '70'.
                ('tax_ids.name', 'ilike', 'EXE_IGV_EXP'), # Filtro por impuesto EXE_IGV_EXP
                # Filtros para excluir productos no deseados
                ('product_id', '!=', False),
                ('product_id.default_code', 'not ilike', '%SERV%'), # Excluir servicios
                ('product_id.default_code', 'not like', '81%')      # Excluir códigos que empiezan con 81
            ]
            
            # Manejar parámetros de ambos formatos de llamada
            if filters:
                date_from = filters.get('date_from')
                date_to = filters.get('date_to')
                partner_id = filters.get('partner_id')
                linea_id = filters.get('linea_id')
                search = filters.get('search')
            
            # Detectar tipo de búsqueda ANTES de construir el dominio
            if search:
                # Búsqueda flexible en varios campos
                domain += [
                    '|', '|', '|', '|',
                    ('move_id.name', 'ilike', search), # Factura
                    ('move_id.invoice_origin', 'ilike', search), # Origen (a menudo el pedido)
                    ('product_id.name', 'ilike', search), # Nombre de producto
                    ('product_id.default_code', 'ilike', search), # Código de producto
                    ('move_id.partner_id.name', 'ilike', search) # Cliente
                ]
            
            # Aplicar filtros de fecha si se proporcionan
            if date_from:
                domain.append(('move_id.invoice_date', '>=', date_from))
            if date_to:
                domain.append(('move_id.invoice_date', '<=', date_to))
            
            # Filtro de cliente
            if partner_id:
                domain.append(('move_id.partner_id', '=', int(partner_id)))
            
            # Filtro de línea comercial
            if linea_id:
                domain.append(('product_id.commercial_line_international_id', '=', linea_id))

            # Contar el total de registros que coinciden con el dominio (para paginación)
            total_count = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move.line', 'search_count',
                [domain]
            )

            # Obtener líneas base con todos los campos necesarios
            query_options = {
                'fields': [
                    'move_id', 'partner_id', 'product_id', 'balance', 'move_name',
                    'quantity', 'price_unit', 'tax_ids', 'amount_currency', 'display_name'
                ],
                'context': {'lang': 'es_PE'}
            }
            
            # Aplicar paginación
            query_options['limit'] = per_page
            query_options['offset'] = (page - 1) * per_page

            sales_lines_base = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move.line', 'search_read',
                [domain],
                query_options
            )
            if not sales_lines_base:
                return []

            # Si no hay líneas, devolver estructura de paginación vacía
            if not sales_lines_base:
                return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}


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
                            'display_name', # <-- CAMBIO: Añadir display_name
                            'commercial_line_international_id', # <-- CAMBIO: Añadir este campo
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
                
                # Con el filtro EXE_IGV_EXP todas las líneas deben tener product_id válido
                if not product_id:
                    logging.warning(f"Línea sin producto encontrada en Odoo: {line}")
                    continue
                
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
                    
                    # 8. Descripción (usando el nombre del producto, igual que el campo 'producto')
                    'descripcion': product.get('display_name', ''),
                    
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
                    'commercial_line_international_id': product.get('commercial_line_international_id'), # <-- CAMBIO: Añadir este campo
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
                    'currency_id': move.get('currency_id'),
                    # Invertir el signo para que las ventas sean positivas y las devoluciones negativas.
                    'amount_currency': -line.get('amount_currency', 0),
                })
            
            # Líneas de S00791 procesadas correctamente
            
            # Devolver tupla (datos, paginación)
            pagination_info = {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            }
            
            # Si se solicita paginación, devolver tupla
            if page is not None and per_page is not None:
                return sales_lines, pagination_info
            else:
                # Si no, devolver solo los datos (comportamiento anterior)
                return sales_lines

            
        except Exception as e:
            logging.error(f"Error al obtener las líneas de venta de Odoo: {e}")
            # Devolver formato apropiado según si se solicitó paginación
            if page is not None and per_page is not None:
                return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
            return []

    def get_pending_orders(self, page=1, per_page=1000, filters=None, date_from=None, date_to=None, partner_id=None, search=None, limit=None):
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
                search = filters.get('search_term') # CORRECCIÓN: Usar el search_term del filtro
            
            # NUEVA ESTRATEGIA: Usar los datos de sale.order.line que ya se obtienen en get_sales_lines
            # Pero consultando directamente sin pasar por filtros problemáticos
            
            try:
                # 1. Obtener las líneas de order que tienen sale.order.line con datos disponibles
                # Usar la misma lógica que get_sales_lines pero enfocada en sale.order.line
                sale_order_lines_data = []

                # Dominio para filtrar por canal INTERNACIONAL y estados relevantes
                domain_international_orders = [
                    ('order_id.team_id.name', 'ilike', 'INTERNACIONAL'),
                    ('order_id.state', 'in', ['credit', 'sale', 'done'])
                ]
                
                # Consultar sale.order.line directamente con filtros mínimos
                basic_domain = [
                    ('product_id', '!=', False), # Asegura que haya un producto, pero permite default_code vacío.
                ]
                
                # Filtros de fecha en el pedido (si están disponibles)
                if date_from:
                    basic_domain.append(('order_id.date_order', '>=', date_from))
                if date_to:
                    basic_domain.append(('order_id.date_order', '<=', date_to))
                
                # Incluir filtro de cliente si se proporciona
                if partner_id:
                    basic_domain.append(('order_id.partner_id', '=', int(partner_id)))

                # Incluir filtro de búsqueda si se proporciona
                if search:
                    # CORRECCIÓN: El dominio de búsqueda debe estar bien anidado para Odoo (n-1 '|' para n condiciones)
                    basic_domain += [
                        '|', '|', '|',
                        ('order_id.partner_id.name', 'ilike', search),
                        ('product_id.default_code', 'ilike', search),
                        ('product_id.name', 'ilike', search),
                        ('order_id.name', 'ilike', search)
                    ]

                # Combinar dominios
                final_domain = basic_domain + domain_international_orders

                # Contar el total para la paginación
                total_count = self.models.execute_kw(
                    self.db, self.uid, self.password, 'sale.order.line', 'search_count',
                    [final_domain]
                )

                # Obtener líneas de pedidos de venta
                order_lines = self.models.execute_kw(
                    self.db, self.uid, self.password, 'sale.order.line', 'search_read',
                    [final_domain],
                    {
                        'fields': [
                            'id', 'order_id', 'product_id', 'name', 'product_uom_qty',
                            'qty_delivered', 'qty_invoiced', 'qty_to_invoice',
                            'price_unit', 'price_subtotal', 'state', 'discount'
                        ],
                        'order': 'order_id desc'
                        ,
                        'limit': per_page,
                        'offset': (page - 1) * per_page
                    }
                )
                
                logging.debug(f"{len(order_lines)} líneas de pedido obtenidas inicialmente.")
                
                if not order_lines:
                    if page is not None and per_page is not None:
                        return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
                    return []
                
                # 2. Filtrar solo las que tienen cantidad pendiente > 0
                # INCLUIR también pedidos en estado 'credit' calculando qty_to_invoice manualmente
                all_pending_lines = []
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
                        all_pending_lines.append(line)
                
                logging.debug(f"{len(all_pending_lines)} líneas con cantidad pendiente de facturar.")

                # 3. Obtener información de pedidos para filtrar por equipo INTERNACIONAL
                order_ids = list(set([line['order_id'][0] for line in all_pending_lines if line.get('order_id')]))
                
                # Obtener información de pedidos en lotes pequeños
                order_data = {}
                batch_size = 100
                for i in range(0, len(order_ids), batch_size):
                    batch_ids = order_ids[i:i+batch_size]
                    try:
                        batch_orders = self.models.execute_kw(self.db, self.uid, self.password, 'sale.order', 'read', [batch_ids], {'fields': ['id', 'name', 'partner_id', 'date_order', 'state', 'amount_total', 'team_id', 'user_id']})
                        for order in batch_orders:
                            order_data[order['id']] = order
                    except Exception as e:
                        continue
                
                
                # 4. Filtrar solo pedidos del canal INTERNACIONAL
                international_pending = all_pending_lines
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
                                    'id', 'name', 'display_name', 'default_code', 'categ_id', # <-- CAMBIO: Añadir display_name
                                    'commercial_line_national_id', 'commercial_line_international_id',
                                    'pharmacological_classification_id',
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
                        
                        # CAMBIO: Se ha eliminado el filtro que excluía productos por su categoría.
                        # Ahora todos los productos del canal internacional aparecerán.
                        
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
                        
                        # CAMBIO: Usar la línea comercial internacional en lugar de la nacional.
                        commercial_line_id = product.get('commercial_line_international_id')
                        
                        pending_record = {
                            # 16 campos específicos
                            'pedido': order.get('name', ''),
                            'cliente': partner.get('name', ''),
                            'partner_id': order.get('partner_id'),
                            'cliente_id': order.get('partner_id')[0] if order.get('partner_id') and isinstance(order.get('partner_id'), (list, tuple)) else None,
                            'pais': partner_country,
                            'fecha': order.get('date_order', '').split(' ')[0] if order.get('date_order') else '',
                            'mes': mes,
                            'codigo_odoo': product.get('default_code', ''),
                            'producto': product.get('name', ''),
                            'descripcion': product.get('display_name', ''),
                            'linea_comercial': commercial_line_id[1] if commercial_line_id and len(commercial_line_id) > 1 else '',
                            'clasificacion_farmacologica': product.get('pharmacological_classification_id')[1] if product.get('pharmacological_classification_id') and isinstance(product.get('pharmacological_classification_id'), list) and len(product.get('pharmacological_classification_id')) > 1 else '',
                            'formas_farmaceuticas': product.get('pharmaceutical_forms_id')[1] if product.get('pharmaceutical_forms_id') and isinstance(product.get('pharmaceutical_forms_id'), list) and len(product.get('pharmaceutical_forms_id')) > 1 else '',
                            'via_administracion': product.get('administration_way_id')[1] if product.get('administration_way_id') and isinstance(product.get('administration_way_id'), list) and len(product.get('administration_way_id')) > 1 else '',
                            'linea_produccion': product.get('production_line_id')[1] if product.get('production_line_id') and isinstance(product.get('production_line_id'), list) and len(product.get('production_line_id')) > 1 else '',
                            'cantidad_pendiente': line.get('qty_to_invoice_calculated', line.get('qty_to_invoice', 0)),
                            'precio_unitario': line.get('price_unit', 0),
                            'discount': line.get('discount', 0),
                            'total_pendiente': line.get('qty_to_invoice_calculated', line.get('qty_to_invoice', 0)) * line.get('price_unit', 0) * (1 - (line.get('discount', 0) / 100)),
                            
                            # Campos adicionales
                            'team_id': order.get('team_id'),
                            'commercial_line_international_id': product.get('commercial_line_international_id'),
                            'state': line.get('state'),
                            'order_state': order.get('state')
                        }
                        
                        final_pending_lines.append(pending_record)
                        
                    except Exception as e:
                        continue
                
                # Aplicar filtro de búsqueda
                # ESTA LÓGICA SE MOVIÓ AL DOMINIO DE LA CONSULTA PARA MAYOR EFICIENCIA
                # if search:
                #     search_lower = search.lower()
                #     filtered_lines = []
                #     for line in final_pending_lines:
                #         if (search_lower in line.get('pedido', '').lower() or
                #             search_lower in line.get('cliente', '').lower() or
                #             search_lower in line.get('codigo_odoo', '').lower() or
                #             search_lower in line.get('producto', '').lower()):
                #             filtered_lines.append(line)
                #     final_pending_lines = filtered_lines

                # La búsqueda ahora se aplica en el dominio principal, por lo que no es necesario
                # un segundo filtrado aquí.
                
                
                # Si se pidió un partner en los filtros, asegurarnos de incluir
                # todos los pedidos del cliente seleccionado aunque no tengan
                # líneas pendientes (total_pendiente = 0).
                if partner_id:
                    try:
                        # Buscar pedidos del cliente en el canal INTERNACIONAL y estados permitidos
                        domain_orders = [
                            ('partner_id', '=', int(partner_id)),
                            ('state', 'in', ['credit', 'sale', 'done']),
                        ]
                        # Intentar filtrar por equipo INTERNACIONAL si el campo existe
                        # Nota: usar search_read para evitar límites
                        partner_orders = self.models.execute_kw(
                            self.db, self.uid, self.password, 'sale.order', 'search_read',
                            [domain_orders],
                            {
                                'fields': ['id', 'name', 'partner_id', 'date_order', 'state', 'amount_total', 'team_id', 'user_id']
                            }
                        )
                    except Exception:
                        partner_orders = []

                    # Construir set de order ids que ya tenemos con pendientes
                    existing_order_ids = set(order_ids) if order_ids else set()

                    for order in partner_orders:
                        try:
                            oid = order.get('id')
                            # Si ya lo tenemos (porque tenía líneas pendientes), saltar
                            if oid in existing_order_ids:
                                continue

                            # Preparar registro con totales a 0 (no hay líneas pendientes)
                            cliente_name = ''
                            if order.get('partner_id') and isinstance(order.get('partner_id'), (list, tuple)) and len(order.get('partner_id')) > 1:
                                cliente_name = order.get('partner_id')[1]

                            fecha = order.get('date_order', '').split(' ')[0] if order.get('date_order') else ''
                            # Intentar obtener mes amigable
                            mes = ''
                            if order.get('date_order'):
                                try:
                                    fecha_obj = datetime.strptime(order['date_order'], '%Y-%m-%d %H:%M:%S')
                                    meses_es = {
                                        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                                        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                                        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                                    }
                                    mes = f"{meses_es.get(fecha_obj.month, '')} {fecha_obj.year}"
                                except Exception:
                                    mes = ''

                            pending_record = {
                                'pedido': order.get('name', ''),
                                'cliente': cliente_name,
                                'partner_id': order.get('partner_id'),
                                'cliente_id': order.get('partner_id')[0] if order.get('partner_id') and isinstance(order.get('partner_id'), (list, tuple)) else None,
                                'order_id': oid,
                                'pais': '',
                                'fecha': fecha,
                                'mes': mes,
                                'codigo_odoo': '',
                                'producto': '',
                                'descripcion': '',
                                'linea_comercial': '',
                                'clasificacion_farmacologica': '',
                                'formas_farmaceuticas': '',
                                'via_administracion': '',
                                'linea_produccion': '',
                                'cantidad_pendiente': 0,
                                'precio_unitario': 0,
                                'discount': 0,
                                'total_pendiente': 0,
                                'team_id': order.get('team_id'),
                                'commercial_line_international_id': None,
                                'state': '',
                                'order_state': order.get('state')
                            }
                            final_pending_lines.append(pending_record)
                        except Exception:
                            continue

                pagination_info = {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                }

                if page is not None and per_page is not None:
                    return final_pending_lines, pagination_info
                else:
                    return final_pending_lines
                
            except Exception as e:
                logging.error(f"Error procesando pedidos pendientes: {e}")
                return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}
                
        except Exception as e:
            logging.error(f"Error general en get_pending_orders: {e}")
            return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}

    def get_sales_dashboard_data(self, date_from=None, date_to=None, linea_id=None, partner_id=None):
        """Obtener datos para el dashboard de ventas"""
        if not self.uid or not self.models:
            return self._get_empty_dashboard_data()

        try:
            # Dominio base para todas las consultas del dashboard internacional
            domain = [
                ('move_id.journal_id.name', '=', 'F150 (Venta exterior)'),
                ('move_id.state', '=', 'posted'),
                ('account_id.code', '=like', '70%'),
                ('tax_ids.name', 'ilike', 'EXE_IGV_EXP'),
                ('product_id', '!=', False),
                ('product_id.default_code', 'not ilike', '%SERV%'),
                ('product_id.default_code', 'not like', '81%')
            ]
            if date_from:
                domain.append(('move_id.invoice_date', '>=', date_from))
            if date_to:
                domain.append(('move_id.invoice_date', '<=', date_to))
            if partner_id:
                domain.append(('move_id.partner_id', '=', int(partner_id)))
            if linea_id:
                domain.append(('product_id.commercial_line_international_id', '=', linea_id))

            # 1. Total de ventas usando read_group para eficiencia
            total_sales_group = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move.line', 'read_group',
                [domain],
                {'fields': ['amount_currency'], 'groupby': []}
            )
            total_sales = -total_sales_group[0]['amount_currency'] if total_sales_group and total_sales_group[0]['amount_currency'] else 0

            if total_sales == 0:
                return self._get_empty_dashboard_data()

            # 2. Top Clientes
            top_clients_data = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move.line', 'read_group',
                [domain],
                {
                    'fields': ['partner_id', 'amount_currency'],
                    'groupby': ['partner_id'],
                    'orderby': 'amount_currency asc', # asc porque los montos son negativos
                    'limit': 10
                }
            )
            top_clients = [(c['partner_id'][1], -c['amount_currency']) for c in top_clients_data if c.get('partner_id')]

            # 3. Top Productos
            top_products_data = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move.line', 'read_group',
                [domain],
                {
                    'fields': ['product_id', 'amount_currency'],
                    'groupby': ['product_id'],
                    'orderby': 'amount_currency asc',
                    'limit': 10
                }
            )
            top_products = [(p['product_id'][1], -p['amount_currency']) for p in top_products_data if p.get('product_id')]

            # 4. Ventas por Línea Comercial
            commercial_lines_data = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move.line', 'read_group',
                [domain],
                {
                    'fields': ['commercial_line_international_id', 'amount_currency', 'quantity'],
                    'groupby': ['commercial_line_international_id'],
                    'orderby': 'amount_currency asc'
                }
            )
            commercial_lines = []
            for line in commercial_lines_data:
                if line.get('commercial_line_international_id'):
                    commercial_lines.append({
                        'name': line['commercial_line_international_id'][1],
                        'amount': -line['amount_currency'],
                        'quantity': line['quantity']
                    })

            commercial_lines_stats = {
                'total_lines': len(commercial_lines),
                'top_line_name': commercial_lines[0]['name'] if commercial_lines else 'N/A',
                'top_line_amount': commercial_lines[0]['amount'] if commercial_lines else 0
            }

            # 5. Ventas por Vendedor
            sellers_data = self.models.execute_kw(
                self.db, self.uid, self.password, 'account.move.line', 'read_group',
                [domain],
                {
                    'fields': ['invoice_user_id', 'amount_currency', 'quantity'],
                    'groupby': ['invoice_user_id'],
                    'orderby': 'amount_currency asc'
                }
            )
            sellers = []
            for seller in sellers_data:
                if seller.get('invoice_user_id'):
                    sellers.append({
                        'name': seller['invoice_user_id'][1],
                        'amount': -seller['amount_currency'],
                        'quantity': seller['quantity']
                    })

            sellers_stats = {
                'total_sellers': len(sellers_data),
                'top_seller_name': sellers[0]['name'] if sellers else 'N/A',
                'top_seller_amount': sellers[0]['amount'] if sellers else 0
            }

            # Otras métricas que aún requieren get_sales_lines o son simples
            total_lines_count = self.models.execute_kw(self.db, self.uid, self.password, 'account.move.line', 'search_count', [domain])

            return {
                'total_sales': total_sales,
                'total_quantity': 0, # Este dato ya no es prioritario y requeriría otra consulta
                'total_lines': total_lines_count,
                'top_clients': top_clients,
                'top_products': top_products,
                'sales_by_month': [],  # Puede implementarse después
                'sales_by_channel': [], # Este dato ya no es prioritario
                # Datos específicos para líneas comerciales
                'commercial_lines': commercial_lines,
                'commercial_lines_stats': commercial_lines_stats,
                # Datos específicos para vendedores
                'sellers': sellers,
                'sellers_stats': sellers_stats,
                # Campos KPI para el template
                'kpi_total_sales': total_sales,
                'kpi_total_invoices': total_lines_count,
                'kpi_total_quantity': 0
            }
            
        except Exception as e:
            logging.error(f"Error obteniendo datos del dashboard: {e}")
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
