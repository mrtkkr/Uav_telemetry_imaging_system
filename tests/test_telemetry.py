# tests/test_telemetry.py
import unittest
from datetime import datetime
import sys
import os

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.telemetry.data_models import TelemetryPacket, GPSData, AttitudeData
from src.database.database_manager import DatabaseManager
from src.mavlink.mavlink_manager import MAVLinkManager


class TestTelemetryDataModels(unittest.TestCase):
    """Telemetri veri modellerinin testleri"""

    def test_gps_data_creation(self):
        """GPS data modeli oluşturma testi"""
        gps = GPSData(
            latitude=39.9334,
            longitude=32.8597,
            altitude=100.0,
            fix_quality=4,
            satellites=12
        )

        self.assertEqual(gps.latitude, 39.9334)
        self.assertEqual(gps.longitude, 32.8597)
        self.assertEqual(gps.altitude, 100.0)
        self.assertEqual(gps.satellites, 12)

    def test_attitude_data_creation(self):
        """Attitude data modeli oluşturma testi"""
        attitude = AttitudeData(
            roll=10.5,
            pitch=-5.2,
            yaw=45.0
        )

        self.assertEqual(attitude.roll, 10.5)
        self.assertEqual(attitude.pitch, -5.2)
        self.assertEqual(attitude.yaw, 45.0)

    def test_telemetry_packet_creation(self):
        """Telemetri paketi oluşturma testi"""
        gps = GPSData(latitude=39.9, longitude=32.8, altitude=150.0)
        attitude = AttitudeData(roll=0.0, pitch=0.0, yaw=90.0)

        packet = TelemetryPacket(
            timestamp=datetime.now(),
            gps=gps,
            attitude=attitude,
            velocity=25.5,
            battery_voltage=24.2,
            battery_percent=85.0,
            status="FLYING"
        )

        self.assertIsInstance(packet.timestamp, datetime)
        self.assertEqual(packet.gps.latitude, 39.9)
        self.assertEqual(packet.velocity, 25.5)
        self.assertEqual(packet.status, "FLYING")


class TestDatabaseManager(unittest.TestCase):
    """Veritabanı yöneticisi testleri"""

    def setUp(self):
        """Test öncesi hazırlık"""
        self.db_manager = DatabaseManager("test_db.db")

    def tearDown(self):
        """Test sonrası temizlik"""
        # Önce bağlantıyı kapat
        if hasattr(self, 'db_manager'):
            self.db_manager.close_connection()

        # Biraz bekle
        import time
        time.sleep(0.1)

        # Dosyayı sil
        if os.path.exists("test_db.db"):
            try:
                os.remove("test_db.db")
            except PermissionError:
                # Windows'ta bazen hala kilitli olabilir, tekrar dene
                time.sleep(0.5)
                try:
                    os.remove("test_db.db")
                except:
                    pass  # Test sonrası temizlik başarısız olsa da devam et

    def test_database_initialization(self):
        """Veritabanı başlatma testi"""
        self.assertIsNotNone(self.db_manager.engine)
        self.assertIsNotNone(self.db_manager.SessionLocal)

    def test_flight_session_creation(self):
        """Uçuş oturumu oluşturma testi"""
        session_id = self.db_manager.start_flight_session("Test Session")
        self.assertIsInstance(session_id, int)
        self.assertEqual(self.db_manager.current_session_id, session_id)

    def test_telemetry_save(self):
        """Telemetri kaydetme testi"""
        # Önce oturum başlat
        self.db_manager.start_flight_session("Test Session")

        # Test telemetri paketi oluştur
        gps = GPSData(latitude=40.0, longitude=33.0, altitude=200.0)
        packet = TelemetryPacket(
            timestamp=datetime.now(),
            gps=gps,
            velocity=15.0,
            battery_voltage=23.5,
            battery_percent=75.0,
            status="CRUISING"
        )

        # Kaydetme testi
        result = self.db_manager.save_telemetry(packet)
        self.assertTrue(result)

    def test_get_database_info(self):
        """Veritabanı bilgi alma testi"""
        info = self.db_manager.get_database_info()

        self.assertIn('database_path', info)
        self.assertIn('total_sessions', info)
        self.assertIn('total_records', info)
        self.assertIsInstance(info['total_sessions'], int)


class TestMAVLinkManager(unittest.TestCase):
    """MAVLink yöneticisi testleri"""

    def setUp(self):
        """Test öncesi hazırlık"""
        self.mavlink_manager = MAVLinkManager()

    def tearDown(self):
        """Test sonrası temizlik"""
        if self.mavlink_manager:
            self.mavlink_manager.stop_listening()

    def test_mavlink_manager_creation(self):
        """MAVLink manager oluşturma testi"""
        self.assertIsNotNone(self.mavlink_manager)
        self.assertFalse(self.mavlink_manager.is_running)

    def test_simulated_connection(self):
        """Simüle bağlantı testi"""
        result = self.mavlink_manager.create_simulated_connection()
        self.assertTrue(result)
        self.assertTrue(self.mavlink_manager.is_connected)
        self.assertIsNone(self.mavlink_manager.connection)  # Simüle modda None olmalı

    def test_connection_status(self):
        """Bağlantı durumu testi"""
        self.mavlink_manager.create_simulated_connection()
        status = self.mavlink_manager.get_connection_status()

        self.assertIn('connected', status)
        self.assertIn('running', status)
        self.assertIn('connection_type', status)
        self.assertEqual(status['connection_type'], 'Simulated')

    def test_callback_assignment(self):
        """Callback atama testi"""

        def dummy_callback(data):
            pass

        self.mavlink_manager.on_gps_data = dummy_callback
        self.assertEqual(self.mavlink_manager.on_gps_data, dummy_callback)


if __name__ == '__main__':
    # Test suite oluştur
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Test sınıflarını ekle
    suite.addTests(loader.loadTestsFromTestCase(TestTelemetryDataModels))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMAVLinkManager))

    # Testleri çalıştır
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Sonuçları yazdır
    print(f"\nTest Sonuçları:")
    print(f"Toplam test: {result.testsRun}")
    print(f"Başarısız: {len(result.failures)}")
    print(f"Hata: {len(result.errors)}")
    print(
        f"Başarı oranı: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")