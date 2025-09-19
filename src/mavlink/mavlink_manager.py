# src/mavlink/mavlink_manager.py
from pymavlink import mavutil
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Callable


class MAVLinkManager:
    """MAVLink protokol yönetimi sınıfı"""

    def __init__(self):
        self.connection = None
        self.is_connected = False
        self.is_running = False
        self.thread = None

        # Callback fonksiyonları
        self.on_heartbeat = None
        self.on_gps_data = None
        self.on_attitude_data = None
        self.on_battery_data = None

        # Son alınan veriler
        self.last_heartbeat = None
        self.last_gps = None
        self.last_attitude = None
        self.last_battery = None

        print("MAVLink Manager başlatıldı")

    def create_simulated_connection(self):
        """Simüle MAVLink bağlantısı oluştur"""
        try:
            # UDP bağlantısı simülasyonu
            # Gerçek projede 'udp:localhost:14550' kullanılabilir
            self.connection = mavutil.mavlink_connection('tcp:localhost:5760',
                                                         source_system=255)
            self.is_connected = True
            print("Simüle MAVLink bağlantısı oluşturuldu")
            return True

        except Exception as e:
            print(f"MAVLink bağlantı hatası: {e}")
            # Bağlantı kurulamazsa simüle modu aktif et
            self.connection = None
            self.is_connected = False
            return False

    def start_listening(self):
        """MAVLink mesaj dinleme thread'ini başlat"""
        if self.is_running:
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("MAVLink dinleme başlatıldı")

    def stop_listening(self):
        """MAVLink dinlemeyi durdur"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        print("MAVLink dinleme durduruldu")

    def _listen_loop(self):
        """MAVLink mesajlarını dinle (ana loop)"""
        while self.is_running:
            try:
                if self.connection:
                    # Gerçek MAVLink mesajı bekle
                    msg = self.connection.recv_match(timeout=1)
                    if msg:
                        self._process_message(msg)
                else:
                    # Simüle mod - kendi mesajlarımızı oluştur
                    self._generate_simulated_messages()
                    time.sleep(1)

            except Exception as e:
                print(f"MAVLink dinleme hatası: {e}")
                time.sleep(1)

    def _process_message(self, msg):
        """Gelen MAVLink mesajını işle"""
        msg_type = msg.get_type()

        if msg_type == 'HEARTBEAT':
            self._handle_heartbeat(msg)
        elif msg_type == 'GPS_RAW_INT':
            self._handle_gps_raw(msg)
        elif msg_type == 'ATTITUDE':
            self._handle_attitude(msg)
        elif msg_type == 'BATTERY_STATUS':
            self._handle_battery_status(msg)
        elif msg_type == 'SYS_STATUS':
            self._handle_sys_status(msg)

    def _handle_heartbeat(self, msg):
        """HEARTBEAT mesajını işle"""
        heartbeat_data = {
            'type': msg.type,
            'autopilot': msg.autopilot,
            'base_mode': msg.base_mode,
            'system_status': msg.system_status,
            'mavlink_version': msg.mavlink_version
        }

        self.last_heartbeat = heartbeat_data

        if self.on_heartbeat:
            self.on_heartbeat(heartbeat_data)

    def _handle_gps_raw(self, msg):
        """GPS_RAW_INT mesajını işle"""
        gps_data = {
            'timestamp': datetime.now(),
            'latitude': msg.lat / 1e7,  # MAVLink int32 formatından derece'ye çevir
            'longitude': msg.lon / 1e7,
            'altitude': msg.alt / 1000.0,  # mm'den metre'ye
            'fix_type': msg.fix_type,
            'satellites_visible': msg.satellites_visible,
            'hdop': msg.eph / 100.0 if msg.eph != 65535 else 0
        }

        self.last_gps = gps_data

        if self.on_gps_data:
            self.on_gps_data(gps_data)

    def _handle_attitude(self, msg):
        """ATTITUDE mesajını işle"""
        attitude_data = {
            'timestamp': datetime.now(),
            'roll': msg.roll * 180.0 / 3.14159,  # radyan'dan derece'ye
            'pitch': msg.pitch * 180.0 / 3.14159,
            'yaw': msg.yaw * 180.0 / 3.14159,
            'rollspeed': msg.rollspeed,
            'pitchspeed': msg.pitchspeed,
            'yawspeed': msg.yawspeed
        }

        self.last_attitude = attitude_data

        if self.on_attitude_data:
            self.on_attitude_data(attitude_data)

    def _handle_battery_status(self, msg):
        """BATTERY_STATUS mesajını işle"""
        battery_data = {
            'timestamp': datetime.now(),
            'voltage': msg.voltages[0] / 1000.0,  # mV'den V'ye
            'current': msg.current_battery / 100.0 if msg.current_battery != -1 else 0,
            'remaining': msg.battery_remaining,
            'consumed': msg.current_consumed
        }

        self.last_battery = battery_data

        if self.on_battery_data:
            self.on_battery_data(battery_data)

    def _handle_sys_status(self, msg):
        """SYS_STATUS mesajını işle (batarya bilgisi için alternatif)"""
        if not self.last_battery:  # BATTERY_STATUS gelmemişse SYS_STATUS kullan
            battery_data = {
                'timestamp': datetime.now(),
                'voltage': msg.voltage_battery / 1000.0,
                'current': msg.current_battery / 100.0 if msg.current_battery != -1 else 0,
                'remaining': msg.battery_remaining,
                'consumed': 0
            }

            self.last_battery = battery_data

            if self.on_battery_data:
                self.on_battery_data(battery_data)

    def _generate_simulated_messages(self):
        """Simüle MAVLink mesajları oluştur (gerçek bağlantı yokken)"""
        import random

        # Simüle HEARTBEAT
        if self.on_heartbeat:
            heartbeat_data = {
                'type': 2,  # MAV_TYPE_QUADROTOR
                'autopilot': 3,  # MAV_AUTOPILOT_ARDUPILOTMEGA
                'base_mode': 81,  # Armed + Custom mode
                'system_status': 4,  # MAV_STATE_ACTIVE
                'mavlink_version': 3
            }
            self.last_heartbeat = heartbeat_data
            self.on_heartbeat(heartbeat_data)

        # Simüle GPS
        if self.on_gps_data:
            gps_data = {
                'timestamp': datetime.now(),
                'latitude': 39.9334 + random.uniform(-0.001, 0.001),
                'longitude': 32.8597 + random.uniform(-0.001, 0.001),
                'altitude': random.uniform(50, 200),
                'fix_type': 3,  # 3D fix
                'satellites_visible': random.randint(8, 15),
                'hdop': random.uniform(0.5, 2.0)
            }
            self.last_gps = gps_data
            self.on_gps_data(gps_data)

        # Simüle ATTITUDE
        if self.on_attitude_data:
            attitude_data = {
                'timestamp': datetime.now(),
                'roll': random.uniform(-15, 15),
                'pitch': random.uniform(-10, 10),
                'yaw': random.uniform(0, 360),
                'rollspeed': random.uniform(-0.5, 0.5),
                'pitchspeed': random.uniform(-0.5, 0.5),
                'yawspeed': random.uniform(-1, 1)
            }
            self.last_attitude = attitude_data
            self.on_attitude_data(attitude_data)

        # Simüle BATTERY
        if self.on_battery_data:
            battery_data = {
                'timestamp': datetime.now(),
                'voltage': random.uniform(22.0, 25.2),
                'current': random.uniform(5, 20),
                'remaining': random.randint(20, 100),
                'consumed': random.randint(500, 3000)
            }
            self.last_battery = battery_data
            self.on_battery_data(battery_data)

    def send_heartbeat(self):
        """HEARTBEAT mesajı gönder"""
        if self.connection:
            try:
                self.connection.mav.heartbeat_send(
                    mavutil.mavlink.MAV_TYPE_GCS,
                    mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                    0, 0, 0
                )
                return True
            except Exception as e:
                print(f"Heartbeat gönderme hatası: {e}")
                return False
        return False

    def get_connection_status(self) -> Dict[str, Any]:
        """Bağlantı durumu bilgisi"""
        return {
            'connected': self.is_connected,
            'running': self.is_running,
            'last_heartbeat': self.last_heartbeat,
            'connection_type': 'Simulated' if not self.connection else 'Real'
        }

    def close_connection(self):
        """Bağlantıyı kapat"""
        self.stop_listening()
        if self.connection:
            self.connection.close()
        self.is_connected = False
        print("MAVLink bağlantısı kapatıldı")