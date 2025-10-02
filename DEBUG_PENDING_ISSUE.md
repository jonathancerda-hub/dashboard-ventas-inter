## DIAGNÓSTICO Y SOLUCIÓN DEL PROBLEMA

### Problema Identificado:
- **Error:** `ValueError: Invalid leaf id` 
- **Origen:** Módulo customizado `agr_sales_channel/models/sale_order.py` línea 290
- **Causa:** El filtro `('order_id.team_id.name', '=', 'VENTA INTERNACIONAL')` está siendo interceptado por código custom que no maneja bien ciertos IDs

### Datos Disponibles:
✅ **520 líneas pendientes encontradas** - La consulta básica funciona
✅ **Canal 'VENTA INTERNACIONAL' existe** - Confirmado en logs de ventas
✅ **Conexión a Odoo estable** - Otras consultas funcionan bien

### Enfoque Actual:
Consultar directamente `sale.order.line` con filtros → ❌ FALLA

### Solución Propuesta:
1. Usar los datos de `sale.order.line` que ya se obtienen en `get_sales_lines()`
2. Calcular cantidades pendientes a partir de datos existentes
3. Evitar consultas problemáticas que pasan por el módulo customizado

### Implementación:
- Modificar `get_pending_orders()` para usar datos ya disponibles
- Usar lógica matemática: `pendiente = pedido - facturado`
- Mantener la misma estructura de datos para el frontend