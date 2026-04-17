# services/security_logger.py
"""
Servicio de logging centralizado para eventos de seguridad.
Auditoría y detección de comportamiento sospechoso.

Este servicio implementa logging de seguridad siguiendo las recomendaciones de:
- OWASP Logging Cheat Sheet
- NIST SP 800-92: Guide to Computer Security Log Management
- CWE-778: Insufficient Logging

Ejemplo de uso:
    >>> from services.security_logger import SecurityLogger
    >>> 
    >>> # En app.py
    >>> security_logger = SecurityLogger(log_dir='logs')
    >>> 
    >>> # Login exitoso
    >>> @app.route('/login/callback')
    >>> def login_callback():
    >>>     # ... autenticación ...
    >>>     security_logger.log_login_attempt(
    >>>         email=user_email,
    >>>         success=True,
    >>>         request=request
    >>>     )
    >>> 
    >>> # Acceso no autorizado
    >>> @app.before_request
    >>> def check_auth():
    >>>     if 'user' not in session:
    >>>         security_logger.log_unauthorized_access(
    >>>             endpoint=request.endpoint,
    >>>             request=request
    >>>         )
    >>> 
    >>> # Exportación de datos
    >>> @app.route('/export/excel/sales')
    >>> def export_sales():
    >>>     # ... generar export ...
    >>>     security_logger.log_export_request(
    >>>         user=session['email'],
    >>>         export_type='sales',
    >>>         num_records=len(data),
    >>>         filters=request.args.to_dict(),
    >>>         request=request
    >>>     )

Archivos de log generados:
    - logs/security.log: Todos los eventos (INFO+)
    - logs/security_critical.log: Solo eventos críticos (WARNING+)

Formato de logs:
    2026-03-26 10:15:23 | INFO | LOGIN_SUCCESS | Email: user@example.com | IP: 192.168.1.100 | UA: Mozilla/5.0...
    2026-03-26 10:20:45 | WARNING | UNAUTHORIZED_ACCESS | Endpoint: dashboard | IP: 10.0.0.50
    2026-03-26 10:25:12 | INFO | EXPORT_REQUEST | User: user@example.com | Type: sales | Records: 1543

Eventos de seguridad capturados:
    - LOGIN_SUCCESS / LOGIN_FAILED: Intentos de autenticación
    - LOGOUT: Cierre de sesión
    - UNAUTHORIZED_ACCESS: Acceso denegado a recursos protegidos
    - VALIDATION_ERROR: Errores de validación de inputs (posible ataque)
    - EXPORT_REQUEST: Exportación de datos sensibles
    - RATE_LIMIT_EXCEEDED: Exceso de requests (posible ataque)
    - SESSION_ACTIVITY: Actividad de sesión (creación, expiración)
    - DATA_ACCESS: Acceso a datos sensibles

Análisis de seguridad:
    # Buscar múltiples login fallidos (posible brute force)
    grep "LOGIN_FAILED" logs/security_critical.log | awk '{print $11}' | sort | uniq -c | sort -rn
    
    # Buscar patrones de injection en validation errors
    grep "VALIDATION_ERROR" logs/security_critical.log | grep -E "(script|SELECT|DROP|<|>)"
    
    # Contar accesos no autorizados por IP
    grep "UNAUTHORIZED_ACCESS" logs/security_critical.log | awk '{print $9}' | sort | uniq -c

Integración futura:
    - SIEM (Splunk, ELK Stack, Azure Sentinel)
    - Alertas en tiempo real (Slack, Teams, email)
    - Dashboard de seguridad (Grafana)
    - Retención y rotación de logs automática
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class SecurityLogger:
    """
    Logger centralizado para eventos de seguridad.
    
    Implementa logging de dos niveles:
    - security.log: Todos los eventos de seguridad (INFO+)
    - security_critical.log: Solo eventos críticos (WARNING+)
    
    Este patrón facilita:
    1. Auditoría completa (security.log)
    2. Respuesta rápida a incidentes (security_critical.log)
    3. Análisis de patrones de ataque
    4. Cumplimiento regulatorio (SOX, GDPR, HIPAA)
    
    Attributes:
        log_dir: Directorio donde se almacenan los logs
        logger: Logger de Python configurado
    
    Example:
        >>> logger = SecurityLogger(log_dir='logs')
        >>> logger.log_login_attempt('admin@test.com', True, request)
        >>> # Output en logs/security.log:
        >>> # 2026-03-26 10:15:23 | INFO | LOGIN_SUCCESS | Email: admin@test.com | IP: 192.168.1.1 | UA: Mozilla/5.0...
    
    Security Notes:
        - Los logs NO deben contener passwords o tokens
        - IPs y emails son suficientes para auditoría
        - User-Agent se trunca a 100 chars para prevenir DoS
        - Todos los logs usan UTF-8 para soportar caracteres internacionales
    """
    
    def __init__(self, log_dir: str = 'logs'):
        """
        Inicializa el logger de seguridad.
        
        Args:
            log_dir: Directorio donde se almacenarán los logs
        """
        # Crear directorio de logs si no existe
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configurar logger
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # Evitar duplicación de handlers
        if not self.logger.handlers:
            # Handler para archivo de seguridad
            security_log_path = self.log_dir / 'security.log'
            file_handler = logging.FileHandler(
                security_log_path, 
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            
            # Formato detallado para seguridad
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Handler adicional para eventos críticos
            critical_log_path = self.log_dir / 'security_critical.log'
            critical_handler = logging.FileHandler(
                critical_log_path,
                encoding='utf-8'
            )
            critical_handler.setLevel(logging.WARNING)
            critical_handler.setFormatter(formatter)
            self.logger.addHandler(critical_handler)
    
    def _get_client_info(self, request) -> str:
        """
        Extrae información del cliente de forma segura.
        
        Args:
            request: Flask request object
        
        Returns:
            str: Información del cliente formateada
        """
        ip = request.remote_addr or 'Unknown'
        user_agent = request.headers.get('User-Agent', 'Unknown')[:100]  # Limitar longitud
        return f"IP: {ip} | UA: {user_agent}"
    
    def log_login_attempt(
        self, 
        email: str, 
        success: bool, 
        request,
        reason: Optional[str] = None
    ):
        """
        Log intentos de login (exitosos y fallidos).
        
        Args:
            email: Email del usuario
            success: Si el login fue exitoso
            request: Flask request object
            reason: Razón del fallo (opcional)
        """
        status = "SUCCESS" if success else "FAILED"
        client_info = self._get_client_info(request)
        
        message = f"LOGIN_{status} | Email: {email} | {client_info}"
        if reason and not success:
            message += f" | Reason: {reason}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.warning(message)
    
    def log_logout(self, email: str, request):
        """
        Log cuando un usuario cierra sesión.
        
        Args:
            email: Email del usuario
            request: Flask request object
        """
        client_info = self._get_client_info(request)
        self.logger.info(f"LOGOUT | Email: {email} | {client_info}")
    
    def log_unauthorized_access(
        self, 
        endpoint: str, 
        user: Optional[str], 
        request
    ):
        """
        Log accesos no autorizados a rutas protegidas.
        
        Args:
            endpoint: Ruta a la que se intentó acceder
            user: Usuario (si está en sesión)
            request: Flask request object
        """
        client_info = self._get_client_info(request)
        user_str = user or 'Anonymous'
        
        self.logger.warning(
            f"UNAUTHORIZED_ACCESS | Endpoint: {endpoint} | "
            f"User: {user_str} | {client_info}"
        )
    
    def log_validation_error(
        self, 
        param: str, 
        value: Any, 
        request,
        error_type: str = "VALIDATION"
    ):
        """
        Log errores de validación (posibles ataques de inyección).
        
        Args:
            param: Parámetro que falló la validación
            value: Valor que causó el error (truncado)
            request: Flask request object
            error_type: Tipo de error de validación
        """
        client_info = self._get_client_info(request)
        
        # Truncar valor para evitar logs masivos
        value_str = str(value)[:100]
        
        self.logger.warning(
            f"{error_type}_ERROR | Param: {param} | "
            f"Value: {value_str} | {client_info}"
        )
    
    def log_export_request(
        self, 
        user: str, 
        export_type: str,
        filters: Dict[str, Any], 
        num_records: int,
        request
    ):
        """
        Log exportaciones de datos (trazabilidad).
        
        Args:
            user: Email del usuario
            export_type: Tipo de exportación (sales, pending, etc.)
            filters: Filtros aplicados
            num_records: Número de registros exportados
            request: Flask request object
        """
        client_info = self._get_client_info(request)
        
        # Sanitizar filtros para logging
        filters_str = str(filters)[:200]
        
        self.logger.info(
            f"EXPORT_REQUEST | User: {user} | Type: {export_type} | "
            f"Records: {num_records} | Filters: {filters_str} | {client_info}"
        )
    
    def log_rate_limit_exceeded(
        self, 
        endpoint: str, 
        user: Optional[str],
        request
    ):
        """
        Log cuando se excede el límite de rate limiting.
        
        Args:
            endpoint: Ruta donde se excedió el límite
            user: Usuario (si está autenticado)
            request: Flask request object
        """
        client_info = self._get_client_info(request)
        user_str = user or 'Anonymous'
        
        self.logger.warning(
            f"RATE_LIMIT_EXCEEDED | Endpoint: {endpoint} | "
            f"User: {user_str} | {client_info}"
        )
    
    def log_session_activity(
        self, 
        user: str, 
        action: str, 
        details: Optional[str] = None
    ):
        """
        Log actividades de sesión importantes.
        
        Args:
            user: Email del usuario
            action: Acción realizada (session_created, session_expired, etc.)
            details: Detalles adicionales
        """
        message = f"SESSION_{action.upper()} | User: {user}"
        if details:
            message += f" | Details: {details}"
        
        self.logger.info(message)
    
    def log_data_access(
        self,
        user: str,
        resource: str,
        filters: Dict[str, Any],
        request
    ):
        """
        Log accesos a datos sensibles.
        
        Args:
            user: Email del usuario
            resource: Recurso accedido (dashboard, sales, etc.)
            filters: Filtros aplicados
            request: Flask request object
        """
        client_info = self._get_client_info(request)
        filters_str = str(filters)[:200]
        
        self.logger.info(
            f"DATA_ACCESS | User: {user} | Resource: {resource} | "
            f"Filters: {filters_str} | {client_info}"
        )
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        user: Optional[str],
        request,
        exc_info: bool = False
    ):
        """
        Log errores de aplicación con contexto de seguridad.
        
        Args:
            error_type: Tipo de error
            error_message: Mensaje de error
            user: Usuario (si está autenticado)
            request: Flask request object
            exc_info: Si incluir stack trace
        """
        client_info = self._get_client_info(request)
        user_str = user or 'Anonymous'
        
        message = (
            f"APP_ERROR | Type: {error_type} | "
            f"Message: {error_message[:200]} | "
            f"User: {user_str} | {client_info}"
        )
        
        self.logger.error(message, exc_info=exc_info)
    
    def log_configuration_change(
        self,
        user: str,
        change_type: str,
        details: str
    ):
        """
        Log cambios en configuración del sistema.
        
        Args:
            user: Usuario que realizó el cambio
            change_type: Tipo de cambio
            details: Detalles del cambio
        """
        self.logger.warning(
            f"CONFIG_CHANGE | User: {user} | Type: {change_type} | "
            f"Details: {details[:200]}"
        )
