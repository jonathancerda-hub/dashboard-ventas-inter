# services/aggregation_service.py
"""
Servicios de agregación de datos de ventas.
Cumple con Single Responsibility Principle (SRP).

Este módulo proporciona servicios especializados para agregar datos de ventas
provenientes de Odoo, organizando la información por cliente, producto y pedido.

Ejemplo de uso:
    >>> from services.aggregation_service import SalesAggregationService
    >>> 
    >>> aggregator = SalesAggregationService()
    >>> sales_data = odoo_manager.get_sales_lines(year=2026)
    >>> 
    >>> # Agregar por cliente
    >>> clientes = aggregator.aggregate_by_client(sales_data)
    >>> # {1: {'cliente_id': 1, 'nombre': 'Cliente A', 'facturado': 50000, ...}}
    >>> 
    >>> # Agregar por producto
    >>> productos = aggregator.aggregate_by_product(sales_data)
    >>> # {'PROD-001': {'codigo': 'PROD-001', 'cantidad': 100, ...}}
    >>> 
    >>> # Agregar por pedido
    >>> pending_data = odoo_manager.get_pending_orders()
    >>> orders = aggregator.aggregate_by_order(sales_data, pending_data)

Patrones de diseño:
    - Single Responsibility: Cada clase/método tiene una sola responsabilidad
    - Dataclass para DTOs: DashboardMetrics es un DTO inmutable
    - Type hints: Toda función tiene tipos explícitos para seguridad

Notas importantes:
    - SIEMPRE usar 'codigo_odoo' como clave única de producto (NO nombre)
    - Los productos se agrupan por código para evitar duplicados
    - El campo 'amount_currency' es el valor canónico para dinero
    - Los partner_id pueden venir como [id, nombre] o como int
"""

from typing import Dict, List, Any, Set
from dataclasses import dataclass


@dataclass
class DashboardMetrics:
    """
    Métricas consolidadas para el dashboard.
    
    Este dataclass es un DTO (Data Transfer Object) que encapsula todas las
    métricas calculadas del dashboard en una estructura inmutable.
    
    Attributes:
        total_facturado: Suma total de ventas facturadas en USD
        total_meta: Suma total de metas asignadas en USD
        porcentaje_cumplimiento: % de cumplimiento de meta (0-100)
        total_pendiente: Total de pedidos pendientes de facturar en USD
        num_clientes: Número único de clientes con ventas
        num_productos: Número único de productos vendidos
        num_pedidos: Número único de pedidos (facturados + pendientes)
    
    Example:
        >>> metrics = DashboardMetrics(
        ...     total_facturado=150000.0,
        ...     total_meta=200000.0,
        ...     porcentaje_cumplimiento=75.0,
        ...     total_pendiente=30000.0,
        ...     num_clientes=25,
        ...     num_productos=150,
        ...     num_pedidos=45
        ... )
        >>> print(f"Cumplimiento: {metrics.porcentaje_cumplimiento}%")
    """
    total_facturado: float
    total_meta: float
    porcentaje_cumplimiento: float
    total_pendiente: float
    num_clientes: int
    num_productos: int
    num_pedidos: int = 0


class SalesAggregationService:
    """
    Servicio para agregación de datos de ventas.
    
    Proporciona métodos optimizados para consolidar y agregar datos de ventas
    provenientes de Odoo, organizando la información por diferentes dimensiones
    (cliente, producto, pedido).
    
    Este servicio es stateless y puede ser reutilizado en múltiples contextos.
    
    Methods:
        aggregate_by_client: Agrupa ventas por cliente
        aggregate_by_product: Agrupa ventas por código de producto
        aggregate_by_order: Agrupa ventas y pendientes por pedido
        calculate_cumplimiento: Calcula porcentaje de cumplimiento de meta
    
    Example:
        >>> service = SalesAggregationService()
        >>> clientes = service.aggregate_by_client(sales_data)
        >>> 
        >>> # Ordenar clientes por facturación
        >>> top_clientes = sorted(
        ...     clientes.values(),
        ...     key=lambda c: c['facturado'],
        ...     reverse=True
        ... )[:10]
    
    Notes:
        - Todos los métodos son seguros con datos vacíos (devuelven {} o 0)
        - Los IDs de Odoo pueden venir como [id, name] o como int
        - amount_currency es el campo canónico para valores monetarios
    """
    
    def aggregate_by_client(self, sales_data: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Agrupa ventas por cliente.
        
        Args:
            sales_data: Lista de ventas desde Odoo
        
        Returns:
            Dict[cliente_id, Dict]: Datos agregados por cliente
        """
        clientes = {}
        
        for sale in sales_data:
            # Obtener cliente_id (puede venir como lista [id, nombre] o int)
            partner_id = sale.get('partner_id')
            if isinstance(partner_id, list) and len(partner_id) > 0:
                cliente_id = partner_id[0]
                cliente_nombre = partner_id[1] if len(partner_id) > 1 else ''
            elif isinstance(partner_id, int):
                cliente_id = partner_id
                cliente_nombre = sale.get('partner_name', '')
            else:
                continue  # Skip si no hay ID válido
            
            if cliente_id not in clientes:
                clientes[cliente_id] = {
                    'cliente_id': cliente_id,
                    'nombre': cliente_nombre,
                    'facturado': 0,
                    'pendiente': 0,
                    'pedidos': set()
                }
            
            # Sumar facturado
            clientes[cliente_id]['facturado'] += sale.get('amount_currency', 0)
            
            # Agregar pedido único
            pedido = sale.get('pedido') or sale.get('order_id')
            if pedido:
                if isinstance(pedido, list) and len(pedido) > 0:
                    pedido_id = pedido[0]
                else:
                    pedido_id = pedido
                clientes[cliente_id]['pedidos'].add(pedido_id)
        
        # Convertir set a count
        for cliente in clientes.values():
            cliente['num_pedidos'] = len(cliente['pedidos'])
            del cliente['pedidos']
        
        return clientes
    
    def aggregate_by_product(self, sales_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Agrupa ventas por producto (usando código de producto).
        
        Args:
            sales_data: Lista de ventas desde Odoo
        
        Returns:
            Dict[codigo_producto, Dict]: Datos agregados por producto
        """
        productos = {}
        
        for sale in sales_data:
            # CRÍTICO: usar codigo_odoo como clave única (NO nombre de producto)
            codigo = sale.get('codigo_odoo') or sale.get('default_code', '')
            if not codigo:
                continue  # Skip productos sin código
            
            if codigo not in productos:
                productos[codigo] = {
                    'codigo': codigo,
                    'nombre': sale.get('producto', ''),
                    'linea_comercial': sale.get('linea_comercial', ''),
                    'cantidad': 0,
                    'facturado': 0,
                    'pendiente': 0
                }
            
            # Agregar cantidades
            productos[codigo]['cantidad'] += sale.get('cantidad_facturada', 0)
            productos[codigo]['facturado'] += sale.get('amount_currency', 0)
        
        return productos
    
    def aggregate_by_order(
        self, 
        sales_data: List[Dict[str, Any]], 
        pending_data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Agrupa ventas y pedidos pendientes por número de pedido.
        
        Args:
            sales_data: Datos facturados
            pending_data: Datos pendientes de facturación
        
        Returns:
            Dict[pedido_num, Dict]: Datos agregados por pedido
        """
        orders = {}
        
        # Procesar facturado
        for sale in sales_data:
            pedido = sale.get('pedido') or sale.get('order_id')
            if not pedido:
                continue
            
            if isinstance(pedido, list) and len(pedido) > 0:
                pedido_num = pedido[1] if len(pedido) > 1 else str(pedido[0])
                pedido_id = pedido[0]
            else:
                pedido_num = str(pedido)
                pedido_id = pedido
            
            if pedido_num not in orders:
                # Obtener cliente
                partner_id = sale.get('partner_id')
                if isinstance(partner_id, list) and len(partner_id) > 0:
                    cliente_id = partner_id[0]
                    cliente_nombre = partner_id[1] if len(partner_id) > 1 else ''
                else:
                    cliente_id = partner_id
                    cliente_nombre = sale.get('partner_name', '')
                
                orders[pedido_num] = {
                    'pedido': pedido_num,
                    'pedido_id': pedido_id,
                    'cliente': cliente_nombre,
                    'cliente_id': cliente_id,
                    'facturado': 0,
                    'pendiente': 0
                }
            
            orders[pedido_num]['facturado'] += sale.get('amount_currency', 0)
        
        # Procesar pendiente
        for pending in pending_data:
            pedido = pending.get('pedido') or pending.get('order_name')
            if not pedido:
                continue
            
            if isinstance(pedido, list) and len(pedido) > 0:
                pedido_num = pedido[1] if len(pedido) > 1 else str(pedido[0])
                pedido_id = pedido[0]
            else:
                pedido_num = str(pedido)
                pedido_id = pedido
            
            if pedido_num not in orders:
                # Obtener cliente
                partner_id = pending.get('partner_id') or pending.get('cliente_id')
                if isinstance(partner_id, list) and len(partner_id) > 0:
                    cliente_id = partner_id[0]
                    cliente_nombre = partner_id[1] if len(partner_id) > 1 else ''
                else:
                    cliente_id = partner_id
                    cliente_nombre = pending.get('partner_name', '') or pending.get('cliente', '')
                
                orders[pedido_num] = {
                    'pedido': pedido_num,
                    'pedido_id': pedido_id,
                    'cliente': cliente_nombre,
                    'cliente_id': cliente_id,
                    'facturado': 0,
                    'pendiente': 0
                }
            
            orders[pedido_num]['pendiente'] += pending.get('total_pendiente', 0)
        
        # Calcular total y porcentaje
        for order in orders.values():
            order['total'] = order['facturado'] + order['pendiente']
            if order['total'] > 0:
                order['porcentaje'] = round(order['facturado'] / order['total'] * 100, 2)
            else:
                order['porcentaje'] = 0
        
        return orders
    
    def aggregate_by_month(self, sales_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Agrupa ventas por mes.
        
        Args:
            sales_data: Lista de ventas con fechas
        
        Returns:
            Dict[mes_YYYY-MM, monto]: Ventas por mes
        """
        months = {}
        
        for sale in sales_data:
            fecha = sale.get('fecha') or sale.get('date')
            if not fecha:
                continue
            
            # Extraer año-mes (formato: YYYY-MM)
            if isinstance(fecha, str) and len(fecha) >= 7:
                mes_key = fecha[:7]  # YYYY-MM
            else:
                continue
            
            if mes_key not in months:
                months[mes_key] = 0
            
            months[mes_key] += sale.get('amount_currency', 0)
        
        return months


class MetricsCalculationService:
    """Servicio para cálculo de KPIs y métricas consolidadas."""
    
    def calculate_dashboard_metrics(
        self,
        sales_data: List[Dict[str, Any]],
        pending_data: List[Dict[str, Any]],
        metas: Dict[str, Any]
    ) -> DashboardMetrics:
        """
        Calcula todas las métricas consolidadas del dashboard.
        
        Args:
            sales_data: Datos facturados
            pending_data: Datos pendientes
            metas: Diccionario de metas por cliente
        
        Returns:
            DashboardMetrics: Métricas calculadas
        """
        # Total facturado
        total_facturado = sum(s.get('amount_currency', 0) for s in sales_data)
        
        # Total pendiente
        total_pendiente = sum(p.get('total_pendiente', 0) for p in pending_data)
        
        # Calcular meta total
        # metas tiene estructura: {cliente_id: {mes: valor}}
        total_meta = 0
        if isinstance(metas, dict):
            for cliente_metas in metas.values():
                if isinstance(cliente_metas, dict):
                    total_meta += sum(cliente_metas.values())
                elif isinstance(cliente_metas, (int, float)):
                    total_meta += cliente_metas
        
        # Porcentaje de cumplimiento
        porcentaje = (total_facturado / total_meta * 100) if total_meta > 0 else 0
        
        # Contar clientes únicos
        clientes_unicos: Set[int] = set()
        for sale in sales_data:
            partner_id = sale.get('partner_id')
            if isinstance(partner_id, list) and len(partner_id) > 0:
                clientes_unicos.add(partner_id[0])
            elif isinstance(partner_id, int):
                clientes_unicos.add(partner_id)
        
        # Contar productos únicos (por código)
        productos_unicos: Set[str] = set()
        for sale in sales_data:
            codigo = sale.get('codigo_odoo') or sale.get('default_code')
            if codigo:
                productos_unicos.add(codigo)
        
        # Contar pedidos únicos
        pedidos_unicos: Set[Any] = set()
        for sale in sales_data:
            pedido = sale.get('pedido') or sale.get('order_id')
            if pedido:
                if isinstance(pedido, list) and len(pedido) > 0:
                    pedidos_unicos.add(pedido[0])
                else:
                    pedidos_unicos.add(pedido)
        
        return DashboardMetrics(
            total_facturado=round(total_facturado, 2),
            total_meta=round(total_meta, 2),
            porcentaje_cumplimiento=round(porcentaje, 2),
            total_pendiente=round(total_pendiente, 2),
            num_clientes=len(clientes_unicos),
            num_productos=len(productos_unicos),
            num_pedidos=len(pedidos_unicos)
        )


class ChartDataService:
    """Servicio para preparación de datos de gráficos."""
    
    def prepare_orders_chart_data(
        self,
        sales_data: List[Dict[str, Any]],
        pending_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prepara datos para gráfico de avance por pedido.
        Incluye facturado + pendiente por pedido.
        
        Args:
            sales_data: Datos facturados
            pending_data: Datos pendientes
        
        Returns:
            List[Dict]: Lista de pedidos con facturado, pendiente y porcentaje
        """
        aggregation_service = SalesAggregationService()
        orders_dict = aggregation_service.aggregate_by_order(sales_data, pending_data)
        
        # Convertir a lista y ordenar por total descendente
        orders_list = list(orders_dict.values())
        orders_list.sort(key=lambda x: x.get('total', 0), reverse=True)
        
        return orders_list
    
    def prepare_client_chart_data(
        self,
        sales_data: List[Dict[str, Any]],
        metas: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prepara datos para gráfico de ventas vs meta por cliente.
        
        Args:
            sales_data: Datos facturados
            metas: Metas por cliente
        
        Returns:
            List[Dict]: Lista de clientes con facturado, meta y porcentaje
        """
        aggregation_service = SalesAggregationService()
        clientes_dict = aggregation_service.aggregate_by_client(sales_data)
        
        # Agregar metas y calcular porcentaje
        clientes_list = []
        for cliente_id, cliente_data in clientes_dict.items():
            # Obtener meta del cliente
            meta_cliente = 0
            if isinstance(metas, dict) and str(cliente_id) in metas:
                cliente_metas = metas[str(cliente_id)]
                if isinstance(cliente_metas, dict):
                    meta_cliente = sum(cliente_metas.values())
                elif isinstance(cliente_metas, (int, float)):
                    meta_cliente = cliente_metas
            
            # Calcular porcentaje
            if meta_cliente > 0:
                porcentaje = round(cliente_data['facturado'] / meta_cliente * 100, 2)
            else:
                porcentaje = 0
            
            clientes_list.append({
                'cliente_id': cliente_id,
                'nombre': cliente_data['nombre'],
                'facturado': cliente_data['facturado'],
                'meta': meta_cliente,
                'porcentaje': porcentaje,
                'num_pedidos': cliente_data['num_pedidos']
            })
        
        # Ordenar por facturado descendente
        clientes_list.sort(key=lambda x: x['facturado'], reverse=True)
        
        return clientes_list
    
    def prepare_product_chart_data(
        self,
        sales_data: List[Dict[str, Any]],
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Prepara datos para gráfico de productos más vendidos.
        
        Args:
            sales_data: Datos facturados
            top_n: Número de productos a retornar
        
        Returns:
            List[Dict]: Top N productos por ventas
        """
        aggregation_service = SalesAggregationService()
        productos_dict = aggregation_service.aggregate_by_product(sales_data)
        
        # Convertir a lista y ordenar por facturado descendente
        productos_list = list(productos_dict.values())
        productos_list.sort(key=lambda x: x['facturado'], reverse=True)
        
        # Retornar top N
        return productos_list[:top_n]
