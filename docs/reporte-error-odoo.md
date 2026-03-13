# Reporte de Error - Conexión Odoo XML-RPC Bloqueada

## Resumen
El módulo de terceros `cs_login_audit_log` instalado en Odoo está bloqueando todas las conexiones XML-RPC debido a un bug en su código.

## Error Completo
```
RuntimeError: object unbound

Traceback:
File "/home/odoo/src/user/addons_vendor/cs_login_audit_log/models/res_users.py", line 23, in _check_credentials
    ip_address = request.httprequest.environ.get('REMOTE_ADDR')
File "/usr/lib/python3/dist-packages/werkzeug/local.py", line 432, in __get__
    obj = instance._get_current_object()
File "/usr/lib/python3/dist-packages/werkzeug/local.py", line 554, in _get_current_object
    return self.__local()
File "/usr/lib/python3/dist-packages/werkzeug/local.py", line 226, in _lookup
    raise RuntimeError("object unbound")
```

## Detalles Técnicos

### Información de Conexión
- **URL Odoo:** https://amah.odoo.com
- **Base de Datos:** amah-main-9110254
- **Método de autenticación probado:** Contraseña y API Key
- **Protocolo:** XML-RPC (xmlrpc.client.ServerProxy)

### Causa Raíz
El módulo `cs_login_audit_log` (ubicado en `/home/odoo/src/user/addons_vendor/`) intenta acceder a `request.httprequest` durante el método `_check_credentials`, pero este objeto no existe en el contexto de llamadas XML-RPC (solo existe en peticiones HTTP web).

### Archivos Involucrados en el Cliente

1. **conectar_odoo.py** - Script de prueba de conexión (ejecutar para reproducir)
2. **odoo_manager.py** - Clase principal que maneja la conexión (líneas 70-130)
3. **.env** - Variables de entorno con credenciales

### Restricciones
- ❌ No podemos modificar el módulo `cs_login_audit_log` (es de terceros)
- ❌ No tenemos acceso root al servidor de Odoo
- ✅ Podemos modificar nuestro código cliente Python
- ✅ Podemos solicitar cambios al administrador de Odoo

## Soluciones Propuestas

### Opción 1: Solicitar al Admin de Odoo (RECOMENDADO)
**Acción:** Desactivar temporalmente el módulo `cs_login_audit_log`

**Pasos:**
1. Acceder como administrador a Odoo
2. Ir a Aplicaciones → Buscar "cs_login_audit_log"
3. Desinstalar o desactivar el módulo
4. Verificar conexión con `python conectar_odoo.py`

### Opción 2: Usuario Técnico sin Auditoría
**Acción:** Crear un usuario específico para integraciones que no active el módulo de auditoría

**Pasos:**
1. Admin crea usuario: `api_integration@agrovetmarket.com`
2. Asignar grupo que evite el trigger del módulo de auditoría
3. Usar ese usuario en nuestro `.env`

### Opción 3: Bypass a Nivel de Código Cliente (EXPERIMENTAL)
**Acción:** Modificar `odoo_manager.py` para intentar autenticación alternativa

**Requiere investigación:** Si Odoo tiene endpoint REST API alternativo o configuración especial.

### Opción 4: Solicitar Corrección del Módulo
**Acción:** Contactar al proveedor del módulo `cs_login_audit_log`

**Fix necesario (solo referencia):**
```python
# En cs_login_audit_log/models/res_users.py línea 23
# Cambiar:
ip_address = request.httprequest.environ.get('REMOTE_ADDR')

# Por:
from odoo.http import request
try:
    ip_address = request.httprequest.environ.get('REMOTE_ADDR') if request else 'API/XML-RPC'
except (RuntimeError, AttributeError):
    ip_address = 'API/XML-RPC'
```

## Pruebas Realizadas

✅ Conexión con contraseña original
✅ Conexión con API Key generada
✅ Verificación de credenciales en `.env`
✅ Test de conectividad de red (ping, https)
❌ Todas bloqueadas por el mismo error

## Información del Sistema
- **Python:** 3.x
- **Librería:** xmlrpc.client (estándar)
- **Sistema Operativo Cliente:** Windows
- **Fecha del reporte:** 13 de marzo de 2026

---


