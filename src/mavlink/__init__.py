# src/mavlink/__init__.py
"""
MAVLink Protokol Desteği Modülü

Bu modül MAVLink protokolü ile telemetri verisi alışverişini sağlar:
- MAVLink mesaj parsing
- Telemetri verilerini MAVLink formatına çevirme
- Bağlantı yönetimi
"""

from .mavlink_manager import MAVLinkManager

__all__ = ['MAVLinkManager']
__version__ = "1.0.0"