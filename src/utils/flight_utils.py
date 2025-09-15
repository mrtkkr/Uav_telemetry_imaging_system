# src/utils/flight_utils.py
"""
İHA uçuş yönetimi için yardımcı sınıflar
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from ..telemetry.data_models import TelemetryPacket


class FlightDataLogger:
    """Uçuş veri kayıt ve analiz sınıfı"""

    def __init__(self, database_manager):
        self.db_manager = database_manager

    def save_telemetry(self, packet: TelemetryPacket) -> bool:
        """Telemetri verisini kaydet"""
        if self.db_manager:
            return self.db_manager.save_telemetry(packet)
        return False

    def load_flight_history(self, session_id: int = None) -> List[Dict]:
        """Uçuş geçmişini yükle"""
        if session_id:
            return self.db_manager.get_session_telemetry(session_id)
        else:
            return self.db_manager.get_latest_telemetry()

    def generate_flight_report(self, session_id: int) -> Dict:
        """Uçuş raporu oluştur"""
        if not self.db_manager:
            return {}

        # Oturum bilgilerini al
        sessions = self.db_manager.get_flight_sessions()
        session_info = next((s for s in sessions if s['id'] == session_id), None)

        if not session_info:
            return {"error": "Oturum bulunamadı"}

        # Telemetri verilerini al
        telemetry_data = self.db_manager.get_session_telemetry(session_id)

        if not telemetry_data:
            return {"error": "Telemetri verisi bulunamadı"}

        # İstatistikleri hesapla
        altitudes = [d['altitude'] for d in telemetry_data if d['altitude']]
        velocities = [d['velocity'] for d in telemetry_data if d['velocity']]
        batteries = [d['battery_percent'] for d in telemetry_data if d['battery_percent']]

        report = {
            'session_info': session_info,
            'statistics': {
                'total_records': len(telemetry_data),
                'max_altitude': max(altitudes) if altitudes else 0,
                'min_altitude': min(altitudes) if altitudes else 0,
                'avg_altitude': sum(altitudes) / len(altitudes) if altitudes else 0,
                'max_velocity': max(velocities) if velocities else 0,
                'avg_velocity': sum(velocities) / len(velocities) if velocities else 0,
                'battery_start': batteries[0] if batteries else 0,
                'battery_end': batteries[-1] if batteries else 0,
                'battery_consumed': batteries[0] - batteries[-1] if len(batteries) > 1 else 0
            },
            'flight_path': [(d['latitude'], d['longitude']) for d in telemetry_data]
        }

        return report


class AlertManager:
    """Alarm ve uyarı yönetimi sınıfı"""

    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.active_alerts = {}

        # Alarm eşikleri
        self.thresholds = {
            'battery_critical': 15.0,
            'battery_warning': 30.0,
            'altitude_max': 400.0,
            'altitude_min': 5.0,
            'velocity_max': 30.0,
            'gps_satellites_min': 6
        }

    def check_battery_levels(self, packet: TelemetryPacket) -> List[Dict]:
        """Batarya seviyelerini kontrol et"""
        alerts = []
        battery = packet.battery_percent

        if battery <= self.thresholds['battery_critical']:
            alert = {
                'type': 'BATTERY_CRITICAL',
                'severity': 'CRITICAL',
                'message': f'KRİTİK BATARYA! {battery:.1f}% - Acil iniş gerekli!',
                'value': battery
            }
            alerts.append(alert)
            self._log_alert(alert)

        elif battery <= self.thresholds['battery_warning']:
            alert = {
                'type': 'BATTERY_LOW',
                'severity': 'WARNING',
                'message': f'Düşük batarya: {battery:.1f}% - İnişe hazır olun',
                'value': battery
            }
            alerts.append(alert)
            self._log_alert(alert)

        return alerts

    def check_gps_quality(self, packet: TelemetryPacket) -> List[Dict]:
        """GPS kalitesini kontrol et"""
        alerts = []
        gps = packet.gps

        if gps.satellites < self.thresholds['gps_satellites_min']:
            alert = {
                'type': 'GPS_POOR',
                'severity': 'WARNING',
                'message': f'Zayıf GPS sinyali: {gps.satellites} uydu (Min: {self.thresholds["gps_satellites_min"]})',
                'value': gps.satellites
            }
            alerts.append(alert)
            self._log_alert(alert)

        if gps.fix_quality < 3:
            alert = {
                'type': 'GPS_FIX_LOST',
                'severity': 'CRITICAL',
                'message': f'GPS kilidi kayboldu! Fix kalitesi: {gps.fix_quality}',
                'value': gps.fix_quality
            }
            alerts.append(alert)
            self._log_alert(alert)

        return alerts

    def check_flight_envelope(self, packet: TelemetryPacket) -> List[Dict]:
        """Uçuş zarfını kontrol et (rakım, hız vb.)"""
        alerts = []

        # Rakım kontrolleri
        if packet.gps.altitude > self.thresholds['altitude_max']:
            alert = {
                'type': 'ALTITUDE_HIGH',
                'severity': 'WARNING',
                'message': f'Yüksek rakım: {packet.gps.altitude:.1f}m (Max: {self.thresholds["altitude_max"]}m)',
                'value': packet.gps.altitude
            }
            alerts.append(alert)
            self._log_alert(alert)

        elif packet.gps.altitude < self.thresholds['altitude_min']:
            alert = {
                'type': 'ALTITUDE_LOW',
                'severity': 'WARNING',
                'message': f'Düşük rakım: {packet.gps.altitude:.1f}m - Çarpma riski!',
                'value': packet.gps.altitude
            }
            alerts.append(alert)
            self._log_alert(alert)

        # Hız kontrolü
        if packet.velocity > self.thresholds['velocity_max']:
            alert = {
                'type': 'VELOCITY_HIGH',
                'severity': 'WARNING',
                'message': f'Yüksek hız: {packet.velocity:.1f} m/s (Max: {self.thresholds["velocity_max"]} m/s)',
                'value': packet.velocity
            }
            alerts.append(alert)
            self._log_alert(alert)

        return alerts

    def trigger_emergency_alerts(self, alert_type: str, message: str):
        """Acil durum alarmı tetikle"""
        alert = {
            'type': alert_type,
            'severity': 'EMERGENCY',
            'message': f'ACİL DURUM: {message}',
            'timestamp': datetime.now()
        }

        self._log_alert(alert)
        print(f"🚨 {alert['message']}")

        return alert

    def _log_alert(self, alert: Dict):
        """Alarmı veritabanına kaydet"""
        if not self.db_manager or not self.db_manager.current_session_id:
            return

        try:
            from ..database.models import AlertLog

            with self.db_manager.get_session() as session:
                alert_log = AlertLog(
                    session_id=self.db_manager.current_session_id,
                    alert_type=alert['type'],
                    severity=alert['severity'],
                    message=alert['message']
                )
                session.add(alert_log)

        except Exception as e:
            print(f"Alarm kayıt hatası: {e}")


class WaypointManager:
    """Waypoint (görev noktası) yönetimi sınıfı"""

    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.current_mission = None
        self.waypoints = []

    def add_waypoint(self, lat: float, lon: float, alt: float,
                     action_type: str = 'FLY_TO', hold_time: float = 0) -> bool:
        """Yeni waypoint ekle"""
        if not self.current_mission:
            self.current_mission = f"Mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        waypoint = {
            'mission_name': self.current_mission,
            'order_index': len(self.waypoints),
            'latitude': lat,
            'longitude': lon,
            'altitude': alt,
            'action_type': action_type,
            'hold_time': hold_time
        }

        self.waypoints.append(waypoint)

        # Veritabanına kaydet
        if self.db_manager:
            try:
                from ..database.models import Waypoint

                with self.db_manager.get_session() as session:
                    wp = Waypoint(**waypoint)
                    session.add(wp)
                    print(f"✅ Waypoint eklendi: {lat:.5f}, {lon:.5f}")
                    return True

            except Exception as e:
                print(f"Waypoint kayıt hatası: {e}")
                return False

        return True

    def calculate_route(self) -> Dict:
        """Rota hesapla"""
        if len(self.waypoints) < 2:
            return {"error": "En az 2 waypoint gerekli"}

        total_distance = 0.0
        route_segments = []

        for i in range(1, len(self.waypoints)):
            prev_wp = self.waypoints[i - 1]
            curr_wp = self.waypoints[i]

            # Mesafe hesapla (Haversine formülü kullanabilir)
            distance = self._calculate_distance(
                prev_wp['latitude'], prev_wp['longitude'],
                curr_wp['latitude'], curr_wp['longitude']
            )

            total_distance += distance

            segment = {
                'from': f"WP{i - 1}",
                'to': f"WP{i}",
                'distance': distance,
                'bearing': self._calculate_bearing(
                    prev_wp['latitude'], prev_wp['longitude'],
                    curr_wp['latitude'], curr_wp['longitude']
                )
            }
            route_segments.append(segment)

        return {
            'total_distance': total_distance,
            'total_waypoints': len(self.waypoints),
            'segments': route_segments,
            'mission_name': self.current_mission
        }

    def estimate_flight_time(self, average_speed: float = 15.0) -> float:
        """Tahmini uçuş süresi hesapla (dakika)"""
        route = self.calculate_route()

        if 'error' in route:
            return 0.0

        # Temel uçuş süresi
        flight_time = (route['total_distance'] / average_speed) / 60  # dakika

        # Waypoint'lerde bekleme süreleri
        hold_time = sum(wp['hold_time'] for wp in self.waypoints) / 60

        # İniş-kalkış için ekstra süre
        extra_time = 2.0  # dakika

        total_time = flight_time + hold_time + extra_time

        return total_time

    def clear_mission(self):
        """Mevcut görev planını temizle"""
        self.waypoints.clear()
        self.current_mission = None
        print("✅ Görev planı temizlendi")

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """İki nokta arası mesafe hesapla (Haversine formülü - metre)"""
        import math

        R = 6371000  # Dünya yarıçapı (metre)

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """İki nokta arası yön açısı hesapla (derece)"""
        import math

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        delta_lon = lon2 - lon1

        y = math.sin(delta_lon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) -
             math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon))

        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360  # 0-360 derece arası

        return bearing