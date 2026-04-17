# services/__init__.py
"""
Capa de servicios para lógica de negocio.
Implementa Single Responsibility Principle (SRP).
"""

from .validation_service import ValidationService
from .aggregation_service import (
    SalesAggregationService,
    MetricsCalculationService,
    ChartDataService,
    DashboardMetrics
)
from .security_logger import SecurityLogger

__all__ = [
    'ValidationService',
    'SalesAggregationService',
    'MetricsCalculationService',
    'ChartDataService',
    'DashboardMetrics',
    'SecurityLogger'
]
