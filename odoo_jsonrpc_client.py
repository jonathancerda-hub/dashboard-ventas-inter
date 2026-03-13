"""
odoo_jsonrpc_client.py

Cliente JSON-RPC para Odoo - Solución al bug de cs_login_audit_log
Compatible con la API de xmlrpc.client para facilitar migración

USO BÁSICO:
-----------
from odoo_jsonrpc_client import OdooJSONRPCClient
import os

# Conectar
client = OdooJSONRPCClient(
    url=os.getenv('ODOO_URL'),
    db=os.getenv('ODOO_DB'),
    username=os.getenv('ODOO_USER'),
    password=os.getenv('ODOO_PASSWORD')
)

# Buscar y leer
products = client.search_read(
    'product.product',
    domain=[('active', '=', True)],
    fields=['name', 'default_code', 'list_price'],
    limit=10
)

# Crear registro
new_partner_id = client.create('res.partner', {
    'name': 'Nuevo Cliente',
    'email': 'cliente@example.com'
})

# Actualizar registro
client.write('res.partner', [new_partner_id], {
    'phone': '+51 999 888 777'
})

# Eliminar registro
client.unlink('res.partner', [new_partner_id])

VENTAJAS:
---------
✅ Evita el bug del módulo cs_login_audit_log
✅ Mejor rendimiento que XML-RPC
✅ Payloads más pequeños (JSON vs XML)
✅ Fácil de debuggear
✅ Compatible con código XML-RPC existente

AUTOR: Jonathan Cerda
FECHA: Marzo 2026
LICENCIA: MIT
"""

import requests
import logging
from typing import List, Dict, Any, Optional, Union

class OdooJSONRPCError(Exception):
    """Excepción personalizada para errores de Odoo"""
    pass

class OdooJSONRPCClient:
    """
    Cliente JSON-RPC para Odoo
    
    Reemplaza xmlrpc.client evitando bugs de módulos que interceptan XML-RPC
    """
    
    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        password: str,
        timeout: int = 30,
        auto_authenticate: bool = True
    ):
        """
        Inicializar cliente Odoo JSON-RPC
        
        Args:
            url: URL base de Odoo (ej: https://mycompany.odoo.com)
            db: Nombre de la base de datos
            username: Usuario de Odoo (email)
            password: Contraseña o API Key
            timeout: Timeout en segundos para peticiones HTTP
            auto_authenticate: Si True, autentica automáticamente al crear instancia
        """
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.timeout = timeout
        self.jsonrpc_url = f"{self.url}/jsonrpc"
        self.uid = None
        self._request_id = 0
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Autenticar
        if auto_authenticate:
            self.authenticate()
    
    def _get_next_id(self) -> int:
        """Generar ID único para peticiones JSON-RPC"""
        self._request_id += 1
        return self._request_id
    
    def _call_json_rpc(
        self,
        service: str,
        method: str,
        args: List[Any]
    ) -> Any:
        """
        Llamada genérica JSON-RPC
        
        Args:
            service: Servicio Odoo ('common', 'object', 'db')
            method: Método a ejecutar
            args: Lista de argumentos
            
        Returns:
            Resultado de la llamada
            
        Raises:
            OdooJSONRPCError: Si hay error en la llamada
        """
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": args
            },
            "id": self._get_next_id()
        }
        
        try:
            response = requests.post(
                self.jsonrpc_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            if "result" in result:
                return result["result"]
            elif "error" in result:
                error = result["error"]
                error_data = error.get("data", {})
                error_msg = error_data.get("message", str(error))
                
                # Log detallado del error
                self.logger.error(f"Odoo Error: {error_msg}")
                if "debug" in error_data:
                    self.logger.debug(f"Debug info: {error_data['debug']}")
                
                raise OdooJSONRPCError(error_msg)
            else:
                raise OdooJSONRPCError("Invalid response from Odoo (no result or error)")
                
        except requests.exceptions.Timeout:
            raise OdooJSONRPCError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise OdooJSONRPCError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise OdooJSONRPCError(f"Request error: {e}")
    
    def authenticate(self) -> int:
        """
        Autenticar y obtener UID
        
        Returns:
            UID del usuario autenticado
            
        Raises:
            OdooJSONRPCError: Si la autenticación falla
        """
        try:
            result = self._call_json_rpc(
                service="common",
                method="authenticate",
                args=[self.db, self.username, self.password, {}]
            )
            
            if result:
                self.uid = result
                self.logger.info(f"✅ Authenticated successfully. UID: {self.uid}")
                return self.uid
            else:
                raise OdooJSONRPCError("Authentication failed: invalid credentials")
                
        except Exception as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            raise
    
    def execute_kw(
        self,
        model: str,
        method: str,
        args: List[Any],
        kwargs: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Ejecutar método de modelo Odoo (compatible con xmlrpc.client)
        
        Args:
            model: Modelo de Odoo (ej: 'res.partner', 'product.product')
            method: Método a ejecutar (ej: 'search', 'read', 'create')
            args: Lista de argumentos posicionales
            kwargs: Diccionario de argumentos con nombre
            
        Returns:
            Resultado del método
            
        Raises:
            OdooJSONRPCError: Si no está autenticado o hay error
        """
        if not self.uid:
            raise OdooJSONRPCError("Not authenticated. Call authenticate() first.")
        
        if kwargs is None:
            kwargs = {}
        
        return self._call_json_rpc(
            service="object",
            method="execute_kw",
            args=[self.db, self.uid, self.password, model, method, args, kwargs]
        )
    
    # ========== MÉTODOS DE CONVENIENCIA ==========
    
    def search(
        self,
        model: str,
        domain: List[Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[int]:
        """
        Buscar IDs de registros
        
        Args:
            model: Modelo de Odoo
            domain: Dominio de búsqueda (ej: [('active', '=', True)])
            limit: Límite de resultados
            offset: Offset para paginación
            order: Orden de resultados (ej: 'name ASC')
            
        Returns:
            Lista de IDs encontrados
        """
        kwargs = {}
        if limit is not None:
            kwargs['limit'] = limit
        if offset is not None:
            kwargs['offset'] = offset
        if order is not None:
            kwargs['order'] = order
        
        return self.execute_kw(model, 'search', [domain], kwargs)
    
    def search_count(self, model: str, domain: List[Any]) -> int:
        """
        Contar registros que coinciden con el dominio
        
        Args:
            model: Modelo de Odoo
            domain: Dominio de búsqueda
            
        Returns:
            Número de registros
        """
        return self.execute_kw(model, 'search_count', [domain])
    
    def read(
        self,
        model: str,
        ids: Union[int, List[int]],
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Leer registros por IDs
        
        Args:
            model: Modelo de Odoo
            ids: ID o lista de IDs
            fields: Lista de campos a leer (None = todos)
            
        Returns:
            Lista de diccionarios con los datos
        """
        if isinstance(ids, int):
            ids = [ids]
        
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        
        return self.execute_kw(model, 'read', [ids], kwargs)
    
    def search_read(
        self,
        model: str,
        domain: List[Any],
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Buscar y leer en una sola operación (más eficiente)
        
        Args:
            model: Modelo de Odoo
            domain: Dominio de búsqueda
            fields: Lista de campos a leer
            limit: Límite de resultados
            offset: Offset para paginación
            order: Orden de resultados
            
        Returns:
            Lista de diccionarios con los datos
        """
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        if limit is not None:
            kwargs['limit'] = limit
        if offset is not None:
            kwargs['offset'] = offset
        if order is not None:
            kwargs['order'] = order
        
        return self.execute_kw(model, 'search_read', [domain], kwargs)
    
    def create(
        self,
        model: str,
        values: Dict[str, Any]
    ) -> int:
        """
        Crear un nuevo registro
        
        Args:
            model: Modelo de Odoo
            values: Diccionario con los valores del registro
            
        Returns:
            ID del registro creado
        """
        return self.execute_kw(model, 'create', [values])
    
    def write(
        self,
        model: str,
        ids: Union[int, List[int]],
        values: Dict[str, Any]
    ) -> bool:
        """
        Actualizar registros existentes
        
        Args:
            model: Modelo de Odoo
            ids: ID o lista de IDs a actualizar
            values: Diccionario con los valores a actualizar
            
        Returns:
            True si la actualización fue exitosa
        """
        if isinstance(ids, int):
            ids = [ids]
        
        return self.execute_kw(model, 'write', [ids, values])
    
    def unlink(
        self,
        model: str,
        ids: Union[int, List[int]]
    ) -> bool:
        """
        Eliminar registros
        
        Args:
            model: Modelo de Odoo
            ids: ID o lista de IDs a eliminar
            
        Returns:
            True si la eliminación fue exitosa
        """
        if isinstance(ids, int):
            ids = [ids]
        
        return self.execute_kw(model, 'unlink', [ids])
    
    def fields_get(
        self,
        model: str,
        fields: Optional[List[str]] = None,
        attributes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Obtener información de campos de un modelo
        
        Args:
            model: Modelo de Odoo
            fields: Lista de campos específicos (None = todos)
            attributes: Lista de atributos a incluir
            
        Returns:
            Diccionario con información de campos
        """
        args = []
        kwargs = {}
        
        if fields:
            args.append(fields)
        if attributes:
            kwargs['attributes'] = attributes
        
        return self.execute_kw(model, 'fields_get', args, kwargs)
    
    def name_search(
        self,
        model: str,
        name: str = '',
        domain: Optional[List[Any]] = None,
        operator: str = 'ilike',
        limit: int = 100
    ) -> List[tuple]:
        """
        Búsqueda por nombre (útil para autocompletado)
        
        Args:
            model: Modelo de Odoo
            name: Texto a buscar
            domain: Dominio adicional
            operator: Operador de búsqueda ('ilike', '=', 'like')
            limit: Límite de resultados
            
        Returns:
            Lista de tuplas (id, display_name)
        """
        if domain is None:
            domain = []
        
        return self.execute_kw(
            model,
            'name_search',
            [name],
            {'args': domain, 'operator': operator, 'limit': limit}
        )
    
    # ========== UTILIDADES ==========
    
    def get_server_version(self) -> Dict[str, Any]:
        """Obtener información de versión del servidor"""
        return self._call_json_rpc(
            service="common",
            method="version",
            args=[]
        )
    
    def check_access_rights(
        self,
        model: str,
        operation: str = 'read',
        raise_exception: bool = False
    ) -> bool:
        """
        Verificar permisos de acceso
        
        Args:
            model: Modelo de Odoo
            operation: 'read', 'write', 'create', 'unlink'
            raise_exception: Si True, lanza excepción en caso de no tener acceso
            
        Returns:
            True si tiene acceso, False si no
        """
        return self.execute_kw(
            model,
            'check_access_rights',
            [operation],
            {'raise_exception': raise_exception}
        )
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        auth_status = "authenticated" if self.uid else "not authenticated"
        return f"<OdooJSONRPCClient url={self.url} db={self.db} user={self.username} {auth_status}>"


# ========== EJEMPLO DE USO ==========

if __name__ == "__main__":
    """Ejemplo de uso del cliente"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Conectar
        print("Conectando a Odoo...")
        client = OdooJSONRPCClient(
            url=os.getenv('ODOO_URL'),
            db=os.getenv('ODOO_DB'),
            username=os.getenv('ODOO_USER'),
            password=os.getenv('ODOO_PASSWORD')
        )
        
        # Versión del servidor
        version = client.get_server_version()
        print(f"\nOdoo Version: {version}")
        
        # Buscar productos
        print("\n📦 Buscando productos...")
        products = client.search_read(
            'product.product',
            domain=[],
            fields=['name', 'default_code', 'list_price'],
            limit=5
        )
        
        print(f"Encontrados {len(products)} productos:")
        for product in products:
            code = product.get('default_code', 'N/A')
            name = product.get('name', 'Sin nombre')
            price = product.get('list_price', 0)
            print(f"  [{code}] {name} - ${price:.2f}")
        
        # Buscar partners
        print("\n👥 Buscando partners...")
        partners_count = client.search_count('res.partner', [])
        print(f"Total partners: {partners_count}")
        
        partners = client.search_read(
            'res.partner',
            domain=[('is_company', '=', True)],
            fields=['name', 'email', 'phone'],
            limit=3
        )
        
        print(f"Empresas encontradas:")
        for partner in partners:
            name = partner.get('name', 'Sin nombre')
            email = partner.get('email', 'N/A')
            phone = partner.get('phone', 'N/A')
            print(f"  {name} - {email} - {phone}")
        
        print("\n✅ Todas las operaciones exitosas")
        
    except OdooJSONRPCError as e:
        print(f"\n❌ Error de Odoo: {e}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
