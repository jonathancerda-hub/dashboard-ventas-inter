import xmlrpc.client
import os  # Importamos la librería del sistema operativo para leer variables de entorno
from dotenv import load_dotenv  # Importamos la función para cargar el archivo .env

# --- 1. CARGAR VARIABLES DE ENTORNO ---
# Esta función busca un archivo .env en la misma carpeta y carga sus variables.
load_dotenv()

# Leemos las credenciales desde las variables de entorno que cargamos.
# os.getenv() obtiene el valor de la variable especificada.
url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USER')
password = os.getenv('ODOO_PASSWORD')

# Verificamos que todas las variables necesarias se hayan cargado correctamente.
if not all([url, db, username, password]):
    print("Error: Faltan una o más variables de entorno (ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD).")
    exit()

# --- 2. AUTENTICACIÓN ---
# El resto del código funciona exactamente igual, pero ahora usa las variables cargadas.
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
print(f"Conectando a {url}...")

try:
    uid = common.authenticate(db, username, password, {})
    if uid:
        print("¡Autenticación exitosa!")
        print(f"UID de usuario: {uid}")
    else:
        print("Error de autenticación: Usuario o contraseña incorrectos.")
        exit()
except Exception as e:
    print(f"Error de conexión: {e}")
    exit()

# --- 3. EJECUTAR UNA ACCIÓN (LEER DATOS) ---
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

try:
    print("\nBuscando 5 productos de ejemplo...")
    product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[]], {'limit': 5})

    if not product_ids:
        print("No se encontraron productos.")
    else:
        products = models.execute_kw(db, uid, password, 'product.product', 'read', [product_ids], {'fields': ['id', 'name', 'default_code']})
        print("5 productos encontrados:")
        for product in products:
            # No imprimir la contraseña ni datos sensibles en producción
            print(f"  - ID: {product['id']}, Código: {product['default_code']}, Nombre: {product['name']}")
except Exception as e:
    print(f"Error al consultar datos de Odoo: {e}")