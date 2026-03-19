"""
Database package - Gestión de conexiones y operaciones con bases de datos
"""

from .odoo_manager import OdooManager
from .supabase_manager import SupabaseManager
from .google_sheets_manager import GoogleSheetsManager

__all__ = ['OdooManager', 'SupabaseManager', 'GoogleSheetsManager']
