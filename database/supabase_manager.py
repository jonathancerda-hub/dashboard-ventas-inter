"""
Supabase Manager - Gestión de metas de clientes en base de datos PostgreSQL
Reemplaza Google Sheets como fuente de datos persistente
"""

import os
import logging
from supabase import create_client, Client
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class SupabaseManager:
    """Gestor de conexión y operaciones con Supabase para metas de clientes"""
    
    def __init__(self):
        """Inicializar cliente de Supabase"""
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados en .env")
        
        try:
            self.client: Client = create_client(self.url, self.key)
            logging.info("✅ Cliente Supabase inicializado correctamente")
        except Exception as e:
            logging.error(f"❌ Error inicializando cliente Supabase: {e}")
            raise
    
    def read_metas_por_cliente(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Lee las metas de clientes desde Supabase.
        
        Retorna estructura anidada compatible con el código existente:
        {
            "2026": {
                "12345": {
                    "cliente_nombre": "Cliente X",
                    "agrovet": 50000.0,
                    "petmedica": 30000.0,
                    "avivet": 20000.0
                }
            }
        }
        """
        try:
            # Consultar todas las metas
            response = self.client.table('metas_clientes').select('*').execute()
            
            if not response.data:
                logging.info("No hay metas registradas en Supabase")
                return {}
            
            # Convertir a estructura anidada
            metas_anidadas = {}
            for record in response.data:
                año = str(record.get('año'))
                cliente_id = str(record.get('cliente_id'))
                
                if not año or not cliente_id:
                    continue
                
                # Crear estructura anidada
                if año not in metas_anidadas:
                    metas_anidadas[año] = {}
                
                if cliente_id not in metas_anidadas[año]:
                    metas_anidadas[año][cliente_id] = {}
                
                # Agregar valores (convertir a float)
                metas_anidadas[año][cliente_id]['cliente_nombre'] = record.get('cliente_nombre', '')
                
                if record.get('agrovet') and float(record.get('agrovet', 0)) > 0:
                    metas_anidadas[año][cliente_id]['agrovet'] = float(record.get('agrovet'))
                
                if record.get('petmedica') and float(record.get('petmedica', 0)) > 0:
                    metas_anidadas[año][cliente_id]['petmedica'] = float(record.get('petmedica'))
                
                if record.get('avivet') and float(record.get('avivet', 0)) > 0:
                    metas_anidadas[año][cliente_id]['avivet'] = float(record.get('avivet'))
            
            logging.info(f"✅ Metas leídas: {len(response.data)} registros")
            return metas_anidadas
            
        except Exception as e:
            logging.error(f"❌ Error leyendo metas de Supabase: {e}")
            return {}
    
    def write_metas_por_cliente(self, data: Dict[str, Dict[str, Dict[str, float]]]) -> bool:
        """
        Escribe las metas de clientes en Supabase.
        
        Recibe estructura anidada y la convierte a formato de tabla.
        Usa UPSERT para actualizar o insertar según corresponda.
        
        Args:
            data: Diccionario anidado con estructura:
                  {año: {cliente_id: {linea: valor, ...}}}
        
        Returns:
            bool: True si la operación fue exitosa
        """
        try:
            # Convertir estructura anidada a lista de registros
            registros = []
            for año, clientes in data.items():
                for cliente_id, metas in clientes.items():
                    registro = {
                        'año': str(año),
                        'cliente_id': str(cliente_id),
                        'cliente_nombre': metas.get('cliente_nombre', ''),
                        'agrovet': float(metas.get('agrovet', 0)),
                        'petmedica': float(metas.get('petmedica', 0)),
                        'avivet': float(metas.get('avivet', 0))
                    }
                    registros.append(registro)
            
            if not registros:
                logging.warning("No hay registros para escribir en Supabase")
                return True
            
            # UPSERT: insertar o actualizar si existe el constraint único (año, cliente_id)
            response = self.client.table('metas_clientes').upsert(
                registros,
                on_conflict='año,cliente_id'
            ).execute()
            
            logging.info(f"✅ Metas guardadas en Supabase: {len(registros)} registros")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error escribiendo metas en Supabase: {e}")
            logging.exception(e)
            return False
    
    def get_metas_por_año(self, año: str) -> Dict[str, Dict[str, float]]:
        """
        Obtiene metas de un año específico.
        
        Args:
            año: Año en formato string (ej: "2026")
        
        Returns:
            Dict con estructura {cliente_id: {linea: valor, ...}}
        """
        try:
            response = self.client.table('metas_clientes').select('*').eq('año', año).execute()
            
            metas = {}
            for record in response.data:
                cliente_id = str(record.get('cliente_id'))
                metas[cliente_id] = {
                    'cliente_nombre': record.get('cliente_nombre', ''),
                    'agrovet': float(record.get('agrovet', 0)),
                    'petmedica': float(record.get('petmedica', 0)),
                    'avivet': float(record.get('avivet', 0))
                }
            
            return metas
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo metas del año {año}: {e}")
            return {}
    
    def delete_metas_cliente(self, año: str, cliente_id: str) -> bool:
        """
        Elimina las metas de un cliente específico en un año.
        
        Args:
            año: Año en formato string
            cliente_id: ID del cliente
        
        Returns:
            bool: True si la operación fue exitosa
        """
        try:
            response = self.client.table('metas_clientes').delete().eq(
                'año', año
            ).eq(
                'cliente_id', cliente_id
            ).execute()
            
            logging.info(f"✅ Metas eliminadas: año={año}, cliente={cliente_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error eliminando metas: {e}")
            return False
    
    def get_años_disponibles(self) -> List[str]:
        """
        Obtiene la lista de años con metas registradas.
        
        Returns:
            Lista de años ordenados descendentemente
        """
        try:
            response = self.client.table('metas_clientes').select('año').execute()
            
            años = sorted(list(set(record['año'] for record in response.data)), reverse=True)
            return años
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo años disponibles: {e}")
            return []


# Función de utilidad para pruebas
def test_connection():
    """Prueba la conexión a Supabase"""
    try:
        manager = SupabaseManager()
        print("✅ Conexión exitosa a Supabase")
        
        # Probar lectura
        metas = manager.read_metas_por_cliente()
        print(f"✅ Metas leídas: {len(metas)} años disponibles")
        
        return True
    except Exception as e:
        print(f"❌ Error en conexión: {e}")
        return False


if __name__ == "__main__":
    # Ejecutar test de conexión
    logging.basicConfig(level=logging.INFO)
    test_connection()
