# 📦 Solución JSON-RPC para Odoo - Kit Completo de Migración

Este directorio contiene la solución completa para migrar proyectos Python + Odoo de XML-RPC a JSON-RPC, evitando el bug del módulo `cs_login_audit_log`.

---

## 📁 Archivos Incluidos

### 🚀 Para Empezar Rápido
| Archivo | Descripción | Para quién |
|---------|-------------|------------|
| **[QUICK_START_MIGRACION.md](QUICK_START_MIGRACION.md)** | Guía rápida de 15 minutos | Desarrolladores que quieren migrar ya |
| **[test_odoo_jsonrpc.py](../test_odoo_jsonrpc.py)** | Script de prueba independiente | Verificar que JSON-RPC funciona |

### 📚 Documentación Completa
| Archivo | Descripción | Para quién |
|---------|-------------|------------|
| **[guia-migracion-xmlrpc-a-jsonrpc.md](guia-migracion-xmlrpc-a-jsonrpc.md)** | Guía técnica completa | Arquitectos, líderes técnicos |
| **[reporte-error-odoo.md](reporte-error-odoo.md)** | Análisis del problema | Administradores de Odoo |

### 🔧 Código Reutilizable
| Archivo | Descripción | Ubicación |
|---------|-------------|-----------|
| **[odoo_jsonrpc_client.py](../odoo_jsonrpc_client.py)** | Cliente JSON-RPC completo | Copia a tu proyecto |
| **[odoo_connector_alternativo.py](../odoo_connector_alternativo.py)** | 4 métodos de conexión | Referencia/testing |

---

## 🎯 ¿Qué Archivo Necesito?

### Si tienes 5 minutos
```bash
# 1. Descarga el cliente
curl -O odoo_jsonrpc_client.py

# 2. Pruébalo
python test_odoo_jsonrpc.py

# 3. Sigue QUICK_START_MIGRACION.md
```

### Si tienes 30 minutos
Lee **guia-migracion-xmlrpc-a-jsonrpc.md** completa para entender:
- Por qué ocurre el problema
- Comparación XML-RPC vs JSON-RPC
- Implementación paso a paso
- Ejemplos de código

### Si necesitas documentar el problema
Envía **reporte-error-odoo.md** a tu equipo o admin de Odoo con:
- Diagnóstico técnico completo
- 4 soluciones alternativas
- Archivos de prueba

---

## 🚀 Quick Start

### 1. Verifica que JSON-RPC funciona
```bash
cd tu-proyecto/
python test_odoo_jsonrpc.py
```

**Salida esperada:**
```
✅ Endpoint JSON-RPC activo
✅ Autenticación exitosa
✅ TODAS LAS PRUEBAS EXITOSAS
```

### 2. Copia el cliente JSON-RPC
```bash
cp odoo_jsonrpc_client.py tu-proyecto/
```

### 3. Actualiza tu código

**Antes (XML-RPC):**
```python
import xmlrpc.client

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, user, pwd, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

partners = models.execute_kw(
    db, uid, pwd,
    'res.partner', 'search_read',
    [[]], {'limit': 10}
)
```

**Después (JSON-RPC):**
```python
from odoo_jsonrpc_client import OdooJSONRPCClient

client = OdooJSONRPCClient(url, db, user, pwd)

partners = client.search_read(
    'res.partner',
    domain=[],
    limit=10
)
```

---

## 📊 Comparación de Soluciones

| Aspecto | XML-RPC | JSON-RPC (esta solución) |
|---------|---------|-------------------------|
| **Bug cs_login_audit_log** | ❌ Afectado | ✅ No afectado |
| **Velocidad** | Regular | ✅ Más rápido |
| **Tamaño payload** | Grande (XML) | ✅ Pequeño (JSON) |
| **Debugging** | Difícil | ✅ Fácil |
| **Código necesario** | 10+ líneas | ✅ 3 líneas |
| **Cambios en servidor** | No | ✅ No |
| **Compatibilidad API** | Completa | ✅ Completa |

---

## 🧪 Testing

### Test Básico
```bash
python test_odoo_jsonrpc.py
```

### Test con tu Cliente Actual
```python
from odoo_jsonrpc_client import OdooJSONRPCClient
import os

client = OdooJSONRPCClient(
    url=os.getenv('ODOO_URL'),
    db=os.getenv('ODOO_DB'),
    username=os.getenv('ODOO_USER'),
    password=os.getenv('ODOO_PASSWORD')
)

# Prueba con tus modelos
result = client.search_read('tu.modelo', domain=[], limit=5)
print(f"✅ {len(result)} registros encontrados")
```

---

## 📖 Casos de Uso

### Flask
```python
from flask import Flask, jsonify
from odoo_jsonrpc_client import OdooJSONRPCClient
import os

app = Flask(__name__)
odoo = OdooJSONRPCClient(
    os.getenv('ODOO_URL'),
    os.getenv('ODOO_DB'),
    os.getenv('ODOO_USER'),
    os.getenv('ODOO_PASSWORD')
)

@app.route('/api/products')
def get_products():
    products = odoo.search_read(
        'product.product',
        domain=[],
        fields=['name', 'list_price'],
        limit=20
    )
    return jsonify(products)
```

### Django
```python
# settings.py
from odoo_jsonrpc_client import OdooJSONRPCClient
import os

ODOO = OdooJSONRPCClient(
    os.getenv('ODOO_URL'),
    os.getenv('ODOO_DB'),
    os.getenv('ODOO_USER'),
    os.getenv('ODOO_PASSWORD')
)

# views.py
from django.conf import settings
from django.http import JsonResponse

def products_view(request):
    products = settings.ODOO.search_read('product.product', [], limit=20)
    return JsonResponse({'products': products})
```

### FastAPI
```python
from fastapi import FastAPI
from odoo_jsonrpc_client import OdooJSONRPCClient
import os

app = FastAPI()
odoo = OdooJSONRPCClient(
    os.getenv('ODOO_URL'),
    os.getenv('ODOO_DB'),
    os.getenv('ODOO_USER'),
    os.getenv('ODOO_PASSWORD')
)

@app.get("/products")
async def get_products():
    products = odoo.search_read('product.product', [], limit=20)
    return {"products": products}
```

---

## 🐛 Troubleshooting

### Error: "Connection refused"
```bash
# Verifica la URL
curl -I https://tu-odoo.com/jsonrpc

# Debe responder 405 (Method Not Allowed) en GET,
# pero significa que el endpoint existe
```

### Error: "Invalid credentials"
```python
# Prueba login en web primero
# Si web funciona pero JSON-RPC no, revisa:
# - Espacios extra en variables de entorno
# - Caracteres especiales en la contraseña

# Solución: usar API Key en lugar de password
# (Odoo > Preferencias > API Keys)
```

### Error: "Module not found: requests"
```bash
pip install requests
```

---

## 📝 Changelog

### v1.0 (Marzo 2026)
- ✅ Cliente JSON-RPC completo
- ✅ Guía de migración rápida
- ✅ Documentación técnica completa
- ✅ Scripts de prueba
- ✅ Ejemplos para Flask/Django/FastAPI

---

## 🤝 Contribuir

¿Mejoras o encontraste un bug?

1. Abre un issue describiendo el problema
2. Si tienes la solución, envía un PR
3. Actualiza la documentación relevant

---

## 📞 Soporte

**Para problemas técnicos:**
1. Ejecuta `python test_odoo_jsonrpc.py` y comparte el output
2. Revisa la sección Troubleshooting en la guía
3. Verifica que tu Odoo sea versión 9+ (JSON-RPC no existe en v8)

**Recursos adicionales:**
- [Documentación oficial Odoo External API](https://www.odoo.com/documentation/16.0/developer/reference/external_api.html)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

---

## 📄 Licencia

MIT License - Libre para usar en proyectos comerciales y personales.

---

## ✍️ Autor

**Jonathan Cerda**  
Desarrollador - Dashboard Ventas INTER  
Marzo 2026

**Contexto:** Solución desarrollada para evitar el bug del módulo `cs_login_audit_log` en Odoo que bloquea conexiones XML-RPC desde integraciones externas.

---

## ⭐ Agradecimientos

Si esta solución te ayudó:
- Dale una ⭐ al repositorio
- Comparte con otros desarrolladores que usen Odoo
- Documenta tu experiencia de migración

---

**Última actualización:** 13 de marzo de 2026
