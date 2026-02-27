# Guía Rápida: Autenticación OAuth2 con Google para Agentes AI

⚡ **Propósito**: Implementar autenticación OAuth2 de Google en aplicaciones Flask rápidamente.

## 🎯 Para el Agente AI: Resumen Ejecutivo

Esta guía te permitirá configurar OAuth2 en ~15 minutos. Pasos principales:
1. Usuario configura Google Cloud Console manualmente (5 min)
2. Tú instalas dependencias (1 min)
3. Tú actualizas `.env` con credenciales (1 min)
4. Tú implementas código OAuth2 en Flask (5 min)
5. Tú modificas template de login (2 min)
6. Usuario prueba el login (1 min)

## 📋 Requisitos Previos (lo que el usuario debe tener)

- Proyecto en Google Cloud Console
- Client ID y Client Secret de OAuth 2.0
- Python 3.8+ instalado
- Flask ya configurado en el proyecto

## 🔧 PASO 1: Usuario configura Google Cloud Console (5 minutos)

**Para el Agente**: Solicita al usuario que complete esto y te proporcione las credenciales.

### Instrucciones para el Usuario:

**1. Accede a Google Cloud Console:**
- URL: https://console.cloud.google.com/apis/credentials
- Selecciona o crea un proyecto

**2. Configura Pantalla de Consentimiento (si no está hecha):**
- Ve a: **Pantalla de consentimiento de OAuth**
- Tipo: **Interno** (recomendado para apps corporativas) o **Externo**
- **Nombre de app**: Pon el nombre de tu aplicación
- **Email de soporte**: Tu correo corporativo
- **Scopes**: `.../auth/userinfo.email`, `.../auth/userinfo.profile`, `openid`
- Guarda

**3. Crear o Reutilizar OAuth Client:**

**Opción A - Reutilizar cliente existente (MÁS RÁPIDO):**
```
1. Selecciona un OAuth Client que ya funcione
2. En "Orígenes JavaScript autorizados", AGREGA:
   - http://localhost:5000
   - http://127.0.0.1:5000
   - https://TU-DOMINIO-PRODUCCION.com (si aplica)

3. En "URIs de redirección autorizados", AGREGA:
   - http://localhost:5000/login/callback
   - http://127.0.0.1:5000/login/callback
   - https://TU-DOMINIO-PRODUCCION.com/login/callback (si aplica)

4. Guarda (espera 2-5 minutos para propagación)
5. Copia el Client ID y Client Secret existentes
```

**Opción B - Crear nuevo cliente:**
```
1. Clic en "+ Crear credenciales" → "ID de cliente de OAuth 2.0"
2. Tipo: "Aplicación web"
3. Nombre: "Dashboard OAuth" (o el que prefieras)
4. Agrega los mismos orígenes y URIs de la Opción A
5. Crea y copia el Client ID y Client Secret
6. IMPORTANTE: Espera 5-60 minutos para que se propague
```

**4. Proporciona al Agente:**
```
GOOGLE_CLIENT_ID=XXXXX-YYYY.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-ZZZZZ
PRODUCTION_URL=https://tu-dominio.com (o tu URL de producción)
```

También proporciona lista de correos autorizados:
```
usuario1@empresa.com
usuario2@empresa.com
admin@empresa.com
```

---

## 🤖 PASO 2: Agente instala dependencias

**Acción**: Verifica que estas librerías estén en `requirements.txt`:

```txt
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
Flask>=3.0.0
python-dotenv>=1.0.0
```

**Comando a ejecutar**:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

---

## 🤖 PASO 3: Agente configura variables de entorno

**Acción**: Actualiza o crea el archivo `.env` con las credenciales del usuario:

```env
# Flask
SECRET_KEY=<generar_con_secrets.token_hex(32)>
FLASK_ENV=development

# Google OAuth2
GOOGLE_CLIENT_ID=<client_id_proporcionado_por_usuario>
GOOGLE_CLIENT_SECRET=<client_secret_proporcionado_por_usuario>

# URLs
PRODUCTION_URL=<url_produccion_proporcionada_por_usuario>
```

**Generar SECRET_KEY**:
```python
import secrets
print(secrets.token_hex(32))
```

**Crear `allowed_users.json`** con los correos autorizados:
```json
[
  "usuario1@empresa.com",
  "usuario2@empresa.com"
]
```

---

## 🤖 PASO 4: Agente implementa código OAuth2

### 4.1 Actualizar `app.py` - Imports y configuración inicial

**Agrega estos imports al inicio del archivo**:
```python
from flask import Flask, session, redirect, url_for, request, flash
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import json
import os
from dotenv import load_dotenv
```

### 4.2 Función de detección de entorno

**Agrega después de `app = Flask(__name__)`**:
```python
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Detección automática de entorno
def is_production():
    """Detecta si está en producción"""
    flask_env = os.getenv('FLASK_ENV', 'development').lower()
    if flask_env == 'production':
        return True
    if os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('HEROKU'):
        return True
    return False

# Configurar entorno
IS_PRODUCTION = is_production()
PRODUCTION_URL = os.getenv('PRODUCTION_URL', 'https://tu-dominio.com')

# OAuth2 Google
if not IS_PRODUCTION:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    BASE_URL = 'http://localhost:5000'
else:
    BASE_URL = PRODUCTION_URL

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

client_secrets = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": [f"{BASE_URL}/login/callback"]
    }
}

# Configuración de sesión
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

### 4.3 Rutas de autenticación

**Reemplaza o actualiza la ruta `/login` existente**:
```python
@app.route('/login')
def login():
    """Muestra la página de login con Google Sign-In"""
    if 'user_email' in session:
        return redirect(url_for('dashboard_clean'))  # Ajusta el nombre de tu dashboard
    return render_template('login.html')

@app.route('/login/google')
def login_google():
    """Inicia el flujo OAuth2 con Google"""
    try:
        flow = Flow.from_client_config(
            client_secrets,
            scopes=[
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'
            ],
            redirect_uri=url_for('callback', _external=True)
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account'
        )
        
        session['state'] = state
        return redirect(authorization_url)
    except Exception as e:
        app.logger.error(f"Error iniciando OAuth2: {e}", exc_info=True)
        flash(f'Error al iniciar sesión con Google: {e}', 'danger')
        return redirect(url_for('login'))

@app.route('/login/callback')
def callback():
    """Procesa la respuesta de Google OAuth2"""
    try:
        # Validar state para prevenir CSRF
        if request.args.get('state') != session.get('state'):
            flash('Estado de sesión inválido. Por favor, intenta nuevamente.', 'danger')
            return redirect(url_for('login'))
        
        # Obtener token de autorización
        flow = Flow.from_client_config(
            client_secrets,
            scopes=[
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'
            ],
            redirect_uri=url_for('callback', _external=True),
            state=session['state']
        )
        
        flow.fetch_token(authorization_response=request.url)
        
        # Verificar el ID token
        credentials = flow.credentials
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # Extraer información del usuario
        user_email = id_info.get('email')
        user_name = id_info.get('name', '')
        
        # Cargar lista blanca de usuarios
        try:
            with open('allowed_users.json', 'r', encoding='utf-8') as f:
                allowed_users = json.load(f)
        except FileNotFoundError:
            app.logger.error("Archivo allowed_users.json no encontrado")
            flash('Error de configuración del servidor', 'danger')
            return redirect(url_for('login'))
        
        # Validar que el usuario esté autorizado
        if user_email not in allowed_users:
            flash(f'Usuario {user_email} no autorizado para acceder', 'danger')
            return redirect(url_for('login'))
        
        # Crear sesión
        session.permanent = True
        session['user_email'] = user_email
        session['user_name'] = user_name
        
        flash(f'Bienvenido, {user_name}!', 'success')
        return redirect(url_for('dashboard_clean'))  # Ajusta a tu ruta principal
        
    except Exception as e:
        app.logger.error(f"Error en callback OAuth2: {e}", exc_info=True)
        flash(f'Error al procesar login: {e}', 'danger')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario"""
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))
```

### 4.4 Decorador de autenticación (proteger rutas)

**Agrega este decorador para proteger rutas**:
```python
from functools import wraps

def login_required(f):
    """Decorador para rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Debes iniciar sesión para acceder', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Ejemplo de uso en rutas existentes:
@app.route('/')
@login_required
def dashboard_clean():
    user_email = session.get('user_email')
    # ... resto del código
```

**Añade `@login_required` a todas las rutas que necesiten autenticación**.

---

## 🤖 PASO 5: Agente actualiza template de login

### 5.1 Localizar el archivo de login

Busca `templates/login.html` o el archivo que contenga el formulario de login.

### 5.2 Reemplazar formulario con botón de Google

**Busca el formulario existente** (algo como `<form>...</form>` con usuario/contraseña).

**Reemplázalo con**:
```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 400px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .google-signin-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: white;
            border: 1px solid #dadce0;
            border-radius: 4px;
            padding: 10px 20px;
            text-decoration: none;
            color: #3c4043;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
            cursor: pointer;
        }
        .google-signin-button:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            border-color: #c6c6c6;
        }
        .google-logo {
            width: 18px;
            height: 18px;
            margin-right: 10px;
        }
        .flash-messages {
            margin-bottom: 20px;
        }
        .alert {
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .alert-danger {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🏥 Dashboard</h1>
        <p class="subtitle">Inicia sesión con tu cuenta corporativa</p>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <a href="/login/google" class="google-signin-button">
            <svg class="google-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                <path fill="none" d="M0 0h48v48H0z"/>
            </svg>
            Sign in with Google
        </a>
    </div>
</body>
</html>
```

**Personaliza**:
- Cambia `🏥 Dashboard` por el nombre de tu aplicación
- Ajusta colores en el CSS si es necesario

---

## 🧪 PASO 6: Usuario prueba el login

**Instrucciones para el Usuario:**

1. Asegúrate de que el servidor Flask esté corriendo:
   ```bash
   python app.py
   ```

2. Abre el navegador (modo incógnito recomendado)

3. Ve a: `http://localhost:5000/login`

4. Haz clic en **"Sign in with Google"**

5. Selecciona tu cuenta corporativa

6. Si sale error `redirect_uri_mismatch`:
   - Espera 5-10 minutos (propagación de Google)
   - Limpia caché del navegador (Ctrl+Shift+Delete)
   - Verifica que las URIs en Google Cloud Console sean exactas

7. Si sale "Usuario no autorizado":
   - Verifica que tu email esté en `allowed_users.json`

---

## 🚀 PASO 7: Despliegue a Producción (cuando esté listo)

### Para el Usuario:

**En tu plataforma de hosting (Render/Railway/Heroku):**

1. Configura estas variables de entorno:
   ```
   SECRET_KEY=<nueva_clave_diferente_a_desarrollo>
   GOOGLE_CLIENT_ID=<mismo_client_id>
   GOOGLE_CLIENT_SECRET=<mismo_client_secret>
   PRODUCTION_URL=https://tu-dominio.com
   FLASK_ENV=production
   ```

2. **En Google Cloud Console**, agrega tu URL de producción:
   - Origen: `https://tu-dominio.com`
   - Redirect: `https://tu-dominio.com/login/callback`

3. Despliega tu aplicación

---

## 🔍 Troubleshooting Rápido

| Error | Solución Inmediata |
|-------|-------------------|
| `redirect_uri_mismatch` | 1. Verifica URIs exactas en Google Cloud Console<br>2. Espera 5-10 min<br>3. Limpia caché del navegador<br>4. Usa modo incógnito |
| `Usuario no autorizado` | Agrega el email a `allowed_users.json` |
| `invalid_client` | Verifica Client ID/Secret en `.env` |
| `ModuleNotFoundError` | Ejecuta `pip install google-auth google-auth-oauthlib` |
| No redirige después de login | Revisa nombre de la ruta en `return redirect(url_for('AQUI'))` |

---

## ✅ Checklist Final para el Agente

Antes de terminar, verifica:

- [ ] Dependencias instaladas (`google-auth`, `google-auth-oauthlib`)
- [ ] `.env` actualizado con credenciales correctas
- [ ] `allowed_users.json` creado con emails autorizados
- [ ] Código OAuth2 agregado a `app.py`
- [ ] Rutas `/login`, `/login/google`, `/login/callback`, `/logout` implementadas
- [ ] Decorador `@login_required` agregado y aplicado a rutas protegidas
- [ ] Template `templates/login.html` actualizado con botón de Google
- [ ] Usuario probó el login y funcionó correctamente
- [ ] `.env` y `credentials.json` están en `.gitignore`

---

## 📝 Notas para el Agente

**Reutilizar Client ID existente es MÁS RÁPIDO** (evita esperar propagación de 5-60 min).

**Si el usuario reporta errores persistentes**, pregunta:
1. ¿Cuánto tiempo pasó desde que guardaste en Google Cloud Console? (si <10 min, esperar)
2. ¿Limpiaste el caché del navegador completamente?
3. ¿El OAuth Client es tipo "Interno" y tu email es corporativo de Google Workspace?
4. ¿Probaste en modo incógnito?

**Archivos a NO commitear**: `.env`, `credentials.json`, `__pycache__/`, `*.pyc`
