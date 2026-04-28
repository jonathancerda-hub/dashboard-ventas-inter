# Sistema de Evaluación de Riesgo en Entregas (Gráfico V2)

## 📊 Objetivo

El gráfico "Avance de Facturación por Cliente (Versión 2)" evalúa el **riesgo de cumplimiento** de cada fecha de entrega usando una **lógica híbrida** que combina:
1. **Tiempo restante** (urgencia)
2. **Avance de facturación** (rendimiento)

---

## 🎯 Concepto Clave

**El color del estado combina dos factores:**

1. **Urgencia (tiempo restante):** Define el color base según cuánto tiempo falta
2. **Rendimiento (brecha facturado vs esperado):** Ajusta el color según el avance real

**¿Por qué lógica híbrida?**
- Un pedido con 63 días (amarillo base) pero 90% facturado (muy adelantado) → merece ser VERDE
- Un pedido con 100 días (verde base) pero 5% facturado vs 30% esperado → merece ser AMARILLO
- Combina la urgencia del tiempo con la realidad del progreso

---

## 📐 Lógica de Evaluación (Híbrida)

### Paso 1: Color Base por Tiempo Restante

| Tiempo Restante | Color Base |
|-----------------|------------|
| **< 30 días** | 🔴 Rojo (urgente) |
| **30-89 días** | 🟡 Amarillo (atención media) |
| **≥ 90 días** | 🟢 Verde (tiempo suficiente) |
| **Fecha pasada** | 🔴 Granate (vencido - no se ajusta) |

### Paso 2: Ajuste por Brecha (Gap)

```
Gap = % Facturado Real - % Esperado
```

| Color Base | Gap | Ajuste | Color Final |
|------------|-----|--------|-------------|
| 🔴 Rojo | ≥ +20% | Mejora | 🟡 Amarillo |
| 🔴 Rojo | < +20% | Sin cambio | 🔴 Rojo |
| 🟡 Amarillo | ≥ +20% | Mejora | 🟢 Verde |
| 🟡 Amarillo | -19% a +19% | Sin cambio | 🟡 Amarillo |
| 🟡 Amarillo | ≤ -20% | Empeora | 🔴 Rojo |
| 🟢 Verde | ≥ -19% | Sin cambio | 🟢 Verde |
| 🟢 Verde | ≤ -20% | Empeora | 🟡 Amarillo |
| 🔴 Granate | Cualquiera | Sin cambio | 🔴 Granate |

### Información Adicional (Siempre Visible)

- **% Facturado Real:** Cuánto se ha facturado del pedido
- **% Esperado:** Cuánto debería llevar facturado según los días restantes (calculado con período estándar de 120 días)
  - Fórmula: `% esperado = (120 - días restantes) / 120 × 100`
  - Ejemplo: Si faltan 60 días → (120-60)/120 = 50% esperado
  - Ejemplo: Si faltan 30 días → (120-30)/120 = 75% esperado
- **Línea vertical "|":** Marca visual del % esperado en la barra de progreso
- **Días restantes:** Tiempo hasta la fecha de entrega

---

## 🎨 Estados y Colores

| Estado | Color | Condición | Significado |
|--------|-------|-----------|-------------|
| **En ritmo** | 🟢 Verde | ≥ 90 días O (+20% adelantado con 30-89 días) | Situación favorable |
| **Leve retraso** | 🟡 Amarillo | 30-89 días O (muy adelantado con <30 días) O (muy atrasado con ≥90 días) | Atención necesaria |
| **Riesgo real** | 🔴 Rojo | < 30 días O (muy atrasado con 30-89 días) | Urgente |
| **Vencido** | 🔴 Granate | Fecha de entrega pasada | Acción inmediata |

---

## 💡 Ejemplos Prácticos

### Caso 1: Pedido Urgente Muy Atrasado 🔴

**Pedido S01937**
- **Fecha de entrega:** 15 May 2026
- **Hoy:** 28 Abr 2026
- **Días restantes:** 17 días
- **% Facturado:** 0%
- **% Esperado:** 86% (calculado: (120-17)/120 × 100)
- **Gap:** 0% - 86% = **-86%**

**Evaluación:**
```
Paso 1: 17 días < 30 días → Color base: ROJO
Paso 2: Gap = -86% (< -20% = muy atrasado) → Sin cambio (ya está en rojo)
```

**Resultado:** 🔴 **Riesgo real**

**Interpretación:** Urgente (17 días) Y muy atrasado (-86%). Doble problema.

---

### Caso 2: Pedido a 2 Meses con Excelente Avance 🟢

**Pedido S01941**
- **Fecha de entrega:** 29 Jun 2026
- **Hoy:** 28 Abr 2026
- **Días restantes:** 63 días
- **% Facturado:** 90%
- **% Esperado:** 48% (calculado: (120-63)/120 × 100)
- **Gap:** 90% - 48% = **+42%**

**Evaluación:**
```
Paso 1: 63 días → Entre 30-90 días → Color base: AMARILLO
Paso 2: Gap = +42% (≥ +20% = muy adelantado) → MEJORA a VERDE
```

**Resultado:** 🟢 **En ritmo** ✅

**Interpretación:** Aunque solo quedan 2 meses, va tan adelantado (+42%) que merece ser verde. Excelente gestión.

---

### Caso 3: Pedido con Mucho Tiempo pero Sin Urgencia 🟢

**Pedido S16184**
- **Fecha de entrega:** 23 Sep 2026
- **Hoy:** 28 Abr 2026
- **Días restantes:** 148 días
- **% Facturado:** 5%
- **% Esperado:** 0% (calculado: (120-148)/120 × 100 = -23%, limitado a 0%)
- **Gap:** 5% - 0% = **+5%**

**Evaluación:**
```
Paso 1: 148 días ≥ 90 días → Color base: VERDE
Paso 2: Gap = +5% (entre -19% y +19% = sin ajuste) → Sin cambio
```

**Resultado:** 🟢 **En ritmo** ✅

**Interpretación:** Tiene casi 5 meses (148 días). Como supera los 120 días estándar, el % esperado es 0%. Cualquier avance (5%) es aceptable.

---

### Caso 4: Pedido Urgente pero Casi Completo 🟡

**Pedido S10890**
- **Fecha de entrega:** 2 May 2026
- **Hoy:** 28 Abr 2026
- **Días restantes:** 4 días
- **% Facturado:** 97%
- **% Esperado:** 97% (calculado: (120-4)/120 × 100)
- **Gap:** 97% - 97% = **0%**

**Evaluación:**
```
Paso 1: 4 días < 30 días → Color base: ROJO
Paso 2: Gap = 0% (< +20% = no hay mejora suficiente) → Sin cambio
```

**Resultado:** 🔴 **Riesgo real**

**Interpretación:** Muy urgente (4 días). Aunque va perfecto (97% facturado = 97% esperado), no está lo suficientemente adelantado para mejorar el color. Sigue siendo rojo por urgencia.

---

### Caso 5: Pedido Medio Plazo Muy Atrasado 🔴

**Pedido S06848**
- **Fecha de entrega:** 30 Jun 2026
- **Hoy:** 28 Abr 2026
- **Días restantes:** 63 días
- **% Facturado:** 10%
- **% Esperado:** 48% (calculado: (120-63)/120 × 100)
- **Gap:** 10% - 48% = **-38%**

**Evaluación:**
```
Paso 1: 63 días → Entre 30-90 días → Color base: AMARILLO
Paso 2: Gap = -38% (≤ -20% = muy atrasado) → EMPEORA a ROJO
```

**Resultado:** 🔴 **Riesgo real** 🚨

**Interpretación:** Aunque tiene 2 meses, va TAN atrasado (-38%) que se convierte en riesgo real. Requiere intervención urgente.

---

## 🔍 Puntos Clave para Recordar

1. **El color combina urgencia (tiempo) + rendimiento (avance)**
   - No es solo tiempo, ni solo % facturado
   - Es una evaluación híbrida inteligente

2. **Umbrales de ajuste: ±20%**
   - Muy adelantado (+20%): Mejora un nivel
   - Muy atrasado (-20%): Empeora un nivel
   - Entre -19% y +19%: Sin cambio

3. **% Esperado calculado con período estándar de 120 días:**
   - Fórmula: `(120 - días restantes) / 120 × 100`
   - Si faltan 60 días → 50% esperado
   - Si faltan 90 días → 25% esperado
   - Si faltan más de 120 días → 0% esperado (sin urgencia)

4. **Ejemplos de lógica híbrida:**
   - 63 días (amarillo) + 90% facturado vs 48% esperado (+42%) = 🟢 VERDE
   - 63 días (amarillo) + 10% facturado vs 48% esperado (-38%) = 🔴 ROJO
   - 148 días (verde) + 5% facturado vs 0% esperado (+5%) = 🟢 VERDE (sin ajuste)

5. **Vencidos nunca mejoran:** Si la fecha pasó, siempre es granate independiente del avance

6. **La línea vertical "|" es clave:** Muestra visualmente dónde deberías estar. Si la barra de color está muy lejos de la línea, el gap es grande.

7. **Beneficios de esta lógica:**
   - ✅ Reconoce pedidos bien gestionados (adelantados) aunque tengan poco tiempo
   - ✅ Alerta sobre pedidos con mucho tiempo pero muy atrasados
   - ✅ Balance entre urgencia y rendimiento real

---

## 📋 Estados de Pedido (Badges)

Adicionalmente, cada pedido muestra su estado operativo en Odoo:

- 🟢 **Orden de venta** (`sale`) - Confirmado, en proceso
- 🟡 **En créditos** (`credit`) - Esperando aprobación de crédito
- 🔵 **En logística** (`done`) - Listo para despacho/facturación

Estos badges ayudan a identificar bloqueos operativos independientes del riesgo de tiempo.

---

## 📌 Uso del Dashboard

### Vista General
Muestra todos los clientes con pedidos activos, ordenados alfabéticamente. El color indica la urgencia del tiempo restante.

### Vista Cliente
Al hacer clic en un cliente, se muestra:
- **Timeline horizontal** con hitos numerados por fecha de entrega
- **Resumen del cliente** con meta total, facturado total y % global
- **Detalle por fecha** con:
  - Pedidos asociados y sus estados operativos
  - Barra de progreso con % facturado real
  - Línea vertical mostrando % esperado (referencia)
  - Días restantes hasta entrega
  - Color del estado según urgencia de tiempo

---

## 🎓 Conclusión

Este sistema permite **identificar el riesgo real** combinando dos dimensiones:

**Pregunta 1:** ¿Cuánto tiempo me queda? (Urgencia)
**Pregunta 2:** ¿Voy adelantado o atrasado según un ritmo estándar? (Rendimiento)

**Cálculo del % esperado:**
- Se usa un **período estándar de 120 días** como referencia
- Fórmula: `% esperado = (120 - días restantes) / 120 × 100`
- **NO depende** de la fecha de confirmación del pedido (evita distorsiones por pedidos antiguos)
- Más justo: todos los pedidos se miden con el mismo estándar

**Ventajas de la lógica híbrida:**
- ✅ **Más justa:** Reconoce pedidos bien gestionados aunque sean urgentes
- ✅ **Más precisa:** Detecta problemas antes (ej: plazo medio pero muy atrasado)
- ✅ **Más útil:** El color refleja el riesgo REAL, no solo la urgencia
- ✅ **Balance perfecto:** Combina la presión del tiempo con la realidad del avance
- ✅ **Refleja la gestión:** Un pedido cercano con 90% facturado demuestra buena planificación
- ✅ **Sin distorsiones:** Pedidos antiguos no tienen % esperado inflado artificialmente

**Casos que la lógica híbrida resuelve mejor:**
- Pedido a 60 días con 90% facturado → 🟢 Verde (va muy adelantado +42%)
- Pedido a 60 días con 10% facturado → 🔴 Rojo (va muy atrasado -38%)
- Pedido a 150 días con 5% facturado → 🟢 Verde (tiene mucho tiempo, sin urgencia)

---

*Documento creado para referencia del equipo de ventas - Dashboard Ventas INTER*
