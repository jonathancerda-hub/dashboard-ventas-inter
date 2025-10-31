import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import logging
import json

class GoogleSheetsManager:
    def __init__(self, credentials_file, sheet_name):
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
            self.client = gspread.authorize(creds)
            logging.info(f"Intentando abrir la hoja de cálculo: '{sheet_name}'")
            self.sheet = self.client.open(sheet_name)
            logging.info("Conexión a Google Sheets establecida exitosamente.")
        except Exception as e:
            logging.error(f"Error al conectar con Google Sheets: {e}")
            logging.info("Asegúrate de que 'credentials.json' existe y el nombre de la hoja en .env es correcto.")
            self.client = None
            self.sheet = None

    def read_equipos(self):
        """Lee la asignación de equipos desde la pestaña 'Equipos'."""
        if not self.sheet:
            return {}
        try:
            worksheet = self.sheet.worksheet("Equipos")
            records = worksheet.get_all_records()
            equipos_dict = {}
            for row in records:
                equipo_id = row.get('equipo_id')
                vendedor_id = row.get('vendedor_id')
                if equipo_id:
                    if equipo_id not in equipos_dict:
                        equipos_dict[equipo_id] = []
                    if vendedor_id and str(vendedor_id).isdigit():
                        equipos_dict[equipo_id].append(int(vendedor_id))
            return equipos_dict
        except gspread.exceptions.WorksheetNotFound:
            logging.warning("Pestaña 'Equipos' no encontrada en Google Sheet. Creándola...")
            self.sheet.add_worksheet(title="Equipos", rows="200", cols="3")
            worksheet = self.sheet.worksheet("Equipos")
            worksheet.update('A1:C1', [['equipo_id', 'vendedor_id', 'vendedor_nombre']])
            return {}
        except Exception as e:
            logging.error(f"Error al leer la pestaña 'Equipos': {e}")
            return {}

    def write_equipos(self, equipos_data, todos_los_vendedores):
        """Escribe la asignación de equipos en la pestaña 'Equipos'."""
        if not self.sheet:
            return
        try:
            worksheet = self.sheet.worksheet("Equipos")
            header = ['equipo_id', 'vendedor_id', 'vendedor_nombre']
            rows = [header]
            vendedores_por_id = {v['id']: v['name'] for v in todos_los_vendedores}

            for equipo_id, vendedor_ids_list in equipos_data.items():
                for vendedor_id in vendedor_ids_list:
                    vendedor_nombre = vendedores_por_id.get(vendedor_id, 'Nombre no encontrado')
                    rows.append([equipo_id, vendedor_id, vendedor_nombre])

            worksheet.clear()
            worksheet.update(rows, value_input_option='USER_ENTERED')
        except Exception as e:
            logging.error(f"Error al escribir en la pestaña 'Equipos': {e}")

    def read_metas(self):
        """Lee las metas desde la pestaña 'Metas' y las transforma a la estructura anidada."""
        if not self.sheet:
            return {}
        try:
            worksheet = self.sheet.worksheet("Metas")
            df = pd.DataFrame(worksheet.get_all_records())
            
            metas_anidadas = {}
            if df.empty:
                return {}

            for _, row in df.iterrows():
                equipo_id = str(row['equipo_id'])
                vendedor_id = str(row['vendedor_id'])
                mes = str(row['mes'])
                
                if equipo_id not in metas_anidadas:
                    metas_anidadas[equipo_id] = {}
                if vendedor_id not in metas_anidadas[equipo_id]:
                    metas_anidadas[equipo_id][vendedor_id] = {}
                
                metas_anidadas[equipo_id][vendedor_id][mes] = {
                    'meta': float(row.get('meta', 0)),
                    'meta_ipn': float(row.get('meta_ipn', 0))
                }
            return metas_anidadas
        except gspread.exceptions.WorksheetNotFound:
            logging.warning("Pestaña 'Metas' no encontrada en Google Sheet. Creándola...")
            self.sheet.add_worksheet(title="Metas", rows="1000", cols="5")
            worksheet = self.sheet.worksheet("Metas")
            worksheet.update('A1:E1', [['equipo_id', 'vendedor_id', 'mes', 'meta', 'meta_ipn']])
            return {}
        except Exception as e:
            logging.error(f"Error al leer la pestaña 'Metas': {e}")
            return {}

    def write_metas(self, metas_anidadas):
        """Toma la estructura anidada, la aplana y la escribe en la pestaña 'Metas'."""
        if not self.sheet:
            return
        
        flat_data = []
        for equipo_id, vendedores in metas_anidadas.items():
            for vendedor_id, meses in vendedores.items():
                for mes, valores in meses.items():
                    flat_data.append({
                        'equipo_id': equipo_id,
                        'vendedor_id': vendedor_id,
                        'mes': mes,
                        'meta': valores.get('meta', 0),
                        'meta_ipn': valores.get('meta_ipn', 0)
                    })
        
        df = pd.DataFrame(flat_data)
        worksheet = self.sheet.worksheet("Metas")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist(), value_input_option='USER_ENTERED')

    def read_metas_por_linea(self):
        """Lee las metas por línea desde la pestaña 'MetasPorLinea'."""
        if not self.sheet:
            return {}
        try:
            worksheet = self.sheet.worksheet("MetasPorLinea")
            records = worksheet.get_all_records()
            metas_por_linea = {}
            for row in records:
                mes_key = row.get('mes_key')
                if mes_key:
                    # Eliminar la clave del mes para no incluirla en los diccionarios de metas
                    del row['mes_key']
                    
                    metas = {}
                    for k, v in row.items():
                        if not k.endswith('_ipn') and v != '':
                            try:
                                metas[k] = float(v)
                            except (ValueError, TypeError):
                                metas[k] = 0.0

                    metas_ipn = {}
                    for k, v in row.items():
                        if k.endswith('_ipn') and v != '':
                            try:
                                metas_ipn[k.replace('_ipn', '')] = float(v)
                            except (ValueError, TypeError):
                                metas_ipn[k.replace('_ipn', '')] = 0.0
                    
                    metas_por_linea[mes_key] = {
                        'metas': metas,
                        'metas_ipn': metas_ipn,
                        'total': sum(metas.values()),
                        'total_ipn': sum(metas_ipn.values())
                    }
            return metas_por_linea
        except gspread.exceptions.WorksheetNotFound:
            logging.warning("Pestaña 'MetasPorLinea' no encontrada. Por favor, créala manualmente.")
            return {}
        except Exception as e:
            logging.error(f"Error al leer la pestaña 'MetasPorLinea': {e}")
            return {}

    def write_metas_por_linea(self, metas_data):
        """Escribe las metas por línea en la pestaña 'MetasPorLinea'."""
        if not self.sheet:
            return
        
        flat_data = []
        all_keys = set(['mes_key'])
        for mes_key, data in metas_data.items():
            row = {'mes_key': mes_key}
            row.update(data.get('metas', {}))
            row.update({f"{k}_ipn": v for k, v in data.get('metas_ipn', {}).items()})
            all_keys.update(row.keys())
            flat_data.append(row)
        
        header = sorted(list(all_keys), key=lambda x: (x.endswith('_ipn'), x))
        df = pd.DataFrame(flat_data, columns=header)
        
        worksheet = self.sheet.worksheet("MetasPorLinea")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.fillna('').values.tolist(), value_input_option='USER_ENTERED')

    def read_metas_por_cliente(self):
        """Lee las metas por cliente desde la hoja 'Metas_cliente' en formato ancho."""
        sheet_name = 'Metas_cliente'
        try:
            worksheet = self.sheet.worksheet(sheet_name)
            records = worksheet.get_all_records()
            
            # Mapeo de nombres de columna a IDs de línea
            linea_map = {'AGROVET': 'agrovet', 'PETMEDICA': 'petmedica', 'AVIVET': 'avivet'}
            
            metas_anidadas = {}
            for record in records:
                año = str(record.get('año'))
                # CORRECCIÓN CLAVE: Asegurarse de que el ID del cliente siempre sea un string.
                # gspread puede leerlo como int si es numérico, lo que causa inconsistencias.
                cliente_id_raw = record.get('cliente_id')
                cliente_id = str(cliente_id_raw) if cliente_id_raw is not None else None
                
                if not año or not cliente_id:
                    continue
                    
                if año not in metas_anidadas:
                    metas_anidadas[año] = {}
                if cliente_id not in metas_anidadas[año]:
                    metas_anidadas[año][cliente_id] = {}
                
                for col_name, linea_id in linea_map.items():
                    meta_str = record.get(col_name, '0')
                    try:
                        # Lógica de limpieza de números robusta:
                        # 1. Convertir a string para asegurar que podemos manipularlo.
                        # 2. Si hay una coma, asumimos que es el separador decimal y quitamos los puntos.
                        # 3. Si no hay coma, asumimos que el punto es el separador decimal y quitamos las comas.
                        s = str(meta_str)
                        if ',' in s:
                            cleaned_str = s.replace('.', '').replace(',', '.')
                        else:
                            cleaned_str = s.replace(',', '')
                        meta_val = float(cleaned_str) if cleaned_str else 0.0
                        if meta_val > 0:
                            metas_anidadas[año][cliente_id][linea_id] = meta_val
                    except (ValueError, TypeError):
                        continue # Ignorar valores no numéricos

            return metas_anidadas
        except gspread.exceptions.WorksheetNotFound:
            logging.warning(f"La hoja '{sheet_name}' no fue encontrada. Creándola...")
            self._create_worksheet_if_not_exists(sheet_name)
            worksheet = self.sheet.worksheet(sheet_name)
            # Crear cabecera para el nuevo formato
            worksheet.update('A1:F1', [['año', 'cliente_id', 'cliente_nombre', 'AGROVET', 'PETMEDICA', 'AVIVET']])
            return {}
        except Exception as e:
            logging.error(f"Error al leer la hoja '{sheet_name}': {e}")
            return {}

    def write_metas_por_cliente(self, data):
        """Toma la estructura anidada, la convierte a formato ancho y la escribe en 'Metas_cliente'."""
        sheet_name = 'Metas_cliente'
        try:
            worksheet = self.sheet.worksheet(sheet_name)
            
            # Mapeo de IDs de línea a nombres de columna
            linea_map_inv = {'agrovet': 'AGROVET', 'petmedica': 'PETMEDICA', 'avivet': 'AVIVET'}
            
            flat_data = []
            for año, clientes in data.items():
                for cliente_id, metas in clientes.items():
                    row = {
                        'año': año,
                        'cliente_id': cliente_id,
                        'cliente_nombre': metas.get('cliente_nombre', ''), # Guardar el nombre del cliente
                        'AGROVET': metas.get('agrovet', 0),
                        'PETMEDICA': metas.get('petmedica', 0),
                        'AVIVET': metas.get('avivet', 0)
                    }
                    row['TOTAL'] = row['AGROVET'] + row['PETMEDICA'] + row['AVIVET']
                    flat_data.append(row)
            
            if not flat_data:
                worksheet.clear()
                worksheet.update('A1:G1', [['año', 'cliente_id', 'cliente_nombre', 'AGROVET', 'PETMEDICA', 'AVIVET', 'TOTAL']])
                return

            df = pd.DataFrame(flat_data)
            worksheet.clear()
            worksheet.update([df.columns.values.tolist()] + df.values.tolist(), value_input_option='USER_ENTERED')
        except gspread.exceptions.WorksheetNotFound:
            logging.warning(f"La hoja '{sheet_name}' no fue encontrada. Creándola y escribiendo datos...")
            worksheet = self._create_worksheet_if_not_exists(sheet_name)
            if worksheet:
                self.write_metas_por_cliente(data) # Reintentar escritura
        except Exception as e:
            logging.error(f"Error al escribir en la hoja '{sheet_name}': {e}")

    def _create_worksheet_if_not_exists(self, title):
        """Crea una hoja de cálculo si no existe."""
        try:
            return self.sheet.add_worksheet(title=title, rows="100", cols="20")
        except gspread.exceptions.APIError as e:
            if 'already exists' in str(e):
                logging.info(f"La hoja '{title}' ya existe, no se creó de nuevo.")
                return self.sheet.worksheet(title)
            else:
                logging.error(f"Error de API al intentar crear la hoja '{title}': {e}")
                raise