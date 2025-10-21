# app.py - Dashboard de Ventas Farmacéuticas

from flask_caching import Cache
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from dotenv import load_dotenv
from odoo_manager import OdooManager
from google_sheets_manager import GoogleSheetsManager
import os
import pandas as pd
import json
import io
import calendar
from datetime import datetime, timedelta
from openpyxl.worksheet.table import Table, TableStyleInfo
import logging

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# --- Configuración de Caché ---
cache_config = {
    "CACHE_TYPE": "SimpleCache",  # Almacenamiento en memoria simple
    "CACHE_DEFAULT_TIMEOUT": 600  # 10 minutos de caché por defecto
}
cache = Cache(config=cache_config)
cache.init_app(app)

# Configuración para deshabilitar cache de templates
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Logging configuration: keep server output concise unless an error occurs
logging.basicConfig(level=logging.INFO)
# Reduce verbosity of the Flask/Werkzeug request logger
logging.getLogger('werkzeug').setLevel(logging.WARNING)
app.logger.setLevel(logging.INFO)

# --- Registrar filtro Jinja personalizado ---
@app.template_filter('format_number')
def format_number_filter(value):
    """Formatea un número con comas como separadores de miles."""
    if value is None:
        return ''
    try:
        return "{:,.0f}".format(int(value))
    except (ValueError, TypeError):
        return value

# --- Inicialización de Managers ---
data_manager = OdooManager()
gs_manager = GoogleSheetsManager(
    credentials_file='credentials.json',
    sheet_name=os.getenv('GOOGLE_SHEET_NAME')
)

# --- Funciones Auxiliares ---

def create_mock_sales_data():
    """Crear datos de prueba simulados para testing"""
    mock_data = []
    
    # Datos internacionales simulados
    for i in range(15):
        mock_data.append({
            'pedido': f'SO00{i+1}',
            'cliente': f'Cliente Internacional {i+1}',
            'pais': 'Ecuador' if i % 3 == 0 else ('Colombia' if i % 3 == 1 else 'Chile'),
            'fecha': f'2025-10-{(i % 30) + 1:02d}',
            'mes': '2025-10',
            'codigo_odoo': f'INTL{i+1:03d}',
            'producto': f'Medicamento Internacional {i+1}',
            'descripcion': f'Descripción del medicamento internacional {i+1}',
            'linea_comercial': 'VENTA INTERNACIONAL',
            'clasificacion_farmacologica': 'Antibióticos' if i % 2 == 0 else 'Analgésicos',
            'formas_farmaceuticas': 'Tabletas' if i % 2 == 0 else 'Cápsulas',
            'via_administracion': 'Oral',
            'linea_produccion': f'Línea Internacional {(i % 3) + 1}',
            'cantidad_facturada': 100 + i * 10,
            'precio_unitario': 15.50 + i,
            'total': (100 + i * 10) * (15.50 + i),
            'sales_channel_id': [1, 'VENTA INTERNACIONAL'],
            'commercial_line_national_id': [1, 'VENTA INTERNACIONAL'],
            'partner_name': f'Cliente Internacional {i+1}',
            'name': f'Medicamento Internacional {i+1}',
            'default_code': f'INTL{i+1:03d}',
            'invoice_date': f'2025-10-{(i % 30) + 1:02d}',
            'balance': (100 + i * 10) * (15.50 + i),
            'pharmacological_classification_id': [i+1, 'Antibióticos' if i % 2 == 0 else 'Analgésicos'],
            'pharmaceutical_forms_id': [i+1, 'Tabletas' if i % 2 == 0 else 'Cápsulas'],
            'administration_way_id': [i+1, 'Oral'],
        })
    
    # Algunos datos locales para contrastar (NO deben aparecer en el filtro)
    for i in range(5):
        mock_data.append({
            'pedido': f'SL00{i+1}',
            'cliente': f'Cliente Local {i+1}',
            'pais': 'Perú',
            'fecha': f'2025-10-{(i % 30) + 1:02d}',
            'mes': '2025-10',
            'codigo_odoo': f'LOCAL{i+1:03d}',
            'producto': f'Producto Nacional {i+1}',
            'descripcion': f'Descripción del producto nacional {i+1}',
            'linea_comercial': 'VENTA NACIONAL',
            'clasificacion_farmacologica': 'Vitaminas',
            'formas_farmaceuticas': 'Jarabe',
            'via_administracion': 'Oral',
            'linea_produccion': 'Línea Nacional',
            'cantidad_facturada': 50 + i * 5,
            'precio_unitario': 10.00 + i,
            'total': (50 + i * 5) * (10.00 + i),
            'sales_channel_id': [2, 'VENTA NACIONAL'],
            'commercial_line_national_id': [2, 'VENTA NACIONAL'],
            'partner_name': f'Cliente Local {i+1}',
            'name': f'Producto Nacional {i+1}',
            'default_code': f'LOCAL{i+1:03d}',
            'invoice_date': f'2025-10-{(i % 30) + 1:02d}',
            'balance': (50 + i * 5) * (10.00 + i),
        })
    
    return mock_data

def get_meses_del_año(año):
    """Genera una lista de meses para un año específico."""
    meses_nombres = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    meses_disponibles = []
    for i in range(1, 13):
        mes_key = f"{año}-{i:02d}"
        mes_nombre = f"{meses_nombres[i-1]} {año}"
        meses_disponibles.append({'key': mes_key, 'nombre': mes_nombre})
    return meses_disponibles

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = data_manager.authenticate_user(username, password)
        if user_data:
            session['username'] = user_data.get('login', username)
            session['user_name'] = user_data.get('name', username)
            flash('¡Inicio de sesión exitoso!', 'success')
            # Cambio: Redirigir al dashboard principal por defecto
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    # Redirigir la ruta raíz al dashboard
    return redirect(url_for('dashboard'))

@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        # Obtener opciones de filtro
        filter_options = data_manager.get_filter_options()
        
        if request.method == 'POST':
            # For POST, get filters from the form
            selected_filters = {
                'date_from': request.form.get('date_from'),
                'date_to': request.form.get('date_to'),
                'search_term': request.form.get('search_term'),
                'partner_id': request.form.get('partner_id'),
                'per_page': request.form.get('per_page', '1000')
            }
        else:
            # For GET, get filters from query parameters
            selected_filters = {
                'date_from': request.args.get('date_from'),
                'date_to': request.args.get('date_to'),
                'search_term': request.args.get('search_term'),
                'partner_id': request.args.get('partner_id'),
                'per_page': request.args.get('per_page', '1000')
            }

        # Create a clean copy for the database query
        query_filters = selected_filters.copy()

        # Clean up filter values for the query
        for key, value in query_filters.items():
            if not value:  # Handles empty strings and None
                query_filters[key] = None

        # --- PAGINACIÓN (se pasa a OdooManager) ---
        page = int(request.args.get('page', 1))
        per_page = int(selected_filters.get('per_page', 1000))

        # Obtener datos y paginación directamente de OdooManager
        sales_data_filtered, pagination_data = data_manager.get_sales_lines(
            page=page,
            per_page=per_page,
            date_from=query_filters.get('date_from'),
            date_to=query_filters.get('date_to'),
            partner_id=query_filters.get('partner_id'),
            search=query_filters.get('search_term')
        )

        total = pagination_data.get('total', 0)
        pages = max(1, (total + per_page - 1) // per_page)
        showing_from = (page - 1) * per_page + 1 if total > 0 else 0
        showing_to = min(page * per_page, total)

        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
            'showing_from': showing_from,
            'showing_to': showing_to,
            'has_prev': page > 1,
            'has_next': page < pages
        }

        return render_template(
            'sales.html',
            sales_data=sales_data_filtered,
            filter_options=filter_options, # filter_options contiene la lista de clientes
            selected_filters=selected_filters,
            fecha_actual=datetime.now(),
            pagination=pagination
        )
    except Exception as e:
        flash(f'Error al obtener datos: {str(e)}', 'danger')
        pagination_default = {
            'page': 1, 'per_page': 1000, 'total': 0, 'pages': 0,
            'showing_from': 0, 'showing_to': 0, 'has_prev': False, 'has_next': False
        }
        return render_template('sales.html', 
                             sales_data=[],
                             filter_options={'lineas': [], 'clientes': []},
                             selected_filters={},
                             fecha_actual=datetime.now(),
                             pagination=pagination_default)

@app.route('/pending', methods=['GET', 'POST'])
def pending():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        # Obtener opciones de filtro
        filter_options = data_manager.get_filter_options()
        
        if request.method == 'POST':
            # For POST, get filters from the form
            selected_filters = {
                'date_from': request.form.get('date_from'),
                'date_to': request.form.get('date_to'),
                'partner_id': request.form.get('partner_id'),
                'search_term': request.form.get('search_term', '')
            }
            
            # Remove empty values
            selected_filters = {k: v for k, v in selected_filters.items() if v}
            
        else:
            # For GET, use query parameters if available
            selected_filters = {
                'date_from': request.args.get('date_from'),
                'date_to': request.args.get('date_to'),
                'partner_id': request.args.get('partner_id'),
                'search_term': request.args.get('search_term', '')
            }
            
            # Remove empty values
            selected_filters = {k: v for k, v in selected_filters.items() if v}

        # --- PAGINACIÓN (se pasa a OdooManager) ---
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 1000))

        # Obtener datos y paginación directamente de OdooManager
        pending_data, pagination_data = data_manager.get_pending_orders(
            page=page,
            per_page=per_page,
            filters=selected_filters
        )

        total = pagination_data.get('total', 0)
        pages = max(1, (total + per_page - 1) // per_page)
        showing_from = (page - 1) * per_page + 1 if total > 0 else 0
        showing_to = min(page * per_page, total)

        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
            'showing_from': showing_from,
            'showing_to': showing_to,
            'has_prev': page > 1,
            'has_next': page < pages
        }
        
        return render_template('pending.html', 
                             pending_data=pending_data,
                             pagination=pagination,
                             filter_options=filter_options,
                             selected_filters=selected_filters,
                             fecha_actual=datetime.now()
        )
    except Exception as e:
        flash(f'Error al obtener datos de pedidos pendientes: {str(e)}', 'danger')
        pagination_default = {
            'page': 1, 'per_page': 1000, 'total': 0, 'pages': 0,
            'showing_from': 0, 'showing_to': 0, 'has_prev': False, 'has_next': False
        }
        return render_template('pending.html', 
                             pending_data=[],
                             filter_options={'lineas': [], 'clientes': []},
                             selected_filters={},
                             fecha_actual=datetime.now(),
                             pagination=pagination_default)

@app.route('/dashboard', methods=['GET', 'POST'])
@cache.cached(timeout=600, query_string=True) # Cachea la respuesta por 10 mins, diferenciando por URL params
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Inicializar variables que necesitaremos en el except
    filter_options = {'lineas': [], 'clientes': []}
    selected_filters = {'cliente_id': None}
    
    try:
        # Obtener opciones de filtro básicas
        filter_options = data_manager.get_filter_options()
        
        # Obtener filtros del formulario o de los parámetros GET
        if request.method == 'POST':
            selected_filters = {'cliente_id': request.form.get('cliente_id')}
            selected_filters['date_from'] = request.form.get('date_from')
            selected_filters['date_to'] = request.form.get('date_to')
        else:
            selected_filters = {'cliente_id': request.args.get('cliente_id')}

        # Limpiar filtros para la consulta
        query_filters = selected_filters.copy()
        for key, value in query_filters.items():
            if not value:
                query_filters[key] = None
        
        # Convertir cliente_id a entero si existe
        partner_id = None
        if query_filters.get('cliente_id'):
            try:
                partner_id = int(query_filters['cliente_id'])
            except ValueError:
                partner_id = None
        
    # Debug info removed
        
        # MODIFICACIÓN: Usar fechas dinámicas. Si no se especifican, usar el año actual por defecto.
        date_from = selected_filters.get('date_from') or f"{datetime.now().year}-01-01"
        date_to = selected_filters.get('date_to') or f"{datetime.now().year}-12-31"
        
        # CORRECCIÓN: get_sales_lines ahora devuelve una tupla (datos, paginación).
        # Desempaquetamos y solo usamos los datos.
        sales_data_year, _ = data_manager.get_sales_lines(
            # Pasar las fechas dinámicas a la función.
            date_from=date_from,
            date_to=date_to,
            partner_id=partner_id,
            page=1,
            per_page=99999 # Pedir un número muy grande para obtener todos los registros
        )
    # Debug info removed
        
        # Los datos para KPIs y gráficos ahora provienen de la misma fuente
        sales_data_raw = sales_data_year

        # CORRECCIÓN: get_pending_orders ahora devuelve una tupla (datos, paginación).
        # Desempaquetamos y solo usamos los datos.
        pending_data, _ = data_manager.get_pending_orders(
            partner_id=partner_id, # CORRECCIÓN: Pasar partner_id directamente para asegurar que los filtros base se apliquen.
            page=1,
            per_page=99999  # Pedir un número muy grande para obtener todos los registros
        )

        # --- Agregación por pedido (backend) para gráfico de pedidos del cliente seleccionado ---
        orders_chart_data = []
        if partner_id:
            # Agrupar facturado por pedido desde sales_data_year
            # Esta lógica es crucial para identificar el nombre del pedido de las líneas de factura
            facturado_by_pedido = {}
            pedido_cliente_map = {}  # mapa pedido -> (cliente_id, cliente_name)
            for s in sales_data_raw: # Usar los datos crudos para la agregación
                # Lógica mejorada para obtener el nombre del pedido de forma fiable
                order_name_from_order = s.get('pedido')
                origin_from_invoice = s.get('invoice_origin')
                move_name = s.get('move_name')
                
                pedido_name = order_name_from_order or origin_from_invoice or move_name or ''
                if not pedido_name or not isinstance(pedido_name, str):
                    continue
                facturado_by_pedido[pedido_name] = facturado_by_pedido.get(pedido_name, 0) + (s.get('amount_currency', 0) or 0)
                # intentar obtener cliente id y nombre desde la línea de venta
                partner = s.get('partner_id') or s.get('partner') or s.get('cliente_id') or s.get('cliente')
                cliente_id = None
                cliente_name = None
                if partner:
                    if isinstance(partner, (list, tuple)) and len(partner) > 0:
                        cliente_id = partner[0]
                        if len(partner) > 1:
                            cliente_name = partner[1]
                    else:
                        # partner puede ser solo id o nombre
                        try:
                            cliente_id = int(partner)
                        except Exception:
                            cliente_name = str(partner)
                if pedido_name and (cliente_id or cliente_name):
                    # solo setear si no existe para no sobreescribir con valores distintos
                    if pedido_name not in pedido_cliente_map:
                        pedido_cliente_map[pedido_name] = {
                            'cliente_id': cliente_id,
                            'cliente': cliente_name,
                            'order_id': s.get('order_id')[0] if s.get('order_id') else None,
                            'partner': s.get('partner_id') or s.get('partner')
                        }

            # Agrupar pendiente por pedido desde pending_data
            pendiente_by_pedido = {}
            for p in pending_data: # Usar los datos crudos de pendientes
                pedido_name = p.get('pedido') or p.get('order_name') or p.get('move_name') or ''
                if not pedido_name:
                    continue
                pendiente_by_pedido[pedido_name] = pendiente_by_pedido.get(pedido_name, 0) + (p.get('total_pendiente', 0) or 0)
                # intentar obtener cliente desde pending
                partner = p.get('partner_id') or p.get('partner') or p.get('cliente_id') or p.get('cliente')
                cliente_id = None
                cliente_name = None
                if partner:
                    if isinstance(partner, (list, tuple)) and len(partner) > 0:
                        cliente_id = partner[0]
                        if len(partner) > 1:
                            cliente_name = partner[1]
                    else:
                        try:
                            cliente_id = int(partner)
                        except Exception:
                            cliente_name = str(partner)
                if pedido_name and (cliente_id or cliente_name):
                    if pedido_name not in pedido_cliente_map:
                        pedido_cliente_map[pedido_name] = {
                            'cliente_id': cliente_id,
                            'cliente': cliente_name,
                            'order_id': p.get('order_id') if p.get('order_id') else None,
                            'partner': p.get('partner_id') or p.get('partner')
                        }

            # --- NUEVA LÓGICA: Construir orders_chart_data a partir de los sale.orders del partner ---
            # Esto asegura que el 'total' de la barra sea el amount_total original del pedido
            partner_sale_orders = data_manager.get_sale_orders_for_partner(partner_id)

            for order_obj in partner_sale_orders:
                order_name = order_obj.get('name')
                if not order_name:
                    continue

                fact = facturado_by_pedido.get(order_name, 0)
                pend = pendiente_by_pedido.get(order_name, 0)
                original_total_order = order_obj.get('amount_total', 0)

                # Solo añadir si hay un total original o alguna actividad (facturado/pendiente)
                if original_total_order > 0 or fact > 0 or pend > 0:
                    orders_chart_data.append({
                        'pedido': order_name,
                        'total': original_total_order, # Usar el amount_total original del pedido
                        'facturado': fact,
                        'pendiente': pend,
                        'cliente_id': partner_id, # Ya sabemos que es este partner
                        'cliente': order_obj.get('partner_id')[1] if order_obj.get('partner_id') else '',
                        'order_id': order_obj.get('id'),
                        'partner': order_obj.get('partner_id')
                    })

            # Ordenar por total descendente
            orders_chart_data = sorted(orders_chart_data, key=lambda x: x['total'], reverse=True)
            # Removed verbose debug logging for orders_chart_data
        else:
            orders_chart_data = []

        sales_data = sales_data_year
        sales_data_international = sales_data_year
        
        ventas_por_linea = {}
        total_sales_year = 0
        
        # NUEVA LÓGICA: Primero agrupar por factura (move_name) para cancelar positivos/negativos
        ventas_por_factura = {}
        
        # Debug logs removed: sales_data_international sampling
        
        todas_las_lineas = set()
        por_facturar_por_linea = {} # Inicializar para evitar errores
        total_por_facturar = 0 # Inicializar para evitar errores
        
        for sale in sales_data_international:
            # Usar 'commercial_line_international_id' para consistencia
            linea_comercial_obj = sale.get('commercial_line_international_id')
            nombre_linea = "Sin Línea Comercial"
            if linea_comercial_obj and isinstance(linea_comercial_obj, list) and len(linea_comercial_obj) > 1:
                nombre_linea = linea_comercial_obj[1]
            
            todas_las_lineas.add(nombre_linea)
            
            # Usar 'amount_currency' que ya tiene el signo correcto desde OdooManager
            venta_amount = sale.get('amount_currency', 0)
            
            ventas_por_linea[nombre_linea] = ventas_por_linea.get(nombre_linea, 0) + venta_amount
            total_sales_year += venta_amount
        
        # Procesar datos pendientes para la tabla
        for pending_item in pending_data:
            linea_nombre = pending_item.get('linea_comercial', 'Sin Línea Comercial')
            total_pendiente = pending_item.get('total_pendiente', 0)
            por_facturar_por_linea[linea_nombre] = por_facturar_por_linea.get(linea_nombre, 0) + total_pendiente
            total_por_facturar += total_pendiente
            todas_las_lineas.add(linea_nombre)
        
        # La línea que añadía "OTROS" ha sido eliminada. Ahora solo se mostrarán líneas con datos.
        
        # Generar datos para la tabla y el gráfico
        datos_lineas = []
        for nombre_linea in todas_las_lineas:
            venta = ventas_por_linea.get(nombre_linea, 0)
            datos_lineas.append({
                'nombre': nombre_linea,
                'venta': venta
            })
        
        # Ordenar por venta descendente
        datos_lineas = sorted(datos_lineas, key=lambda x: x['venta'], reverse=True)
        
        # Procesar datos por producto para gráfico (usando ventas internacionales del año)
        ventas_por_producto = {}
        
        for sale in sales_data_international:
            # Usar el campo "name" directamente para el nombre del producto
            nombre_producto = sale.get('name', 'Producto Sin Nombre')
            
            # MODIFICACIÓN: Usar 'amount_currency' para consistencia con el cálculo de líneas comerciales.
            # 'total' puede ser 0 si la factura está pagada, pero 'amount_currency' mantiene el valor de la línea.
            venta_amount = sale.get('amount_currency', 0)
            if venta_amount > 0:  # Solo procesar ventas con monto
                ventas_por_producto[nombre_producto] = ventas_por_producto.get(nombre_producto, 0) + venta_amount
        
        # Generar datos para el gráfico de productos (Top 7)
        productos_ordenados = sorted(ventas_por_producto.items(), key=lambda x: x[1], reverse=True)[:7]
        datos_productos = []
        for nombre_producto, venta in productos_ordenados:
            if venta > 0:
                datos_productos.append({
                    'nombre': nombre_producto,
                    'venta': venta
                })
        
        # Calcular KPIs adicionales
        unique_clients = len(set(sale['cliente'] for sale in sales_data_international if sale.get('cliente')))
        total_products = len(set(sale['producto'] for sale in sales_data_international if sale.get('producto')))
        total_invoices = len(set(sale['factura'] for sale in sales_data_international if sale.get('factura')))

        # Calcular Brecha Comercial (Meta - Venta). Meta es 0 por ahora.
        meta_total_kpi = 0
        brecha_comercial = meta_total_kpi - total_sales_year


        # --- LÓGICA PARA GRÁFICOS ADICIONALES (Ciclo de Vida, Forma Farmacéutica) ---
        ventas_por_forma_farmaceutica = {}
        
        for sale in sales_data_international:
            venta_amount = sale.get('amount_currency', 0)
            
            # Agrupar por forma farmacéutica
            forma_farma = sale.get('pharmaceutical_forms_id')
            nombre_forma = forma_farma[1] if forma_farma and len(forma_farma) > 1 else 'Instrumental'
            ventas_por_forma_farmaceutica[nombre_forma] = ventas_por_forma_farmaceutica.get(nombre_forma, 0) + venta_amount

        datos_forma_farmaceutica = [{'forma': f, 'venta': v} for f, v in ventas_por_forma_farmaceutica.items()]
        # --- LÓGICA PARA GRÁFICO DRILLDOWN JERÁRQUICO ---
        drilldown_data = {}
        drilldown_titles = {}
        top_products_by_level = {}
        pie_chart_data_by_level = {}

        if sales_data_international:
            df_sales = pd.DataFrame(sales_data_international)
            
            # Asegurarse de que la columna de venta exista y sea numérica
            if 'amount_currency' in df_sales.columns:
                df_sales['venta'] = pd.to_numeric(df_sales['amount_currency'], errors='coerce').fillna(0)

                # Extraer nombres de campos relacionados
                def extract_name(field):
                    if isinstance(field, list) and len(field) > 1:
                        return field[1]
                    return 'No Definido'

                df_sales['linea_comercial_nombre'] = df_sales['commercial_line_international_id'].apply(extract_name)
                df_sales['clasificacion_farma_nombre'] = df_sales['pharmacological_classification_id'].apply(extract_name)
                df_sales['producto_nombre'] = df_sales['name']

                # Nivel 0: Agrupación por Línea Comercial (root)
                level0_data = df_sales.groupby('linea_comercial_nombre')['venta'].sum().reset_index()
                drilldown_data['root'] = [
                    [row['linea_comercial_nombre'], row['venta'], 'root', f"level1_{row['linea_comercial_nombre']}"]
                    for _, row in level0_data.iterrows()
                ]
                drilldown_titles['root'] = 'Ventas por Línea Comercial'
                top_products_by_level['root'] = datos_productos # Top productos general
                pie_chart_data_by_level['root'] = datos_forma_farmaceutica
                # CORRECCIÓN: El gráfico de pastel en el nivel raíz debe mostrar la agrupación por Clasificación Farmacológica.
                # Se restaura la lógica para usar los datos correctos.
                pie_data_root = df_sales.groupby('clasificacion_farma_nombre')['venta'].sum().reset_index()
                pie_chart_data_by_level['root'] = [
                    {'name': r['clasificacion_farma_nombre'], 'value': r['venta']} for _, r in pie_data_root.iterrows()
                ]

                # Niveles 1 y 2: Agrupación por Clasificación y Producto
                for linea, group_linea in df_sales.groupby('linea_comercial_nombre'):
                    # Nivel 1: Clasificación Farmacológica para esta línea
                    level1_id = f"level1_{linea}"
                    level1_data = group_linea.groupby('clasificacion_farma_nombre')['venta'].sum().reset_index()
                    drilldown_data[level1_id] = [
                        [row['clasificacion_farma_nombre'], row['venta'], level1_id, f"level2_{linea}_{row['clasificacion_farma_nombre']}"]
                        for _, row in level1_data.iterrows()
                    ]
                    drilldown_titles[level1_id] = f'Ventas en {linea} por Clasificación'
                    
                    # Top productos para este nivel
                    top_products_linea = group_linea.groupby('producto_nombre')['venta'].sum().nlargest(7).reset_index()
                    top_products_by_level[level1_id] = top_products_linea.to_dict('records')

                    # CORRECCIÓN: El gráfico de pastel para este nivel (Línea Comercial) debe agrupar por Clasificación Farmacológica.
                    # Esta lógica se había perdido y se ha restaurado.
                    pie_data_linea = group_linea.groupby('clasificacion_farma_nombre')['venta'].sum().reset_index()
                    pie_chart_data_by_level[level1_id] = [{'name': r['clasificacion_farma_nombre'], 'value': r['venta']}
                                                          for _, r in pie_data_linea.iterrows() if r['venta'] > 0]


                    for clasificacion, group_clasificacion in group_linea.groupby('clasificacion_farma_nombre'):
                        # Nivel 2: Productos para esta clasificación
                        level2_id = f"level2_{linea}_{clasificacion}"
                        level2_data = group_clasificacion.groupby('producto_nombre')['venta'].sum().reset_index()
                        drilldown_data[level2_id] = [
                            [row['producto_nombre'], row['venta'], level2_id, None] # Último nivel, no hay childGroupId
                            for _, row in level2_data.iterrows()
                        ]
                        drilldown_titles[level2_id] = f'Ventas de {clasificacion} en {linea}'
                        
                        # Top productos para este nivel (son todos los productos de la clasificación)
                        top_products_by_level[level2_id] = level2_data.to_dict('records')

                        # CORRECCIÓN: El gráfico de pastel para este nivel (Clasificación) debe agrupar por Producto.
                        # Esta lógica se había perdido y se ha restaurado.
                        pie_data_clasif = group_clasificacion.groupby('producto_nombre')['venta'].sum().reset_index()
                        pie_chart_data_by_level[level2_id] = [{'name': r['producto_nombre'], 'value': r['venta']}
                                                              for _, r in pie_data_clasif.iterrows() if r['venta'] > 0]

        # Convertir todos los datos de gráficos a JSON
        all_stacked_chart_data = json.dumps(
            data_manager.get_commercial_lines_stacked_data(date_from=date_from, date_to=date_to, partner_id=partner_id)
        )

        # Para la tabla (agregar datos adicionales si es necesario)
        datos_lineas_tabla = datos_lineas.copy()
        for linea in datos_lineas_tabla:
            venta_total_linea = linea.get('venta', 0)
            por_facturar_linea = por_facturar_por_linea.get(linea['nombre'], 0)
            meta_linea = 0  # Meta se establece en 0 por ahora
            
            # Calcular brecha y avance
            venta_proyectada = venta_total_linea + por_facturar_linea
            brecha = venta_proyectada - meta_linea
            porcentaje_avance_meta = (venta_proyectada / meta_linea * 100) if meta_linea > 0 else 0

            linea.update({
                'por_facturar': por_facturar_linea,
                'porcentaje_sobre_total': (venta_total_linea / total_sales_year * 100) if total_sales_year > 0 else 0,
                'meta': meta_linea,
                'brecha': brecha,
                'porcentaje_avance_meta': porcentaje_avance_meta
            })
        
        # Calcular KPIs totales
        meta_total_general = 0 # Meta total se establece en 0 por ahora
        venta_proyectada_total = total_sales_year + total_por_facturar
        total_brecha = venta_proyectada_total - meta_total_general
        porcentaje_avance_total = (venta_proyectada_total / meta_total_general * 100) if meta_total_general > 0 else 0

        kpis = {
            # KPIs que el template espera (usando total_sales_year para consistencia con la tabla)
            'meta_total': meta_total_general,
            'venta_total': total_sales_year,  # Usar el total del año que coincide con la suma de líneas comerciales
            'total_por_facturar': total_por_facturar,
            'porcentaje_avance': porcentaje_avance_total,
            'total_brecha': total_brecha
        }
        
        # --- LÓGICA PARA GRÁFICO DE AVANCE POR CLIENTE ---
        facturado_por_cliente = {}
        for sale in sales_data_international:
            cliente_nombre = sale.get('cliente')
            if cliente_nombre:
                facturado_por_cliente[cliente_nombre] = facturado_por_cliente.get(cliente_nombre, 0) + sale.get('amount_currency', 0)

        pendiente_por_cliente = {}
        for pending in pending_data:
            cliente_nombre = pending.get('cliente')
            if cliente_nombre:
                pendiente_por_cliente[cliente_nombre] = pendiente_por_cliente.get(cliente_nombre, 0) + pending.get('total_pendiente', 0)

        # Unir todos los clientes que tienen datos facturados o pendientes
        all_clients = set(facturado_por_cliente.keys()) | set(pendiente_por_cliente.keys())
        
        bullet_chart_data = []
        for cliente in all_clients:
            facturado = max(0, facturado_por_cliente.get(cliente, 0))
            pendiente = max(0, pendiente_por_cliente.get(cliente, 0))
            total_pedido = facturado + pendiente
            if total_pedido > 0:
                bullet_chart_data.append({
                    'total_pedido': total_pedido,
                    'cliente': cliente,
                    'facturado': facturado
                })
        
        # Variables para el template
        fecha_actual = datetime.now()
        mes_nombre = fecha_actual.strftime('%B %Y').title()  # Ejemplo: "October 2025"
        dia_actual = fecha_actual.day
        
        # Obtener nombre del cliente seleccionado
        nombre_cliente_seleccionado = None
        if partner_id and filter_options.get('clientes'):
            for cliente in filter_options['clientes']:
                if cliente[0] == partner_id:
                    nombre_cliente_seleccionado = cliente[1]
                    break

        # --- LÓGICA PARA AVANCE DEL CLIENTE SELECCIONADO (NUEVA TARJETA) ---
        avance_cliente_seleccionado = None
        if partner_id and bullet_chart_data and nombre_cliente_seleccionado:
            # El nombre del cliente ya se obtuvo en la variable `nombre_cliente_seleccionado`
            # Usamos el nombre sin el país para la comparación
            nombre_cliente_simple = nombre_cliente_seleccionado.split(' (')[0]
            for data in bullet_chart_data:
                if data.get('cliente') == nombre_cliente_simple:
                    total_pedido_cliente = data.get('total_pedido', 0)
                    avance_cliente_seleccionado = {
                        'nombre': data['cliente'],
                        'facturado': data.get('facturado', 0),
                        'total_pedido': total_pedido_cliente,
                        'porcentaje': (data.get('facturado', 0) / total_pedido_cliente * 100) if total_pedido_cliente > 0 else 0
                    }
                    break
        
        return render_template('dashboard_clean.html',
                             sales_data=sales_data,
                             kpis=kpis, # kpis ahora se basa en el total del año
                             filter_options=filter_options,
                             selected_filters=selected_filters,
                             fecha_actual=fecha_actual,
                             mes_nombre=mes_nombre,
                             dia_actual=dia_actual,
                             nombre_cliente_seleccionado=nombre_cliente_seleccionado,
                             # Variables adicionales que el template pueda necesitar
                             meses_disponibles=get_meses_del_año(fecha_actual.year),
                             mes_seleccionado=fecha_actual.strftime('%Y-%m'),
                             datos_lineas=datos_lineas,
                             datos_lineas_tabla=datos_lineas_tabla,
                             datos_productos=datos_productos,
                             datos_forma_farmaceutica=datos_forma_farmaceutica,
                             drilldown_data=drilldown_data,                             
                             total_sales=total_sales_year + total_por_facturar, # Suma de facturado + por facturar
                             unique_clients=unique_clients,
                             total_products=total_products,
                             total_invoices=total_invoices,
                             meta_total_kpi=meta_total_kpi,
                             brecha_comercial=brecha_comercial,
                             bullet_chart_data=bullet_chart_data,
                             orders_chart_data=orders_chart_data,
                             avance_cliente_seleccionado=avance_cliente_seleccionado,
                             drilldown_titles=drilldown_titles,
                             top_products_by_level=top_products_by_level,
                             pie_chart_data_by_level=pie_chart_data_by_level,
                             all_stacked_chart_data=all_stacked_chart_data,
                             pending_data=pending_data,
                             avance_lineal_pct=0,
                             faltante_meta=0,
                             avance_lineal_ipn_pct=0,
                             faltante_meta_ipn=0)
    
    except Exception as e:
        # Informar al usuario y registrar el error
        flash('Ocurrió un error inesperado al cargar el dashboard. Por favor, intente de nuevo más tarde.', 'danger')
        app.logger.error(f"ERROR EN DASHBOARD: {str(e)}")
        app.logger.exception(e)

        # Preparar datos por defecto para renderizar la plantilla de error
        fecha_actual = datetime.now()
        mes_nombre = fecha_actual.strftime('%B %Y').title()
        dia_actual = fecha_actual.day

        # Obtener filter_options incluso en caso de error si no se pudo antes
        if not filter_options or filter_options == {'lineas': [], 'clientes': []}:
            try:
                filter_options = data_manager.get_filter_options()
            except Exception:
                filter_options = {'lineas': [], 'clientes': []}

        return render_template('dashboard_clean.html',
                             sales_data=[],
                             kpis={
                                 'meta_total': 0,
                                 'venta_total': 0,
                                 'total_por_facturar': 0,
                                 'porcentaje_avance': 0
                             },
                             filter_options=filter_options,
                             selected_filters=selected_filters,
                             fecha_actual=fecha_actual, # Mantener para consistencia
                             mes_nombre=mes_nombre,
                             dia_actual=dia_actual,
                             meses_disponibles=[],
                             mes_seleccionado=fecha_actual.strftime('%Y-%m'),
                             datos_lineas=[],
                             datos_lineas_tabla=[],
                             datos_productos=[],
                             datos_forma_farmaceutica=[],
                             total_sales=0,
                             unique_clients=0,
                             total_products=0,
                             total_invoices=0,
                             meta_total_kpi=0,
                             brecha_comercial=0,
                             bullet_chart_data=[],
                             avance_cliente_seleccionado=None,
                             drilldown_data={},
                             drilldown_titles={},
                             top_products_by_level={},
                             pie_chart_data_by_level={},
                             all_stacked_chart_data="{}",
                             avance_lineal_pct=0,
                             faltante_meta=0,
                             avance_lineal_ipn_pct=0,
                             faltante_meta_ipn=0)

@app.route('/dashboard_linea')
def dashboard_linea():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        # --- 1. OBTENER FILTROS ---
        fecha_actual = datetime.now()
        mes_seleccionado = request.args.get('mes', fecha_actual.strftime('%Y-%m'))
        año_actual = fecha_actual.year
        meses_disponibles = get_meses_del_año(año_actual)

        linea_seleccionada_nombre = request.args.get('linea_nombre', 'PETMEDICA') # Default a PETMEDICA si no se especifica

        # --- NUEVA LÓGICA DE FILTRADO POR DÍA ---
        dia_fin_param = request.args.get('dia_fin')
        año_sel, mes_sel = mes_seleccionado.split('-')

        if dia_fin_param:
            try:
                dia_actual = int(dia_fin_param)
                fecha_fin = f"{año_sel}-{mes_sel}-{str(dia_actual).zfill(2)}"
            except (ValueError, TypeError):
                dia_fin_param = None
        
        if not dia_fin_param:
            if mes_seleccionado == fecha_actual.strftime('%Y-%m'):
                dia_actual = fecha_actual.day
            else:
                ultimo_dia_mes = calendar.monthrange(int(año_sel), int(mes_sel))[1]
                dia_actual = ultimo_dia_mes
            fecha_fin = f"{año_sel}-{mes_sel}-{str(dia_actual).zfill(2)}"
        
        fecha_inicio = f"{año_sel}-{mes_sel}-01"
        # --- FIN DE LA NUEVA LÓGICA ---

        # Mapeo de nombre de línea a ID para cargar metas
        mapeo_nombre_a_id = {
            'PETMEDICA': 'petmedica', 'AGROVET': 'agrovet', 'PET NUTRISCIENCE': 'pet_nutriscience',
            'AVIVET': 'avivet', 'OTROS': 'otros',
            'GENVET': 'genvet', 'INTERPET': 'interpet',
        }
        linea_seleccionada_id = mapeo_nombre_a_id.get(linea_seleccionada_nombre.upper(), 'petmedica')

        # --- 2. OBTENER DATOS ---
        # fecha_inicio y fecha_fin se calculan arriba usando la lógica de dia_fin.
        # Asegurar que fecha_inicio siempre esté definida
        año_sel, mes_sel = mes_seleccionado.split('-')
        fecha_inicio = f"{año_sel}-{mes_sel}-01"
        # Si no se definió fecha_fin arriba (por alguna razón), usar el último día del mes
        if 'fecha_fin' not in locals():
            ultimo_dia = calendar.monthrange(int(año_sel), int(mes_sel))[1]
            fecha_fin = f"{año_sel}-{mes_sel}-{ultimo_dia}"

        # Cargar metas de vendedores para el mes y línea seleccionados
        # La estructura es metas[equipo_id][vendedor_id][mes_key]
        metas_vendedores_historicas = gs_manager.read_metas()
        # 1. Obtener todas las metas del equipo/línea
        metas_del_equipo = metas_vendedores_historicas.get(linea_seleccionada_id, {})

        # Obtener todos los vendedores de Odoo
        todos_los_vendedores = {str(v['id']): v['name'] for v in data_manager.get_all_sellers()}

        # Obtener ventas del mes
        sales_data = data_manager.get_sales_lines(
            date_from=fecha_inicio,
            date_to=fecha_fin,
            limit=10000
        )

        # --- PRE-FILTRAR VENTAS INTERNACIONALES PARA EFICIENCIA ---
        sales_data_processed = []
        for sale in sales_data:
            # Excluir VENTA INTERNACIONAL (exportaciones) por línea comercial
            linea_comercial = sale.get('commercial_line_national_id')
            if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                if 'VENTA INTERNACIONAL' in linea_comercial[1].upper():
                    continue
            
            # Excluir VENTA INTERNACIONAL por canal de ventas
            canal_ventas = sale.get('sales_channel_id')
            if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
                nombre_canal = canal_ventas[1].upper()
                if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                    continue
            
            sales_data_processed.append(sale)

        # --- 3. PROCESAR Y AGREGAR DATOS POR VENDEDOR ---
        ventas_por_vendedor = {}
        ventas_ipn_por_vendedor = {}
        ventas_vencimiento_por_vendedor = {}
        ventas_por_producto = {}
        ventas_por_forma = {}
        ajustes_sin_vendedor = 0 # Para notas de crédito sin vendedor
        nombres_vendedores_con_ventas = {} # BUGFIX: Guardar nombres de vendedores con ventas

        for sale in sales_data_processed: # Usar los datos pre-filtrados
            linea_comercial = sale.get('commercial_line_national_id')
            if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                nombre_linea_actual = linea_comercial[1].upper()

                # Filtrar por la línea comercial seleccionada
                if nombre_linea_actual == linea_seleccionada_nombre.upper():
                    balance = float(sale.get('balance', 0))
                    user_info = sale.get('invoice_user_id')

                    # Si hay un vendedor asignado, se procesa normalmente
                    if user_info and isinstance(user_info, list) and len(user_info) > 1:
                        vendedor_id = str(user_info[0])
                        nombres_vendedores_con_ventas[vendedor_id] = user_info[1] # Guardar el nombre

                        # Agrupar ventas totales
                        ventas_por_vendedor[vendedor_id] = ventas_por_vendedor.get(vendedor_id, 0) + balance

                        # Agrupar ventas IPN
                        if sale.get('product_life_cycle') == 'nuevo':
                            ventas_ipn_por_vendedor[vendedor_id] = ventas_ipn_por_vendedor.get(vendedor_id, 0) + balance
                        
                        # Agrupar ventas por vencimiento < 6 meses
                        ruta = sale.get('route_id')
                        if isinstance(ruta, list) and len(ruta) > 0 and ruta[0] in [18, 19]:
                            ventas_vencimiento_por_vendedor[vendedor_id] = ventas_vencimiento_por_vendedor.get(vendedor_id, 0) + balance
                    
                    # Si NO hay vendedor, se agrupa como un ajuste (ej. Nota de Crédito)
                    else:
                        ajustes_sin_vendedor += balance

                    # Agrupar para gráficos (Top Productos, Ciclo Vida, Forma Farmacéutica)
                    # Esto se hace para todas las transacciones de la línea, con o sin vendedor
                    producto_nombre = sale.get('name', '').strip()
                    if producto_nombre:
                        ventas_por_producto[producto_nombre] = ventas_por_producto.get(producto_nombre, 0) + balance

                    forma_farma = sale.get('pharmaceutical_forms_id')
                    nombre_forma = forma_farma[1] if forma_farma and len(forma_farma) > 1 else 'Instrumental'
                    ventas_por_forma[nombre_forma] = ventas_por_forma.get(nombre_forma, 0) + balance

        # --- 4. CONSTRUIR ESTRUCTURA DE DATOS PARA LA PLANTILLA ---
        datos_vendedores = []
        total_meta = 0
        total_venta = 0
        total_meta_ipn = 0
        total_venta_ipn = 0
        total_vencimiento = 0

        # --- 4.1. UNIFICAR VENDEDORES ---
        # Combinar los vendedores oficiales del equipo con los que tuvieron ventas reales en la línea.
        # Esto asegura que mostremos a todos los miembros del equipo (incluso con 0 ventas)
        # y también a cualquier otra persona que haya vendido en esta línea sin ser miembro oficial.
        equipos_guardados = gs_manager.read_equipos()
        miembros_oficiales_ids = {str(vid) for vid in equipos_guardados.get(linea_seleccionada_id, [])}
        vendedores_con_ventas_ids = set(ventas_por_vendedor.keys())
        
        todos_los_vendedores_a_mostrar_ids = sorted(list(miembros_oficiales_ids | vendedores_con_ventas_ids))

        # --- 4.2. CONSTRUIR LA TABLA DE VENDEDORES ---
        for vendedor_id in todos_los_vendedores_a_mostrar_ids:
            # BUGFIX: Priorizar el nombre de la venta, luego la lista general, y como último recurso el ID.
            vendedor_nombre = nombres_vendedores_con_ventas.get(vendedor_id, 
                                todos_los_vendedores.get(vendedor_id, f"Vendedor ID {vendedor_id}"))

            
            # Obtener ventas (será 0 si es un miembro oficial sin ventas)
            venta = ventas_por_vendedor.get(vendedor_id, 0)
            venta_ipn = ventas_ipn_por_vendedor.get(vendedor_id, 0)
            vencimiento = ventas_vencimiento_por_vendedor.get(vendedor_id, 0)

            # Asignar meta SOLO si el vendedor es un miembro oficial del equipo
            meta = 0
            meta_ipn = 0
            if vendedor_id in miembros_oficiales_ids:
                meta_guardada = metas_del_equipo.get(vendedor_id, {}).get(mes_seleccionado, {})
                meta = float(meta_guardada.get('meta', 0))
                meta_ipn = float(meta_guardada.get('meta_ipn', 0))

            # Añadir la fila del vendedor a la tabla
            datos_vendedores.append({
                'id': vendedor_id,
                'nombre': vendedor_nombre,
                'meta': meta,
                'venta': venta,
                'porcentaje_avance': (venta / meta * 100) if meta > 0 else 0,
                'meta_ipn': meta_ipn,
                'venta_ipn': venta_ipn,
                'porcentaje_avance_ipn': (venta_ipn / meta_ipn * 100) if meta_ipn > 0 else 0,
                'vencimiento_6_meses': vencimiento
            })

            # Sumar a los totales generales de la línea.
            # La meta solo se suma si fue asignada (es decir, si es miembro oficial).
            # La venta se suma siempre.
            total_meta += meta
            total_venta += venta
            total_meta_ipn += meta_ipn
            total_venta_ipn += venta_ipn
            total_vencimiento += vencimiento

        # --- 4.3. AÑADIR AJUSTES SIN VENDEDOR ---
        if ajustes_sin_vendedor != 0:
            datos_vendedores.append({
                'id': 'ajustes',
                'nombre': 'Ajustes y Notas de Crédito (Sin Vendedor)',
                'meta': 0, 'venta': ajustes_sin_vendedor, 'porcentaje_avance': 0,
                'meta_ipn': 0, 'venta_ipn': 0, 'porcentaje_avance_ipn': 0,
                'vencimiento_6_meses': 0
            })
            # Sumar los ajustes al total de ventas de la línea
            total_venta += ajustes_sin_vendedor

        # Añadir porcentaje sobre el total a cada vendedor
        if total_venta > 0:
            for v in datos_vendedores:
                v['porcentaje_sobre_total'] = (v.get('venta', 0) / total_venta) * 100
        else:
            for v in datos_vendedores:
                v['porcentaje_sobre_total'] = 0

        # --- 4.4. FILTRAR VENDEDORES CON VENTA NEGATIVA ---
        # Si un vendedor solo tiene notas de crédito (venta < 0), no se muestra en la tabla,
        # pero su valor ya fue sumado (restado) al total_venta para mantener la consistencia.
        datos_vendedores_final = [v for v in datos_vendedores if v['venta'] >= 0 or v['id'] == 'ajustes']

        # Ordenar por venta descendente
        datos_vendedores_final = sorted(datos_vendedores_final, key=lambda x: x['venta'], reverse=True)

        # --- 5. CALCULAR KPIs DE LÍNEA ---
        ritmo_diario_requerido_linea = 0
        if mes_seleccionado == fecha_actual.strftime('%Y-%m'):
            hoy = fecha_actual.day
            ultimo_dia_mes = calendar.monthrange(año_actual, fecha_actual.month)[1]
            dias_restantes = 0
            for dia in range(hoy, ultimo_dia_mes + 1):
                if datetime(año_actual, fecha_actual.month, dia).weekday() < 6: # L-S
                    dias_restantes += 1
            
            porcentaje_restante = 100 - ((total_venta / total_meta * 100) if total_meta > 0 else 100)
            if porcentaje_restante > 0 and dias_restantes > 0:
                ritmo_diario_requerido_linea = porcentaje_restante / dias_restantes

        # KPIs generales para la línea
        kpis = {
            'meta_total': total_meta,
            'venta_total': total_venta,
            'porcentaje_avance': (total_venta / total_meta * 100) if total_meta > 0 else 0,
            'meta_ipn': total_meta_ipn,
            'venta_ipn': total_venta_ipn,
            'porcentaje_avance_ipn': (total_venta_ipn / total_meta_ipn * 100) if total_meta_ipn > 0 else 0,
            'vencimiento_6_meses': total_vencimiento,
            'avance_diario_total': ((total_venta / total_meta * 100) / dia_actual) if total_meta > 0 and dia_actual > 0 else 0,
            'avance_diario_ipn': ((total_venta_ipn / total_meta_ipn * 100) / dia_actual) if total_meta_ipn > 0 and dia_actual > 0 else 0,
            'ritmo_diario_requerido': ritmo_diario_requerido_linea
        }

        # --- Avance lineal específico de la línea: proyección de cierre y faltante ---
        try:
            dias_en_mes = calendar.monthrange(int(año_sel), int(mes_sel))[1]
        except Exception:
            dias_en_mes = 30

        if dia_actual > 0:
            proyeccion_mensual_linea = (total_venta / dia_actual) * dias_en_mes
        else:
            proyeccion_mensual_linea = 0

        avance_lineal_pct = (proyeccion_mensual_linea / total_meta * 100) if total_meta > 0 else 0
        faltante_meta = max(total_meta - total_venta, 0)

        # Cálculos específicos para IPN de la línea
        if dia_actual > 0:
            promedio_diario_ipn_linea = total_venta_ipn / dia_actual
            proyeccion_mensual_ipn_linea = promedio_diario_ipn_linea * dias_en_mes
        else:
            proyeccion_mensual_ipn_linea = 0

        avance_lineal_ipn_pct = (proyeccion_mensual_ipn_linea / total_meta_ipn * 100) if total_meta_ipn > 0 else 0
        faltante_meta_ipn = max(total_meta_ipn - total_venta_ipn, 0)

        # Datos para gráficos
        productos_ordenados = sorted(ventas_por_producto.items(), key=lambda x: x[1], reverse=True)[:7]
        datos_productos = [{'nombre': n, 'venta': v} for n, v in productos_ordenados]

        datos_forma_farmaceutica = [{'forma': f, 'venta': v} for f, v in ventas_por_forma.items()]

        # Lista dinámica de todas las líneas para el selector (a partir de ventas y metas)
        lineas_set = set()
        # Extraer líneas desde los datos de ventas crudos
        for sale in sales_data:
            linea_obj = sale.get('commercial_line_national_id')
            if linea_obj and isinstance(linea_obj, list) and len(linea_obj) > 1:
                nombre_linea = linea_obj[1].upper()
                if 'VENTA INTERNACIONAL' in nombre_linea:
                    continue
                if nombre_linea.upper() in ['LICITACION', 'NINGUNO', 'ECOMMERCE']:
                    continue
                lineas_set.add(nombre_linea)

        # Añadir líneas desde las metas (reconstruir nombre desde el id)
        for linea_id_meta in metas_vendedores_historicas.keys():
            nombre_reconstruido = linea_id_meta.replace('_', ' ').upper()
            if nombre_reconstruido not in lineas_set:
                lineas_set.add(nombre_reconstruido)

        # Fallback a la lista estática si quedó vacío
        if not lineas_set:
            lineas_disponibles = ['PETMEDICA', 'AGROVET', 'PET NUTRISCIENCE', 'AVIVET', 'OTROS', 'GENVET', 'INTERPET']
        else:
            lineas_disponibles = sorted(list(lineas_set))
        return render_template('dashboard_linea.html',
                               linea_nombre=linea_seleccionada_nombre,
                               mes_seleccionado=mes_seleccionado,
                               meses_disponibles=meses_disponibles,
                               kpis=kpis,
                               datos_vendedores=datos_vendedores_final,
                               datos_productos=datos_productos,
                               datos_forma_farmaceutica=datos_forma_farmaceutica,
                               lineas_disponibles=lineas_disponibles,
                               fecha_actual=fecha_actual,
                               dia_actual=dia_actual,
                               avance_lineal_pct=avance_lineal_pct,
                               faltante_meta=faltante_meta,
                               avance_lineal_ipn_pct=avance_lineal_ipn_pct,
                               faltante_meta_ipn=faltante_meta_ipn)

    except Exception as e:
        flash(f'Error al generar el dashboard para la línea: {str(e)}', 'danger')
        # En caso de error, renderizar la plantilla con datos vacíos para no romper la UI
        fecha_actual = datetime.now()
        año_actual = fecha_actual.year
        meses_disponibles = get_meses_del_año(año_actual)
        linea_seleccionada_nombre = request.args.get('linea_nombre', 'PETMEDICA')
        lineas_disponibles = [
            'PETMEDICA', 'AGROVET', 'PET NUTRISCIENCE', 'AVIVET', 'OTROS', 'GENVET', 'INTERPET'
        ]
        dia_actual = fecha_actual.day
        kpis_default = {
            'meta_total': 0, 'venta_total': 0, 'porcentaje_avance': 0,
            'meta_ipn': 0, 'venta_ipn': 0, 'porcentaje_avance_ipn': 0,
            'vencimiento_6_meses': 0, 'avance_diario_total': 0, 'avance_diario_ipn': 0
        }
        
        return render_template('dashboard_linea.html',
                               linea_nombre=linea_seleccionada_nombre,
                               mes_seleccionado=fecha_actual.strftime('%Y-%m'),
                               meses_disponibles=meses_disponibles,
                               kpis=kpis_default,
                               datos_vendedores=[],
                               datos_productos=[],
                               datos_forma_farmaceutica=[],
                               lineas_disponibles=lineas_disponibles,
                               fecha_actual=fecha_actual,
                               dia_actual=dia_actual,
                               avance_lineal_pct=0,
                               faltante_meta=0,
                               avance_lineal_ipn_pct=0,
                               faltante_meta_ipn=0)


@app.route('/meta', methods=['GET', 'POST'])
def meta():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        # Líneas comerciales estáticas de la empresa
        lineas_comerciales_estaticas = [
            {'nombre': 'PETMEDICA', 'id': 'petmedica'},
            {'nombre': 'AGROVET', 'id': 'agrovet'},
            {'nombre': 'PET NUTRISCIENCE', 'id': 'pet_nutriscience'},
            {'nombre': 'AVIVET', 'id': 'avivet'},
            {'nombre': 'OTROS', 'id': 'otros'},
            {'nombre': 'GENVET', 'id': 'genvet'},
            {'nombre': 'INTERPET', 'id': 'interpet'},
        ]
        
        # Obtener año actual y mes seleccionado
        fecha_actual = datetime.now()
        año_actual = fecha_actual.year
        mes_seleccionado = request.args.get('mes', fecha_actual.strftime('%Y-%m'))
        
        # Crear todos los meses del año actual
        meses_año = [{'es_actual': m['key'] == fecha_actual.strftime('%Y-%m'), **m} for m in get_meses_del_año(año_actual)]
        
        if request.method == 'POST':
            # Obtener el mes del formulario
            mes_formulario = request.form.get('mes_seleccionado', mes_seleccionado)
            
            # Procesar metas enviadas
            metas_data = {}
            metas_ipn_data = {}
            total_meta = 0
            total_meta_ipn = 0
            
            for linea in lineas_comerciales_estaticas:
                # Procesar Meta Total
                meta_value = request.form.get(f"meta_{linea['id']}", '0')
                try:
                    clean_value = str(meta_value).replace(',', '') if meta_value else '0'
                    valor = float(clean_value) if clean_value else 0.0
                    metas_data[linea['id']] = valor
                    total_meta += valor
                except (ValueError, TypeError):
                    metas_data[linea['id']] = 0.0
                
                # Procesar Meta IPN
                meta_ipn_value = request.form.get(f"meta_ipn_{linea['id']}", '0')
                try:
                    clean_value_ipn = str(meta_ipn_value).replace(',', '') if meta_ipn_value else '0'
                    valor_ipn = float(clean_value_ipn) if clean_value_ipn else 0.0
                    metas_ipn_data[linea['id']] = valor_ipn
                    total_meta_ipn += valor_ipn
                except (ValueError, TypeError):
                    metas_ipn_data[linea['id']] = 0.0
            
            # --- Procesar Meta ECOMMERCE (campo estático) ---
            # Procesar Meta Total ECOMMERCE
            meta_ecommerce_value = request.form.get('meta_ecommerce', '0')
            try:
                clean_value_ecommerce = str(meta_ecommerce_value).replace(',', '') if meta_ecommerce_value else '0'
                valor_ecommerce = float(clean_value_ecommerce) if clean_value_ecommerce else 0.0
                metas_data['ecommerce'] = valor_ecommerce
                total_meta += valor_ecommerce
            except (ValueError, TypeError):
                metas_data['ecommerce'] = 0.0

            # Procesar Meta IPN ECOMMERCE
            meta_ipn_ecommerce_value = request.form.get('meta_ipn_ecommerce', '0')
            try:
                clean_value_ipn_ecommerce = str(meta_ipn_ecommerce_value).replace(',', '') if meta_ipn_ecommerce_value else '0'
                valor_ipn_ecommerce = float(clean_value_ipn_ecommerce) if clean_value_ipn_ecommerce else 0.0
                metas_ipn_data['ecommerce'] = valor_ipn_ecommerce
                total_meta_ipn += valor_ipn_ecommerce
            except (ValueError, TypeError):
                metas_ipn_data['ecommerce'] = 0.0
            # --- Fin del procesamiento de ECOMMERCE ---

            # Encontrar el nombre del mes
            mes_obj = next((m for m in meses_año if m['key'] == mes_formulario), None)
            mes_nombre_formulario = mes_obj['nombre'] if mes_obj else ""
            
            metas_historicas = gs_manager.read_metas_por_linea()
            metas_historicas[mes_formulario] = {
                'metas': metas_data,
                'metas_ipn': metas_ipn_data,
                'total': total_meta,
                'total_ipn': total_meta_ipn,
                'mes_nombre': mes_nombre_formulario
            }
            gs_manager.write_metas_por_linea(metas_historicas)
            
            flash(f'Metas guardadas exitosamente para {mes_nombre_formulario}. Total: $ {total_meta:,.0f}', 'success')
            
            # Actualizar mes seleccionado después de guardar
            mes_seleccionado = mes_formulario
        
        # Obtener todas las metas históricas
        metas_historicas = gs_manager.read_metas_por_linea()
        
        # Obtener metas y total del mes seleccionado
        metas_actuales = metas_historicas.get(mes_seleccionado, {}).get('metas', {})
        metas_ipn_actuales = metas_historicas.get(mes_seleccionado, {}).get('metas_ipn', {})
        total_actual = sum(metas_actuales.values()) if metas_actuales else 0
        total_ipn_actual = sum(metas_ipn_actuales.values()) if metas_ipn_actuales else 0
        
        # Encontrar el nombre del mes seleccionado
        mes_obj_seleccionado = next((m for m in meses_año if m['key'] == mes_seleccionado), meses_año[fecha_actual.month - 1])
        
        return render_template('meta.html',
                             lineas_comerciales=lineas_comerciales_estaticas,
                             metas_actuales=metas_actuales,
                             metas_ipn_actuales=metas_ipn_actuales,
                             metas_historicas=metas_historicas,
                             meses_año=meses_año,
                             mes_seleccionado=mes_seleccionado,
                             mes_nombre=mes_obj_seleccionado['nombre'],
                             total_actual=total_actual,
                             total_ipn_actual=total_ipn_actual,
                             fecha_actual=fecha_actual)
    
    except Exception as e:
        flash(f'Error al procesar metas: {str(e)}', 'danger')
        return render_template('meta.html',
                             lineas_comerciales=[],
                             metas_actuales={},
                             metas_ipn_actuales={},
                             metas_historicas={},
                             meses_año=[],
                             mes_seleccionado="",
                             mes_nombre="",
                             total_actual=0,
                             total_ipn_actual=0,
                             fecha_actual=datetime.now())

@app.route('/export/excel/sales')
def export_excel_sales():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        # Obtener filtros de la URL
        # Para el dashboard, solo necesitamos el cliente_id. Las fechas se manejan por defecto (año actual).
        cliente_id = request.args.get('cliente_id')
        
        # Convertir a tipos apropiados
        partner_id = None
        if cliente_id:
            try:
                partner_id = int(cliente_id)
            except (ValueError, TypeError):
                partner_id = None
        
        # Obtener datos de ventas para el cliente seleccionado (o todos si no hay selección)
        # Usando las fechas por defecto del año actual, igual que el dashboard.
        date_from = f"{datetime.now().year}-01-01"
        date_to = f"{datetime.now().year}-12-31"
        
        # CORRECCIÓN: Desempaquetar la tupla devuelta por get_sales_lines
        sales_data_raw, _ = data_manager.get_sales_lines(
            date_from=date_from, 
            date_to=date_to, 
            partner_id=partner_id,
            page=1,
            per_page=99999 # Sin límite para exportar todo
        )
        
        # Crear DataFrame
        df = pd.DataFrame(sales_data_raw)
        
        # Seleccionar y renombrar las columnas según lo solicitado
        column_mapping = {
            'pedido': 'Pedido',
            'factura': 'Factura',
            'cliente': 'Cliente',
            'pais': 'País',
            'fecha': 'Fecha',
            'mes': 'Mes',
            'codigo_odoo': 'Código Odoo',
            'producto': 'Producto',
            'descripcion': 'Descripcion',
            'linea_comercial': 'Linea Comercial',
            'clasificacion_farmacologica': 'Clasificación farmacológica',
            'formas_farmaceuticas': 'Formas Farmacéuticas',
            'via_administracion': 'Vía de Administración',
            'linea_produccion': 'Línea de producción',
            'cantidad_facturada': 'Cantidad Facturada',
            'precio_unitario': 'Precio unitario ($)',
            'amount_currency': 'Total ($)' # Usar amount_currency para el total
        }
        
        # Filtrar el DataFrame para que solo contenga las columnas deseadas
        df_export = df[list(column_mapping.keys())].copy()
        
        # Renombrar las columnas
        df_export.rename(columns=column_mapping, inplace=True)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='Detalle_Ventas_Internacional', index=False)

            # Aplicar estilo de tabla
            workbook = writer.book
            worksheet = writer.sheets['Detalle_Ventas_Internacional']
            
            (max_row, max_col) = df_export.shape
            # El rango de la tabla es desde A1 hasta la última celda con datos
            table_ref = f"A1:{chr(ord('A') + max_col - 1)}{max_row + 1}"
            table = Table(displayName="VentasFacturadas", ref=table_ref)
            style = TableStyleInfo(name="TableStyleLight9", showFirstColumn=False, showLastColumn=False, showRowStripes=True, showColumnStripes=False)
            table.tableStyleInfo = style
            worksheet.add_table(table)

        output.seek(0)
        
        # Generar nombre de archivo con fecha en formato dd-mm-yyyy
        timestamp = datetime.now().strftime("%d-%m-%Y")
        filename = f'Pedidos_Facturados_{timestamp}.xlsx'
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Error al exportar datos: {str(e)}', 'danger')
        return redirect(url_for('sales'))

@app.route('/export/excel/pending')
def export_excel_pending():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        # Obtener el cliente_id de la URL
        cliente_id = request.args.get('cliente_id')
        
        partner_id = None
        if cliente_id:
            try:
                partner_id = int(cliente_id)
            except (ValueError, TypeError):
                partner_id = None
        
        # Obtener datos de pedidos pendientes para el cliente seleccionado
        # CORRECCIÓN: Desempaquetar la tupla y pedir todos los registros
        pending_data_raw, _ = data_manager.get_pending_orders(
            filters={'partner_id': partner_id},
            page=1,
            per_page=99999 # Sin límite para exportar todo
        )
        
        if not pending_data_raw:
            flash('No hay datos pendientes de facturar para exportar.', 'info')
            return redirect(url_for('dashboard', cliente_id=cliente_id))

        # Crear DataFrame
        df = pd.DataFrame(pending_data_raw)
        
        # Seleccionar y renombrar las columnas para el export
        # Usamos un subconjunto de las columnas disponibles en pending_data
        column_mapping = {
            'pedido': 'Pedido', 'cliente': 'Cliente', 'pais': 'País',
            'fecha': 'Fecha Pedido', 'codigo_odoo': 'Código Odoo',
            'producto': 'Producto', 'descripcion': 'Descripcion',
            'linea_comercial': 'Linea Comercial',
            # --- NUEVAS COLUMNAS ---
            'clasificacion_farmacologica': 'Clasificación farmacológica',
            'formas_farmaceuticas': 'Formas Farmacéuticas',
            'via_administracion': 'Vía de Administración',
            'linea_produccion': 'Línea de producción',
            # --- FIN NUEVAS COLUMNAS ---
            'cantidad_pendiente': 'Cantidad Pendiente', 'precio_unitario': 'Precio unitario ($)',
            'total_pendiente': 'Total Pendiente ($)'
        }
        
        df_export = df[list(column_mapping.keys())].copy()
        df_export.rename(columns=column_mapping, inplace=True)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='Pendiente_Facturar', index=False)

            # Aplicar estilo de tabla
            workbook = writer.book
            worksheet = writer.sheets['Pendiente_Facturar']

            (max_row, max_col) = df_export.shape
            table_ref = f"A1:{chr(ord('A') + max_col - 1)}{max_row + 1}"
            table = Table(displayName="PendienteFacturar", ref=table_ref)
            style = TableStyleInfo(name="TableStyleLight9", showFirstColumn=False, showLastColumn=False, showRowStripes=True, showColumnStripes=False)
            table.tableStyleInfo = style
            worksheet.add_table(table)

        output.seek(0)
        
        timestamp = datetime.now().strftime("%d-%m-%Y")
        filename = f'Pedidos_Pendientes_{timestamp}.xlsx'
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Error al exportar datos pendientes: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/metas_vendedor', methods=['GET', 'POST'])
def metas_vendedor():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Obtener meses y líneas comerciales para los filtros
    fecha_actual = datetime.now()
    año_actual = fecha_actual.year
    meses_disponibles = get_meses_del_año(año_actual)
    lineas_comerciales_estaticas = [
        {'nombre': 'PETMEDICA', 'id': 'petmedica'},
        {'nombre': 'AGROVET', 'id': 'agrovet'},
        {'nombre': 'PET NUTRISCIENCE', 'id': 'pet_nutriscience'},
        {'nombre': 'AVIVET', 'id': 'avivet'},
        {'nombre': 'OTROS', 'id': 'otros'},
        {'nombre': 'GENVET', 'id': 'genvet'},
        {'nombre': 'INTERPET', 'id': 'interpet'},
    ]
    equipos_definidos = [
        {'id': 'petmedica', 'nombre': 'PETMEDICA'},
        {'id': 'agrovet', 'nombre': 'AGROVET'},
        {'id': 'pet_nutriscience', 'nombre': 'PET NUTRISCIENCE'},
        {'id': 'avivet', 'nombre': 'AVIVET'},
        {'id': 'otros', 'nombre': 'OTROS'},
        {'id': 'interpet', 'nombre': 'INTERPET'},
    ]

    # Determinar mes y línea seleccionados (desde form o por defecto)
    mes_seleccionado = request.form.get('mes_seleccionado', fecha_actual.strftime('%Y-%m'))
    linea_seleccionada = request.form.get('linea_seleccionada', lineas_comerciales_estaticas[0]['id'])

    if request.method == 'POST':
        # --- 1. GUARDAR ASIGNACIONES DE EQUIPOS ---
        equipo_actualizado_id = request.form.get('guardar_equipo') # Para el mensaje flash
        todos_los_vendedores_para_guardar = data_manager.get_all_sellers()
        equipos_guardados = gs_manager.read_equipos()

        for equipo in equipos_definidos:
            campo_vendedores = f'vendedores_{equipo["id"]}'
            if campo_vendedores in request.form:
                vendedores_str = request.form.get(campo_vendedores, '')
                if vendedores_str:
                    vendedores_ids = [int(vid) for vid in vendedores_str.split(',') if vid.isdigit()]
                    equipos_guardados[equipo['id']] = vendedores_ids
                else:
                    equipos_guardados[equipo['id']] = []
        gs_manager.write_equipos(equipos_guardados, todos_los_vendedores_para_guardar)

        # --- 2. GUARDAR TODAS LAS METAS (ESTRUCTURA PIVOT) ---
        metas_vendedores_historicas = gs_manager.read_metas()
        
        for equipo in equipos_definidos:
            equipo_id = equipo['id']
            if equipo_id not in metas_vendedores_historicas:
                metas_vendedores_historicas[equipo_id] = {}

            vendedores_ids_en_equipo = equipos_guardados.get(equipo_id, [])
            for vendedor_id in vendedores_ids_en_equipo:
                vendedor_id_str = str(vendedor_id)
                if vendedor_id_str not in metas_vendedores_historicas[equipo_id]:
                    metas_vendedores_historicas[equipo_id][vendedor_id_str] = {}

                for mes in meses_disponibles:
                    mes_key = mes['key']
                    # No es necesario crear la clave del mes aquí, se crea si hay datos

                    meta_valor_str = request.form.get(f'meta_{equipo_id}_{vendedor_id_str}_{mes_key}')
                    meta_ipn_valor_str = request.form.get(f'meta_ipn_{equipo_id}_{vendedor_id_str}_{mes_key}')

                    # Convertir a float, manejar valores vacíos como None para no guardar ceros innecesarios
                    meta = float(meta_valor_str) if meta_valor_str else None
                    meta_ipn = float(meta_ipn_valor_str) if meta_ipn_valor_str else None

                    if meta is not None or meta_ipn is not None:
                        # Si la clave del mes no existe, créala
                        if mes_key not in metas_vendedores_historicas[equipo_id][vendedor_id_str]:
                             metas_vendedores_historicas[equipo_id][vendedor_id_str][mes_key] = {}
                        metas_vendedores_historicas[equipo_id][vendedor_id_str][mes_key] = {
                            'meta': meta or 0.0,
                            'meta_ipn': meta_ipn or 0.0
                        }
                    # Si ambos son None y la clave existe, se elimina para limpiar el JSON
                    elif mes_key in metas_vendedores_historicas[equipo_id][vendedor_id_str]:
                        del metas_vendedores_historicas[equipo_id][vendedor_id_str][mes_key]

        gs_manager.write_metas(metas_vendedores_historicas)
        
        if equipo_actualizado_id:
            flash(f'Miembros del equipo actualizados. Ahora puedes asignar sus metas.', 'info')
        else:
            flash('Equipos y metas guardados correctamente.', 'success')

        # Redirigir con los parámetros para recargar la página con los filtros correctos
        return redirect(url_for('metas_vendedor'))

    # GET o después de POST
    todos_los_vendedores = data_manager.get_all_sellers()
    vendedores_por_id = {v['id']: v for v in todos_los_vendedores}
    equipos_guardados = gs_manager.read_equipos()

    # Construir la estructura de datos para la plantilla
    equipos_con_vendedores = []
    for equipo_def in equipos_definidos:
        equipo_id = equipo_def['id']
        vendedores_ids = equipos_guardados.get(equipo_id, [])
        vendedores_de_equipo = [vendedores_por_id[vid] for vid in vendedores_ids if vid in vendedores_por_id]
        
        equipos_con_vendedores.append({
            'id': equipo_id,
            'nombre': equipo_def['nombre'],
            'vendedores_ids': [str(vid) for vid in vendedores_ids], # Para Tom-Select
            'vendedores': sorted(vendedores_de_equipo, key=lambda v: v['name']) # Para la tabla
        })

    # Para la vista, pasamos todas las metas cargadas
    metas_guardadas = gs_manager.read_metas()

    return render_template('metas_vendedor.html',
                           meses_disponibles=meses_disponibles,
                           lineas_comerciales=lineas_comerciales_estaticas,
                           equipos_con_vendedores=equipos_con_vendedores,
                           todos_los_vendedores=todos_los_vendedores,
                           metas_guardadas=metas_guardadas)

@app.route('/export/dashboard/details')
def export_dashboard_details():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        # Obtener el mes seleccionado de los parámetros de la URL
        mes_seleccionado = request.args.get('mes')
        if not mes_seleccionado:
            flash('No se especificó un mes para la exportación.', 'danger')
            return redirect(url_for('dashboard'))

        # Calcular fechas para el mes seleccionado
        año_sel, mes_sel = mes_seleccionado.split('-')
        fecha_inicio = f"{año_sel}-{mes_sel}-01"
        ultimo_dia = calendar.monthrange(int(año_sel), int(mes_sel))[1]
        fecha_fin = f"{año_sel}-{mes_sel}-{ultimo_dia}"

        # Obtener datos de ventas reales desde Odoo para ese mes
        sales_data = data_manager.get_sales_lines(
            date_from=fecha_inicio,
            date_to=fecha_fin,
            limit=10000  # Límite alto para exportación
        )

        # Filtrar VENTA INTERNACIONAL (exportaciones), igual que en el dashboard
        sales_data_filtered = []
        for sale in sales_data:
            linea_comercial = sale.get('commercial_line_national_id')
            if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                if 'VENTA INTERNACIONAL' in linea_comercial[1].upper():
                    continue
            
            canal_ventas = sale.get('sales_channel_id')
            if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
                nombre_canal = canal_ventas[1].upper()
                if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                    continue
            
            sales_data_filtered.append(sale)

        # Convertir el balance a positivo para que coincida con el dashboard
        for sale in sales_data_filtered:
            if 'balance' in sale and sale['balance'] is not None:
                sale['balance'] = float(sale['balance']) # Ya viene con el signo correcto desde OdooManager

        # Crear DataFrame de Pandas con los datos filtrados
        df = pd.DataFrame(sales_data_filtered)

        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=f'Detalle Ventas {mes_seleccionado}', index=False)
        output.seek(0)

        # Generar nombre de archivo
        filename = f'detalle_ventas_{mes_seleccionado}.xlsx'

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        flash(f'Error al exportar los detalles del dashboard: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


if __name__ == '__main__':
    # Startup info via logger instead of print
    app.logger.info("Iniciando Dashboard de Ventas Farmacéuticas...")
    app.logger.info("Disponible en: http://127.0.0.1:5000")
    app.logger.info("Usuario: configurado en .env")
    app.run(debug=False)
