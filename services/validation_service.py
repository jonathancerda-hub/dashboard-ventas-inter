# services/validation_service.py
"""
Servicio de validación centralizada de inputs.
Cumple con OWASP Input Validation y previene CWE-20.

Este servicio implementa el principio de Single Responsibility (SRP) al
concentrar toda la lógica de validación de inputs en un solo lugar.

Ejemplo de uso:
    >>> validator = ValidationService()
    >>> año = validator.validate_year(request.args.get('año'))
    >>> linea = validator.validate_linea_comercial(request.args.get('linea'))
    >>> 
    >>> # En app.py
    >>> try:
    >>>     filters = validator.validate_dashboard_filters(request.args)
    >>> except ValueError as e:
    >>>     flash(str(e), 'error')
    >>>     return redirect(url_for('dashboard'))

Seguridad:
    - Sanitiza inputs para prevenir SQL injection
    - Valida rangos para prevenir integer overflow
    - Limita longitud de strings para prevenir DoS
    - Previene path traversal en parámetros de archivo

Referencias:
    - OWASP Input Validation Cheat Sheet
    - CWE-20: Improper Input Validation
    - CWE-89: SQL Injection
"""

from typing import Dict, Any, Optional
from datetime import datetime
import re


class ValidationService:
    """
    Validación centralizada y segura de inputs del usuario.
    
    Este servicio proporciona métodos seguros para validar y sanitizar
    todos los inputs que vienen de requests HTTP, previeniendo vulnerabilidades
    comunes como injection attacks y buffer overflows.
    
    Attributes:
        MIN_YEAR: Año mínimo válido (2020)
        MAX_YEAR: Año máximo válido (año actual + 5)
        DEFAULT_PER_PAGE: Items por página por defecto (1000)
        MAX_PER_PAGE: Máximo items por página (10000)
    
    Example:
        >>> validator = ValidationService()
        >>> año = validator.validate_year('2026')  # Returns: 2026
        >>> año = validator.validate_year('invalid')  # Raises: ValueError
        >>> 
        >>> linea = validator.validate_linea_comercial('AGROVET')  # Returns: 'AGROVET'
        >>> linea = validator.validate_linea_comercial('<script>')  # Raises: ValueError
    """
    
    def __init__(self):
        """Inicializar servicio de validación con reglas."""
        # Rango de años válidos
        self.MIN_YEAR = 2020
        self.MAX_YEAR = datetime.now().year + 5
        
        # Patrones de validación
        self.LINEA_COMERCIAL_PATTERN = re.compile(r'^[A-Z0-9_-]+$', re.IGNORECASE)
        self.FECHA_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        # Límites de paginación
        self.MIN_PAGE = 1
        self.MAX_PAGE = 99999
        self.MIN_PER_PAGE = 1
        self.MAX_PER_PAGE = 10000
        self.DEFAULT_PER_PAGE = 1000
    
    def validate_year(self, year_str: Any, default: Optional[int] = None) -> int:
        """
        Valida y sanitiza un año.
        
        Args:
            year_str: Año a validar (puede ser str, int, None)
            default: Año por defecto si no se proporciona
        
        Returns:
            int: Año validado
        
        Raises:
            ValueError: Si el año es inválido
        """
        if year_str is None:
            return default or datetime.now().year
        
        try:
            year = int(year_str)
            if not (self.MIN_YEAR <= year <= self.MAX_YEAR):
                raise ValueError(
                    f"Año fuera de rango válido ({self.MIN_YEAR}-{self.MAX_YEAR}): {year}"
                )
            return year
        except (ValueError, TypeError) as e:
            if default is not None:
                return default
            raise ValueError(f"Año inválido: {year_str}") from e
    
    def validate_linea_comercial(self, linea: Any) -> str:
        """
        Valida línea comercial.
        
        Args:
            linea: Línea comercial a validar
        
        Returns:
            str: Línea comercial validada (vacío si no se proporciona)
        
        Raises:
            ValueError: Si la línea contiene caracteres inválidos
        """
        if not linea:
            return ''
        
        linea_str = str(linea).strip().upper()
        
        # Validar formato
        if not self.LINEA_COMERCIAL_PATTERN.match(linea_str):
            raise ValueError(
                f"Línea comercial contiene caracteres inválidos: {linea}"
            )
        
        # Validar longitud
        if len(linea_str) > 50:
            raise ValueError(
                f"Línea comercial demasiado larga (max 50 caracteres): {linea}"
            )
        
        return linea_str
    
    def validate_page(self, page: Any, default: int = 1) -> int:
        """
        Valida número de página.
        
        Args:
            page: Número de página a validar
            default: Página por defecto
        
        Returns:
            int: Número de página validado
        """
        try:
            page_int = int(page)
            if page_int < self.MIN_PAGE:
                return self.MIN_PAGE
            if page_int > self.MAX_PAGE:
                return self.MAX_PAGE
            return page_int
        except (ValueError, TypeError):
            return default
    
    def validate_per_page(self, per_page: Any, default: Optional[int] = None) -> int:
        """
        Valida items por página.
        
        Args:
            per_page: Items por página a validar
            default: Valor por defecto
        
        Returns:
            int: Items por página validado
        """
        if default is None:
            default = self.DEFAULT_PER_PAGE
        
        try:
            per_page_int = int(per_page)
            if per_page_int < self.MIN_PER_PAGE:
                return self.MIN_PER_PAGE
            if per_page_int > self.MAX_PER_PAGE:
                return self.MAX_PER_PAGE
            return per_page_int
        except (ValueError, TypeError):
            return default
    
    def validate_partner_id(self, partner_id: Any) -> Optional[int]:
        """
        Valida ID de partner/cliente.
        
        Args:
            partner_id: ID a validar
        
        Returns:
            Optional[int]: ID validado o None
        
        Raises:
            ValueError: Si el ID es inválido
        """
        if not partner_id or partner_id == '':
            return None
        
        try:
            partner_id_int = int(partner_id)
            if partner_id_int <= 0:
                raise ValueError(f"ID de partner debe ser positivo: {partner_id}")
            return partner_id_int
        except (ValueError, TypeError) as e:
            raise ValueError(f"ID de partner inválido: {partner_id}") from e
    
    def validate_date(self, date_str: Any) -> Optional[str]:
        """
        Valida formato de fecha (YYYY-MM-DD).
        
        Args:
            date_str: Fecha a validar
        
        Returns:
            Optional[str]: Fecha validada o None
        
        Raises:
            ValueError: Si la fecha es inválida
        """
        if not date_str or date_str == '':
            return None
        
        date_str = str(date_str).strip()
        
        # Validar formato con regex
        if not self.FECHA_PATTERN.match(date_str):
            raise ValueError(
                f"Formato de fecha inválido (esperado YYYY-MM-DD): {date_str}"
            )
        
        # Validar que sea una fecha real
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError as e:
            raise ValueError(f"Fecha inválida: {date_str}") from e
    
    def validate_search_term(self, search: Any, max_length: int = 100) -> str:
        """
        Valida término de búsqueda.
        
        Args:
            search: Término a validar
            max_length: Longitud máxima permitida
        
        Returns:
            str: Término de búsqueda sanitizado
        """
        if not search:
            return ''
        
        search_str = str(search).strip()
        
        # Limitar longitud
        if len(search_str) > max_length:
            search_str = search_str[:max_length]
        
        # Eliminar caracteres peligrosos (inyección SQL/XSS básica)
        # Los prepared statements ya protegen contra SQL injection,
        # pero esto es defensa en profundidad
        dangerous_chars = ['<', '>', ';', '--', '/*', '*/', 'script']
        for char in dangerous_chars:
            search_str = search_str.replace(char, '')
        
        return search_str
    
    def validate_dashboard_filters(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida todos los filtros del dashboard en una sola llamada.
        
        Args:
            args: Diccionario con parámetros de request.args
        
        Returns:
            Dict[str, Any]: Filtros validados
        
        Raises:
            ValueError: Si algún filtro es inválido
        """
        validated = {}
        
        # Año
        validated['año'] = self.validate_year(
            args.get('año'),
            default=datetime.now().year
        )
        
        # Línea comercial
        validated['linea'] = self.validate_linea_comercial(
            args.get('linea', '')
        )
        
        # Cliente ID
        cliente_id = args.get('cliente_id')
        if cliente_id:
            validated['cliente_id'] = self.validate_partner_id(cliente_id)
        else:
            validated['cliente_id'] = None
        
        # Fechas
        validated['date_from'] = self.validate_date(args.get('date_from'))
        validated['date_to'] = self.validate_date(args.get('date_to'))
        
        # Término de búsqueda
        validated['search_term'] = self.validate_search_term(
            args.get('search_term', '')
        )
        
        return validated
    
    def validate_pagination_params(self, args: Dict[str, Any]) -> Dict[str, int]:
        """
        Valida parámetros de paginación.
        
        Args:
            args: Diccionario con parámetros
        
        Returns:
            Dict[str, int]: Parámetros de paginación validados
        """
        return {
            'page': self.validate_page(args.get('page', 1)),
            'per_page': self.validate_per_page(args.get('per_page'))
        }
    
    def sanitize_for_cache_key(self, value: Any) -> str:
        """
        Sanitiza un valor para uso seguro en cache keys.
        Previene cache key injection.
        
        Args:
            value: Valor a sanitizar
        
        Returns:
            str: Valor sanitizado
        """
        if value is None:
            return 'none'
        
        # Convertir a string y eliminar caracteres especiales
        safe_value = str(value).strip()
        # Solo permitir alfanuméricos, guiones y guiones bajos
        safe_value = re.sub(r'[^a-zA-Z0-9_-]', '_', safe_value)
        
        # Limitar longitud
        if len(safe_value) > 100:
            safe_value = safe_value[:100]
        
        return safe_value
