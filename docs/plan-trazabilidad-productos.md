# Plan: Trazabilidad Logística de Productos Pendientes

## 📋 Problema Identificado

**Situación actual:**
- ✅ Sabemos QUÉ productos faltan facturar
- ✅ Sabemos de QUÉ pedidos son
- ✅ Sabemos cuántos días han transcurrido/faltan
- ❌ **NO sabemos dónde está el producto ni qué falta para facturarlo**

**Gap operativo:**
El equipo de ventas ve productos pendientes pero no sabe si:
- Está en almacén listo para despachar → Solo falta picking/entrega
- Está en tránsito desde proveedor → Hay que esperar recepción
- Necesita traslado entre almacenes → Hay que coordinar logística interna
- No hay stock suficiente → Falta hacer compra urgente

⚠️ **CRÍTICO para Ventas Internacionales:**
- **Fecha de expiración** puede descalificar stock "disponible"
- Productos con expiración próxima NO pueden exportarse (requisitos de cada país)
- Stock disponible ≠ Stock facturable si la fecha de vencimiento está cerca

---

## 🎯 Objetivo

Agregar **visibilidad del estado logístico** sin hacer pesado el proyecto:
- Mostrar disponibilidad real del producto
- Identificar cuellos de botella (compras pendientes, traslados, etc.)
- Priorizar acciones (¿qué puedo facturar YA? ¿qué necesita acción?)

---

## 💡 Opciones de Solución

### Opción A: **Indicador Simple de Stock** (LIGERA - Recomendada para empezar)

**Qué muestra:**
- 🟢 **Disponible**: Hay stock suficiente en almacén principal (con vida útil adecuada)
- 🟡 **Stock Parcial**: Hay algo pero no suficiente
- 🔴 **Sin Stock**: No hay en ningún almacén
- 🔵 **En Tránsito**: Hay compra u orden pendiente
- ⚠️ **Stock Próximo a Vencer**: Hay stock pero fecha de expiración no permite exportación

**Ventajas:**
- Implementación rápida (1 consulta extra a `stock.quant`)
- No impacta performance significativamente
- Información clara y accionable

**Datos Odoo necesarios:**
```python
# Consulta a stock.quant + stock.production.lot (para fecha expiración)
{
    'product_id': 123,
    'location_id': almacen_principal,
    'quantity': stock_disponible,
    'reserved_quantity': stock_reservado,
    'lot_id': lote_info,  # Para rastrear fecha de expiración
    'expiration_date': '2026-06-15',  # Desde stock.production.lot
    'stock_exportable': True/False  # Si cumple requisitos de exportación
}
```

**⚠️ Regla de Expiración (Ventas Internacionales):**
```python
# Ejemplo: Producto debe tener mínimo 6 meses de vida útil para exportar
MIN_MESES_EXPORTACION = 6
fecha_limite = datetime.now() + timedelta(days=180)

# Solo considerar stock "disponible" si:
stock_exportable = (expiration_date > fecha_limite) or (expiration_date is None)
```

**Visualización:**
```
[31126PER00003] HEMATOFOS B12  
🟢 Stock: 1,200 unidades (Exp: 2027-08-15) | Falta: 756 unidades
                        ↑ Vida útil OK           ↑ Ya se puede facturar parcialmente

[31126PER00004] ANTIBIÓTICO XYZ
⚠️ Stock: 800 unidades (Exp: 2026-04-10) | Falta: 1,000 unidades
                       ↑ 43 días restantes - NO exportable
```

---

### Opción B: **Semáforo con Detalle** (INTERMEDIA - Mayor valor operativo)

**Qué muestra (en tooltip o modal expandido):**

```
📦 ESTADO LOGÍSTICO DEL PRODUCTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cantidad pendiente: 756 unidades

✅ Disponible ahora: 450 und (Almacén Lima)
   └─ Lote A123: 300 und (Exp: 2027-08-15) ✓ Exportable
   └─ Lote B456: 150 und (Exp: 2026-11-20) ✓ Exportable
🟡 En otro almacén: 200 und (Almacén Callao) → Necesita traslado
   └─ Lote C789: 200 und (Exp: 2027-01-10) ✓ Exportable
🔵 En tránsito: 300 und (OC-12345) → Llega: 2026-03-15
⚠️ Stock NO exportable: 250 und (Almacén Lima)
   └─ Lote D999: 250 und (Exp: 2026-04-10) ✗ Vence en 43 días
❌ Faltante: 106 und → Requiere compra urgente

📊 Resumen:
- Listo para facturar (exportable): 450 und (59%)
- En proceso/traslado: 200 und (26%)
- NO exportable (prox. vencer): 250 und (33%)
- Requiere compra: 106 und (14%)

⚠️ CRÍTICO: Stock total físico: 900 und, pero solo 650 und exportable
```

**Datos Odoo necesarios:**
```python
# 1. Stock por almacén con lotes (stock.quant + stock.production.lot)
# 2. Órdenes de compra pendientes (purchase.order.line)
# 3. Traslados en proceso (stock.picking donde state != 'done')
# 4. Fechas de expiración por lote (stock.production.lot.expiration_date)
```

**⚠️ REGLA CRÍTICA - Ventas Internacionales:**
```python
# Cada país tiene requisitos mínimos de vida útil
# Ejemplo: USA/Europa requieren mínimo 6 meses, LATAM 4 meses

def es_stock_exportable(expiration_date, destino_pais):
    if not expiration_date:
        return True  # Productos sin vencimiento
    
    meses_minimos = {
        'USA': 6,
        'EUR': 6,
        'LATAM': 4,
        'default': 3
    }
    
    dias_restantes = (expiration_date - datetime.now()).days
    dias_minimos = meses_minimos.get(destino_pais, 3) * 30
    
    return dias_restantes >= dias_minimos

# Stock físico ≠ Stock exportable
# SIEMPRE validar fecha de expiración antes de prometer disponibilidad
```

**Ventajas:**
- Información muy completa
- Priorización clara de acciones
- Identifica cuellos de botella específicos

**Desventajas:**
- Más consultas a Odoo (puede ser lento con muchos productos)
- Requiere lógica más compleja

---

### Opción C: **Dashboard Logístico Separado** (COMPLETA - Para fase futura)

Panel independiente con:
- Estado de órdenes de compra críticas
- Traslados pendientes entre almacenes
- Proyección de disponibilidad por fecha
- Alertas de productos críticos sin plan de abastecimiento

**Cuándo implementar:** Cuando Opción A o B genere demanda de más detalle.

---

## 🏗️ Arquitectura Propuesta (Opción A - Inicio rápido)

### 1. Backend: Nuevo método en `odoo_manager.py`

```python
def get_stock_availability(self, product_codes, almacen_principal_id=None, min_dias_exportacion=180):
    """
    Consulta stock disponible por producto CON validación de fecha de expiración.
    
    Args:
        product_codes: Lista de códigos de producto
        almacen_principal_id: ID del almacén principal
        min_dias_exportacion: Días mínimos de vida útil para considerar exportable (default: 180 = 6 meses)
    
    Returns:
        {
            '31126PER00003': {
                'disponible_total': 5000,           # Stock físico total
                'exportable': 2500,                  # Stock con >6 meses vida útil
                'solo_local': 2000,                  # Stock con 1-6 meses vida útil
                'por_vencer': 500,                   # Stock con <1 mes vida útil
                'reservado': 450,
                'en_transito': 300,                  # Desde purchase orders
                'expiracion_proxima': '2026-04-15', # Lote con expiración más próxima
                'dias_expiracion': 48,               # Días hasta expiración más próxima
                'estado': 'exportable' | 'solo_local' | 'sin_stock' | 'por_vencer',
                'lotes': [                           # Detalle por lote (Fase 2)
                    {'lote': 'A123', 'cantidad': 1000, 'expira': '2027-08-15', 'exportable': True},
                    {'lote': 'Z999', 'cantidad': 500, 'expira': '2026-04-15', 'exportable': False}
                ]
            }
        }
    """
    pass
```

### 2. Modificar `app.py`: Agregar info de stock al procesar pending_data

```python
# En la función que genera products_chart_data
product_codes = [p['codigo'] for p in pending_data]
stock_info = odoo_manager.get_stock_availability(product_codes, min_dias_exportacion=180)

# Agregar 'stock_status' a cada producto con diferenciación exportable/local
for producto in products_chart_data:
    codigo = producto['codigo']
    info = stock_info.get(codigo, {})
    
    # CRÍTICO: Diferenciar stock físico vs stock exportable
    producto['stock_total'] = info.get('disponible_total', 0)
    producto['stock_exportable'] = info.get('exportable', 0)
    producto['stock_solo_local'] = info.get('solo_local', 0)
    producto['stock_por_vencer'] = info.get('por_vencer', 0)
    producto['stock_estado'] = info.get('estado', 'sin_stock')
    producto['expiracion_proxima'] = info.get('expiracion_proxima')
    producto['dias_expiracion'] = info.get('dias_expiracion')
    
    # Para ventas internacionales, priorizar stock exportable
    producto['stock_disponible_real'] = info.get('exportable', 0)  # El que realmente se puede usar
```

### 3. Frontend: Agregar indicador visual con validación de expiración

**En el gráfico:**
```javascript
// Tooltip enriquecido con diferenciación exportable/local
let stockInfo = '';
const stockExportable = productoData.stock_exportable || 0;
const stockSoloLocal = productoData.stock_solo_local || 0;
const stockPorVencer = productoData.stock_por_vencer || 0;
const expiracionProxima = productoData.expiracion_proxima;
const diasExpiracion = productoData.dias_expiracion;

if (stockExportable > 0) {
    stockInfo = `<br/>🟢 Stock exportable: ${stockExportable.toLocaleString()} und`;
    if (expiracionProxima) {
        stockInfo += `<br/>   └─ Expira: ${expiracionProxima} (${diasExpiracion} días)`;
    }
} else if (stockSoloLocal > 0) {
    stockInfo = `<br/>⚠️ Stock solo local: ${stockSoloLocal.toLocaleString()} und`;
    stockInfo += `<br/>   └─ Expira: ${expiracionProxima} (${diasExpiracion} días) - NO exportable`;
} else if (stockPorVencer > 0) {
    stockInfo = `<br/>🔴 Por vencer: ${stockPorVencer.toLocaleString()} und (${diasExpiracion} días) - Liquidar YA`;
} else if (stockEnTransito > 0) {
    stockInfo = `<br/>🔵 En tránsito: ${stockEnTransito.toLocaleString()} und`;
} else {
    stockInfo = `<br/>🔴 Sin stock - Requiere compra urgente`;
}

// CRÍTICO: Diferenciar en el mensaje si hay stock físico pero no exportable
if (stockSoloLocal > 0 && stockExportable === 0) {
    stockInfo += `<br/>⚠️ NOTA: Hay stock físico pero NO es exportable (expira pronto)`;
}
```

**En el modal drill-down:**
Agregar columnas con información de stock y expiración:
- **"Stock Exportable"**: Cantidad con vida útil >6 meses (🟢)
- **"Stock Local"**: Cantidad con vida útil 1-6 meses (⚠️)
- **"Expira"**: Fecha de expiración más próxima
- **"Estado"**: Emoji indicando estado (🟢 Exportable / ⚠️ Solo Local / 🔴 Por Vencer)

Ejemplo de tabla en modal:
```
| Producto          | Pendiente | Stock Export. | Stock Local | Expira     | Estado |
|-------------------|-----------|---------------|-------------|------------|--------|
| HEMATOFOS B12     | 16,296    | 2,500         | 5,500       | 2026-04-15 | ⚠️ Local|
| ANTIBIÓTICO XYZ   | 8,450     | 8,450         | 0           | 2027-09-15 | 🟢 OK   |
```

---

## 📦 Consideraciones de Performance

### Problema: Consultas adicionales pueden ralentizar

**Soluciones:**

1. **Caché agresivo** (stock cambia menos que ventas):
```python
@cache_manager.cache('stock_availability', expire_seconds=900)  # 15 min
def get_stock_availability(...):
    pass
```

2. **Consulta en batch** (1 sola llamada para todos los productos):
```python
# En lugar de N consultas:
stock.quant.search_read([('product_id', 'in', product_ids)])
```

3. **Lazy loading** (solo cuando se expande el detalle):
```javascript
// No cargar stock hasta que usuario haga click en "Ver disponibilidad"
onClick: async (producto) => {
    const stock = await fetch(`/api/stock/${producto.codigo}`);
}
```

4. **Consulta opcional** (parámetro en URL):
```python
# /dashboard?include_stock=true
# Solo usuarios que necesitan stock activan el flag
```

---

## 🚀 Plan de Implementación (Fases)

### **Fase 1: Indicador Simple + Validación de Expiración** (3-4 horas)
- [ ] Agregar método `get_stock_availability()` en `odoo_manager.py`
- [ ] **CRÍTICO:** Consultar `stock.production.lot` con fechas de expiración
- [ ] Calcular stock exportable (>180 días vida útil) vs stock local (<180 días)
- [ ] Integrar en `app.py` al generar `products_chart_data`
- [ ] Mostrar emoji + cantidad + estado de expiración en tooltip:
  - 🟢 Stock exportable (X und, Exp: YYYY-MM-DD)
  - ⚠️ Stock solo local (X und, expira en N días)
  - 🔴 Por vencer (X und, expira en N días - liquidar)
- [ ] Agregar columna "Stock Exportable" en modal drill-down
- [ ] Testear con productos reales que tengan lotes con diferentes fechas
- [ ] Implementar caché de 15 minutos
- [ ] **Validación:** Verificar que stock físico ≠ stock exportable en productos con lotes próximos a vencer

**Resultado:** Usuario ve de un vistazo qué productos están listos para exportar (no solo disponibles en almacén).

### **Fase 2: Detalle Logístico + Breakdown por Lote** (5-6 horas)
- [ ] Consultar órdenes de compra pendientes (`purchase.order.line`)
- [ ] Consultar traslados en proceso (`stock.picking`)
- [ ] **Breakdown por lote:** Mostrar cada lote con su fecha de expiración individual
- [ ] Agregar sección expandible "📦 Detalle Logístico" en modal
- [ ] Mostrar breakdown completo:
  - Disponible exportable (por lote con fecha exp)
  - Disponible solo local (lotes con <6 meses)
  - En traslado (con fechas de expiración)
  - En compra/tránsito
  - Faltante
- [ ] Colores/estados visuales por tipo y estado de expiración
- [ ] Calcular compatibilidad por destino (USA/EUR requiere 6m, LATAM 4m)
- [ ] Sugerencias automáticas: "Lote X: reasignar a mercado local"

**Resultado:** Usuario sabe exactamente qué falta, dónde está, y si puede exportarlo o no.

### **Fase 3: Accionabilidad + Gestión de Lotes Críticos** (3-4 horas - opcional)
- [ ] Botón "Iniciar Traslado" si hay stock en otro almacén
- [ ] Botón "Ver Orden de Compra" con link a Odoo
- [ ] Alerta automática si producto crítico sin plan de abastecimiento
- [ ] **Alerta de lotes por vencer:** "⚠️ 5,500 und de HEMATOFOS expiran en <6 meses"
- [ ] **Sugerencia de reasignación:** "Reasignar Lote Z999 (1,500 und) a pedidos locales"
- [ ] **Acción de liquidación:** "Liquidar urgente: Lote X vence en 15 días"
- [ ] Link directo a gestión de lotes en Odoo para tomar acción inmediata
- [ ] **Priorización inteligente:** Sugerir qué lotes usar para qué pedidos (exportación vs local)

**Resultado:** Dashboard no solo informa, sino que ayuda a tomar acción y previene pérdidas por productos vencidos.

---

## 🎨 Mockup Visual (Modal Expandido - Fase 2)

```
┌─────────────────────────────────────────────────────────────────┐
│ 📦 [31126PER00003] HEMATOFOS B12 (X 100 ML, STD)                │
│ Pedidos pendientes • Avance total: 1.0%                          │
├─────────────────────────────────────────────────────────────────┤
│ 📊 Resumen: 4 pedidos • Cantidad: 16,296 • Monto: $ 422,386    │
│                                                                   │
│ ┌─── 📦 ESTADO LOGÍSTICO ───────────────────────────────────┐  │
│ │ Cantidad pendiente total: 16,296 unidades                  │  │
│ │                                                             │  │
│ │ ✅ Listo para facturar: 1,200 und (7%)   [Almacén Lima]   │  │
│ │    ├─ Lote A123: 800 und (Exp: 2027-08-15) ✓ Exportable  │  │
│ │    └─ Lote B456: 400 und (Exp: 2027-01-10) ✓ Exportable  │  │
│ │                                                             │  │
│ │ 🟡 En otro almacén: 3,500 und (21%)     [Almacén Callao]  │  │
│ │    ├─ Lote C789: 2,500 und (Exp: 2026-12-05) ✓ Exportable│  │
│ │    └─ Lote D111: 1,000 und (Exp: 2027-03-20) ✓ Exportable│  │
│ │    └→ Traslado TRA-00234 (En proceso) • ETA: 2026-02-28   │  │
│ │                                                             │  │
│ │ 🔵 En tránsito: 8,000 und (49%)                            │  │
│ │    └→ OC-12345 • Proveedor XYZ • Llega: 2026-03-15        │  │
│ │                                                             │  │
│ │ ⚠️ Stock NO exportable: 2,900 und (18%) [Almacén Lima]   │  │
│ │    ├─ Lote Z999: 1,500 und (Exp: 2026-04-15) ✗ 48 días   │  │
│ │    └─ Lote Z888: 1,400 und (Exp: 2026-05-01) ✗ 64 días   │  │
│ │    └→ ⚠️ CRÍTICO: Vencen antes de poder exportar          │  │
│ │                                                             │  │
│ │ ❌ Faltante: 3,596 und (22%)                               │  │
│ │    └→ ⚠️  Sin orden de compra activa                       │  │
│ │                                                             │  │
│ │ 📊 RESUMEN EXPORTABLE:                                      │  │
│ │    Stock físico total: 7,600 und                           │  │
│ │    Stock exportable: 4,700 und (62%)                       │  │
│ │    Stock NO exportable: 2,900 und (38%) - Expira pronto   │  │
│ │                                                             │  │
│ │ 💡 Acción recomendada:                                      │  │
│ │    1. Generar OC urgente por 3,596 und                     │  │
│ │    2. Liquidar lotes Z999/Z888 en mercado local           │  │
│ └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│ [Tabla de pedidos...]                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚨 CONSIDERACIÓN CRÍTICA: Fecha de Expiración (Ventas Internacionales)

### ⚠️ NO OLVIDAR: Stock Disponible ≠ Stock Exportable

**Problema real:**
- Odoo puede mostrar 5,000 unidades "disponibles" en almacén
- Pero si 3,000 expiran en 2 meses → **NO son exportables**
- Ventas promete entrega basado en stock "disponible"
- Logística rechaza: "ese lote no se puede exportar"
- Cliente molesto + ventas internacionales perdidas

### 📋 Reglas de Exportación por Destino

| Destino | Vida Útil Mínima Requerida | Ejemplo (Hoy: 2026-02-26) |
|---------|---------------------------|---------------------------|
| **USA** | 6 meses (180 días) | Debe expirar después de: 2026-08-26 |
| **Europa** | 6 meses (180 días) | Debe expirar después de: 2026-08-26 |
| **LATAM** | 4 meses (120 días) | Debe expirar después de: 2026-06-26 |
| **Mercado Local** | 1 mes (30 días) | Debe expirar después de: 2026-03-26 |

### 🔴 Escenarios Críticos a Mostrar

**Escenario 1: Stock "fantasma"**
```
Producto: HEMATOFOS B12
Stock físico en Odoo: 8,000 unidades ✓
Stock exportable (>6 meses): 2,500 unidades ✓
Stock NO exportable (<6 meses): 5,500 unidades ✗
Pedido cliente (USA): 6,000 unidades
Estado real: ❌ FALTANTE 3,500 und - Requiere compra urgente
```

**Escenario 2: Priorización de lotes**
```
Lote A: 1,000 und (Exp: 2026-04-10) → 43 días → Liquidar local ⚡
Lote B: 3,000 und (Exp: 2027-09-15) → 18 meses → Exportar ✅
Lote C: 2,000 und (Exp: 2026-11-20) → 9 meses → Exportar ✅

Decisión automatizada:
- Facturar exportación con Lotes B y C (5,000 und exportables)
- Lote A: Reasignar a pedidos locales o liquidación urgente
```

### 💡 Implementación en Dashboard

**Fase 1 (Simple):**
```javascript
// Mostrar solo si pasa filtro de exportación
if (diasRestantes >= 180) {
    🟢 Stock: 2,500 und (Exp: 2027-09-15) ✓ Exportable
} else if (diasRestantes >= 30) {
    ⚠️ Stock: 5,500 und (Exp: 2026-04-15) ⚡ Solo mercado local
} else {
    🔴 Lote próximo a vencer: 500 und (Exp: 2026-03-05) - Liquidar YA
}
```

**Fase 2 (Detallado):**
- Mostrar breakdown por lote con fecha exacta de expiración
- Calcular automáticamente a qué destinos SÍ se puede enviar cada lote
- Sugerir reasignación de lotes no exportables a mercado local

### 📊 Datos Odoo Necesarios

```python
# Modelo: stock.production.lot
campos_requeridos = [
    'name',                    # Número de lote (ej: LOT-A123)
    'product_id',              # ID del producto
    'expiration_date',         # CRÍTICO: Fecha de vencimiento
    'product_qty',             # Cantidad en este lote
    'location_id',             # Dónde está el lote
]

# Consulta ejemplo:
lotes = models.execute_kw(db, uid, password,
    'stock.production.lot', 'search_read',
    [[['product_id', 'in', product_ids], 
      ['expiration_date', '!=', False]]],
    {'fields': campos_requeridos}
)
```

### ⚡ Accionabilidad

1. **Alerta automática:** "Tienes 5,500 und de HEMATOFOS que expiran en <6 meses. Reasignar a mercado local."
2. **Recomendación de compra:** "Necesitas 3,500 und exportables. OC sugerida: 4,000 und con proveedor XYZ."
3. **Priorización de picking:** "Para pedido PE-00123 (USA), usar Lotes B y C únicamente (exportables)."

### 📝 Checklist de Implementación

**Fase 1:**
- [ ] Consultar `stock.production.lot` para obtener fechas de expiración
- [ ] Calcular días restantes hasta vencimiento
- [ ] Filtrar stock por umbral de exportación (180 días)
- [ ] Mostrar indicador visual: Exportable ✓ / Local ⚡ / Vencer 🔴
- [ ] Tooltip/modal con fecha exacta de expiración más próxima

**Fase 2:**
- [ ] Breakdown por lote individual con expiración
- [ ] Cálculo automático de compatibilidad por destino (USA/EUR/LATAM)
- [ ] Sugerencia de reasignación de lotes a mercado local
- [ ] Alerta de lotes por vencer (<30 días)
- [ ] Link a gestión de lotes en Odoo para acción inmediata

---

## ⚖️ Recomendación Final

**Empezar con Opción A (Indicador Simple):**

✅ **Por qué:**
- Rápido de implementar (medio día)
- Impacto visual inmediato
- No afecta performance significativamente
- Valida la utilidad antes de invertir más

✅ **Siguiente paso natural:**
Si el equipo lo usa mucho y pide más detalle → Fase 2 (Detalle Logístico)

✅ **Métricas de éxito:**
- "Ahora sé qué productos puedo facturar hoy"
- "Redujimos tiempo de búsqueda de stock en X%"
- "Identificamos cuellos de botella más rápido"

---

## 📌 Siguiente Acción

¿Procedemos con **Fase 1: Indicador Simple + Validación de Expiración**?

Si apruebas, implemento:
1. Consulta de stock en `odoo_manager.py` (con `stock.production.lot` para fechas)
2. Cálculo de stock exportable vs no exportable (filtro de 180 días para internacional)
3. Integración en `products_chart_data` con indicadores visuales
4. Display en tooltip y modal:
   - 🟢 Stock exportable (>6 meses vida útil)
   - ⚠️ Stock solo local (<6 meses, >1 mes)
   - 🔴 Lote por vencer (<1 mes)
5. Caché de 15 minutos para no impactar performance

**⚠️ CRÍTICO:** La solución diferenciará entre "stock físico disponible" y "stock exportable", evitando promesas de venta que no se pueden cumplir.

Tiempo estimado: 3-4 horas (incluye lógica de expiración).
