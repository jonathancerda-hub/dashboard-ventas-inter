# Arquitectura del Sistema - Dashboard de Ventas

**Versión**: 1.0  
**Fecha**: Febrero 2026  
**Propósito**: Documentación técnica para auditoría y revisión de arquitectura

---

## 📋 Resumen Ejecutivo

Sistema web de análisis y visualización de ventas farmacéuticas que integra datos de Odoo ERP y Google Sheets, con autenticación OAuth2 de Google. El dashboard permite a usuarios autorizados visualizar métricas de ventas, seguimiento de metas y análisis de clientes/productos.

**Stack Tecnológico**:
- **Backend**: Python 3.12 + Flask 3.1.2
- **Frontend**: HTML5 + JavaScript (vanilla)
- **Visualizaciones**: ECharts 5.x + Chart.js
- **Integraciones**: Odoo XML-RPC, Google Sheets API, Google OAuth2
- **Hosting**: Render.com (producción)

---

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                      USUARIOS AUTORIZADOS                    │
│              (Lista blanca: allowed_users.json)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    GOOGLE OAUTH2 SSO                         │
│           (Autenticación y autorización de acceso)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FLASK APPLICATION                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   app.py     │  │   Jinja2     │  │   Sessions   │     │
│  │  (Routing)   │  │ (Templates)  │  │   (Flask)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────┬──────────────────────┬──────────────────────┬────────┘
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Odoo API    │    │ Google Sheets│    │   Cache      │
│  (XML-RPC)   │    │     API      │    │  (In-Memory) │
│              │    │              │    │              │
│ - Ventas     │    │ - Metas      │    │ - TTL: 30min │
│ - Clientes   │    │ - Equipos    │    │              │
│ - Productos  │    │              │    │              │
│ - Pedidos    │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 🔐 Seguridad y Autenticación

### 1. Autenticación OAuth2

**Proveedor**: Google OAuth 2.0  
**Tipo**: Interno (Google Workspace)  
**Flujo**: Authorization Code Flow

**Endpoints de autenticación**:
```
/login              → Página de login (botón Google Sign-In)
/login/google       → Inicia flujo OAuth2
/login/callback     → Procesa respuesta de Google
/logout             → Cierra sesión
```

**Scopes solicitados**:
- `openid`
- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/userinfo.profile`

**Seguridad OAuth2**:
- ✅ State parameter (protección CSRF)
- ✅ Token ID verification con Google
- ✅ HTTPS obligatorio en producción
- ✅ Redirect URI validation

### 2. Control de Acceso

**Lista Blanca**: `allowed_users.json`  
**Ubicación**: Raíz del proyecto (excluido de Git)  
**Formato**: Array JSON con emails autorizados

```json
[
  "usuario1@empresa.com",
  "usuario2@empresa.com"
]
```

**Validación**: 
1. Usuario completa autenticación OAuth2 con Google
2. Sistema extrae email del token ID
3. Sistema verifica email contra `allowed_users.json`
4. Acceso denegado si email no está en lista blanca

**Protección de rutas**: Decorador `@login_required` en todas las rutas sensibles.

### 3. Gestión de Sesiones

**Mecanismo**: Flask sessions (cookie-based)  
**Configuración**:
```python
SESSION_COOKIE_HTTPONLY = True      # Previene XSS
SESSION_COOKIE_SECURE = True        # HTTPS only (producción)
SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF protection
session.permanent = True             # Sesión persistente
```

**Datos almacenados en sesión**:
- `user_email`: Email del usuario autenticado
- `user_name`: Nombre completo
- `state`: Token CSRF para OAuth2

---

## 🔌 Integraciones Externas

### 1. Odoo ERP (XML-RPC)

**Propósito**: Fuente de datos transaccionales (ventas, clientes, productos, pedidos)

**Conexión**:
- **Protocolo**: XML-RPC
- **URL**: `https://amah.odoo.com` (variable: `ODOO_URL`)
- **Base de datos**: `amah-main-9110254` (variable: `ODOO_DB`)
- **Autenticación**: Usuario/contraseña (variables: `ODOO_USER`, `ODOO_PASSWORD`)

**Módulo**: `odoo_manager.py`

**Modelos accedidos**:
```python
sale.order              # Pedidos de venta
sale.order.line         # Líneas de pedidos
account.move.line       # Líneas de facturas
res.partner             # Clientes
product.product         # Productos
```

**Métodos principales**:
- `get_sales_lines(año, canal, equipo)`: Ventas facturadas por año/canal/equipo
- `get_pending_orders()`: Pedidos pendientes de facturación (todos los años)
- `search_read()`: Consultas genéricas con dominios

**Filtros aplicados**:
- Ventas: Por año, canal de venta, equipo de ventas
- Pendientes: Solo ordenes activas (sin filtro de fecha)
- Exclusiones: Productos con `is_pack=True`

**Nota de seguridad**: Credenciales Odoo almacenadas en `.env`, no expuestas al cliente.

### 2. Google Sheets API

**Propósito**: Almacenamiento de metas comerciales y configuración de equipos

**Autenticación**: Service Account (OAuth2 JWT)  
**Credenciales**: `credentials.json` (excluido de Git)  
**Hoja de cálculo**: Variable `GOOGLE_SHEET_NAME` (nombre de la hoja)

**Módulo**: `google_sheets_manager.py`

**Pestañas utilizadas**:
```
Metas_Clientes_2024     # Metas por cliente por año
Metas_Clientes_2025
Metas_Clientes_2026
equipos_ventas          # Configuración de equipos
```

**Operaciones**:
- **Lectura**: Metas de clientes, configuración de equipos
- **Escritura**: Actualización de metas (endpoint `/update_meta`)

**Permisos del Service Account**:
- Editor en la hoja de cálculo específica
- Sin acceso a otros archivos del Drive

### 3. Google OAuth2

**Propósito**: Autenticación de usuarios (Single Sign-On)

**Configuración**: Ver sección "Seguridad y Autenticación"

**Google Cloud Console**:
- Proyecto: Portal Corporativo
- OAuth Client Type: Web Application
- Consent Screen: Interno (Google Workspace)

**URIs autorizados**:
- Desarrollo: `http://localhost:5000`, `http://127.0.0.1:5000`
- Producción: Según variable `PRODUCTION_URL`

---

## 📁 Estructura del Proyecto

```
Dashboard-Ventas-INTER/
├── .env                          # Variables de entorno (NO en Git)
├── .gitignore                    # Archivos excluidos de Git
├── allowed_users.json            # Lista blanca usuarios (NO en Git)
├── credentials.json              # Service Account Google (NO en Git)
├── requirements.txt              # Dependencias Python
├── runtime.txt                   # Versión Python (Render.com)
├── app.py                        # Aplicación Flask principal (2692 líneas)
├── conectar_odoo.py              # Script de prueba Odoo
├── odoo_manager.py               # Gestión API Odoo
├── google_sheets_manager.py      # Gestión Google Sheets
├── templates/                    # Templates Jinja2
│   ├── base.html                 # Template base
│   ├── login.html                # Página de login (OAuth2)
│   ├── dashboard_clean.html      # Dashboard principal
│   └── ...
├── static/                       # Archivos estáticos
│   ├── css/style.css
│   ├── js/script.js
│   └── world.json                # Datos geográficos mapas
├── docs/                         # Documentación
│   ├── arquitectura-sistema.md   # Este documento
│   └── configurar-oauth2-google.md
└── __pycache__/                  # Cache Python (NO en Git)
```

### Archivos críticos de seguridad

**NO deben estar en Git**:
- `.env` → Variables de entorno y credenciales
- `credentials.json` → Service Account de Google
- `allowed_users.json` → Lista de usuarios autorizados
- `__pycache__/` → Cache de Python

**Verificar `.gitignore`**:
```gitignore
.env
credentials.json
allowed_users.json
__pycache__/
*.pyc
venv/
```

---

## 🔧 Variables de Entorno

**Archivo**: `.env` (local) o configuración del hosting (producción)

### Variables obligatorias:

```env
# Flask
SECRET_KEY                # Clave secreta para sesiones (64 chars hex)
FLASK_ENV                 # development | production

# Odoo
ODOO_URL                  # URL del servidor Odoo
ODOO_DB                   # Nombre de la base de datos Odoo
ODOO_USER                 # Usuario Odoo (email)
ODOO_PASSWORD             # Contraseña o API key Odoo

# Google OAuth2
GOOGLE_CLIENT_ID          # Client ID del OAuth 2.0
GOOGLE_CLIENT_SECRET      # Client Secret del OAuth 2.0

# Google Sheets
GOOGLE_SHEET_NAME         # Nombre de la hoja de cálculo

# Producción
PRODUCTION_URL            # URL completa producción (ej: https://dominio.com)
```

### Generación de SECRET_KEY:

```python
import secrets
print(secrets.token_hex(32))
```

**Recomendación**: Usar SECRET_KEY diferente entre desarrollo y producción.

---

## 🚀 Flujo de Datos

### 1. Flujo de Autenticación

```
Usuario → /login
    ↓
Botón "Sign in with Google"
    ↓
/login/google → Redirige a Google OAuth2
    ↓
Usuario autoriza en Google
    ↓
Google → /login/callback (con code + state)
    ↓
Sistema valida state (CSRF)
    ↓
Sistema intercambia code por token
    ↓
Sistema verifica token ID con Google
    ↓
Sistema extrae email del token
    ↓
Sistema verifica email en allowed_users.json
    ↓
¿Email autorizado?
    ├─ NO → Mostrar error, redirigir a /login
    └─ SÍ → Crear sesión, redirigir a dashboard
```

### 2. Flujo de Visualización de Dashboard

```
Usuario autenticado → GET /
    ↓
Sistema verifica sesión (@login_required)
    ↓
¿Sesión válida?
    ├─ NO → Redirigir a /login
    └─ SÍ → Continuar
         ↓
    Sistema obtiene parámetros (año, equipo, canal)
         ↓
    ¿Datos en caché?
         ├─ SÍ → Usar datos en caché
         └─ NO → Consultar Odoo + Google Sheets
              ↓
         Odoo: Ventas facturadas (por año)
         Odoo: Pedidos pendientes (todos)
         Sheets: Metas clientes (por año)
         Sheets: Equipos ventas
              ↓
         Procesar y agregar datos
              ↓
         Guardar en caché (TTL: 30 min)
              ↓
    Renderizar template con datos
         ↓
    Cliente recibe HTML + JSON embebido
         ↓
    JavaScript renderiza gráficos (ECharts/Chart.js)
```

### 3. Flujo de Actualización de Metas

```
Usuario → Modifica meta en dashboard
    ↓
JavaScript → POST /update_meta
    ↓
Sistema verifica sesión
    ↓
Sistema valida datos (cliente, monto, año)
    ↓
GoogleSheetsManager.update_goal()
    ↓
Google Sheets API actualiza celda
    ↓
Sistema invalida caché
    ↓
Respuesta JSON {success: true}
    ↓
Cliente actualiza UI
```

---

## 💾 Almacenamiento y Cache

### Cache en Memoria

**Mecanismo**: Dictionary Python con TTL  
**TTL**: 30 minutos  
**Scope**: Por proceso (no compartido entre workers)

**Datos cacheados**:
- Ventas por año/equipo/canal
- Pedidos pendientes
- Metas de clientes
- Configuración de equipos

**Invalidación**:
- Automática por TTL
- Manual al actualizar metas

**Límites**: Sin límite de memoria definido (puede crecer con uso)

### Persistencia

**No hay base de datos local**. Todos los datos se obtienen de:
- Odoo (datos transaccionales)
- Google Sheets (metas y configuración)

**Sesiones**: Flask session (cookie serializada, firmada con SECRET_KEY)

---

## 🔄 Detección Automática de Entorno

**Función**: `is_production()` en `app.py`

**Lógica de detección**:
```python
1. Si FLASK_ENV=production → Producción
2. Si existe variable RENDER → Producción (Render.com)
3. Si existe variable RAILWAY_ENVIRONMENT → Producción (Railway)
4. Si existe variable HEROKU → Producción (Heroku)
5. En otro caso → Desarrollo
```

**Diferencias por entorno**:

| Configuración | Desarrollo | Producción |
|---------------|-----------|------------|
| BASE_URL | `http://localhost:5000` | Variable `PRODUCTION_URL` |
| HTTPS requerido | No | Sí |
| Cookies SECURE | No | Sí |
| Debug mode | Sí | No |
| OAUTHLIB_INSECURE_TRANSPORT | '1' | No definida |

---

## 📊 Endpoints de la Aplicación

### Autenticación

| Método | Ruta | Autenticación | Descripción |
|--------|------|---------------|-------------|
| GET | `/login` | No | Página de login |
| GET | `/login/google` | No | Inicia OAuth2 |
| GET | `/login/callback` | No | Callback OAuth2 |
| GET | `/logout` | Sí | Cierra sesión |

### Dashboards y Visualizaciones

| Método | Ruta | Autenticación | Descripción |
|--------|------|---------------|-------------|
| GET | `/` | Sí | Dashboard principal |
| GET | `/dashboard_linea` | Sí | Dashboard por línea |
| GET | `/equipo_ventas` | Sí | Dashboard de equipo |
| GET | `/metas_cliente` | Sí | Gestión de metas |

### API Endpoints

| Método | Ruta | Autenticación | Descripción |
|--------|------|---------------|-------------|
| POST | `/update_meta` | Sí | Actualizar meta cliente |
| GET | `/sales` | Sí | Datos de ventas (JSON) |
| GET | `/pending` | Sí | Pedidos pendientes (JSON) |

### Utilidades

| Método | Ruta | Autenticación | Descripción |
|--------|------|---------------|-------------|
| GET | `/debug_info` | Sí | Info de debug (desarrollo) |

---

## 🔍 Auditoría y Logs

### Logging

**Framework**: Python `logging` module

**Niveles utilizados**:
- `INFO`: Conexiones exitosas, operaciones normales
- `ERROR`: Errores de autenticación, fallos de API
- `WARNING`: (no utilizado actualmente)

**Eventos registrados**:
```python
INFO: Conexión a Odoo exitosa. UID: X
INFO: Conexión a Google Sheets establecida exitosamente
INFO: Entorno: DESARROLLO / PRODUCCIÓN
ERROR: Error iniciando OAuth2: [detalle]
ERROR: Error en callback OAuth2: [detalle]
ERROR: Archivo allowed_users.json no encontrado
```

**Ubicación logs (Render.com)**:
- Dashboard → Logs (tiempo real)
- Retención: 7 días (plan gratuito)

### Auditoría de Accesos

**NO implementado actualmente**. Para auditoría completa se recomienda:

1. **Agregar logging de accesos**:
```python
@app.after_request
def log_access(response):
    app.logger.info(f"ACCESS: {request.remote_addr} {request.method} {request.path} - {response.status_code} - User: {session.get('user_email', 'anonymous')}")
    return response
```

2. **Persistir logs en almacenamiento externo** (no implementado):
   - AWS CloudWatch
   - Google Cloud Logging
   - Syslog externo

3. **Monitoreo de cambios en metas** (parcial):
   - Actualmente: Log en consola al actualizar meta
   - Recomendado: Log estructurado con timestamp, usuario, cambio anterior/nuevo

---

## 🛡️ Análisis de Riesgos y Mitigaciones

### Riesgos Identificados

| Riesgo | Severidad | Mitigación Actual | Recomendación |
|--------|-----------|-------------------|---------------|
| Exposición de credenciales en Git | CRÍTICA | `.gitignore`, docs de seguridad | ✅ Adecuado |
| Acceso no autorizado | ALTA | OAuth2 + lista blanca | ✅ Adecuado |
| Session hijacking | MEDIA | HTTPONLY, SECURE, SameSite cookies | ✅ Adecuado |
| CSRF en actualización de metas | MEDIA | OAuth2 state, SameSite cookies | ⚠️ Agregar CSRF token en formularios |
| Inyección en consultas Odoo | MEDIA | Inputs controlados por código | ✅ Adecuado (XML-RPC parametrizado) |
| DDoS | MEDIA | (depende del hosting) | ⚠️ Rate limiting |
| Falta de auditoría completa | MEDIA | Logs básicos | ⚠️ Implementar auditoría estructurada |
| Cache sin límite de memoria | BAJA | TTL de 30 min | ℹ️ Monitorear uso memoria |
| Secret Key débil | CRÍTICA | Generado con `secrets` module | ✅ Adecuado (si se usa correctamente) |

### Recomendaciones de Seguridad

**Alta prioridad**:
1. ✅ **Rotar SECRET_KEY** periódicamente (cada 3-6 meses)
2. ✅ **Auditar allowed_users.json** mensualmente (remover usuarios inactivos)
3. ⚠️ **Implementar rate limiting** (ej: Flask-Limiter)
4. ⚠️ **Agregar CSRF tokens** a formularios de modificación

**Media prioridad**:
5. ℹ️ Implementar auditoría completa de accesos
6. ℹ️ Agregar monitoreo de errores (Sentry, Rollbar)
7. ℹ️ Implementar respaldos de allowed_users.json

**Baja prioridad**:
8. ℹ️ Migrar cache a Redis (para múltiples workers)
9. ℹ️ Agregar health check endpoint (`/health`)

---

## 📈 Escalabilidad y Rendimiento

### Limitaciones Actuales

1. **Cache in-memory**: No compartido entre workers/instancias
2. **Sin rate limiting**: Vulnerable a abuso
3. **Consultas Odoo síncronas**: Bloquean el thread
4. **Sin workers asíncronos**: Gunicorn con workers sync

### Configuración de Producción (Render.com)

```yaml
# render.yaml (recomendado)
services:
  - type: web
    name: dashboard-ventas
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 2 -b 0.0.0.0:$PORT app:app
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
      # ... resto de variables desde Render Dashboard
```

**Workers**: 2 (plan gratuito Render.com)  
**Memoria**: 512 MB (plan gratuito)  
**Timeout**: 30 segundos

### Optimizaciones Implementadas

- ✅ Cache de 30 minutos para datos Odoo/Sheets
- ✅ Consultas Odoo filtradas (solo campos necesarios)
- ✅ Compresión de respuestas JSON
- ✅ Templates Jinja2 cacheados

### Optimizaciones Pendientes

- ⚠️ Implementar Redis para cache distribuido
- ⚠️ Usar workers asíncronos (gevent/eventlet)
- ⚠️ Lazy loading de gráficos en frontend
- ⚠️ CDN para assets estáticos

---

## 🧪 Testing y QA

### Testing Actual

**Estado**: No hay suite de tests automatizados

**Testing manual**:
- ✅ Flujo OAuth2 completo
- ✅ Validación de lista blanca
- ✅ Visualización de dashboards
- ✅ Actualización de metas

### Recomendaciones de Testing

```python
# tests/test_auth.py
def test_login_redirect():
    """Login sin sesión debe redirigir a /login"""
    
def test_oauth_callback_invalid_state():
    """Callback con state inválido debe rechazar"""
    
def test_unauthorized_user():
    """Usuario no en lista blanca debe ser rechazado"""

# tests/test_api.py
def test_odoo_connection():
    """Conexión a Odoo debe ser exitosa"""
    
def test_google_sheets_connection():
    """Conexión a Google Sheets debe ser exitosa"""

# tests/test_data.py
def test_sales_aggregation():
    """Agregación de ventas debe ser correcta"""
```

---

## 📝 Checklist de Auditoría

### Seguridad

- [ ] `.env` no está en Git
- [ ] `credentials.json` no está en Git
- [ ] `allowed_users.json` no está en Git
- [ ] SECRET_KEY tiene al menos 64 caracteres aleatorios
- [ ] SECRET_KEY de producción es diferente a desarrollo
- [ ] Cookies tienen flags HTTPONLY, SECURE, SameSite
- [ ] OAuth2 implementa protección CSRF (state)
- [ ] Todas las rutas sensibles tienen `@login_required`
- [ ] Lista blanca de usuarios está actualizada

### Integraciones

- [ ] Credenciales Odoo son válidas
- [ ] Credenciales Google Sheets son válidas
- [ ] OAuth Client ID está activo en Google Cloud Console
- [ ] URIs de redirección están configuradas correctamente
- [ ] Service Account tiene permisos en la hoja de cálculo

### Operacional

- [ ] Variables de entorno están configuradas en producción
- [ ] Logs son accesibles y se monitorean
- [ ] Hay alertas configuradas para errores críticos
- [ ] Se realizan respaldos de allowed_users.json
- [ ] Documentación está actualizada

### Cumplimiento

- [ ] No se exponen datos de clientes a usuarios no autorizados
- [ ] Sesiones expiran apropiadamente
- [ ] No hay datos sensibles en logs
- [ ] Cumple con políticas de retención de datos

---

## 📞 Contactos y Responsabilidades

**Desarrollo**: [Equipo de desarrollo]  
**Operaciones**: [Equipo de IT]  
**Seguridad**: [Responsable de seguridad]  
**Auditoría**: [Auditor asignado]

---

## 📚 Referencias

- [Documentación OAuth2 Google](https://developers.google.com/identity/protocols/oauth2)
- [Documentación Flask](https://flask.palletsprojects.com/)
- [Odoo XML-RPC External API](https://www.odoo.com/documentation/16.0/developer/api/external_api.html)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Guía de configuración OAuth2](./configurar-oauth2-google.md)

---

**Documento generado para**: Auditoría técnica y revisión de arquitectura  
**Última actualización**: Febrero 2026  
**Versión del sistema**: v1.0 (OAuth2 implementado)
