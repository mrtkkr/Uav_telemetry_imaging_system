# src/database/models.py
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()


class FlightSession(Base):
    """Uçuş oturumu tablosu"""
    __tablename__ = 'flight_sessions'

    id = Column(Integer, primary_key=True)
    session_name = Column(String(200), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.now)
    end_time = Column(DateTime)
    total_duration = Column(Float)  # saniye
    max_altitude = Column(Float)
    max_velocity = Column(Float)
    min_battery = Column(Float)
    total_distance = Column(Float)  # metre
    status = Column(String(50), default='ACTIVE')
    notes = Column(Text)

    def __repr__(self):
        return f"<FlightSession(id={self.id}, name='{self.session_name}', status='{self.status}')>"


class TelemetryRecord(Base):
    """Telemetri kayıt tablosu"""
    __tablename__ = 'telemetry_records'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, nullable=False)  # FlightSession'a referans
    timestamp = Column(DateTime, nullable=False, default=datetime.now)

    # GPS verileri
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)

    # Hareket verileri
    velocity = Column(Float)
    roll = Column(Float)
    pitch = Column(Float)
    yaw = Column(Float)

    # Güç sistemi
    battery_voltage = Column(Float)
    battery_percent = Column(Float)

    # Durum
    status = Column(String(50))
    raw_data = Column(Text)  # JSON formatında orijinal veri

    def __repr__(self):
        return f"<TelemetryRecord(id={self.id}, session={self.session_id}, time={self.timestamp})>"


class AlertLog(Base):
    """Alarm/Uyarı kayıt tablosu"""
    __tablename__ = 'alert_logs'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    alert_type = Column(String(100), nullable=False)  # BATTERY_LOW, GPS_LOST, etc.
    severity = Column(String(20), nullable=False)  # INFO, WARNING, CRITICAL
    message = Column(String(500), nullable=False)
    resolved = Column(String(10), default='NO')  # YES/NO
    resolved_time = Column(DateTime)

    def __repr__(self):
        return f"<AlertLog(type='{self.alert_type}', severity='{self.severity}')>"


class Waypoint(Base):
    """Waypoint/Görev noktaları tablosu"""
    __tablename__ = 'waypoints'

    id = Column(Integer, primary_key=True)
    mission_name = Column(String(200), nullable=False)
    order_index = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    action_type = Column(String(50), default='FLY_TO')  # FLY_TO, LAND, TAKEOFF, HOVER
    hold_time = Column(Float, default=0)  # saniye
    radius = Column(Float, default=5)  # metre
    notes = Column(Text)
    created_time = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Waypoint(mission='{self.mission_name}', order={self.order_index})>"