# Code Review Arquitectónico — Dashboard-Ventas-INTER (Architectural Code Review)
## Análisis Senior: SOLID, Seguridad, Rendimiento, Mantenibilidad (Senior Analysis: SOLID, Security, Performance, Maintainability)

> 📅 **Última actualización (Last update)**: 26 de marzo de 2026  
> 📊 **Progreso (Progress)**: 7.2/10  
> ✅ **Fortalezas (Strengths)**: OAuth2 implementado, Migración exitosa a Supabase, Caching funcional, Separación en módulos database/, Servicios de validación/agregación/logging implementados, Headers de seguridad y rate limiting configurados, CDN con SRI, Validación estricta en exports, Docstrings OWASP-compliant  
> 🔴 **Crítico (Critical)**: Función dashboard() +1,200 líneas (refactorización planificada), N+1 queries en Odoo  
> 🔄 **Siguiente fase (Next phase)**: Q2 2026 - Refactorización dashboard() y tests, Q3 2026 - Monitoreo y optimización

---

## Resumen Ejecutivo (Executive Summary)

**Puntuación General (Overall Score): 7.2/10**

| Área (Area) | Puntuación (Score) | Estado (Status) | Prioridad (Priority) | Cambios (Changes) |
|-------------|---------------------|-----------------|----------------------|-------------------|
| Principios SOLID (SOLID Principles) | 4/10 | 🔴 | Alta | ⬆️ |
| Seguridad OWASP (OWASP Security) | 8/10 | ✅ | Alta | ⬆️⬆️ |
| Rendimiento (Performance) | 5/10 | ⚠️ | Alta | = |
| Mantenibilidad (Maintainability) | 6/10 | ⚠️ | Media | ⬆️ |
| Arquitectura (Architecture) | 7/10 | ⚠️ | Alta | ⬆️ |

### ✅ Mejoras Implementadas Recientemente (Recent Improvements)

1. **Migración Supabase completada** (Marzo 2026)
   - 60 registros de metas migrados desde Google Sheets
   - Tabla `metas_clientes` con RLS y constraints
   - Reducción de latencia: ~2s → ~200ms

2. **Reorganización de estructura** (Marzo 2026)
   - Creación de carpetas: `database/`, `migrations/`, `scripts/`
   - Separación de responsabilidades en managers

3. **Campos de trazabilidad agregados** (Marzo 2026)
   - Lote y fecha de vencimiento en exports de ventas facturadas
   - Integración con módulo stock de Odoo

4. **Servicios de validación y agregación** (Marzo 2026)
   - `ValidationService`: Validación centralizada de inputs con sanitización
   - `AggregationService`: Lógica de agregación reutilizable para clientes, productos y pedidos
   - Mejora en mantenibilidad y testabilidad

5. **Headers de seguridad implementados** (Marzo 2026)
   - 10 headers OWASP (X-Frame-Options, CSP, HSTS, etc.)
   - Middleware aplicado a todas las respuestas
   - Cookie SAMESITE cambiado de 'Lax' a 'Strict'

6. **Rate Limiting configurado** (Marzo 2026)
   - 6 rutas críticas protegidas (login, dashboard, exports)
   - Límites: 5 req/min (login), 10 req/min (exports), 30 req/min (dashboard)
   - Redis como backend de almacenamiento

7. **Security Logging implementado** (Marzo 2026)
   - `SecurityLogger`: Sistema de auditoría de eventos de seguridad
   - 8 eventos capturados (login, logout, access denied, validation errors, exports)
   - Logs persistentes en `logs/security.log` y `logs/security_critical.log`

8. **Validación estricta en exports** (Marzo 2026)
   - 3 rutas de exportación protegidas con límites de registros (15,000 máx)
   - Validación de rangos de fechas (máx 5 años atrás)
   - Flash warnings para resultados truncados
   - Prevención de DoS por exportaciones masivas

9. **CDN con Subresource Integrity (SRI)** (Marzo 2026)
   - 9 recursos CDN asegurados con integrity hashes
   - Protección contra compromiso de CDN (XSS supply-chain)
   - Templates actualizados: base.html, dashboard_clean.html, login.html, equipo_ventas.html
   - Compliance con OWASP ASVS V14.2

10. **Docstrings OWASP-compliant** (Marzo 2026)
    - ~250 líneas de documentación profesional agregadas
    - Referencias a OWASP Logging Cheat Sheet, NIST SP 800-92, CWE-778, CWE-20
    - Ejemplos de uso y comandos bash para análisis de logs
    - Servicios documentados: ValidationService, AggregationService, SecurityLogger

### 🔴 Issues Críticos Priorizados (Prioritized Critical Issues)

1. **🔴 CRÍTICO** - Violación masiva de SRP en `app.py::dashboard()` [líneas 521-1748]
   - 1,227 líneas en una sola función
   - Mezcla routing + agregación + KPIs + caché + renderizado
   - **Impacto**: Imposible de testear, mantener o escalar

2. **🔴 CRÍTICO** - N+1 queries en `odoo_manager.py::get_sales_lines()` [líneas 453-730]
   - 1 query principal + 4 fetches relacionados × N registros
   - Con 1,000 líneas = 5,000 llamadas RPC
   - **Impacto**: Timeout (30s), latencia extrema

3. **✅ RESUELTO** - ~~Falta validación de inputs en todas las rutas~~
   - ✅ `ValidationService` implementado con try-catch y sanitización
   - ✅ Validación centralizada en rutas críticas (dashboard, exports)
   - ✅ Error messages genéricos (sin exponer detalles internos)
   - **Resolución**: Marzo 2026 - Task 3, 4, 5

4. **✅ RESUELTO** - ~~Headers de seguridad ausentes~~
   - ✅ 10 headers OWASP implementados (middleware)
   - ✅ X-Frame-Options: DENY, CSP configurado, HSTS habilitado
   - ✅ Rate limiting en 6 rutas críticas
   - **Resolución**: Marzo 2026 - Task 1, 8

5. **✅ RESUELTO** - ~~Cookie SAMESITE='Lax' débil~~
   - ✅ Cambiado a SAMESITE='Strict'
   - ✅ Security logging para eventos de autenticación
   - **Resolución**: Marzo 2026 - Task 2, 9

---

## 1️⃣ Principios SOLID (SOLID Principles)

### Puntuación General: 3/10

---

### 1.1 Single Responsibility Principle (SRP) — 2/10 ❌

**Estado Actual (Current State)**: **VIOLACIÓN MASIVA**

#### Archivos que Violan SRP (Files Violating SRP)

##### 🔴 **app.py::dashboard()** [líneas 521-1748]

**Problema (Problem)**:
```python
# Línea 521-1748 (1,227 líneas)
@app.route('/dashboard')
def dashboard():
    # 1. Autenticación y sesiones (líneas 521-550)
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # 2. Validación y filtros (líneas 551-600)
    año = request.args.get('año', datetime.now().year)
    linea = request.args.get('linea', '')
    
    # 3. Construcción de cache keys (líneas 601-620)
    cache_key = f"dashboard_{año}_{linea}_{salesperson_id}"
    
    # 4. Gestión de caché (líneas 621-650)
    cached_data = cache.get(cache_key)
    
    # 5. Queries a Odoo (líneas 651-900)
    sales_data = data_manager.get_sales_lines(...)
    pending_data = data_manager.get_pending_orders(...)
    
    # 6. Agregaciones por cliente (líneas 901-1050)
    for sale in sales_data:
        cliente_id = sale['partner_id']
        # Agregación compleja...
    
    # 7. Agregaciones por producto (líneas 1051-1200)
    productos_dict = {}
    for sale in sales_data:
        # Más agregaciones...
    
    # 8. Cálculo de KPIs (líneas 1201-1350)
    total_facturado = sum(...)
    total_meta = ...
    porcentaje_cumplimiento = ...
    
    # 9. Preparación de datos para charts (líneas 1351-1550)
    orders_chart_data = []
    productos_chart_data = []
    
    # 10. Construcción de contexto (líneas 1551-1680)
    context = {
        'sales_data': sales_data,
        'pending_data': pending_data,
        # ... 50+ variables más
    }
    
    # 11. Almacenamiento en caché (líneas 1681-1720)
    cache.set(cache_key, context, timeout=600)
    
    # 12. Renderizado (líneas 1721-1748)
    return render_template('dashboard_clean.html', **context)
```

**Responsabilidades Detectadas** (12 en total):
1. ✅ Autenticación y control de acceso
2. ✅ Validación de parámetros de entrada
3. ✅ Gestión de caché (construcción de keys, get/set)
4. ✅ Orquestación de queries a Odoo
5. ✅ Transformación de datos de ventas
6. ✅ Agregación por cliente
7. ✅ Agregación por producto
8. ✅ Cálculo de KPIs y métricas
9. ✅ Preparación de datos para visualizaciones
10. ✅ Carga de metas desde Supabase
11. ✅ Construcción de contexto de vista
12. ✅ Renderizado de plantilla

**Complejidad Ciclomática Estimada**: > 50 (crítico, límite recomendado: 10)

---

#### ✅ Refactor Sugerido (Suggested Refactor)

**Paso 1: Crear capa de servicios**

```python
# services/dashboard_service.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DashboardFilters:
    """Filtros para el dashboard"""
    año: int
    linea: str
    salesperson_id: Optional[int]
    cliente_id: Optional[int]

@dataclass
class DashboardMetrics:
    """Métricas clave del dashboard"""
    total_facturado: float
    total_meta: float
    porcentaje_cumplimiento: float
    total_pendiente: float
    num_clientes: int
    num_productos: int

class SalesAggregationService:
    """Servicio para agregación de datos de ventas"""
    
    def aggregate_by_client(self, sales_data: List[Dict]) -> Dict:
        """Agrupa ventas por cliente"""
        clientes = {}
        for sale in sales_data:
            cliente_id = sale.get('partner_id', [0])[0]
            if cliente_id not in clientes:
                clientes[cliente_id] = {
                    'nombre': sale.get('partner_name', ''),
                    'facturado': 0,
                    'pedidos': set()
                }
            clientes[cliente_id]['facturado'] += sale.get('amount_currency', 0)
            if sale.get('pedido'):
                clientes[cliente_id]['pedidos'].add(sale['pedido'])
        
        # Convertir set a count
        for cliente in clientes.values():
            cliente['num_pedidos'] = len(cliente['pedidos'])
            del cliente['pedidos']
        
        return clientes
    
    def aggregate_by_product(self, sales_data: List[Dict]) -> Dict:
        """Agrupa ventas por producto"""
        productos = {}
        for sale in sales_data:
            codigo = sale.get('codigo_odoo', sale.get('default_code', ''))
            if not codigo:
                continue
                
            if codigo not in productos:
                productos[codigo] = {
                    'nombre': sale.get('producto', ''),
                    'linea_comercial': sale.get('linea_comercial', ''),
                    'cantidad': 0,
                    'facturado': 0
                }
            
            productos[codigo]['cantidad'] += sale.get('cantidad_facturada', 0)
            productos[codigo]['facturado'] += sale.get('amount_currency', 0)
        
        return productos

class MetricsCalculationService:
    """Servicio para cálculo de KPIs"""
    
    def calculate_dashboard_metrics(
        self, 
        sales_data: List[Dict],
        pending_data: List[Dict],
        metas: Dict
    ) -> DashboardMetrics:
        """Calcula todas las métricas del dashboard"""
        total_facturado = sum(s.get('amount_currency', 0) for s in sales_data)
        total_pendiente = sum(p.get('total_pendiente', 0) for p in pending_data)
        
        # Calcular meta total
        total_meta = sum(
            sum(cliente.values()) 
            for cliente in metas.values() 
            if isinstance(cliente, dict)
        )
        
        porcentaje = (total_facturado / total_meta * 100) if total_meta > 0 else 0
        
        # Contar únicos
        clientes_unicos = set(s.get('partner_id', [0])[0] for s in sales_data)
        productos_unicos = set(s.get('codigo_odoo', '') for s in sales_data if s.get('codigo_odoo'))
        
        return DashboardMetrics(
            total_facturado=total_facturado,
            total_meta=total_meta,
            porcentaje_cumplimiento=round(porcentaje, 2),
            total_pendiente=total_pendiente,
            num_clientes=len(clientes_unicos),
            num_productos=len(productos_unicos)
        )

class ChartDataService:
    """Servicio para preparación de datos de gráficos"""
    
    def prepare_orders_chart_data(
        self, 
        sales_data: List[Dict],
        pending_data: List[Dict]
    ) -> List[Dict]:
        """Prepara datos para gráfico de órdenes"""
        orders_by_pedido = {}
        
        # Facturado por pedido
        for sale in sales_data:
            pedido = sale.get('pedido', '')
            if not pedido:
                continue
            if pedido not in orders_by_pedido:
                orders_by_pedido[pedido] = {
                    'pedido': pedido,
                    'cliente': sale.get('partner_name', ''),
                    'cliente_id': sale.get('partner_id', [0])[0],
                    'facturado': 0,
                    'pendiente': 0
                }
            orders_by_pedido[pedido]['facturado'] += sale.get('amount_currency', 0)
        
        # Pendiente por pedido
        for pending in pending_data:
            pedido = pending.get('pedido', '')
            if not pedido:
                continue
            if pedido in orders_by_pedido:
                orders_by_pedido[pedido]['pendiente'] += pending.get('total_pendiente', 0)
            else:
                orders_by_pedido[pedido] = {
                    'pedido': pedido,
                    'cliente': pending.get('partner_name', ''),
                    'cliente_id': pending.get('partner_id', [0])[0],
                    'facturado': 0,
                    'pendiente': pending.get('total_pendiente', 0)
                }
        
        return list(orders_by_pedido.values())

class DashboardService:
    """Servicio principal del dashboard - orquesta otros servicios"""
    
    def __init__(self, data_manager, supabase_manager, cache):
        self.data_manager = data_manager
        self.supabase_manager = supabase_manager
        self.cache = cache
        self.sales_aggregation = SalesAggregationService()
        self.metrics_calculator = MetricsCalculationService()
        self.chart_data_service = ChartDataService()
    
    def get_dashboard_data(self, filters: DashboardFilters) -> Dict:
        """Obtiene todos los datos del dashboard con caché"""
        
        # 1. Construir cache key
        cache_key = f"dashboard_{filters.año}_{filters.linea}_{filters.salesperson_id}"
        
        # 2. Intentar obtener de caché
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # 3. Obtener datos frescos de Odoo
        sales_data = self.data_manager.get_sales_lines(
            year=filters.año,
            linea=filters.linea,
            salesperson_id=filters.salesperson_id
        )
        
        pending_data = self.data_manager.get_pending_orders(
            linea=filters.linea,
            salesperson_id=filters.salesperson_id
        )
        
        # 4. Obtener metas de Supabase
        metas = self.supabase_manager.read_metas_por_cliente(str(filters.año))
        
        # 5. Agregar datos
        clientes_aggregated = self.sales_aggregation.aggregate_by_client(sales_data)
        productos_aggregated = self.sales_aggregation.aggregate_by_product(sales_data)
        
        # 6. Calcular métricas
        metrics = self.metrics_calculator.calculate_dashboard_metrics(
            sales_data, pending_data, metas
        )
        
        # 7. Preparar datos de gráficos
        orders_chart = self.chart_data_service.prepare_orders_chart_data(
            sales_data, pending_data
        )
        
        # 8. Construir contexto completo
        dashboard_data = {
            'sales_data': sales_data,
            'pending_data': pending_data,
            'clientes': clientes_aggregated,
            'productos': productos_aggregated,
            'metrics': metrics.__dict__,
            'orders_chart_data': orders_chart,
            'metas': metas,
            'filtros': filters.__dict__
        }
        
        # 9. Almacenar en caché (10 minutos)
        self.cache.set(cache_key, dashboard_data, timeout=600)
        
        return dashboard_data
```

**Paso 2: Simplificar ruta en app.py**

```python
# app.py (refactorizado)
from services.dashboard_service import DashboardService, DashboardFilters
from services.validation_service import ValidationService

# Inicializar servicios (línea ~100)
dashboard_service = DashboardService(data_manager, supabase_manager, cache)
validation_service = ValidationService()

@app.route('/dashboard')
def dashboard():
    """Dashboard principal - solo orquestación"""
    # 1. Autenticación
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # 2. Validar y extraer parámetros
    try:
        filters = validation_service.validate_dashboard_params(request.args, session)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('dashboard'))
    
    # 3. Obtener datos del dashboard
    try:
        dashboard_data = dashboard_service.get_dashboard_data(filters)
    except Exception as e:
        app.logger.error(f"Error en dashboard: {e}", exc_info=True)
        flash('Error al cargar el dashboard', 'error')
        return render_template('error.html'), 500
    
    # 4. Renderizar
    return render_template('dashboard_clean.html', **dashboard_data)
```

**Paso 3: Servicio de validación**

```python
# services/validation_service.py
from typing import Dict
from datetime import datetime
import re

class ValidationService:
    """Validación centralizada de inputs"""
    
    def validate_dashboard_params(self, args: Dict, session: Dict) -> DashboardFilters:
        """Valida y sanitiza parámetros del dashboard"""
        
        # Validar año
        año_str = args.get('año', str(datetime.now().year))
        try:
            año = int(año_str)
            if not (2020 <= año <= 2030):
                raise ValueError(f"Año fuera de rango: {año}")
        except ValueError:
            raise ValueError(f"Año inválido: {año_str}")
        
        # Validar línea comercial
        linea = args.get('linea', '')
        if linea and not re.match(r'^[A-Z0-9_-]+$', linea):
            raise ValueError(f"Línea comercial inválida: {linea}")
        
        # Obtener salesperson_id de sesión
        salesperson_id = session.get('salesperson_id')
        if salesperson_id and not isinstance(salesperson_id, int):
            raise ValueError("salesperson_id debe ser entero")
        
        # Cliente ID (opcional)
        cliente_id = None
        cliente_id_str = args.get('cliente_id')
        if cliente_id_str:
            try:
                cliente_id = int(cliente_id_str)
            except ValueError:
                raise ValueError(f"cliente_id inválido: {cliente_id_str}")
        
        return DashboardFilters(
            año=año,
            linea=linea,
            salesperson_id=salesperson_id,
            cliente_id=cliente_id
        )
```

---

#### 📊 Impacto del Refactor (Refactor Impact)

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Líneas en dashboard() | 1,227 | 28 | -98% |
| Complejidad ciclomática | ~50 | ~5 | -90% |
| Servicios reutilizables | 0 | 5 | ♾️ |
| Testeable | No | Sí | ✅ |
| Tiempo de onboarding | 2-3 días | 2-3 horas | -90% |

**Beneficios (Benefits)**:
- ✅ Cada clase tiene una sola responsabilidad
- ✅ Servicios reutilizables en otras rutas
- ✅ Fácil de testear unitariamente
- ✅ Mantenimiento localizado (cambios aislados)
- ✅ Mejor legibilidad y comprensión

---

### 1.2 Open/Closed Principle (OCP) — 3/10 ⚠️

**Estado Actual (Current State)**: **CERRADO A EXTENSIÓN**

#### Áreas Cerradas a Extensión (Areas Closed to Extension)

##### 🟠 **Agregación de Líneas Comerciales** [app.py, líneas 1000-1100]

**Problema**: Cada nueva línea comercial requiere modificar código existente.

```python
# Línea 1050-1080 app.py
# Hardcoded: Si se agrega nueva línea (ej: "EQUINET"), hay que modificar aquí
if linea == 'AGROVET':
    clientes_filtrados = [c for c in clientes if c.get('linea') == 'AGROVET']
elif linea == 'PETMEDICA':
    clientes_filtrados = [c for c in clientes if c.get('linea') == 'PETMEDICA']
elif linea == 'AVIVET':
    clientes_filtrados = [c for c in clientes if c.get('linea') == 'AVIVET']
else:
    clientes_filtrados = clientes
```

**✅ Solución con Strategy Pattern**:

```python
# strategies/linea_filter_strategy.py
from abc import ABC, abstractmethod
from typing import List, Dict

class LineaFilterStrategy(ABC):
    """Estrategia base para filtrado por línea comercial"""
    
    @abstractmethod
    def filter(self, data: List[Dict]) -> List[Dict]:
        """Filtra datos según criterio de línea"""
        pass

class AllLineasFilter(LineaFilterStrategy):
    """Sin filtro - todas las líneas"""
    
    def filter(self, data: List[Dict]) -> List[Dict]:
        return data

class SpecificLineaFilter(LineaFilterStrategy):
    """Filtro por línea específica"""
    
    def __init__(self, linea_nombre: str):
        self.linea_nombre = linea_nombre
    
    def filter(self, data: List[Dict]) -> List[Dict]:
        return [
            item for item in data 
            if item.get('linea_comercial', '') == self.linea_nombre
        ]

class MultiLineaFilter(LineaFilterStrategy):
    """Filtro por múltiples líneas (para reportes combinados)"""
    
    def __init__(self, lineas: List[str]):
        self.lineas = set(lineas)
    
    def filter(self, data: List[Dict]) -> List[Dict]:
        return [
            item for item in data 
            if item.get('linea_comercial', '') in self.lineas
        ]

class LineaFilterFactory:
    """Factory para crear estrategias de filtrado"""
    
    @staticmethod
    def create(linea: str) -> LineaFilterStrategy:
        """Crea estrategia según parámetro recibido"""
        if not linea or linea == 'TODAS':
            return AllLineasFilter()
        elif ',' in linea:
            # Soporte para múltiples líneas: "AGROVET,PETMEDICA"
            lineas = [l.strip() for l in linea.split(',')]
            return MultiLineaFilter(lineas)
        else:
            return SpecificLineaFilter(linea)

# Uso en dashboard service
class DashboardService:
    def get_dashboard_data(self, filters: DashboardFilters) -> Dict:
        # ...
        sales_data = self.data_manager.get_sales_lines(...)
        
        # Aplicar estrategia de filtrado
        filter_strategy = LineaFilterFactory.create(filters.linea)
        sales_filtered = filter_strategy.filter(sales_data)
        
        # Continuar con agregaciones...
```

**Beneficio**: Agregar nueva línea comercial "EQUINET" NO requiere modificar código:
- ✅ Solo configuración en base de datos
- ✅ `SpecificLineaFilter` la maneja automáticamente
- ✅ Extensible sin modificación

---

##### 🟠 **Exportadores de Datos** [app.py, líneas 2376-2480]

**Problema**: Agregar nuevo formato de export (PDF, CSV) require modificar ruta existente.

```python
# Línea 2376 app.py
@app.route('/export/excel/sales')
def export_excel_sales():
    # 100+ líneas para generar Excel
    # Si queremos PDF, hay que crear otra ruta y duplicar lógica
```

**✅ Solución con Template Method + Strategy**:

```python
# exporters/base_exporter.py
from abc import ABC, abstractmethod
from typing import List, Dict
import io

class DataExporter(ABC):
    """Clase base para exportadores de datos"""
    
    def export(self, data: List[Dict], column_mapping: Dict) -> io.BytesIO:
        """Template method para exportación"""
        # 1. Validar datos
        self.validate_data(data)
        
        # 2. Transformar datos (común)
        transformed_data = self.transform_data(data, column_mapping)
        
        # 3. Generar archivo (específico por formato)
        output = self.generate_file(transformed_data)
        
        return output
    
    def validate_data(self, data: List[Dict]):
        """Validación común"""
        if not data:
            raise ValueError("No hay datos para exportar")
    
    def transform_data(self, data: List[Dict], column_mapping: Dict) -> List[Dict]:
        """Transformación común de datos"""
        transformed = []
        for row in data:
            new_row = {}
            for old_key, new_key in column_mapping.items():
                new_row[new_key] = row.get(old_key, '')
            transformed.append(new_row)
        return transformed
    
    @abstractmethod
    def generate_file(self, data: List[Dict]) -> io.BytesIO:
        """Genera archivo en formato específico"""
        pass
    
    @abstractmethod
    def get_mimetype(self) -> str:
        """Retorna MIME type del formato"""
        pass
    
    @abstractmethod
    def get_extension(self) -> str:
        """Retorna extensión del archivo"""
        pass

# exporters/excel_exporter.py
from .base_exporter import DataExporter
import pandas as pd

class ExcelExporter(DataExporter):
    """Exportador a formato Excel"""
    
    def generate_file(self, data: List[Dict]) -> io.BytesIO:
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Datos', index=False)
            
            # Aplicar formato
            workbook = writer.book
            worksheet = writer.sheets['Datos']
            
            # Headers con estilo
            for cell in worksheet[1]:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="366092", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
        
        output.seek(0)
        return output
    
    def get_mimetype(self) -> str:
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    def get_extension(self) -> str:
        return 'xlsx'

# exporters/csv_exporter.py
class CSVExporter(DataExporter):
    """Exportador a formato CSV"""
    
    def generate_file(self, data: List[Dict]) -> io.BytesIO:
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        # UTF-8 con BOM para Excel
        csv_str = df.to_csv(index=False, encoding='utf-8-sig')
        output.write(csv_str.encode('utf-8-sig'))
        output.seek(0)
        
        return output
    
    def get_mimetype(self) -> str:
        return 'text/csv'
    
    def get_extension(self) -> str:
        return 'csv'

# exporters/pdf_exporter.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

class PDFExporter(DataExporter):
    """Exportador a formato PDF"""
    
    def generate_file(self, data: List[Dict]) -> io.BytesIO:
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        
        # Preparar datos para tabla
        if not data:
            return output
        
        headers = list(data[0].keys())
        table_data = [headers]
        for row in data:
            table_data.append([str(row.get(h, '')) for h in headers])
        
        # Crear tabla
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        doc.build([table])
        output.seek(0)
        return output
    
    def get_mimetype(self) -> str:
        return 'application/pdf'
    
    def get_extension(self) -> str:
        return 'pdf'

# exporters/factory.py
class ExporterFactory:
    """Factory para crear exportadores"""
    
    _exporters = {
        'excel': ExcelExporter,
        'csv': CSVExporter,
        'pdf': PDFExporter,
    }
    
    @classmethod
    def create(cls, format_type: str) -> DataExporter:
        """Crea exportador según formato"""
        exporter_class = cls._exporters.get(format_type.lower())
        if not exporter_class:
            raise ValueError(f"Formato no soportado: {format_type}")
        return exporter_class()
    
    @classmethod
    def register(cls, format_type: str, exporter_class: type):
        """Registra nuevo exportador (extensión sin modificación)"""
        cls._exporters[format_type] = exporter_class

# Uso en app.py (ruta genérica)
@app.route('/export/<format_type>/sales')
def export_sales(format_type):
    """Ruta genérica para exportar en cualquier formato"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Obtener datos
    filters = validation_service.validate_dashboard_params(request.args, session)
    sales_data = data_manager.get_sales_lines(...)
    
    # Column mapping
    column_mapping = {
        'pedido': 'Pedido',
        'cliente': 'Cliente',
        'fecha': 'Fecha',
        # ... resto de mapeo
    }
    
    # Crear exportador y generar archivo
    try:
        exporter = ExporterFactory.create(format_type)
        file_output = exporter.export(sales_data, column_mapping)
        
        filename = f"ventas_{datetime.now().strftime('%Y%m%d')}.{exporter.get_extension()}"
        
        return send_file(
            file_output,
            mimetype=exporter.get_mimetype(),
            as_attachment=True,
            download_name=filename
        )
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('dashboard'))
```

**Extensibilidad Lograda**:
- ✅ Agregar formato JSON: crear `JSONExporter` y registrar
- ✅ Agregar formato XML: crear `XMLExporter` y registrar  
- ✅ NO modificar código existente
- ✅ Reutilizar lógica común (transformación, validación)

---

### 1.3 Liskov Substitution Principle (LSP) — N/A

**Estado**: No aplica - proyecto no usa herencia de clases extensivamente.

**Observación**: El proyecto usa composición y managers funcionales, lo cual es correcto. LSP sería relevante si se implementan las abstracciones sugeridas arriba (ej: `DataExporter`).

---

### 1.4 Interface Segregation Principle (ISP) — 4/10 ⚠️

**Problema Detectado**: Managers tienen interfaces "gordas".

##### 🟠 **OdooManager** [database/odoo_manager.py]

```python
class OdooManager:
    """Manager con 20+ métodos públicos"""
    
    # Autenticación
    def connect(self): ...
    def authenticate_user(self, email, password): ...
    
    # Ventas
    def get_sales_lines(self, year, linea, ...): ...
    def get_pending_orders(self, linea, ...): ...
    def get_sales_by_client(self, client_id): ...
    
    # Clientes
    def get_international_clients(self): ...
    def get_client_details(self, client_id): ...
    
    # Productos
    def get_products(self): ...
    def get_product_details(self, product_id): ...
    
    # Órdenes
    def get_orders(self, filters): ...
    def get_order_details(self, order_id): ...
    
    # Equipos
    def get_sales_teams(self): ...
    
    # Stock (recién agregado)
    def get_stock_lots(self, product_id): ...
    
    # ... más métodos
```

**Problema**: Un cambio en autenticación afecta a todos los consumidores del manager, aunque solo usen métodos de ventas.

**✅ Solución: Segregar en interfaces específicas**

```python
# database/interfaces/authentication_interface.py
from abc import ABC, abstractmethod

class AuthenticationInterface(ABC):
    """Interfaz para autenticación"""
    
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def authenticate_user(self, email: str, password: str) -> Dict:
        pass

# database/interfaces/sales_interface.py
class SalesDataInterface(ABC):
    """Interfaz para datos de ventas"""
    
    @abstractmethod
    def get_sales_lines(self, year: int, filters: Dict) -> List[Dict]:
        pass
    
    @abstractmethod
    def get_pending_orders(self, filters: Dict) -> List[Dict]:
        pass

# database/interfaces/client_interface.py
class ClientsDataInterface(ABC):
    """Interfaz para datos de clientes"""
    
    @abstractmethod
    def get_international_clients(self) -> List[Dict]:
        pass
    
    @abstractmethod
    def get_client_details(self, client_id: int) -> Dict:
        pass

# database/odoo_manager.py (refactorizado)
class OdooManager(AuthenticationInterface, SalesDataInterface, ClientsDataInterface):
    """Manager que implementa múltiples interfaces segregadas"""
    
    # Implementar métodos de cada interfaz...
    pass

# Consumidores pueden depender solo de lo que necesitan:
class DashboardService:
    def __init__(self, sales_data: SalesDataInterface, clients_data: ClientsDataInterface):
        self.sales_data = sales_data  # Solo usa métodos de ventas
        self.clients_data = clients_data  # Solo usa métodos de clientes
        # No necesita AuthenticationInterface
```

---

### 1.5 Dependency Inversion Principle (DIP) — 3/10 ⚠️

**Problema**: Dependencias concretas hardcodeadas.

##### 🔴 **App.py - Dependencias Hardcodeadas** [líneas 95-115]

```python
# Línea 95-115 app.py
# Instanciación directa de clases concretas
data_manager = OdooManager(
    url=os.getenv('ODOO_URL'),
    db=os.getenv('ODOO_DB'),
    username=os.getenv('ODOO_USER'),
    password=os.getenv('ODOO_PASSWORD')
)

supabase_manager = SupabaseManager()
gs_manager = GoogleSheetsManager()

# En cada ruta, uso directo:
@app.route('/dashboard')
def dashboard():
    sales_data = data_manager.get_sales_lines(...)  # Acoplamiento fuerte
```

**Problemas**:
- ❌ Difícil de testear (no se puede mockear fácilmente)
- ❌ Cambiar de Odoo a otro ERP = modificar todo el código
- ❌ No hay abstracción entre capa de negocio y datos

**✅ Solución: Dependency Injection con abstracciones**

```python
# database/interfaces/erp_interface.py
from abc import ABC, abstractmethod

class ERPDataSource(ABC):
    """Interfaz abstracta para fuentes de datos ERP"""
    
    @abstractmethod
    def authenticate(self, email: str, password: str) -> Dict:
        pass
    
    @abstractmethod
    def get_sales_data(self, filters: Dict) -> List[Dict]:
        pass
    
    @abstractmethod
    def get_pending_orders(self, filters: Dict) -> List[Dict]:
        pass

class MetasDataSource(ABC):
    """Interfaz abstracta para fuente de metas"""
    
    @abstractmethod
    def read_metas(self, año: str) -> Dict:
        pass
    
    @abstractmethod
    def write_metas(self, año: str, data: Dict) -> bool:
        pass

# database/odoo_adapter.py
class OdooAdapter(ERPDataSource):
    """Adaptador de Odoo que implementa la interfaz abstracta"""
    
    def __init__(self, config: Dict):
        self.odoo_manager = OdooManager(**config)
    
    def authenticate(self, email: str, password: str) -> Dict:
        return self.odoo_manager.authenticate_user(email, password)
    
    def get_sales_data(self, filters: Dict) -> List[Dict]:
        return self.odoo_manager.get_sales_lines(**filters)
    
    def get_pending_orders(self, filters: Dict) -> List[Dict]:
        return self.odoo_manager.get_pending_orders(**filters)

# database/supabase_adapter.py
class SupabaseAdapter(MetasDataSource):
    """Adaptador de Supabase"""
    
    def __init__(self, config: Dict):
        self.supabase_manager = SupabaseManager(**config)
    
    def read_metas(self, año: str) -> Dict:
        return self.supabase_manager.read_metas_por_cliente(año)
    
    def write_metas(self, año: str, data: Dict) -> bool:
        return self.supabase_manager.write_metas_por_cliente(año, data)

# config/dependencies.py
from database.interfaces.erp_interface import ERPDataSource, MetasDataSource
from database.odoo_adapter import OdooAdapter
from database.supabase_adapter import SupabaseAdapter

class DependencyContainer:
    """Contenedor de dependencias para inyección"""
    
    def __init__(self):
        self._instances = {}
    
    def register_erp_source(self, source: ERPDataSource):
        """Registra fuente de datos ERP"""
        self._instances['erp_source'] = source
    
    def register_metas_source(self, source: MetasDataSource):
        """Registra fuente de metas"""
        self._instances['metas_source'] = source
    
    def get_erp_source(self) -> ERPDataSource:
        return self._instances['erp_source']
    
    def get_metas_source(self) -> MetasDataSource:
        return self._instances['metas_source']

# app.py (refactorizado con DI)
from config.dependencies import DependencyContainer

# Configurar contenedor de dependencias (línea ~95)
container = DependencyContainer()

# Registrar implementaciones concretas
odoo_config = {
    'url': os.getenv('ODOO_URL'),
    'db': os.getenv('ODOO_DB'),
    'username': os.getenv('ODOO_USER'),
    'password': os.getenv('ODOO_PASSWORD')
}
container.register_erp_source(OdooAdapter(odoo_config))

supabase_config = {
    'url': os.getenv('SUPABASE_URL'),
    'key': os.getenv('SUPABASE_KEY')
}
container.register_metas_source(SupabaseAdapter(supabase_config))

# Inicializar servicios con dependencias inyectadas
dashboard_service = DashboardService(
    erp_source=container.get_erp_source(),
    metas_source=container.get_metas_source(),
    cache=cache
)

# Ahora DashboardService depende de abstracciones, no de implementaciones concretas
class DashboardService:
    def __init__(
        self, 
        erp_source: ERPDataSource,  # Abstracción, no OdooManager
        metas_source: MetasDataSource,  # Abstracción, no SupabaseManager
        cache
    ):
        self.erp_source = erp_source
        self.metas_source = metas_source
        self.cache = cache
```

**Beneficios del DIP implementado**:
- ✅ Fácil de testear: inyectar mocks en tests
- ✅ Cambiar ERP (Odoo → SAP): solo crear `SAPAdapter(ERPDataSource)`
- ✅ Cambiar storage de metas: solo crear nuevo adapter
- ✅ Servicios desacoplados de implementaciones concretas

**Ejemplo de test con DI**:

```python
# tests/test_dashboard_service.py
import pytest
from unittest.mock import Mock

def test_dashboard_metrics_calculation():
    # Crear mocks de las interfaces
    mock_erp = Mock(spec=ERPDataSource)
    mock_metas = Mock(spec=MetasDataSource)
    mock_cache = Mock()
    
    # Configurar comportamiento de mocks
    mock_erp.get_sales_data.return_value = [
        {'amount_currency': 1000, 'partner_id': [1, 'Cliente A']},
        {'amount_currency': 2000, 'partner_id': [1, 'Cliente A']},
    ]
    mock_metas.read_metas.return_value = {'1': {'AGROVET': 5000}}
    
    # Inyectar mocks
    service = DashboardService(
        erp_source=mock_erp,
        metas_source=mock_metas,
        cache=mock_cache
    )
    
    # Test
    filters = DashboardFilters(año=2026, linea='AGROVET', salesperson_id=None)
    result = service.get_dashboard_data(filters)
    
    assert result['metrics']['total_facturado'] == 3000
    assert mock_erp.get_sales_data.called
```

---

## 2️⃣ Seguridad OWASP Top 10 (OWASP Top 10 Security)

### Puntuación General: 7/10 ⚠️ → ✅

**Mejoras Recientes (Marzo 2026)**: +1 punto por implementación de headers de seguridad, rate limiting y security logging.

---

### 2.1 A01: Broken Authentication — 8/10 ✅

**Estado**: Seguro, mejoras implementadas exitosamente.

#### ✅ Fortalezas Implementadas (Implemented Strengths)

1. **OAuth2 con Google OIDC** [líneas 272-341]
```python
# Línea 272-341 app.py
@app.route('/auth/callback')
def auth_callback():
    # ✅ Validación de state token (CSRF protection)
    if request.args.get('state') != session.get('oauth_state'):
        return redirect(url_for('login'))
    
    # ✅ Exchange code por token
    token_info = flow.fetch_token(...)
    
    # ✅ Validar identity token con Google
    credentials = Credentials(token=token_info)
    idinfo = id_token.verify_oauth2_token(...)
    
    # ✅ Almacenar info en sesión
    session['user'] = {
        'email': idinfo.get('email'),
        'name': idinfo.get('name'),
        # ...
    }
```

2. **Configuración de sesiones seguras** [líneas 75-80]
```python
# Línea 75-80 app.py
app.config['SESSION_COOKIE_SECURE'] = True  # ✅ Solo HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # ✅ No accesible desde JS
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # ✅ MEJORADO (26/03/2026)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)  # ✅ Expiración
```

3. **Security Logging implementado** (26/03/2026)
```python
# Línea ~180 app.py
logger = SecurityLogger(app)

# Eventos de autenticación logueados automáticamente
@app.route('/login/callback')
def login_callback():
    # ...
    logger.log_login_attempt(email, True, request.remote_addr, request.user_agent.string)
```

#### 🟢 Mejoras Recientes (Recent Improvements)

1. **Cookie SAMESITE='Strict'** (26/03/2026)
   - ✅ Antes: 'Lax' (permitía ataques CSRF en ciertos escenarios)
   - ✅ Ahora: 'Strict' (protección completa contra CSRF)

2. **Security event logging** (26/03/2026)
   - ✅ Login exitoso/fallido
   - ✅ Logout
   - ✅ Unauthorized access attempts

---

### 2.5 A05: Security Misconfiguration — 8/10 ✅

**Estado**: Mejorado significativamente (26/03/2026) - ✅ SRI implementado, ✅ Validación en exports

#### ✅ Headers de Seguridad Implementados (Security Headers Implemented)

**Middleware aplicado** [services/security_headers.py]:

```python
@app.after_request
def add_security_headers(response):
    """Agrega headers de seguridad OWASP a todas las respuestas"""
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self'"
    )
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
```

**Cobertura de headers**:
- ✅ **X-Frame-Options**: DENY (previene clickjacking)
- ✅ **X-Content-Type-Options**: nosniff (previene MIME sniffing)
- ✅ **X-XSS-Protection**: 1; mode=block (protección XSS legacy browsers)
- ✅ **Strict-Transport-Security (HSTS)**: 1 año (fuerza HTTPS)
- ✅ **Content-Security-Policy**: Configurado para CDNs permitidos
- ✅ **Referrer-Policy**: strict-origin-when-cross-origin
- ✅ **Permissions-Policy**: Desactiva features sensibles (geolocation, camera, mic)
- ✅ **Cache-Control/Pragma/Expires**: No cacheo de datos sensibles

#### ✅ Rate Limiting Implementado (Rate Limiting Implemented)

**Rutas protegidas** [app.py]:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379",
    default_limits=["100 per hour"]
)

# Login (estricto)
@app.route('/login/callback')
@limiter.limit("5 per minute")
def login_callback():
    pass

# Dashboard (moderado)
@app.route('/dashboard')
@limiter.limit("30 per minute")
def dashboard():
    pass

# Exports (controlado)
@app.route('/export/excel/sales')
@limiter.limit("10 per minute")
def export_excel_sales():
    pass
```

**Límites configurados**:
| Ruta | Límite | Justificación |
|------|--------|---------------|
| `/login/callback` | 5 req/min | Prevenir brute force |
| `/dashboard` | 30 req/min | Balance usabilidad/seguridad |
| `/export/excel/sales` | 10 req/min | Evitar sobrecarga servidor |
| `/export/excel/pending` | 10 req/min | Evitar sobrecarga servidor |
| `/export/dashboard/details` | 10 req/min | Evitar sobrecarga servidor |
| Default (global) | 100 req/hora | Protección general |

#### ✅ Mejoras Completadas (Marzo 2026) ✨

1. **✅ COMPLETADO** - CDN con SRI (Subresource Integrity) - **Task 11**
   ```html
   <!-- templates/base.html, dashboard_clean.html, login.html, equipo_ventas.html - ✅ SRI IMPLEMENTADO -->
   <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"
           integrity="sha384-wcWxZWuhOHltHKN2NXyFdZiHqgKNbm/Y6UbwRfh+WaNd8wC4BYKnUPlmSvy0fPoQ"
           crossorigin="anonymous"></script>
   <!-- ✅ ECharts asegurado con SHA-384 -->
   
   <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.js"
           integrity="sha384-eoFilVKkfw2e2IbZJWZ5TfDh+dF8lS2jPz4I5t5vQvJhZN8c5R4U9HpHKLhJhMQ"
           crossorigin="anonymous"></script>
   <!-- ✅ Chart.js asegurado con SHA-384 -->
   ```
   
   **Recursos CDN asegurados (9 total)**:
   - ✅ ECharts 5.5.0
   - ✅ Chart.js 4.4.3  
   - ✅ html2canvas 1.4.1
   - ✅ jsPDF 2.5.1
   - ✅ Bootstrap Icons 1.11.3 (CSS + Font)
   - ✅ Tom Select 2.3.1 (JS + CSS)
   
   **Beneficios**:
   - Protección contra supply-chain attacks (compromiso de CDN)
   - Cumple OWASP ASVS V14.2.3
   - Verificación automática de integridad por navegador
   - Si CDN comprometido → script bloqueado automáticamente

2. **✅ COMPLETADO** - Validación estricta en exports - **Task 10**
   ```python
   # app.py - Rutas de exportación con validación (líneas ~2543, ~2675, ~2895)
   
   # ✅ Validación de rango de años
   año_seleccionado = int(request.args.get('año', año_actual))
   if año_seleccionado < (año_actual - 5) or año_seleccionado > (año_actual + 1):
       flash(f'Rango de año inválido. Use entre {año_actual - 5} y {año_actual + 1}.', 'warning')
       return redirect(url_for('dashboard'))
   
   # ✅ Límite de registros para prevenir DoS
   per_page=15000  # ✅ Reducido de 99,999 (antes sin límite efectivo)
   if len(sales_data_raw) >= 15000:
       flash(
           f'Resultado truncado: se encontraron {len(sales_data_raw)}+ registros. '
           'Use filtros más específicos.',
           'warning'
       )
   
   # ✅ Validación de mes
   mes_int = int(mes)
   if not (1 <= mes_int <= 12):
       flash('Mes inválido. Debe estar entre 1 y 12.', 'danger')
       return redirect(url_for('dashboard'))
   ```
   
   **Rutas protegidas (3 exports)**:
   - ✅ `/export/excel/sales` (ventas facturadas)
   - ✅ `/export/excel/pending` (pendientes)
   - ✅ `/export/dashboard/details` (detalles por mes)
   
   **Beneficios**:
   - Previene DoS por exportaciones masivas (15K límite vs antes sin límite)
   - Validación de rangos de fechas (máx 5 años atrás)
   - Flash warnings graduales (informa sin bloquear completamente)
   - Reduce carga en Odoo (queries más controladas)
   - Cumple CWE-400 (Uncontrolled Resource Consumption)

3. **✅ BAJO** - Secrets en variables de entorno (ya implementado correctamente)
   - ✅ `.env` en `.gitignore`
   - ✅ Secrets no commiteados
   - ⚠️ Considerar: Azure Key Vault o HashiCorp Vault para producción

#### 📊 Score Evolution A05 (Evolución de Puntuación)

| Fecha | Score | Mejoras |
|-------|-------|----------|
| Feb 2026 | 6/10 | Baseline (sin headers, sin rate limiting) |
| Mar 2026 (early) | 7.5/10 | Headers OWASP + Rate limiting |
| **Mar 2026 (late)** | **8/10** | **+ SRI en CDN (9 recursos) + Validación exports**

---

### 2.9 A09: Security Logging and Monitoring — 8/10 ✅

**Estado**: Implementado exitosamente (26/03/2026)

#### ✅ SecurityLogger Implementado (SecurityLogger Implemented)

**Servicio creado** [services/security_logger.py]:

```python
import logging
from pathlib import Path
from datetime import datetime

class SecurityLogger:
    """Sistema de logging centralizado para eventos de seguridad"""
    
    def __init__(self, app):
        self.app = app
        self.security_logger = self._setup_logger()
    
    def _setup_logger(self):
        """Configura logger con 2 archivos: all events + critical only"""
        logs_dir = Path('logs/')
        logs_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('security')
        logger.setLevel(logging.INFO)
        
        # Handler 1: Todos los eventos
        all_handler = logging.FileHandler('logs/security.log')
        all_handler.setLevel(logging.INFO)
        
        # Handler 2: Solo críticos (WARNING+)
        critical_handler = logging.FileHandler('logs/security_critical.log')
        critical_handler.setLevel(logging.WARNING)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        all_handler.setFormatter(formatter)
        critical_handler.setFormatter(formatter)
        
        logger.addHandler(all_handler)
        logger.addHandler(critical_handler)
        
        return logger
    
    def log_login_attempt(self, email, success, ip, user_agent):
        """Loguea intento de login"""
        if success:
            self.security_logger.info(
                f"LOGIN_SUCCESS | Email: {email} | IP: {ip} | UA: {user_agent}"
            )
        else:
            self.security_logger.warning(
                f"LOGIN_FAILED | Email: {email} | IP: {ip} | UA: {user_agent}"
            )
    
    def log_logout(self, email, ip):
        """Loguea logout de usuario"""
        self.security_logger.info(f"LOGOUT | Email: {email} | IP: {ip}")
    
    def log_unauthorized_access(self, endpoint, user, ip):
        """Loguea intento de acceso no autorizado"""
        self.security_logger.warning(
            f"UNAUTHORIZED_ACCESS | Endpoint: {endpoint} | User: {user} | IP: {ip}"
        )
    
    def log_validation_error(self, param, value, ip):
        """Loguea error de validación de inputs"""
        self.security_logger.warning(
            f"VALIDATION_ERROR | Param: {param} | Value: {value} | IP: {ip}"
        )
    
    def log_export_request(self, user, export_type, num_records, filters, ip):
        """Loguea request de exportación de datos"""
        self.security_logger.info(
            f"EXPORT_REQUEST | User: {user} | Type: {export_type} | "
            f"Records: {num_records} | Filters: {filters} | IP: {ip}"
        )
```

**Integración en app.py**:

```python
# Línea ~180 app.py
from services.security_logger import SecurityLogger

logger = SecurityLogger(app)

# Login callback
@app.route('/login/callback')
def login_callback():
    try:
        # ... autenticación ...
        logger.log_login_attempt(email, True, request.remote_addr, request.user_agent.string)
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.log_login_attempt(email, False, request.remote_addr, request.user_agent.string)
        flash('Error en autenticación', 'error')
        return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    email = session.get('user', {}).get('email', 'Anonymous')
    logger.log_logout(email, request.remote_addr)
    session.clear()
    return redirect(url_for('login'))

# Unauthorized access (before_request)
@app.before_request
def check_authentication():
    if request.endpoint not in ['login', 'login_callback', 'static']:
        if 'user' not in session:
            logger.log_unauthorized_access(
                request.endpoint, 
                'Anonymous', 
                request.remote_addr
            )
            return redirect(url_for('login'))

# Validation error (dashboard)
@app.route('/dashboard')
def dashboard():
    try:
        filters = validation_service.validate_dashboard_params(request.args, session)
    except ValueError as e:
        logger.log_validation_error(
            'dashboard_filters',
            request.args.to_dict(),
            request.remote_addr
        )
        flash('Parámetros inválidos', 'error')
        return redirect(url_for('dashboard'))

# Export request
@app.route('/export/excel/sales')
def export_excel_sales():
    email = session['user']['email']
    filters = request.args.to_dict()
    # ... generar export ...
    logger.log_export_request(
        email, 
        'sales', 
        len(sales_data), 
        filters, 
        request.remote_addr
    )
    return send_file(...)
```

#### 📊 Eventos de Seguridad Capturados (Security Events Captured)

| Evento | Severidad | Ubicación | Detalles Logueados |
|--------|-----------|-----------|-------------------|
| **Login exitoso** | INFO | `/login/callback` | Email, IP, User-Agent |
| **Login fallido** | WARNING | `/login/callback` | Email, IP, User-Agent |
| **Logout** | INFO | `/logout` | Email, IP |
| **Acceso no autorizado** | WARNING | `@before_request` | Endpoint, User, IP |
| **Error de validación** | WARNING | `/dashboard`, exports | Parámetro, Valor, IP |
| **Exportación de datos** | INFO | `/export/*` | User, Type, Records, Filters, IP |

#### 📁 Archivos de Log (Log Files)

**Estructura**:
```
logs/
├── security.log             # Todos los eventos (INFO+)
└── security_critical.log    # Solo críticos (WARNING+)
```

**Ejemplo de logs/security.log**:
```log
2026-03-26 10:15:23 | INFO | LOGIN_SUCCESS | Email: user@company.com | IP: 192.168.1.100 | UA: Mozilla/5.0...
2026-03-26 10:16:45 | WARNING | UNAUTHORIZED_ACCESS | Endpoint: dashboard | User: Anonymous | IP: 10.0.0.50
2026-03-26 10:18:12 | INFO | EXPORT_REQUEST | User: user@company.com | Type: sales | Records: 1543 | Filters: {'año': 2026}
2026-03-26 10:20:33 | WARNING | VALIDATION_ERROR | Param: dashboard_filters | Value: año=invalid | IP: 192.168.1.100
2026-03-26 10:22:45 | INFO | LOGOUT | Email: user@company.com | IP: 192.168.1.100
```

**Ejemplo de logs/security_critical.log** (solo WARNING+):
```log
2026-03-26 10:16:45 | WARNING | UNAUTHORIZED_ACCESS | Endpoint: dashboard | User: Anonymous | IP: 10.0.0.50
2026-03-26 10:20:33 | WARNING | VALIDATION_ERROR | Param: dashboard_filters | Value: año=invalid | IP: 192.168.1.100
2026-03-26 11:05:12 | WARNING | LOGIN_FAILED | Email: attacker@mail.com | IP: 45.33.22.11 | UA: curl/7.68.0
```

#### 🔍 Uso para Monitoreo (Monitoring Usage)

**Alertas recomendadas**:

1. **Múltiples login fallidos** (posible brute force)
   ```bash
   # Contar login fallidos por IP en última hora
   grep "LOGIN_FAILED" logs/security.log | grep "$(date -d '1 hour ago' +'%Y-%m-%d %H')" | awk '{print $11}' | sort | uniq -c | sort -rn
   ```

2. **Accesos no autorizados**
   ```bash
   # Contar unauthorized access attempts
   grep "UNAUTHORIZED_ACCESS" logs/security_critical.log | wc -l
   ```

3. **Validación errors (posible injection attempts)**
   ```bash
   # Buscar patrones sospechosos en validation errors
   grep "VALIDATION_ERROR" logs/security_critical.log | grep -E "(script|SELECT|DROP|<|>)"
   ```

#### 🟡 Mejoras Futuras (Future Improvements)

1. **🟡 MEDIO** - Integrar SIEM (Security Information and Event Management)
   - Enviar logs a Splunk, ELK Stack, o Azure Sentinel
   - Análisis automático de patrones de ataque

2. **🟡 BAJO** - Alertas en tiempo real
   - Webhook a Slack/Teams cuando hay WARNING+
   - Email automático a admin en eventos críticos

3. **🟡 BAJO** - Retención de logs
   - Rotación automática (log rotation)
   - Archivar logs > 30 días a storage frío

---

## 📈 Resumen de Mejoras OWASP (OWASP Improvements Summary)

### Score Evolution (Evolución de Puntuación)

| Categoría OWASP | Pre-Mejoras | Fase 1 (early Mar 2026) | Fase 2 (late Mar 2026) 🆕 | Cambio Total |
|-----------------|-------------|------------------------|---------------------------|--------------|
| **A01: Broken Authentication** | 7/10 | **8/10** | **8/10** | ⬆️ +1 |
| **A05: Security Misconfiguration** | 6/10 | **7.5/10** | **8/10** 🆕 | ⬆️ +2 |
| **A09: Security Logging** | 4/10 | **8/10** | **8/10** | ⬆️ +4 |
| **Score General OWASP** | 6/10 | **7/10** | **7.5-8/10** 🆕 | ⬆️ +1.5-2 |

**Mejoras Fase 2 (late Marzo 2026)** 🆕:
- ✅ **Task 10**: Validación estricta en 3 rutas de export (límites 15K, rangos de fechas)
- ✅ **Task 11**: SRI implementado en 9 recursos CDN (protección supply-chain)
- ✅ **Task 12**: Docstrings OWASP-compliant (~250 líneas con referencias CWE/NIST)

### Próximos Pasos (Next Steps)

1. ✅ **Completado**: Security headers, rate limiting, logging, SRI, validación exports (26/03/2026) 
2. ⏳ **En progreso**: Refactorización dashboard() para mejor testeo de seguridad (Task 7 - HIGH RISK)
3. **Planificado Q2 2026**: Tests de penetración, fuzzing de inputs, Pydantic validation en dashboard
4. **Planificado Q3 2026**: SIEM integration, automated security scanning