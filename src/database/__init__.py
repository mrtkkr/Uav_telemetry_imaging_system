# src/database/__init__.py
"""
İHA Telemetri Veri Tabanı Modülü

Bu modül veri tabanı işlemlerini yönetir:
- Telemetri verilerinin kaydedilmesi
- Uçuş oturumlarının takibi
- Alarm ve uyarı kayıtları
- Waypoint (görev noktaları) yönetimi
"""

from .database_manager import DatabaseManager
from .models import Base, FlightSession, TelemetryRecord, AlertLog, Waypoint

__all__ = [
    'DatabaseManager',
    'Base',
    'FlightSession',
    'TelemetryRecord',
    'AlertLog',
    'Waypoint'
]

# Versioning
__version__ = "1.0.0"