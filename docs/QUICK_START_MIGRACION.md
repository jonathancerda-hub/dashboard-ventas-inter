# 🚀 Quick Start: Migrar tu Proyecto Odoo a JSON-RPC

> **Problema:** ¿Tu app Python + Odoo falla con `RuntimeError: object unbound` del módulo `cs_login_audit_log`?  
> **Solución:** Migra de XML-RPC a JSON-RPC en 3 pasos (15 minutos)

---

## ⚡ Versión Ultra Rápida (3 pasos)

### 1️⃣ Copia el cliente JSON-RPC
```bash
# Descarga el archivo
curl -O https://raw.githubusercontent.com/tu-repo/odoo_jsonrpc_client.py

# O copia manualmente odoo_jsonrpc_client.py a tu proyecto
```

### 2️⃣ Instala dependencias
```bash
pip install requests
```

### 3️⃣ Reemplaza tu código
**Antes:**
```python
import xmlrpc.client

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

**Después:**
```python
from odoo_jsonrpc_client import OdooJSONRPCClient

client = OdooJSONRPCClient(url, db, username, password)
# Ya está autenticado y listo para usar
```

**Llamadas al modelo:**
```python
# Antes
result = models.execute_kw(db, uid, password, 'res.partner', 'search_read', [[]], {'limit': 10})

# Después
result = client.search_read('res.partner', domain=[], limit=10)
```

✅ ¡Listo! Tu código ahora evita el bug.

---

## 📋 Migración Paso a Paso

### Método 1: Usar el Cliente Standalone

Si quieres una solución limpia y moderna:

1. **Copia estos archivos a tu proyecto:**
   - `odoo_jsonrpc_client.py`

2. **Actualiza tu código:**
```python
# En tu archivo principal (ej: main.py, app.py)

# ANTES
import xmlrpc.client
import os

url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USER')
password = os.getenv('ODOO_PASSWORD')

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Buscar productos
product_ids = models.execute_kw(
    db, uid, password,
    'product.product', 'search',
    [[('active', '=', True)]], {'limit': 10}
)

# Leer productos
products = models.execute_kw(
    db, uid, password,
    'product.product', 'read',
    [product_ids], {'fields': ['name', 'default_code']}
)
```

```python
# DESPUÉS
from odoo_jsonrpc_client import OdooJSONRPCClient
import os

client = OdooJSONRPCClient(
    url=os.getenv('ODOO_URL'),
    db=os.getenv('ODOO_DB'),
    username=os.getenv('ODOO_USER'),
    password=os.getenv('ODOO_PASSWORD')
)

# Buscar y leer en una sola operación (más eficiente)
products = client.search_read(
    'product.product',
    domain=[('active', '=', True)],
    fields=['name', 'default_code'],
    limit=10
)
```

### Método 2: Migrar Clase Existente

Si tienes una clase `OdooManager` o similar:

```python
# En tu odoo_manager.py o similar

# AGREGAR al inicio
import requests
import json

class OdooManager:
    def __init__(self):
        # ... tu código existente ...
        
        # REEMPLAZAR la sección de autenticación:
        
        # ANTES (borrar esto)
        # common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        # self.uid = common.authenticate(self.db, self.username, self.password, {})
        # self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        
        # DESPUÉS (usar esto)
        self.jsonrpc_url = f"{self.url}/jsonrpc"
        self.rpc_timeout = 30
        
        # Autenticar via JSON-RPC
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [self.db, self.username, self.password, {}]
            },
            "id": 1
        }
        
        response = requests.post(self.jsonrpc_url, json=payload, headers=headers, timeout=self.rpc_timeout)
        result = response.json()
        
        if "result" in result and result["result"]:
            self.uid = result["result"]
            self.models = self._create_jsonrpc_proxy()
        else:
            self.uid = None
            self.models = None
    
    def _create_jsonrpc_proxy(self):
        """Wrapper para mantener compatibilidad con código XML-RPC"""
        class JSONRPCProxy:
            def __init__(self, manager):
                self.manager = manager
            
            def execute_kw(self, db, uid, password, model, method, args, kwargs=None):
                if kwargs is None:
                    kwargs = {}
                
                headers = {"Content-Type": "application/json"}
                payload = {
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "service": "object",
                        "method": "execute_kw",
                        "args": [db, uid, password, model, method, args, kwargs]
                    },
                    "id": 1
                }
                
                response = requests.post(
                    self.manager.jsonrpc_url,
                    json=payload,
                    headers=headers,
                    timeout=self.manager.rpc_timeout
                )
                result = response.json()
                
                return result.get("result")
        
        return JSONRPCProxy(self)
```

---

## 🧪 Prueba tu Migración

Crea un archivo `test_conexion.py`:

```python
from odoo_jsonrpc_client import OdooJSONRPCClient
import os
from dotenv import load_dotenv

load_dotenv()

# Test
client = OdooJSONRPCClient(
    url=os.getenv('ODOO_URL'),
    db=os.getenv('ODOO_DB'),
    username=os.getenv('ODOO_USER'),
    password=os.getenv('ODOO_PASSWORD')
)

print(f"✅ UID: {client.uid}")

# Prueba consulta
partners = client.search_read('res.partner', domain=[], limit=3)
print(f"✅ Encontrados {len(partners)} partners")
for p in partners:
    print(f"   - {p['name']}")

print("\n🎉 Migración exitosa!")
```

Ejecuta:
```bash
python test_conexion.py
```

Si ves el mensaje `🎉 Migración exitosa!`, ya está listo.

---

## 📊 Tabla de Equivalencias

| XML-RPC (Antes) | JSON-RPC (Después) |
|----------------|-------------------|
| `models.execute_kw(db, uid, pwd, model, 'search', [domain], kwargs)` | `client.search(model, domain, **kwargs)` |
| `models.execute_kw(db, uid, pwd, model, 'read', [ids], kwargs)` | `client.read(model, ids, fields=kwargs.get('fields'))` |
| `models.execute_kw(db, uid, pwd, model, 'search_read', [domain], kwargs)` | `client.search_read(model, domain, **kwargs)` |
| `models.execute_kw(db, uid, pwd, model, 'create', [vals])` | `client.create(model, vals)` |
| `models.execute_kw(db, uid, pwd, model, 'write', [ids, vals])` | `client.write(model, ids, vals)` |
| `models.execute_kw(db, uid, pwd, model, 'unlink', [ids])` | `client.unlink(model, ids)` |

---

## 🔧 Para Flask/Django

### Flask
```python
# app.py
from odoo_jsonrpc_client import OdooJSONRPCClient
import os

app = Flask(__name__)

# Crear cliente global
odoo = OdooJSONRPCClient(
    url=os.getenv('ODOO_URL'),
    db=os.getenv('ODOO_DB'),
    username=os.getenv('ODOO_USER'),
    password=os.getenv('ODOO_PASSWORD')
)

@app.route('/products')
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
ODOO_CLIENT = None

# apps.py
from django.apps import AppConfig
from odoo_jsonrpc_client import OdooJSONRPCClient
import os

class MyAppConfig(AppConfig):
    def ready(self):
        from django.conf import settings
        settings.ODOO_CLIENT = OdooJSONRPCClient(
            url=os.getenv('ODOO_URL'),
            db=os.getenv('ODOO_DB'),
            username=os.getenv('ODOO_USER'),
            password=os.getenv('ODOO_PASSWORD')
        )

# views.py
from django.conf import settings

def products_view(request):
    products = settings.ODOO_CLIENT.search_read(
        'product.product',
        domain=[],
        limit=20
    )
    return JsonResponse({'products': products})
```

---

## ❓ FAQ

**P: ¿Necesito cambiar algo en Odoo?**  
R: No, es solo cambio en el cliente Python.

**P: ¿Funciona con Odoo.sh?**  
R: Sí, funciona con cualquier Odoo 9+.

**P: ¿Es más lento que XML-RPC?**  
R: No, es **más rápido** (JSON es más ligero que XML).

**P: ¿Puedo usar API Keys?**  
R: Sí, reemplaza `password` con tu API Key.

**P: ¿Funciona con Odoo 8?**  
R: No, JSON-RPC existe desde Odoo 9+.

**P: ¿Pierdo alguna funcionalidad?**  
R: No, JSON-RPC tiene todas las capacidades de XML-RPC.

---

## 📂 Archivos para Copiar a Otros Proyectos

Descarga estos archivos de este repositorio:

```
docs/
  └── guia-migracion-xmlrpc-a-jsonrpc.md  ← Guía completa
  └── QUICK_START_MIGRACION.md            ← Este archivo
odoo_jsonrpc_client.py                   ← Cliente reutilizable
test_odoo_connection.py                   ← Script de prueba (opcional)
```

Copia solo `odoo_jsonrpc_client.py` si quieres la versión mínima.

---

## ⏱️ Tiempo Estimado

- **Proyecto pequeño:** 15 minutos
- **Proyecto mediano:** 30-45 minutos  
- **Proyecto grande:** 1-2 horas

La mayoría del tiempo es buscar/reemplazar llamadas `execute_kw`.

---

## ✅ Checklist Final

- [ ] Instalé `requests`
- [ ] Copié `odoo_jsonrpc_client.py`
- [ ] Actualicé el código de autenticación
- [ ] Reemplacé llamadas `execute_kw`
- [ ] Probé con `test_conexion.py`
- [ ] Verifiqué que la app funciona correctamente
- [ ] Commit y deploy

---

## 🆘 Ayuda

Si algo no funciona:

1. **Verifica conectividad:**
   ```bash
   curl -X POST https://tu-odoo.com/jsonrpc \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"call","params":{"service":"common","method":"version","args":[]},"id":1}'
   ```

2. **Revisa las credenciales:**
   - ¿Puedes hacer login en Odoo web con ese usuario?
   - ¿El archivo `.env` está en la raíz del proyecto?

3. **Aumenta el timeout:**
   ```python
   client = OdooJSONRPCClient(..., timeout=60)
   ```

---

**Autor:** Jonathan Cerda  
**Repositorio:** [dashboard-ventas-inter](.)  
**Licencia:** MIT  
**Última actualización:** Marzo 2026
