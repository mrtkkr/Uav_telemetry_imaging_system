# src/database/database_manager.py
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from .models import Base, FlightSession, TelemetryRecord
from ..telemetry.data_models import TelemetryPacket


class DatabaseManager:
    """Veritabanı yönetim sınıfı"""

    def __init__(self, db_path: str = "flight_data.db"):
        self.db_path = Path(db_path)
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.current_session_id = None

        # Veritabanını başlat
        self._initialize_database()

    def _initialize_database(self):
        """Veritabanı tablolarını oluştur"""
        Base.metadata.create_all(self.engine)
        print(f"Veritabanı başlatıldı: {self.db_path.absolute()}")

    @contextmanager
    def get_session(self):
        """Database session context manager"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            session.close()

    def start_flight_session(self, session_name: str = None) -> int:
        """Yeni uçuş oturumu başlat"""
        if not session_name:
            session_name = f"Flight_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with self.get_session() as session:
            flight_session = FlightSession(
                session_name=session_name,
                start_time=datetime.now(),
                status='ACTIVE'
            )
            session.add(flight_session)
            session.flush()  # ID'yi al
            session_id = flight_session.id

        self.current_session_id = session_id
        print(f"Yeni uçuş oturumu başlatıldı: {session_name} (ID: {session_id})")
        return session_id

    def close_connection(self):
        """Veritabanı bağlantısını kapat"""
        # SQLAlchemy engine'i kapatır
        if hasattr(self, 'engine'):
            self.engine.dispose()
        print("Veritabanı bağlantısı kapatıldı")

    def end_flight_session(self, session_id: int = None):
        """Uçuş oturumunu sonlandır"""
        if not session_id:
            session_id = self.current_session_id

        if not session_id:
            print("Sonlandırılacak aktif oturum bulunamadı")
            return

        with self.get_session() as session:
            flight_session = session.query(FlightSession).filter_by(id=session_id).first()
            if flight_session:
                flight_session.end_time = datetime.now()
                flight_session.status = 'COMPLETED'

                # İstatistikleri hesapla
                stats = self._calculate_session_stats(session_id)
                flight_session.total_duration = stats['duration']
                flight_session.max_altitude = stats['max_altitude']
                flight_session.max_velocity = stats['max_velocity']
                flight_session.min_battery = stats['min_battery']
                flight_session.total_distance = stats['total_distance']

                print(f"Uçuş oturumu sonlandırıldı: {flight_session.session_name}")

        self.current_session_id = None

    def save_telemetry(self, packet: TelemetryPacket) -> bool:
        """Telemetri verisini kaydet"""
        if not self.current_session_id:
            self.start_flight_session()  # Otomatik oturum başlat

        try:
            with self.get_session() as session:
                record = TelemetryRecord(
                    session_id=self.current_session_id,
                    timestamp=packet.timestamp,
                    latitude=packet.gps.latitude,
                    longitude=packet.gps.longitude,
                    altitude=packet.gps.altitude,
                    velocity=packet.velocity,
                    roll=packet.attitude.roll if packet.attitude else None,
                    pitch=packet.attitude.pitch if packet.attitude else None,
                    yaw=packet.attitude.yaw if packet.attitude else None,
                    battery_voltage=packet.battery_voltage,
                    battery_percent=packet.battery_percent,
                    status=packet.status,
                    raw_data=packet.json()
                )
                session.add(record)
            return True
        except Exception as e:
            print(f"Telemetri kayıt hatası: {e}")
            return False

    def get_flight_sessions(self) -> List[Dict]:
        """Tüm uçuş oturumlarını getir"""
        with self.get_session() as session:
            sessions = session.query(FlightSession).order_by(FlightSession.start_time.desc()).all()
            return [self._session_to_dict(s) for s in sessions]

    def get_session_telemetry(self, session_id: int, limit: int = None) -> List[Dict]:
        """Belirli oturumun telemetri verilerini getir"""
        with self.get_session() as session:
            query = session.query(TelemetryRecord).filter_by(session_id=session_id)
            query = query.order_by(TelemetryRecord.timestamp)

            if limit:
                query = query.limit(limit)

            records = query.all()
            return [self._record_to_dict(r) for r in records]

    def get_latest_telemetry(self, count: int = 100) -> List[Dict]:
        """En son telemetri kayıtlarını getir"""
        with self.get_session() as session:
            records = (session.query(TelemetryRecord)
                       .order_by(TelemetryRecord.timestamp.desc())
                       .limit(count)
                       .all())
            return [self._record_to_dict(r) for r in records[::-1]]  # Ters çevir

    def _calculate_session_stats(self, session_id: int) -> Dict:
        """Oturum istatistiklerini hesapla"""
        with self.get_session() as session:
            records = session.query(TelemetryRecord).filter_by(session_id=session_id).all()

            if not records:
                return {'duration': 0, 'max_altitude': 0, 'max_velocity': 0,
                        'min_battery': 100, 'total_distance': 0}

            # Süre hesapla
            start_time = min(r.timestamp for r in records)
            end_time = max(r.timestamp for r in records)
            duration = (end_time - start_time).total_seconds()

            # Diğer istatistikler
            altitudes = [r.altitude for r in records if r.altitude is not None]
            velocities = [r.velocity for r in records if r.velocity is not None]
            batteries = [r.battery_percent for r in records if r.battery_percent is not None]

            # Mesafe hesapla (basit Euclidean)
            total_distance = 0
            for i in range(1, len(records)):
                prev = records[i - 1]
                curr = records[i]
                if prev.latitude and curr.latitude:
                    # Basit mesafe hesaplaması (gerçek projede Haversine kullanın)
                    lat_diff = curr.latitude - prev.latitude
                    lon_diff = curr.longitude - prev.longitude
                    distance = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111000  # Yaklaşık metre
                    total_distance += distance

            return {
                'duration': duration,
                'max_altitude': max(altitudes) if altitudes else 0,
                'max_velocity': max(velocities) if velocities else 0,
                'min_battery': min(batteries) if batteries else 100,
                'total_distance': total_distance
            }

    def _session_to_dict(self, session: FlightSession) -> Dict:
        """FlightSession nesnesini dict'e çevir"""
        return {
            'id': session.id,
            'session_name': session.session_name,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'total_duration': session.total_duration,
            'max_altitude': session.max_altitude,
            'max_velocity': session.max_velocity,
            'min_battery': session.min_battery,
            'total_distance': session.total_distance,
            'status': session.status,
            'notes': session.notes
        }

    def _record_to_dict(self, record: TelemetryRecord) -> Dict:
        """TelemetryRecord nesnesini dict'e çevir"""
        return {
            'id': record.id,
            'session_id': record.session_id,
            'timestamp': record.timestamp,
            'latitude': record.latitude,
            'longitude': record.longitude,
            'altitude': record.altitude,
            'velocity': record.velocity,
            'roll': record.roll,
            'pitch': record.pitch,
            'yaw': record.yaw,
            'battery_voltage': record.battery_voltage,
            'battery_percent': record.battery_percent,
            'status': record.status
        }

    def export_session_csv(self, session_id: int, output_path: str):
        """Oturum verilerini CSV olarak dışa aktar"""
        import pandas as pd

        records = self.get_session_telemetry(session_id)
        if not records:
            print("Dışa aktarılacak veri bulunamadı")
            return

        df = pd.DataFrame(records)
        df.to_csv(output_path, index=False)
        print(f"Veriler dışa aktarıldı: {output_path}")

    def get_database_info(self) -> Dict:
        """Veritabanı bilgilerini getir"""
        with self.get_session() as session:
            total_sessions = session.query(FlightSession).count()
            total_records = session.query(TelemetryRecord).count()
            active_sessions = session.query(FlightSession).filter_by(status='ACTIVE').count()

            return {
                'database_path': str(self.db_path.absolute()),
                'database_size': self.db_path.stat().st_size if self.db_path.exists() else 0,
                'total_sessions': total_sessions,
                'total_records': total_records,
                'active_sessions': active_sessions
            }