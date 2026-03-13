# 🎯 GUÍA RÁPIDA: ¿Qué Archivo Necesito?

> Elige según tu situación y nivel de experiencia

---

## 🤖 Para Agentes IA (Claude, ChatGPT, etc.)

### Si el agente tiene contexto del problema
**Usa:** [COPY_PASTE_PARA_CLAUDE.md](COPY_PASTE_PARA_CLAUDE.md)
- ✅ Instrucciones directas y ejecutables
- ✅ Código copy-paste listo
- ✅ Sin explicaciones innecesarias
- ⏱️ 2 minutos de lectura

### Si el agente necesita instrucciones detalladas
**Usa:** [PROMPT_PARA_AGENTE_IA.md](PROMPT_PARA_AGENTE_IA.md)
- ✅ Paso a paso completo
- ✅ Contexto del problema
- ✅ Múltiples escenarios
- ⏱️ 5 minutos de lectura

### Si el agente trabaja con checklist
**Usa:** [CHECKLIST_MIGRACION.md](CHECKLIST_MIGRACION.md)
- ✅ Lista verificable paso a paso
- ✅ Estimación de tiempos
- ✅ Criterios de éxito claros
- ⏱️ 50 minutos de ejecución

---

## 👨‍💻 Para Desarrolladores Humanos

### Si tienes 15 minutos
**Usa:** [QUICK_START_MIGRACION.md](QUICK_START_MIGRACION.md)
- ✅ Lo mínimo necesario
- ✅ Copy-paste rápido
- ✅ Sin teoría extra
- ⏱️ 15 minutos implementación

### Si quieres entender todo el contexto
**Usa:** [guia-migracion-xmlrpc-a-jsonrpc.md](guia-migracion-xmlrpc-a-jsonrpc.md)
- ✅ Explicación técnica completa
- ✅ Comparativas XML-RPC vs JSON-RPC
- ✅ Ejemplos detallados
- ⏱️ 30 minutos de lectura

### Si necesitas ver código real
**Usa:** [EJEMPLO_ANTES_DESPUES.md](EJEMPLO_ANTES_DESPUES.md)
- ✅ Código completo antes/después
- ✅ Comparación visual
- ✅ Comentarios en cada cambio
- ⏱️ 10 minutos de lectura

---

## 🏢 Para Equipos y Managers

### Si reportas al admin de Odoo
**Usa:** [reporte-error-odoo.md](reporte-error-odoo.md)
- ✅ Análisis técnico del problema
- ✅ Soluciones alternativas
- ✅ Impacto en el negocio
- ⏱️ Documento formal

### Si necesitas documentación completa del proyecto
**Usa:** [README_MIGRACION_JSONRPC.md](README_MIGRACION_JSONRPC.md)
- ✅ Índice de todos los recursos
- ✅ Casos de uso (Flask/Django/FastAPI)
- ✅ FAQ y troubleshooting
- ⏱️ Referencia completa

---

## 🧪 Para Testing

### Probar antes de migrar
**Usa:** [`../test_odoo_jsonrpc.py`](../test_odoo_jsonrpc.py)
```bash
python test_odoo_jsonrpc.py
```
- ✅ Verifica que JSON-RPC funciona
- ✅ Colores y feedback visual
- ✅ Prueba todos los métodos

### Cliente JSON-RPC reutilizable
**Usa:** [`../odoo_jsonrpc_client.py`](../odoo_jsonrpc_client.py)
```python
from odoo_jsonrpc_client import OdooJSONRPCClient
client = OdooJSONRPCClient(url, db, user, pwd)
```
- ✅ Clase completa y documentada
- ✅ Métodos de conveniencia
- ✅ Manejo de errores

### Ver todas las alternativas
**Usa:** [`../odoo_connector_alternativo.py`](../odoo_connector_alternativo.py)
- ✅ 4 métodos de conexión
- ✅ Comparativa automática
- ✅ Útil para debugging

---

## 🎓 Flujo Recomendado

### Para implementar en un proyecto nuevo (Primera vez)

```
1. Lee: QUICK_START_MIGRACION.md (15 min)
   ↓
2. Prueba: python test_odoo_jsonrpc.py (2 min)
   ↓
3. Mira: EJEMPLO_ANTES_DESPUES.md (10 min)
   ↓
4. Implementa: Copia código de ejemplo (15 min)
   ↓
5. Verifica: Sigue CHECKLIST_MIGRACION.md (10 min)
   ↓
6. ✅ Listo!
```

**Tiempo total:** ~50 minutos

### Para pasarle el trabajo a un agente IA

```
1. Copia contenido de: COPY_PASTE_PARA_CLAUDE.md
   ↓
2. Pégalo en el chat con Claude/ChatGPT
   ↓
3. Adjunta tu archivo odoo_manager.py
   ↓
4. El agente hace los cambios
   ↓
5. ✅ Verificas con test_odoo_jsonrpc.py
```

**Tiempo total:** ~10 minutos

### Para entender el problema a fondo

```
1. Lee: reporte-error-odoo.md (10 min)
   ↓
2. Lee: guia-migracion-xmlrpc-a-jsonrpc.md (30 min)
   ↓
3. Compara: EJEMPLO_ANTES_DESPUES.md (10 min)
   ↓
4. ✅ Ya entiendes todo el contexto
```

**Tiempo total:** ~50 minutos

---

## 📦 Kit de Migración Mínimo

Si solo puedes copiar 2 archivos a otro proyecto:

1. **`odoo_jsonrpc_client.py`** - Cliente reutilizable
2. **`COPY_PASTE_PARA_CLAUDE.md`** - Instrucciones mínimas

Con eso es suficiente para migrar cualquier proyecto.

---

## 🆘 Ayuda Rápida

### "¿Por dónde empiezo?"
→ [QUICK_START_MIGRACION.md](QUICK_START_MIGRACION.md)

### "Necesito el código exacto"
→ [EJEMPLO_ANTES_DESPUES.md](EJEMPLO_ANTES_DESPUES.md)

### "Quiero que un agente IA lo haga"
→ [COPY_PASTE_PARA_CLAUDE.md](COPY_PASTE_PARA_CLAUDE.md)

### "Necesito entender el problema"
→ [guia-migracion-xmlrpc-a-jsonrpc.md](guia-migracion-xmlrpc-a-jsonrpc.md)

### "Quiero verificar que funciona"
→ Ejecuta `python test_odoo_jsonrpc.py`

### "Algo salió mal"
→ Sección Troubleshooting en [README_MIGRACION_JSONRPC.md](README_MIGRACION_JSONRPC.md)

---

## 📚 Tabla Resumen de Archivos

| Archivo | Tipo | Para | Tiempo | Complejidad |
|---------|------|------|--------|-------------|
| **COPY_PASTE_PARA_CLAUDE.md** | Prompt | Agentes IA | 2 min | ⭐ Muy fácil |
| **QUICK_START_MIGRACION.md** | Tutorial | Devs rápidos | 15 min | ⭐⭐ Fácil |
| **EJEMPLO_ANTES_DESPUES.md** | Referencia | Visual | 10 min | ⭐⭐ Fácil |
| **CHECKLIST_MIGRACION.md** | Checklist | Metódicos | 50 min | ⭐⭐ Fácil |
| **PROMPT_PARA_AGENTE_IA.md** | Prompt | Agentes IA | 5 min | ⭐⭐ Fácil |
| **guia-migracion-xmlrpc-a-jsonrpc.md** | Guía | Técnicos | 30 min | ⭐⭐⭐ Media |
| **README_MIGRACION_JSONRPC.md** | Índice | Todos | - | ⭐ Referencia |
| **reporte-error-odoo.md** | Reporte | Managers | 15 min | ⭐⭐ Media |
| **odoo_jsonrpc_client.py** | Código | Reutilizar | - | ⭐⭐⭐ Media |
| **test_odoo_jsonrpc.py** | Test | Testing | 2 min | ⭐ Muy fácil |

---

## 🎯 Casos de Uso Específicos

### "Tengo que arreglarlo YA en producción"
1. `test_odoo_jsonrpc.py` → verifica que JSON-RPC funciona
2. `QUICK_START_MIGRACION.md` → implementa lo mínimo
3. Deploy y monitorea

### "Quiero hacerlo bien y entender todo"
1. `guia-migracion-xmlrpc-a-jsonrpc.md` → lee completo
2. `EJEMPLO_ANTES_DESPUES.md` → ve las diferencias
3. `CHECKLIST_MIGRACION.md` → sigue paso a paso
4. Documenta tu experiencia

### "Soy nuevo en el proyecto"
1. `reporte-error-odoo.md` → entiende el problema
2. `QUICK_START_MIGRACION.md` → aprende la solución
3. `EJEMPLO_ANTES_DESPUES.md` → ve el código
4. Implementa con confianza

### "Voy a hacer esto en 10 proyectos"
1. Copia `odoo_jsonrpc_client.py` a tu toolkit
2. Guarda `COPY_PASTE_PARA_CLAUDE.md` como snippet
3. Automatiza con script el proceso
4. Capacita al equipo con `QUICK_START_MIGRACION.md`

---

## 📞 Preguntas Frecuentes

**P: ¿Qué archivo le paso a otro desarrollador?**
R: `QUICK_START_MIGRACION.md` + `EJEMPLO_ANTES_DESPUES.md`

**P: ¿Qué archivo le paso a un agente IA?**
R: `COPY_PASTE_PARA_CLAUDE.md`

**P: ¿Qué archivo necesito para entender el bug?**
R: `reporte-error-odoo.md`

**P: ¿Hay un TL;DR?**
R: Sí: XML-RPC está bugueado, usa JSON-RPC. Código en `EJEMPLO_ANTES_DESPUES.md`

**P: ¿Puedo usar esto en proyectos comerciales?**
R: Sí, licencia MIT.

---

## ✨ Recomendación Final

**Si solo tienes 5 minutos:**
→ Lee [COPY_PASTE_PARA_CLAUDE.md](COPY_PASTE_PARA_CLAUDE.md) y pásaselo a Claude

**Si tienes 15 minutos:**
→ Sigue [QUICK_START_MIGRACION.md](QUICK_START_MIGRACION.md)

**Si tienes 1 hora:**
→ Lee [guia-migracion-xmlrpc-a-jsonrpc.md](guia-migracion-xmlrpc-a-jsonrpc.md) completa

**Si eres admin de Odoo:**
→ Lee [reporte-error-odoo.md](reporte-error-odoo.md) y arregla el módulo

---

**Última actualización:** Marzo 2026  
**Mantenedor:** Jonathan Cerda  
**Licencia:** MIT
