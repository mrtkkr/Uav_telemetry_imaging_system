# src/telemetry/data_generator.py - VERİTABANI ENTEGRASYONLİ
import random
import time
from datetime import datetime, timedelta
from PySide6.QtCore import QThread, Signal, QTimer

# Eski (yanlış)
# from data_models import TelemetryPacket, GPSData, AttitudeData

# Yeni (doğru)
from .data_models import TelemetryPacket, GPSData, AttitudeData



class TelemetryWorker(QThread):
    """Telemetri veri üretici - Veritabanı entegrasyonlu"""

    new_data = Signal(TelemetryPacket)

    def __init__(self, database_manager=None, use_mavlink=False, parent=None):
        super().__init__(parent)
        self.database_manager = database_manager
        self.use_mavlink = use_mavlink  # YENİ
        self.running = True

        # MAVLink manager (eğer kullanılacaksa)
        self.mavlink_manager = None
        if self.use_mavlink:
            try:
                from ..mavlink.mavlink_manager import MAVLinkManager
                self.mavlink_manager = MAVLinkManager()
                print("MAVLink modu aktif")
            except ImportError as e:
                print(f"MAVLink import hatası: {e}")
                self.mavlink_manager = None
                self.use_mavlink = False

        # Simülasyon parametreleri (MAVLink kullanılmıyorsa)
        self.current_lat = 39.9334

        # Simülasyon parametreleri
        self.current_lat = 39.9334  # Ankara
        self.current_lon = 32.8597
        self.current_alt = 100.0
        self.battery_level = 100.0
        self.flight_time = 0

        # Hareket yönü
        self.direction_lat = random.uniform(-0.001, 0.001)
        self.direction_lon = random.uniform(-0.001, 0.001)
        self.direction_alt = random.uniform(-2, 2)

        print("🚁 TelemetryWorker başlatıldı (Database entegrasyonlu)")
        if self.database_manager:
            print("✅ Veritabanı bağlantısı aktif")
        else:
            print("⚠️ Veritabanı bağlantısı YOK - sadece görselleştirme modu")

    def run(self):
        """Ana thread döngüsü - MAVLink desteği ile"""

        if self.use_mavlink and self.mavlink_manager:
            # MAVLink callback'lerini ayarla
            self.mavlink_manager.on_gps_data = self._on_mavlink_gps
            self.mavlink_manager.on_attitude_data = self._on_mavlink_attitude
            self.mavlink_manager.on_battery_data = self._on_mavlink_battery

            # MAVLink bağlantısını başlat
            self.mavlink_manager.create_simulated_connection()
            self.mavlink_manager.start_listening()

            print("MAVLink dinleme modu başlatıldı")

            # MAVLink modunda sadece bekle
            while self.running:
                time.sleep(1)

        else:
            # Klasik simülasyon modu
            while self.running:
                try:
                    packet = self._generate_packet()

                    if self.database_manager:
                        success = self.database_manager.save_telemetry(packet)
                        if not success:
                            print("Veritabanı kayıt hatası!")

                    self.new_data.emit(packet)
                    self._update_simulation()
                    time.sleep(1)

                except Exception as e:
                    print(f"TelemetryWorker hatası: {e}")
                    time.sleep(1)

    def _on_mavlink_gps(self, gps_data):
        """MAVLink GPS verisi callback"""
        from .data_models import GPSData, AttitudeData

        # GPS verisi
        gps = GPSData(
            latitude=gps_data['latitude'],
            longitude=gps_data['longitude'],
            altitude=gps_data['altitude'],
            fix_quality=gps_data['fix_type'],
            satellites=gps_data['satellites_visible']
        )

        # Son attitude verisini al
        attitude = None
        if self.mavlink_manager.last_attitude:
            att_data = self.mavlink_manager.last_attitude
            attitude = AttitudeData(
                roll=att_data['roll'],
                pitch=att_data['pitch'],
                yaw=att_data['yaw']
            )

        # Telemetri paketi oluştur
        packet = self._create_mavlink_packet(gps, attitude)

        # Veritabanına kaydet
        if self.database_manager:
            self.database_manager.save_telemetry(packet)

        # GUI'ye gönder
        self.new_data.emit(packet)

    def _on_mavlink_attitude(self, attitude_data):
        """MAVLink attitude verisi callback"""
        # Attitude verisi geldiğinde GPS güncellemesi bekle
        pass

    def _on_mavlink_battery(self, battery_data):
        """MAVLink battery verisi callback"""
        # Battery verisi geldiğinde diğer verilerle birleştir
        pass

    def _create_mavlink_packet(self, gps, attitude=None):
        """MAVLink verilerinden telemetri paketi oluştur"""


        # Battery verisi
        battery_voltage = 24.0
        battery_percent = 100.0

        if self.mavlink_manager.last_battery:
            battery_voltage = self.mavlink_manager.last_battery['voltage']
            battery_percent = self.mavlink_manager.last_battery['remaining']

        # Hız hesapla (basit)
        velocity = 15.0  # Sabit değer, gerçekte GPS'den hesaplanabilir

        # Durum belirle
        status = "FLYING"
        if battery_percent < 20:
            status = "LOW_BATTERY"

        packet = TelemetryPacket(
            timestamp=datetime.now(),
            gps=gps,
            attitude=attitude,
            velocity=velocity,
            battery_voltage=battery_voltage,
            battery_percent=battery_percent,
            status=status
        )

        return packet

    def _generate_packet(self) -> TelemetryPacket:
        """Simüle telemetri paketi oluştur"""

        # GPS verisi
        gps = GPSData(
            latitude=self.current_lat,
            longitude=self.current_lon,
            altitude=self.current_alt,
            fix_quality=4 if random.random() > 0.05 else 3,  # %95 iyi sinyal
            satellites=random.randint(8, 15)
        )

        # Attitude verisi (uçuş açıları)
        attitude = AttitudeData(
            roll=random.uniform(-15, 15),
            pitch=random.uniform(-10, 10),
            yaw=random.uniform(0, 360)
        )

        # Durum belirle
        status = "FLYING"
        if self.battery_level < 20:
            status = "LOW_BATTERY"
        elif gps.fix_quality < 3:
            status = "GPS_POOR"
        elif self.current_alt < 10:
            status = "LANDING"

        # Telemetri paketi oluştur
        packet = TelemetryPacket(
            timestamp=datetime.now(),
            gps=gps,
            attitude=attitude,
            velocity=random.uniform(5, 25),  # m/s
            battery_voltage=random.uniform(22.0, 25.2),
            battery_percent=self.battery_level,
            status=status
        )

        return packet

    def _update_simulation(self):
        """Simülasyon parametrelerini güncelle"""

        # Pozisyonu güncelle
        self.current_lat += self.direction_lat * random.uniform(0.5, 1.5)
        self.current_lon += self.direction_lon * random.uniform(0.5, 1.5)
        self.current_alt += self.direction_alt * random.uniform(0.5, 1.5)

        # Sınırları kontrol et
        self.current_alt = max(10, min(500, self.current_alt))

        # Bazen yön değiştir
        if random.random() < 0.1:  # %10 şans
            self.direction_lat = random.uniform(-0.001, 0.001)
            self.direction_lon = random.uniform(-0.001, 0.001)
            self.direction_alt = random.uniform(-2, 2)

        # Batarya seviyesini azalt
        self.flight_time += 1
        battery_drain = random.uniform(0.30, 0.45)  # Dakikada %0.05-0.15
        self.battery_level = max(0, self.battery_level - battery_drain)

        # Kritik batarya durumunda inmesi için rakımı azalt
        if self.battery_level < 10:
            self.direction_alt = -abs(self.direction_alt)  # Aşağı yönlü hareket

    def stop(self):
        """Thread'i durdur"""
        print("🛑 TelemetryWorker durduruluyor...")
        self.running = False

        # MAVLink manager'ı da durdur
        if self.mavlink_manager:
            self.mavlink_manager.stop_listening()
            self.mavlink_manager.close_connection()

    def stop_session(self):
        """Mevcut oturumu sonlandır"""
        if self.database_manager and self.database_manager.current_session_id:
            self.database_manager.end_flight_session()
            print("✅ Uçuş oturumu sonlandırıldı")

    def restart_simulation(self):
        """Simülasyonu yeniden başlat"""
        print("🔄 Simülasyon sıfırlanıyor...")
        self.current_lat = 39.9334 + random.uniform(-0.01, 0.01)
        self.current_lon = 32.8597 + random.uniform(-0.01, 0.01)
        self.current_alt = random.uniform(50, 200)
        self.battery_level = 100.0
        self.flight_time = 0
        print("✅ Simülasyon sıfırlandı")

    def __del__(self):
        """Destructor"""
        self.running = False
        if self.database_manager:
            # Son oturumu sonlandır
            if hasattr(self.database_manager, 'current_session_id') and self.database_manager.current_session_id:
                self.database_manager.end_flight_session()